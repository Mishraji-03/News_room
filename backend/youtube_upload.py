"""
AutoNews AI - YouTube Upload v3.0
Robust YouTube Shorts uploader with resumable uploads, async support,
exponential backoff, supervisor integration, and clean error handling.
"""

import json
import logging
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import config

log = logging.getLogger(__name__)

# ========================== CONFIG ==========================
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

TOKEN_FILE = Path(config.DATA_DIR) / "youtube_token.json"
CLIENT_SECRETS_FILE = Path(config.BASE_DIR) / "client_secret.json"

UPLOAD_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB

# Retry settings
MAX_RETRIES = 3
INITIAL_DELAY = 2  # seconds
MAX_DELAY = 30


# ========================== SUPERVISOR INTEGRATION ==========================
def _update_supervisor(status: str, message: str):
    """Update uploader status in supervisor for dashboard."""
    try:
        from supervisor import supervisor_state
        supervisor_state.update_agent("uploader", status, message)
    except Exception:
        pass  # Supervisor not imported / not running


# ========================== AUTHENTICATION WITH RETRY ==========================
def get_youtube_service():
    """Return authenticated YouTube service with token management and retries."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
    except ImportError:
        log.error("Missing Google packages. Run: pip install google-api-python-client google-auth-oauthlib")
        return None

    creds = None
    retry_count = 0
    max_auth_retries = 2

    while retry_count <= max_auth_retries:
        # Load saved token
        if TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
            except Exception as e:
                log.warning(f"Failed to load saved token: {e}")

        # Refresh or re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    log.info("✅ YouTube token refreshed successfully")
                except Exception as e:
                    log.warning(f"Token refresh failed: {e}")
                    creds = None

            if not creds:
                if not CLIENT_SECRETS_FILE.exists():
                    log.error(f"❌ client_secret.json not found at {CLIENT_SECRETS_FILE}")
                    log.error("Please download it from Google Cloud Console → Credentials")
                    _update_supervisor("error", "Missing client_secret.json")
                    return None

                log.info("Starting OAuth flow...")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
                    creds = flow.run_local_server(port=8090, open_browser=True)
                except Exception as e:
                    log.error(f"OAuth flow failed: {e}")
                    retry_count += 1
                    if retry_count <= max_auth_retries:
                        log.info(f"Retrying authentication ({retry_count}/{max_auth_retries})...")
                        time.sleep(2)
                        continue
                    return None

            # Save token
            try:
                TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
                log.info(f"✅ YouTube token saved to {TOKEN_FILE}")
            except Exception as e:
                log.warning(f"Could not save token: {e}")

        # Build service
        try:
            return build("youtube", "v3", credentials=creds)
        except Exception as e:
            log.error(f"Failed to build YouTube service: {e}")
            retry_count += 1
            if retry_count <= max_auth_retries:
                log.info(f"Retrying service build ({retry_count}/{max_auth_retries})...")
                time.sleep(2)
                continue
            return None

    return None


def _request_with_retry(func, *args, **kwargs):
    """Execute a function with exponential backoff retries."""
    delay = INITIAL_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.warning(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(delay)
            delay = min(delay * 2, MAX_DELAY)


# ========================== CORE UPLOAD ==========================
def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    category_id: str = "28",      # Science & Technology
    privacy: str = "public",
    is_short: bool = True,
) -> Optional[Dict[str, Any]]:
    """Upload video to YouTube with progress tracking and retries."""
    _update_supervisor("active", "Authenticating with YouTube...")

    service = get_youtube_service()
    if not service:
        _update_supervisor("error", "YouTube authentication failed")
        return None

    video_path = Path(video_path)
    if not video_path.exists():
        log.error(f"Video file not found: {video_path}")
        _update_supervisor("error", "Video file not found")
        return None

    # Optimize title for Shorts
    final_title = title
    if is_short and "#Shorts" not in final_title and "#shorts" not in final_title.lower():
        if len(final_title) + 9 <= 100:
            final_title = f"{final_title} #Shorts"

    # Tags
    default_tags = getattr(config, "DEFAULT_TAGS", ["tech", "news", "trending"])
    final_tags = tags or default_tags
    if is_short:
        final_tags = list(set(final_tags + ["Shorts", "youtube shorts"]))
    final_tags = final_tags[:500]

    body = {
        "snippet": {
            "title": final_title[:100],
            "description": (description or "")[:5000],
            "tags": final_tags,
            "categoryId": category_id,
            "defaultLanguage": "hi" if getattr(config, "LANGUAGE", "hinglish") in ["hindi", "hinglish"] else "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
        }
    }

    try:
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=UPLOAD_CHUNK_SIZE,
        )

        _update_supervisor("active", f"Uploading: {final_title[:50]}...")

        request = service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        response = None
        last_logged = 0

        while response is None:
            # next_chunk can raise exceptions; we rely on outer retry
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                if progress - last_logged >= 10:   # Log every 10%
                    log.info(f"YouTube upload progress: {progress}%")
                    _update_supervisor("active", f"Uploading... {progress}%")
                    last_logged = progress

        video_id = response.get("id")
        if not video_id:
            raise ValueError("No video ID returned")

        result = {
            "platform": "youtube",
            "video_id": video_id,
            "url": f"https://youtube.com/shorts/{video_id}",
            "title": final_title,
            "status": "uploaded",
            "uploaded_at": datetime.now().isoformat(),
        }

        log.info(f"✅ YouTube upload successful → https://youtube.com/shorts/{video_id}")
        _update_supervisor("done", f"Published → {video_id[:8]}...")

        return result

    except Exception as e:
        log.exception("YouTube upload failed")
        _update_supervisor("error", f"Upload failed: {str(e)[:80]}")
        return None


def set_thumbnail(video_id: str, thumbnail_path: str) -> bool:
    """Upload custom thumbnail with retry."""
    service = get_youtube_service()
    if not service:
        return False

    if not Path(thumbnail_path).exists():
        log.error(f"Thumbnail not found: {thumbnail_path}")
        return False

    try:
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")

        def _set():
            service.thumbnails().set(videoId=video_id, media_body=media).execute()
        _request_with_retry(_set)

        log.info(f"✅ Thumbnail set for video {video_id}")
        _update_supervisor("done", "Thumbnail updated")
        return True
    except Exception as e:
        log.error(f"Failed to set thumbnail: {e}")
        _update_supervisor("error", "Thumbnail failed")
        return False


def get_channel_stats() -> Optional[Dict[str, Any]]:
    """Fetch channel statistics with retry."""
    service = get_youtube_service()
    if not service:
        return None

    try:
        def _get():
            return service.channels().list(
                part="snippet,statistics",
                mine=True
            ).execute()
        response = _request_with_retry(_get)

        if not response.get("items"):
            return None

        channel = response["items"][0]
        stats = channel.get("statistics", {})

        return {
            "channel_name": channel.get("snippet", {}).get("title", "Unknown"),
            "subscribers": int(stats.get("subscriberCount", 0)),
            "total_views": int(stats.get("viewCount", 0)),
            "total_videos": int(stats.get("videoCount", 0)),
            "fetched_at": datetime.now().isoformat()
        }
    except Exception as e:
        log.error(f"Failed to get channel stats: {e}")
        return None


# ========================== ASYNC WRAPPERS ==========================
async def upload_video_async(*args, **kwargs) -> Optional[Dict]:
    """Async version using thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, upload_video, *args, **kwargs)


async def set_thumbnail_async(video_id: str, thumbnail_path: str) -> bool:
    """Async version of set_thumbnail."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, set_thumbnail, video_id, thumbnail_path)


async def get_channel_stats_async() -> Optional[Dict[str, Any]]:
    """Async version of get_channel_stats."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_channel_stats)


# ========================== CLI TEST ==========================
if __name__ == "__main__":
    print("YouTube Upload Module v3.0")
    print("=" * 55)

    stats = get_channel_stats()
    if stats:
        print(f"✅ Channel     : {stats['channel_name']}")
        print(f"   Subscribers : {stats['subscribers']:,}")
        print(f"   Total Views : {stats['total_views']:,}")
    else:
        print("❌ Not authenticated yet.")
        print("Run this script once to complete OAuth login.")