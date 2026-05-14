"""
AutoNews AI - Advanced Pipeline Orchestrator v2.2
Production-ready news-to-video pipeline with robust error handling.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
from news_scraper import get_trending_news
from fact_checker import filter_news
from script_writer import generate_script, generate_seo_metadata
from video_maker import create_video
from youtube_upload import upload_video, set_thumbnail
from insta_upload import upload_local_video


# ========================== ENUMS ==========================
class PipelineStatus(str, Enum):
    STARTED = "started"
    SCRIPT_FAILED = "script_failed"
    VIDEO_FAILED = "video_failed"
    UPLOADED = "uploaded"
    PENDING_APPROVAL = "pending_approval"
    FAILED = "failed"


class QueueStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED_UPLOADED = "approved_uploaded"
    UPLOAD_FAILED = "upload_failed"


# ========================== MODELS ==========================
@dataclass
class PipelineRun:
    run_id: str
    timestamp: str
    videos_produced: int
    auto_uploaded: bool
    successful: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> PipelineRun:
        """Create PipelineRun from dict, providing default for older state files."""
        return cls(
            run_id=data["run_id"],
            timestamp=data["timestamp"],
            videos_produced=data["videos_produced"],
            auto_uploaded=data["auto_uploaded"],
            successful=data.get("successful", 0)
        )


@dataclass
class PipelineState:
    runs: List[PipelineRun] = field(default_factory=list)
    total_videos: int = 0
    last_run: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> PipelineState:
        runs = [PipelineRun.from_dict(r) for r in data.get("runs", [])]
        return cls(
            runs=runs,
            total_videos=data.get("total_videos", 0),
            last_run=data.get("last_run")
        )

    def to_dict(self) -> dict:
        return {
            "runs": [asdict(r) for r in self.runs[-100:]],  # Keep last 100 runs
            "total_videos": self.total_videos,
            "last_run": self.last_run,
        }


# ========================== LOGGING ==========================
def setup_logging() -> logging.Logger:
    log_dir = Path(config.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    return logging.getLogger("pipeline")


log = setup_logging()


# ========================== FILE HELPERS ==========================
DATA_PATH = Path(config.DATA_DIR)
STATE_FILE = DATA_PATH / "pipeline_state.json"
QUEUE_FILE = DATA_PATH / "approval_queue.json"


def atomic_write_json(file_path: Path, data: Any) -> None:
    """Write JSON atomically to prevent corruption."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_suffix(".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(file_path)
    except Exception:
        # Clean up temporary file on failure
        tmp_path.unlink(missing_ok=True)
        raise


def load_json_file(file_path: Path, default: Any = None) -> Any:
    """Load JSON from file. Returns default if file missing or corrupt."""
    if not file_path.exists():
        return default if default is not None else ([] if isinstance(default, list) else {})
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        log.exception(f"Failed to load {file_path}")
        return default if default is not None else ([] if isinstance(default, list) else {})


# ========================== CORE PIPELINE ==========================
def run_pipeline(auto_upload: bool = False, max_videos: int = 1) -> List[Dict[str, Any]]:
    """Main pipeline entry point."""
    state = load_state()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results: List[Dict[str, Any]] = []

    log.info("=" * 80)
    log.info(f"🚀 PIPELINE STARTED | Run ID: {run_id} | Auto-upload: {auto_upload} | Max: {max_videos}")
    log.info("=" * 80)

    # Step 1: Trending News
    news_items = _fetch_trending_news(max_videos)
    if not news_items:
        return results

    # Step 2: Fact Checking
    verified_news = _filter_verified_news(news_items)
    if not verified_news:
        return results

    # Process each video
    for i, news_item in enumerate(verified_news[:max_videos]):
        result = _process_single_item(run_id, i + 1, news_item, auto_upload, max_videos)
        results.append(result)

    # Update state
    successful = sum(1 for r in results if r["status"] in (PipelineStatus.UPLOADED.value, PipelineStatus.PENDING_APPROVAL.value))
    
    state.runs.append(PipelineRun(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        videos_produced=len(results),
        auto_uploaded=auto_upload,
        successful=successful
    ))
    state.total_videos += successful
    state.last_run = datetime.now().isoformat()

    save_state(state)

    log.info("=" * 80)
    log.info(f"🏁 PIPELINE COMPLETED | Run: {run_id} | Videos: {len(results)} | Successful: {successful}")
    log.info("=" * 80)

    return results


