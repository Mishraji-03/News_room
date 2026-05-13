"""
AutoNews AI - Scheduler
Runs the pipeline at scheduled times: 6AM, 12PM, 5PM, 7PM IST.
Uses the `schedule` library for simple cron-like scheduling.

USAGE:
  python scheduler.py          # Run scheduler (keeps running)
  python scheduler.py --once   # Run pipeline once and exit
"""
import sys
import time
import logging
from datetime import datetime

import schedule

import config
from pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "scheduler.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("scheduler")


def scheduled_run():
    """Run the pipeline for scheduled slot."""
    now = datetime.now()
    log.info(f"⏰ Scheduled run triggered at {now.strftime('%I:%M %p')}")

    try:
        results = run_pipeline(auto_upload=False, max_videos=1)
        for r in results:
            log.info(f"  → [{r['status']}] {r['news']['title'][:50]}")
    except Exception as e:
        log.error(f"Pipeline error: {e}")


def setup_schedule():
    """Setup daily schedule based on config."""
    for slot in config.SCHEDULE_SLOTS:
        schedule.every().day.at(slot).do(scheduled_run)
        log.info(f"📅 Scheduled: {slot} IST")


def main():
    if "--once" in sys.argv:
        log.info("Running pipeline once...")
        scheduled_run()
        return

    log.info(f"{'='*50}")
    log.info(f"AutoNews AI Scheduler Started")
    log.info(f"Channel: {config.CHANNEL_NAME}")
    log.info(f"Videos/day: {config.VIDEOS_PER_DAY}")
    log.info(f"{'='*50}")

    setup_schedule()

    log.info(f"\nWaiting for scheduled times...")
    log.info(f"Slots: {', '.join(config.SCHEDULE_SLOTS)}")
    log.info(f"Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
