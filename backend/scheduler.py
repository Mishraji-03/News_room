"""
AutoNews AI - Scheduler v3.0 (Enterprise Ready)
Advanced scheduler with timezone support (IST), missed run recovery,
persistent state, graceful shutdown, retries, rate limiting,
and overlap prevention.
"""

import sys
import time
import signal
import logging
import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from threading import Lock

import schedule

import config
from pipeline import run_pipeline

# ========================== LOGGING ==========================
LOG_DIR = Path(config.LOGS_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scheduler.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
    force=True,
)
log = logging.getLogger("scheduler")

# ========================== TIMEZONE ==========================
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist() -> datetime:
    return datetime.now(IST)

# ========================== CONFIGURATION ==========================
SLOTS = getattr(config, "SCHEDULE_SLOTS", ["06:00", "12:00", "17:00", "19:00"])
VIDEOS_PER_RUN = getattr(config, "VIDEOS_PER_DAY", 1)
MIN_INTERVAL_MINUTES = getattr(config, "SCHEDULER_MIN_INTERVAL", 30)   # Avoid back-to-back runs
MAX_RETRIES = getattr(config, "SCHEDULER_MAX_RETRIES", 2)
RETRY_DELAY_MINUTES = getattr(config, "SCHEDULER_RETRY_DELAY", 5)

# ========================== STATE MANAGEMENT ==========================
STATE_FILE = Path(config.DATA_DIR) / "scheduler_state.json"
RUN_LOCK_FILE = Path(config.DATA_DIR) / "scheduler.lock"
lock = Lock()


class SchedulerState:
    def __init__(self):
        self.last_runs: Dict[str, str] = {}       # key: "YYYY-MM-DD_HH:MM"
        self.run_attempts: Dict[str, int] = {}    # track retries
        self.total_runs: int = 0
        self.successful_runs: int = 0
        self.videos_generated: int = 0
        self.last_run_at: Optional[str] = None
        self.last_run_success: bool = False

    @classmethod
    def load(cls) -> "SchedulerState":
        state = cls()
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                state.last_runs = data.get("last_runs", {})
                state.run_attempts = data.get("run_attempts", {})
                state.total_runs = data.get("total_runs", 0)
                state.successful_runs = data.get("successful_runs", 0)
                state.videos_generated = data.get("videos_generated", 0)
                state.last_run_at = data.get("last_run_at")
                state.last_run_success = data.get("last_run_success", False)
            except Exception as e:
                log.warning(f"Failed to load scheduler state: {e}")
        return state

    def save(self):
        data = {
            "last_runs": self.last_runs,
            "run_attempts": self.run_attempts,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "videos_generated": self.videos_generated,
            "last_run_at": self.last_run_at,
            "last_run_success": self.last_run_success,
            "updated_at": now_ist().isoformat(),
        }
        try:
            STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            log.warning(f"Failed to save scheduler state: {e}")


state = SchedulerState.load()


# ========================== RUN LOCK (Prevent Overlap) ==========================
def acquire_run_lock() -> bool:
    """Acquire a lock file to prevent concurrent runs."""
    try:
        if RUN_LOCK_FILE.exists():
            lock_age = time.time() - RUN_LOCK_FILE.stat().st_mtime
            if lock_age < 3600:  # Lock older than 1 hour -> stale, remove
                log.warning("Run lock exists but is recent. Another run may be in progress.")
                return False
            else:
                log.warning("Stale lock detected (>1 hour). Removing.")
                RUN_LOCK_FILE.unlink()
        RUN_LOCK_FILE.write_text(str(now_ist().timestamp()))
        return True
    except Exception as e:
        log.error(f"Failed to acquire run lock: {e}")
        return False


def release_run_lock():
    """Release the run lock."""
    try:
        if RUN_LOCK_FILE.exists():
            RUN_LOCK_FILE.unlink()
    except Exception:
        pass


# ========================== RATE LIMITING ==========================
def is_too_soon() -> bool:
    """Prevent runs if last run was within MIN_INTERVAL_MINUTES."""
    if state.last_run_at is None:
        return False
    last = datetime.fromisoformat(state.last_run_at)
    if last.tzinfo is None:
        last = last.replace(tzinfo=IST)
    elapsed = (now_ist() - last).total_seconds() / 60
    return elapsed < MIN_INTERVAL_MINUTES