def _fetch_trending_news(max_results: int) -> List[Dict]:
    log.info("📡 STEP 1/6: Fetching trending news...")
    try:
        news_items = get_trending_news(max_results=max_results * 3)
        if not news_items:
            log.warning("⚠️ No trending news found.")
            return []
        log.info(f"✅ Found {len(news_items)} trending items")
        return news_items
    except Exception as e:
        log.exception(f"❌ News fetching failed: {e}")
        return []


def _filter_verified_news(news_items: List[Dict]) -> List[Dict]:
    log.info("🔍 STEP 2/6: Fact checking...")
    try:
        verified = filter_news(news_items, min_score=50)
        if not verified:
            log.warning("⚠️ No news passed fact check.")
            return []
        log.info(f"✅ {len(verified)} items passed verification")
        return verified
    except Exception as e:
        log.exception(f"❌ Fact checker failed: {e}")
        return []


def _process_single_item(run_id: str, video_num: int, news_item: Dict, 
                        auto_upload: bool, max_videos: int) -> Dict[str, Any]:
    """Process one news item through the full pipeline."""
    log.info(f"\n{'─' * 60}")
    log.info(f"🎬 Processing Video {video_num}/{max_videos}: {news_item.get('title', '')[:70]}")
    log.info(f"{'─' * 60}")

    result: Dict[str, Any] = {
        "run_id": run_id,
        "video_num": video_num,
        "news": news_item,
        "status": PipelineStatus.STARTED.value,
        "started_at": datetime.now().isoformat(),
    }

    try:
        # Step 3: Script
        script_data = _generate_script_with_seo(news_item, result)
        if not script_data:
            return result

        # Step 4: Video
        video_data = _create_video(script_data, result)
        if not video_data:
            return result

        # Step 5: Upload / Queue
        if auto_upload:
            _upload_to_platforms(script_data, video_data, result)
            result["status"] = PipelineStatus.UPLOADED.value
        else:
            _save_to_queue(run_id, video_num, news_item, script_data, video_data)
            result["status"] = PipelineStatus.PENDING_APPROVAL.value

    except Exception as e:
        log.exception(f"Unexpected error processing video {video_num}")
        result["status"] = PipelineStatus.FAILED.value
        result["error"] = str(e)

    finally:
        result["completed_at"] = datetime.now().isoformat()

    log.info(f"✅ Completed: {result['status']}")
    return result


# ====================== Private Helpers ======================
def _generate_script_with_seo(news_item: Dict, result: Dict) -> Optional[Dict]:
    log.info("✍️ STEP 3/6: Generating script...")
    try:
        script_data = generate_script(news_item)
        if not script_data:
            result["status"] = PipelineStatus.SCRIPT_FAILED.value
            return None

        # SEO (non-blocking)
        try:
            seo = generate_seo_metadata(script_data)
            if seo:
                script_data.update({
                    "title_youtube": seo.get("optimized_title", script_data.get("title_youtube")),
                    "description": seo.get("optimized_description", script_data.get("description")),
                    "tags": seo.get("optimized_tags", script_data.get("tags", [])),
                })
        except Exception as e:
            log.warning(f"SEO generation failed (continuing): {e}")

        result["script"] = script_data
        return script_data

    except Exception as e:
        log.exception("Script generation failed")
        result["status"] = PipelineStatus.SCRIPT_FAILED.value
        return None


