"""
AutoNews AI - Instagram Upload v3.0
Robust Instagram Reels uploader using Meta Graph API with retries,
supervisor integration, and clear guidance for local video hosting.
"""

import json
import logging
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Tuple

import requests

import config

log = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

# Retry configuration
MAX_RETRIES = 3
INITIAL_DELAY = 2  # seconds
MAX_DELAY = 30

# Processing timeout (seconds)
PROCESSING_TIMEOUT = 360  # 6 minutes
PROCESSING_POLL_INTERVAL = 10


# ========================== CONFIG & HELPERS ==========================
def _get_credentials() -> Tuple[Optional[str], Optional[str]]:
    token = getattr(config, "META_ACCESS_TOKEN", None)
    account_id = getattr(config, "INSTAGRAM_ACCOUNT_ID", None)

    if not token or not account_id:
        log.error("❌ META_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID not configured!")
        return None, None
    return token, account_id


def _update_supervisor(agent_status: str, message: str):
    """Update supervisor agent status if available."""
    try:
        from supervisor import supervisor_state
        supervisor_state.update_agent("uploader", agent_status, message)
    except Exception:
        pass  # Supervisor may not be imported or function not available


def _request_with_retry(method: str, url: str, **kwargs) -> Optional[requests.Response]:
    """
    Make a request with exponential backoff retries.
    Returns Response object or None.
    """
    retries = MAX_RETRIES
    delay = INITIAL_DELAY
    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(method, url, timeout=kwargs.pop('timeout', 45), **kwargs)
            if resp.status_code >= 500:
                # Server error, retry
                raise requests.exceptions.HTTPError(f"Server error {resp.status_code}")
            resp.raise_for_status()
            return resp
        except Exception as e:
            log.warning(f"Request attempt {attempt}/{retries} failed: {e}")
            if attempt == retries:
                log.error(f"All {retries} attempts failed for {url}")
                return None
            time.sleep(delay)
            delay = min(delay * 2, MAX_DELAY)
    return None


# ========================== CORE UPLOAD ==========================
def upload_reel(video_url: str, caption: str, share_to_feed: bool = True) -> Optional[Dict[str, Any]]:
    """
    Upload Reel using a publicly accessible video URL.
    """
    token, account_id = _get_credentials()
    if not token or not account_id:
        return None

    _update_supervisor("active", "Creating Instagram media container...")

    try:
        # 1. Create Container
        container_url = f"{GRAPH_API_BASE}/{account_id}/media"
        container_data = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "share_to_feed": share_to_feed,
            "access_token": token,
        }

        resp = _request_with_retry("POST", container_url, data=container_data)
        if not resp:
            _update_supervisor("error", "Failed to create container after retries")
            return None

        container_id = resp.json().get("id")
        if not container_id:
            log.error("No container ID in response")
            _update_supervisor("error", "No container ID returned")
            return None

        log.info(f"✅ Media container created: {container_id}")
        _update_supervisor("active", "Video processing by Instagram...")

        # 2. Poll for processing completion
        status_url = f"{GRAPH_API_BASE}/{container_id}"
        start_time = time.time()
        attempt = 0
        while time.time() - start_time < PROCESSING_TIMEOUT:
            attempt += 1
            time.sleep(PROCESSING_POLL_INTERVAL)

            status_resp = _request_with_retry(
                "GET", status_url,
                params={"fields": "status_code", "access_token": token}
            )
            if not status_resp:
                continue

            status_code = status_resp.json().get("status_code")
            log.info(f"Processing status: {status_code} (attempt {attempt})")

            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                log.error("Instagram processing ERROR")
                _update_supervisor("error", "Processing error on Instagram side")
                return None
        else:
            log.error(f"Timeout waiting for video processing ({PROCESSING_TIMEOUT}s)")
            _update_supervisor("error", "Processing timeout")
            return None

        # 3. Publish
        _update_supervisor("active", "Publishing Reel...")
        publish_url = f"{GRAPH_API_BASE}/{account_id}/media_publish"
        publish_data = {
            "creation_id": container_id,
            "access_token": token,
        }

        pub_resp = _request_with_retry("POST", publish_url, data=publish_data)
        if not pub_resp:
            _update_supervisor("error", "Failed to publish after retries")
            return None

        media_id = pub_resp.json().get("id")
        if not media_id:
            log.error("No media ID in publish response")
            return None

        result = {
            "platform": "instagram",
            "media_id": media_id,
            "container_id": container_id,
            "status": "published",
            "uploaded_at": datetime.now().isoformat(),
        }

        log.info(f"🎉 Instagram Reel published! Media ID: {media_id}")
        _update_supervisor("done", f"Reel published (ID: {media_id[-8:]})")

        return result

    except Exception as e:
        log.exception("Unexpected error during Instagram upload")
        _update_supervisor("error", str(e)[:100])
        return None