# ========================== CORE RUNNER WITH RETRY ==========================
def run_pipeline_with_retry(slot: Optional[str] = None, is_retry: bool = False) -> bool:
    """Execute pipeline with retry logic. Returns True if successful."""
    if not is_retry and is_too_soon():
        log.warning(f"Rate limit: last run was less than {MIN_INTERVAL_MINUTES} minutes ago. Skipping.")
        return False

    if not acquire_run_lock():
        log.warning("Another pipeline run is already in progress. Skipping.")
        return False

    start_time = now_ist()
    run_id = start_time.strftime("%Y%m%d_%H%M%S")
    slot_info = f" (slot: {slot})" if slot else ""
    log.info(f"⏰ Starting run {run_id}{slot_info} at {start_time.strftime('%I:%M %p IST')}")

    success = False
    videos_produced = 0
    error_msg = None

    try:
        results = run_pipeline(auto_upload=False, max_videos=VIDEOS_PER_RUN)
        videos_produced = sum(1 for r in results if r.get("status") in ("pending_approval", "uploaded", "ready"))
        success = videos_produced > 0

        # Update state
        state.total_runs += 1
        if success:
            state.successful_runs += 1
            state.videos_generated += videos_produced
        state.last_run_at = start_time.isoformat()
        state.last_run_success = success

        # Mark slot as completed (or attempted)
        today_key = f"{start_time.date().isoformat()}_{slot or start_time.strftime('%H:%M')}"
        state.last_runs[today_key] = start_time.isoformat()
        if not success:
            # Track retry attempts
            state.run_attempts[today_key] = state.run_attempts.get(today_key, 0) + 1
        else:
            # Clear attempts on success
            state.run_attempts.pop(today_key, None)

        state.save()

        log.info(f"✅ Run completed | Success: {success} | Videos: {videos_produced}")

        # Log summary
        for i, result in enumerate(results[:5]):
            status = result.get("status", "unknown")
            title = result.get("news", {}).get("title", "Untitled")[:65]
            log.info(f"   {i+1:02d}. [{status.upper()}] {title}")

    except Exception as e:
        error_msg = str(e)
        log.exception(f"❌ Critical error during run: {e}")
        state.total_runs += 1
        state.save()
        success = False

    finally:
        release_run_lock()

    # Retry logic (only if this is not already a retry and failure)
    if not success and not is_retry and MAX_RETRIES > 0:
        log.warning(f"Run failed. Will retry up to {MAX_RETRIES} times after {RETRY_DELAY_MINUTES} minutes.")
        # Schedule a retry job (simple sleep in separate thread)
        import threading
        def retry_job():
            time.sleep(RETRY_DELAY_MINUTES * 60)
            log.info(f"Retrying failed run (original slot: {slot})")
            run_pipeline_with_retry(slot=slot, is_retry=True)
        threading.Thread(target=retry_job, daemon=True).start()

    return success


# ========================== SCHEDULED RUN WRAPPER ==========================
def scheduled_run(slot: str):
    """Wrapper for scheduled execution."""
    run_pipeline_with_retry(slot=slot, is_retry=False)


# ========================== MISSED RUN RECOVERY ==========================
def recover_missed_runs():
    """Detect and recover any missed scheduled runs (with retry tracking)."""
    log.info("🔍 Checking for missed scheduled runs...")
    today = now_ist().date().isoformat()

    for slot in SLOTS:
        key = f"{today}_{slot}"
        if key not in state.last_runs:
            slot_dt = datetime.strptime(slot, "%H:%M").time()
            expected = datetime.combine(now_ist().date(), slot_dt, tzinfo=IST)
            if expected <= now_ist():
                # Check if we've already attempted and failed too many times
                attempts = state.run_attempts.get(key, 0)
                if attempts >= MAX_RETRIES:
                    log.warning(f"Slot {slot} IST already failed {MAX_RETRIES} times. Skipping.")
                    continue
                log.warning(f"⚠️ Missed run detected for {slot} IST → Executing now (attempt {attempts+1})")
                run_pipeline_with_retry(slot=slot, is_retry=False)


# ========================== SCHEDULING ==========================
def setup_schedule():
    schedule.clear()
    for slot in SLOTS:
        schedule.every().day.at(slot).do(scheduled_run, slot=slot)
        log.info(f"📅 Scheduled daily pipeline at {slot} IST")


# ========================== HEALTH STATUS ==========================
def print_health_status():
    log.info("=" * 70)
    log.info("📊 SCHEDULER HEALTH STATUS")
    log.info("=" * 70)
    log.info(f"Total Runs       : {state.total_runs}")
    log.info(f"Successful Runs  : {state.successful_runs}")
    log.info(f"Videos Generated : {state.videos_generated}")
    log.info(f"Success Rate     : {(state.successful_runs/state.total_runs*100):.1f}%" if state.total_runs > 0 else "N/A")
    log.info(f"Last Run         : {state.last_run_at or 'Never'}")
    log.info(f"Last Run Success : {state.last_run_success}")
    log.info(f"Next Runs        : {[job.next_run.strftime('%H:%M') for job in schedule.jobs if job.next_run]}")
    log.info("=" * 70)


# ========================== GRACEFUL SHUTDOWN ==========================
def graceful_shutdown(signum, frame):
    log.info(f"\n🛑 Shutdown signal received (signal {signum}). Saving state and exiting.")
    print_health_status()
    state.save()
    sys.exit(0)


# ========================== MAIN ==========================
def main():
    # Register graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    log.info("=" * 70)
    log.info("🚀 AutoNews AI Scheduler v3.0 Started")
    log.info(f"Channel          : {getattr(config, 'CHANNEL_NAME', 'AutoNews AI')}")
    log.info(f"Timezone         : IST (UTC+5:30)")
    log.info(f"Scheduled Slots  : {SLOTS}")
    log.info(f"Min interval     : {MIN_INTERVAL_MINUTES} minutes")
    log.info(f"Max retries      : {MAX_RETRIES} (delay {RETRY_DELAY_MINUTES} min)")
    log.info("=" * 70)

    # Command line modes
    if "--once" in sys.argv:
        log.info("🔧 Running pipeline once (manual trigger)")
        run_pipeline_with_retry(slot="manual", is_retry=False)
        return

    if "--test" in sys.argv:
        log.info("🔧 TEST MODE - Running pipeline immediately")
        run_pipeline_with_retry(slot="test", is_retry=False)
        return

    # Normal scheduled mode
    setup_schedule()
    recover_missed_runs()
    print_health_status()

    log.info("✅ Scheduler is running. Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        graceful_shutdown(0, None)


if __name__ == "__main__":
    main()