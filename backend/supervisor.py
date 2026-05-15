"""
AutoNews AI - Team Leader (Supervisor) Agent v2.0
Oversees the entire pipeline, handles retries, and maintains global state for the dashboard.
Features: thread-safe state, cancellation support, exponential backoff, run persistence.
"""
import logging
import time
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

import config


# Optional: use tenacity for robust retries
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

log = logging.getLogger("supervisor")

# ========================== GLOBAL STATE (Thread-safe) ==========================
class SupervisorState:
    """Thread-safe container for supervisor state."""
    def __init__(self):
        self._lock = threading.RLock()
        self._is_running = False
        self._cancel_requested = False
        self._current_task = "Idle"
        self._run_id = None
        self._agents = {
            "scraper": {"status": "idle", "message": "Waiting..."},
            "fact_checker": {"status": "idle", "message": "Waiting..."},
            "script_writer": {"status": "idle", "message": "Waiting..."},
            "video_maker": {"status": "idle", "message": "Waiting..."},
            "uploader": {"status": "idle", "message": "Waiting..."},
        }
        self._logs = []  # list of {"timestamp": ..., "message": ...}
        self._max_logs = 500  # keep last 500 logs

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._is_running

    @is_running.setter
    def is_running(self, value: bool):
        with self._lock:
            self._is_running = value

    @property
    def cancel_requested(self) -> bool:
        with self._lock:
            return self._cancel_requested

    def request_cancel(self):
        with self._lock:
            self._cancel_requested = True

    def reset_cancel(self):
        with self._lock:
            self._cancel_requested = False

    @property
    def current_task(self) -> str:
        with self._lock:
            return self._current_task

    @current_task.setter
    def current_task(self, value: str):
        with self._lock:
            self._current_task = value

    @property
    def run_id(self) -> Optional[str]:
        with self._lock:
            return self._run_id

    @run_id.setter
    def run_id(self, value: Optional[str]):
        with self._lock:
            self._run_id = value

    def get_agents(self) -> Dict:
        with self._lock:
            return self._agents.copy()

    def get_logs(self) -> List:
        with self._lock:
            return self._logs.copy()

    def update_agent(self, agent_name: str, status: str, message: str):
        with self._lock:
            if agent_name in self._agents:
                self._agents[agent_name] = {"status": status, "message": message}
            log_msg = f"[{agent_name.upper()}] {status.upper()}: {message}"
            log.info(log_msg)
            self._logs.append({"timestamp": datetime.now().isoformat(), "message": log_msg})
            # Trim logs
            if len(self._logs) > self._max_logs:
                self._logs = self._logs[-self._max_logs:]

    def add_log(self, message: str):
        with self._lock:
            log_entry = {"timestamp": datetime.now().isoformat(), "message": message}
            self._logs.append(log_entry)
            if len(self._logs) > self._max_logs:
                self._logs = self._logs[-self._max_logs:]

    def reset(self):
        """Reset state for a new run."""
        with self._lock:
            self._is_running = False
            self._cancel_requested = False
            self._current_task = "Idle"
            self._run_id = None
            self._agents = {
                "scraper": {"status": "idle", "message": "Waiting..."},
                "fact_checker": {"status": "idle", "message": "Waiting..."},
                "script_writer": {"status": "idle", "message": "Waiting..."},
                "video_maker": {"status": "idle", "message": "Waiting..."},
                "uploader": {"status": "idle", "message": "Waiting..."},
            }
            # Keep logs (optional)
            self.add_log("Supervisor state reset.")


# Global instance
supervisor_state = SupervisorState()

# Optional SSE broadcast callback (set by FastAPI)
_broadcast_callback: Optional[Callable[[str], None]] = None

def set_broadcast_callback(callback: Callable[[str], None]):
    """Register a function to broadcast state updates (e.g., via SSE)."""
    global _broadcast_callback
    _broadcast_callback = callback

def _broadcast(message: str = None):
    """Send current state as JSON via callback if registered."""
    if _broadcast_callback:
        data = {
            "is_running": supervisor_state.is_running,
            "current_task": supervisor_state.current_task,
            "run_id": supervisor_state.run_id,
            "agents": supervisor_state.get_agents(),
            "logs": supervisor_state.get_logs()[-20:],  # last 20 logs
        }
        _broadcast_callback(json.dumps(data))