# ========================== LOCAL VIDEO UPLOAD ==========================
def upload_local_video(video_path: str | Path, caption: str, hosting_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Upload local video. Requires public URL.
    For production, host on Cloudinary, AWS S3, or similar.
    """
    video_path = Path(video_path)

    if not video_path.exists():
        log.error(f"Video file not found: {video_path}")
        _update_supervisor("error", "Video file not found")
        return None

    if hosting_url:
        log.info(f"Using provided public URL: {hosting_url[:80]}...")
        return upload_reel(hosting_url, caption)

    # No public URL provided – give actionable instructions
    file_size_mb = video_path.stat().st_size / (1024 * 1024)
    log.warning("⚠️ Instagram requires a **publicly accessible** video URL.")
    log.warning("Recommended free/cheap solutions:")
    log.warning("   1. Cloudinary (free tier: 25 credits/month, easy upload)")
    log.warning("   2. Firebase Storage (free 5GB)")
    log.warning("   3. AWS S3 + CloudFront (pay-as-you-go, very cheap)")
    log.warning("   4. Railway.app static hosting")
    log.warning(f"   Current file: {video_path.name} ({file_size_mb:.1f} MB)")
    log.warning("   For testing, you can upload to a public server and pass the URL via hosting_url argument")
    _update_supervisor("error", "No public URL for local video")
    return None


# ========================== ASYNC VERSIONS ==========================
async def upload_reel_async(video_url: str, caption: str, share_to_feed: bool = True) -> Optional[Dict[str, Any]]:
    """Async wrapper for upload_reel (runs in thread pool)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, upload_reel, video_url, caption, share_to_feed)


async def upload_local_video_async(video_path: str | Path, caption: str, hosting_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Async wrapper for upload_local_video."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, upload_local_video, video_path, caption, hosting_url)


# ========================== ACCOUNT INSIGHTS ==========================
def get_account_insights() -> Optional[Dict[str, Any]]:
    """Fetch Instagram Business Account basic info."""
    token, account_id = _get_credentials()
    if not token or not account_id:
        return None

    try:
        url = f"{GRAPH_API_BASE}/{account_id}"
        params = {
            "fields": "username,followers_count,media_count,biography,name",
            "access_token": token,
        }
        resp = _request_with_retry("GET", url, params=params)
        if not resp:
            return None

        data = resp.json()
        return {
            "username": data.get("username"),
            "followers": data.get("followers_count", 0),
            "total_posts": data.get("media_count", 0),
            "biography": data.get("biography"),
            "name": data.get("name"),
            "fetched_at": datetime.now().isoformat(),
        }
    except Exception as e:
        log.error(f"Failed to fetch Instagram insights: {e}")
        return None


# ========================== CLI TEST ==========================
if __name__ == "__main__":
    print("Instagram Upload Module v3.0")
    print("=" * 55)

    insights = get_account_insights()
    if insights:
        print(f"✅ Connected to Instagram Account: @{insights['username']}")
        print(f"   Followers : {insights['followers']:,}")
        print(f"   Posts     : {insights['total_posts']}")
    else:
        print("❌ Not configured. Please set META_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in config.py")