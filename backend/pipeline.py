"""
AutoNews AI - Main Pipeline Orchestrator
Connects all agents: Scrape → Verify → Script → Video → Upload

This is the brain of the system. It runs the full pipeline
from trending news detection to video upload.
"""
import json
import logging
from datetime import datetime
from pathlib import Path

import config
from news_scraper import get_trending_news
from fact_checker import filter_news
from script_writer import generate_script, generate_seo_metadata
from video_maker import create_video
from youtube_upload import upload_video, set_thumbnail
from insta_upload import upload_local_video

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "pipeline.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("pipeline")

# Pipeline state file
STATE_FILE = config.DATA_DIR / "pipeline_state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"runs": [], "total_videos": 0, "last_run": None}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def run_pipeline(auto_upload: bool = False, max_videos: int = 1) -> list[dict]:
    """
    Run the full content pipeline.

    Args:
        auto_upload: If True, upload directly without approval.
                     If False, save to queue for manual approval.
        max_videos: Maximum videos to produce in this run.

    Returns:
        List of pipeline results.
    """
    state = load_state()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    log.info(f"{'='*60}")
    log.info(f"Pipeline run started: {run_id}")
    log.info(f"Auto-upload: {auto_upload} | Max videos: {max_videos}")
    log.info(f"{'='*60}")

    # ── STEP 1: Fetch trending news ──────────────────────────
    log.info("STEP 1/6: Fetching trending news...")
    news_items = get_trending_news(max_results=max_videos * 3)

    if not news_items:
        log.warning("No trending news found. Aborting pipeline.")
        return results

    log.info(f"Found {len(news_items)} trending items")

    # ── STEP 2: Fact check & filter ──────────────────────────
    log.info("STEP 2/6: Fact checking...")
    verified_news = filter_news(news_items, min_score=50)

    if not verified_news:
        log.warning("No news passed fact check. Aborting pipeline.")
        return results

    log.info(f"{len(verified_news)} items passed fact check")

    # ── Process top items ────────────────────────────────────
    for i, news_item in enumerate(verified_news[:max_videos]):
        video_num = i + 1
        log.info(f"\n{'─'*40}")
        log.info(f"Processing video {video_num}/{max_videos}: {news_item['title'][:50]}")
        log.info(f"{'─'*40}")

        pipeline_result = {
            "run_id": run_id,
            "video_num": video_num,
            "news": news_item,
            "status": "started",
            "started_at": datetime.now().isoformat(),
        }

        # ── STEP 3: Generate script ─────────────────────────
        log.info(f"STEP 3/6: Generating script...")
        script_data = generate_script(news_item)

        if not script_data:
            log.error("Script generation failed")
            pipeline_result["status"] = "script_failed"
            results.append(pipeline_result)
            continue

        pipeline_result["script"] = script_data

        # SEO optimization
        seo_data = generate_seo_metadata(script_data)
        if seo_data:
            script_data.update({
                "title_youtube": seo_data.get("optimized_title", script_data.get("title_youtube", "")),
                "description": seo_data.get("optimized_description", script_data.get("description", "")),
                "tags": seo_data.get("optimized_tags", script_data.get("tags", [])),
            })

        # ── STEP 4: Create video ─────────────────────────────
        log.info(f"STEP 4/6: Creating video...")
        video_data = create_video(script_data)

        if not video_data or video_data.get("status") != "ready":
            log.error("Video creation failed")
            pipeline_result["status"] = "video_failed"
            results.append(pipeline_result)
            continue

        pipeline_result["video"] = video_data

        # ── STEP 5: Upload (or queue) ────────────────────────
        if auto_upload:
            log.info(f"STEP 5/6: Uploading to YouTube...")
            yt_result = upload_video(
                video_path=video_data["video_path"],
                title=script_data.get("title_youtube", news_item["title"]),
                description=script_data.get("description", ""),
                tags=script_data.get("tags", []),
            )

            if yt_result:
                pipeline_result["youtube"] = yt_result

                # Set thumbnail
                if video_data.get("thumbnail_path"):
                    set_thumbnail(yt_result["video_id"], video_data["thumbnail_path"])

            # Instagram
            log.info(f"STEP 5/6: Uploading to Instagram...")
            ig_result = upload_local_video(
                video_path=video_data["video_path"],
                caption=script_data.get("title_instagram", ""),
            )
            if ig_result:
                pipeline_result["instagram"] = ig_result

            pipeline_result["status"] = "uploaded"
        else:
            # Save to approval queue
            log.info(f"STEP 5/6: Saved to approval queue")
            queue_item = {
                "id": run_id + f"_{video_num}",
                "news": news_item,
                "script": script_data,
                "video": video_data,
                "status": "pending_approval",
                "created_at": datetime.now().isoformat(),
            }
            queue_file = config.DATA_DIR / "approval_queue.json"
            queue = json.loads(queue_file.read_text(encoding="utf-8")) if queue_file.exists() else []
            queue.append(queue_item)
            queue_file.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")

            pipeline_result["status"] = "pending_approval"

        # ── STEP 6: Log analytics ────────────────────────────
        log.info(f"STEP 6/6: Logging results...")
        pipeline_result["completed_at"] = datetime.now().isoformat()
        results.append(pipeline_result)

    # Save state
    state["runs"].append({
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "videos_produced": len(results),
        "auto_uploaded": auto_upload,
    })
    state["total_videos"] += len([r for r in results if r["status"] in ["uploaded", "pending_approval"]])
    state["last_run"] = datetime.now().isoformat()
    save_state(state)

    log.info(f"\n{'='*60}")
    log.info(f"Pipeline run complete: {run_id}")
    log.info(f"Videos produced: {len(results)}")
    log.info(f"{'='*60}")

    return results


def approve_and_upload(queue_item_id: str) -> dict | None:
    """Approve a queued item and upload it."""
    queue_file = config.DATA_DIR / "approval_queue.json"
    if not queue_file.exists():
        log.error("No items in approval queue")
        return None

    queue = json.loads(queue_file.read_text(encoding="utf-8"))
    item = None
    for q in queue:
        if q["id"] == queue_item_id:
            item = q
            break

    if not item:
        log.error(f"Queue item not found: {queue_item_id}")
        return None

    # Upload to YouTube
    script = item.get("script", {})
    video = item.get("video", {})

    yt_result = upload_video(
        video_path=video.get("video_path", ""),
        title=script.get("title_youtube", ""),
        description=script.get("description", ""),
        tags=script.get("tags", []),
    )

    # Update queue
    item["status"] = "approved_uploaded" if yt_result else "upload_failed"
    item["youtube"] = yt_result
    item["approved_at"] = datetime.now().isoformat()
    queue_file.write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")

    return item


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        results = run_pipeline(auto_upload=True, max_videos=1)
    else:
        results = run_pipeline(auto_upload=False, max_videos=1)

    for r in results:
        print(f"\n[{r['status']}] {r['news']['title'][:50]}")