def _create_video(script_data: Dict, result: Dict) -> Optional[Dict]:
    log.info("🎥 STEP 4/6: Creating video...")
    try:
        video_data = create_video(script_data)
        if not video_data or video_data.get("status") != "ready":
            result["status"] = PipelineStatus.VIDEO_FAILED.value
            return None

        result["video"] = video_data
        return video_data
    except Exception as e:
        log.exception("Video creation failed")
        result["status"] = PipelineStatus.VIDEO_FAILED.value
        return None


def _upload_to_platforms(script: Dict, video: Dict, result: Dict) -> None:
    """
    Upload to YouTube & Instagram, storing results/errors in the 'result' dict.
    """
    log.info("📤 STEP 5/6: Uploading to platforms...")

    # YouTube
    try:
        yt_result = upload_video(
            video_path=video["video_path"],
            title=script.get("title_youtube", ""),
            description=script.get("description", ""),
            tags=script.get("tags", []),
        )
        if yt_result:
            result["youtube"] = yt_result
            if video.get("thumbnail_path"):
                set_thumbnail(yt_result.get("video_id"), video["thumbnail_path"])
    except Exception as e:
        log.exception("YouTube upload failed")
        result["youtube_error"] = str(e)

    # Instagram
    try:
        ig_result = upload_local_video(
            video_path=video["video_path"],
            caption=script.get("title_instagram", script.get("title", "")),
        )
        if ig_result:
            result["instagram"] = ig_result
    except Exception as e:
        log.exception("Instagram upload failed")
        result["instagram_error"] = str(e)


def _save_to_queue(run_id: str, video_num: int, news: Dict, script: Dict, video: Dict) -> None:
    log.info("📋 STEP 5/6: Saving to approval queue")
    queue = load_json_file(QUEUE_FILE, [])
    queue.append({
        "id": f"{run_id}_{video_num}",
        "news": news,
        "script": script,
        "video": video,
        "status": QueueStatus.PENDING_APPROVAL.value,
        "created_at": datetime.now().isoformat(),
    })
    atomic_write_json(QUEUE_FILE, queue)


# ========================== STATE HELPERS ==========================
def load_state() -> PipelineState:
    data = load_json_file(STATE_FILE, {})
    return PipelineState.from_dict(data)


def save_state(state: PipelineState) -> None:
    atomic_write_json(STATE_FILE, state.to_dict())


# ========================== APPROVAL ==========================
def approve_and_upload(queue_item_id: str) -> Optional[Dict[str, Any]]:
    """Approve a queued item and upload it."""
    queue = load_json_file(QUEUE_FILE, [])
    item = next((q for q in queue if q.get("id") == queue_item_id), None)

    if not item:
        log.error(f"Queue item {queue_item_id} not found")
        return None

    script = item.get("script", {})
    video = item.get("video", {})

    log.info(f"Approving & uploading: {queue_item_id}")

    try:
        _upload_to_platforms(script, video, item)
        item["status"] = QueueStatus.APPROVED_UPLOADED.value
        item["approved_at"] = datetime.now().isoformat()
        log.info(f"✅ Successfully uploaded {queue_item_id}")
    except Exception as e:
        log.exception(f"Upload failed for {queue_item_id}")
        item["status"] = QueueStatus.UPLOAD_FAILED.value
        item["error"] = str(e)

    atomic_write_json(QUEUE_FILE, queue)
    return item


# ========================== CLI ==========================
if __name__ == "__main__":
    import sys

    auto_flag = "--auto" in sys.argv
    max_videos = 1

    # Parse --max-videos argument if present
    for i, arg in enumerate(sys.argv):
        if arg == "--max-videos" and i + 1 < len(sys.argv):
            try:
                max_videos = int(sys.argv[i + 1])
            except ValueError:
                pass

    results = run_pipeline(auto_upload=auto_flag, max_videos=max_videos)

    for r in results:
        print(f"[{r['status'].upper()}] {r.get('news', {}).get('title', '')[:60]}")