# ========================== RETRY HELPER ==========================
def run_with_retry(agent_name: str, func: Callable, *args, max_retries: int = 3, **kwargs) -> Any:
    """
    Execute agent function with retries and exponential backoff.
    Returns function result or None if all retries fail.
    """
    if TENACITY_AVAILABLE:
        # Use tenacity for cleaner retries
        @retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(Exception),
            reraise=False
        )
        def _wrapped():
            supervisor_state.update_agent(agent_name, "active", f"Attempting...")
            result = func(*args, **kwargs)
            if result is None or (isinstance(result, (list, dict)) and not result):
                raise ValueError(f"{agent_name} returned empty result")
            return result

        try:
            result = _wrapped()
            supervisor_state.update_agent(agent_name, "done", "Completed successfully")
            return result
        except Exception as e:
            supervisor_state.update_agent(agent_name, "failed", f"All retries exhausted: {str(e)[:100]}")
            log.error(f"{agent_name} failed after {max_retries} attempts: {e}")
            return None
    else:
        # Fallback manual retry with exponential backoff
        for attempt in range(1, max_retries + 1):
            try:
                supervisor_state.update_agent(agent_name, "active", f"Attempt {attempt}/{max_retries}...")
                result = func(*args, **kwargs)
                if result is None or (isinstance(result, (list, dict)) and not result):
                    raise ValueError(f"{agent_name} returned empty result")
                supervisor_state.update_agent(agent_name, "done", "Completed successfully")
                return result
            except Exception as e:
                supervisor_state.update_agent(agent_name, "error", f"Error: {str(e)}")
                log.error(f"{agent_name} failed on attempt {attempt}: {e}")
                if attempt < max_retries:
                    delay = 2 ** (attempt - 1)  # 1, 2, 4 seconds
                    supervisor_state.update_agent(agent_name, "retrying", f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    supervisor_state.update_agent(agent_name, "failed", "Max retries reached.")
                    return None
        return None


# ========================== MAIN PIPELINE ORCHESTRATION ==========================
def start_pipeline_run(max_videos: int = 1, auto_upload: bool = False):
    """
    Main orchestration loop run by the Team Leader.
    This function runs synchronously – call it in a background thread.
    """
    if supervisor_state.is_running:
        log.warning("Supervisor is already running a pipeline. Use cancel_pipeline_run() first.")
        return

    # Reset and prepare
    supervisor_state.reset()
    supervisor_state.is_running = True
    supervisor_state.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    supervisor_state.current_task = "Initializing"
    supervisor_state.add_log(f"🚀 Team Leader starting pipeline run: {supervisor_state.run_id}")
    _broadcast()

    try:
        # Local imports to avoid circular dependency at load time
        from news_scraper import get_trending_news
        from fact_checker import filter_news
        from script_writer import generate_script, generate_seo_metadata
        from video_maker import create_video
        from youtube_upload import upload_video, set_thumbnail

        # ========== STEP 1: Scraper ==========
        if supervisor_state.cancel_requested:
            supervisor_state.add_log("❌ Pipeline cancelled by user.")
            return
        supervisor_state.current_task = "Scraping News"
        supervisor_state.add_log("📡 Step 1/5: Fetching trending news...")
        _broadcast()
        news_items = run_with_retry("scraper", get_trending_news, max_results=max_videos * 3)
        if not news_items:
            supervisor_state.add_log("❌ No trending news found. Pipeline aborted.")
            return
        supervisor_state.add_log(f"✅ Found {len(news_items)} trending articles")

        # ========== STEP 2: Fact Checker ==========
        if supervisor_state.cancel_requested:
            return
        supervisor_state.current_task = "Fact Checking"
        supervisor_state.add_log("🔍 Step 2/5: Verifying facts...")
        _broadcast()
        verified_news = run_with_retry("fact_checker", filter_news, news_list=news_items, min_score=50)
        if not verified_news:
            supervisor_state.add_log("❌ No news passed fact check. Pipeline aborted.")
            return
        supervisor_state.add_log(f"✅ {len(verified_news)} articles passed verification")

        results = []
        for i, news_item in enumerate(verified_news[:max_videos]):
            if supervisor_state.cancel_requested:
                break

            supervisor_state.add_log(f"📰 Processing: {news_item.get('title', '')[:60]}")
            _broadcast()

            # ========== STEP 3: Script Writer ==========
            supervisor_state.current_task = "Script Writing"
            supervisor_state.add_log("✍️ Step 3/5: Generating script...")
            _broadcast()
            script_data = run_with_retry("script_writer", generate_script, news_item=news_item)
            if not script_data:
                supervisor_state.add_log(f"⚠️ Script generation failed for item {i+1}. Skipping.")
                continue
            supervisor_state.add_log(f"✅ Script generated: {script_data.get('title_youtube', '')[:50]}")

            # SEO optimization (non-critical)
            try:
                seo_data = generate_seo_metadata(script_data)
                if seo_data:
                    script_data.update({
                        "title_youtube": seo_data.get("optimized_title", script_data.get("title_youtube", "")),
                        "description": seo_data.get("optimized_description", script_data.get("description", "")),
                        "tags": seo_data.get("optimized_tags", script_data.get("tags", [])),
                    })
            except Exception as e:
                log.warning(f"SEO optimization failed: {e}")

            # ========== STEP 4: Video Maker ==========
            supervisor_state.current_task = "Video Rendering"
            supervisor_state.add_log("🎬 Step 4/5: Creating video...")
            _broadcast()
            video_data = run_with_retry("video_maker", create_video, script_data=script_data)
            if not video_data or video_data.get("status") != "ready":
                supervisor_state.add_log(f"⚠️ Video creation failed for item {i+1}. Skipping.")
                continue
            supervisor_state.add_log(f"✅ Video ready: {video_data.get('video_id', '')}")

            # ========== STEP 5: Uploader / Queue ==========
            if auto_upload:
                supervisor_state.current_task = "Uploading Video"
                supervisor_state.add_log("📤 Step 5/5: Uploading to YouTube...")
                _broadcast()
                yt_result = run_with_retry(
                    "uploader",
                    upload_video,
                    video_path=video_data["video_path"],
                    title=script_data.get("title_youtube", news_item["title"]),
                    description=script_data.get("description", ""),
                    tags=script_data.get("tags", [])
                )
                if yt_result and video_data.get("thumbnail_path"):
                    try:
                        set_thumbnail(yt_result["video_id"], video_data["thumbnail_path"])
                    except Exception as e:
                        log.warning(f"Thumbnail set failed: {e}")
                supervisor_state.update_agent("uploader", "done", "Uploaded to YouTube")
            else:
                # Save to approval queue
                supervisor_state.current_task = "Saving to Queue"
                supervisor_state.add_log("📋 Step 5/5: Saving to approval queue...")
                supervisor_state.update_agent("uploader", "active", "Saving to approval queue...")
                queue_item = {
                    "id": supervisor_state.run_id + f"_{i+1}",
                    "news": news_item,
                    "script": script_data,
                    "video": video_data,
                    "status": "pending_approval",
                    "created_at": datetime.now().isoformat(),
                }
                queue_file = Path(config.DATA_DIR) / "approval_queue.json"
                try:
                    queue = json.loads(queue_file.read_text(encoding="utf-8")) if queue_file.exists() else []
                    queue.append(queue_item)
                    queue_file.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")
                    supervisor_state.update_agent("uploader", "done", "Saved to approval queue")
                    supervisor_state.add_log(f"✅ Video saved to approval queue — go to Content Queue to review")
                except Exception as e:
                    supervisor_state.update_agent("uploader", "error", f"Queue save failed: {e}")
                    continue

            results.append({"status": "completed", "video": video_data})

        supervisor_state.current_task = "Pipeline Finished"
        supervisor_state.add_log(f"🏁 Pipeline finished. Processed {len(results)} videos.")
        log.info(f"Team Leader finished pipeline. Videos: {len(results)}")

    except Exception as e:
        supervisor_state.add_log(f"💥 Unhandled error in pipeline: {e}")
        log.exception("Supervisor encountered critical error")
    finally:
        supervisor_state.is_running = False
        supervisor_state.reset_cancel()
        _broadcast()


def cancel_pipeline_run():
    """Request cancellation of the currently running pipeline."""
    if supervisor_state.is_running:
        supervisor_state.request_cancel()
        supervisor_state.add_log("🛑 Pipeline cancellation requested...")
        _broadcast()
        log.info("Pipeline cancellation requested.")
    else:
        log.warning("No pipeline running to cancel.")


def get_supervisor_state() -> Dict[str, Any]:
    """Return current state for dashboard API."""
    return {
        "is_running": supervisor_state.is_running,
        "current_task": supervisor_state.current_task,
        "run_id": supervisor_state.run_id,
        "agents": supervisor_state.get_agents(),
        "logs": supervisor_state.get_logs(),
    }


# ========================== CLI TEST ==========================
if __name__ == "__main__":
    # Simple test (does not require FastAPI)
    import sys
    if "--cancel" in sys.argv:
        cancel_pipeline_run()
    else:
        # Run in a separate thread to keep CLI responsive
        thread = threading.Thread(target=start_pipeline_run, kwargs={"max_videos": 1, "auto_upload": False})
        thread.start()
        # Wait for completion
        thread.join()
        print("Pipeline finished. Final state:")
        print(json.dumps(get_supervisor_state(), indent=2, default=str))