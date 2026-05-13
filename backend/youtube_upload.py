"""
AutoNews AI - YouTube Upload
Uploads videos to YouTube using YouTube Data API v3 (free).
Supports Shorts format and scheduled publishing.

SETUP:
1. Go to https://console.cloud.google.com
2. Create a new project
3. Enable "YouTube Data API v3"
4. Create OAuth 2.0 credentials (Desktop app)
5. Download client_secret.json to backend/ folder
6. Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in config.py
"""
import json
import logging
from datetime import datetime
from pathlib import Path

import config

log = logging.getLogger(__name__)

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
                  "https://www.googleapis.com/auth/youtube"]
TOKEN_FILE = config.DATA_DIR / "youtube_token.json"
CLIENT_SECRETS_FILE = config.BASE_DIR / "client_secret.json"


def get_youtube_service():
    """Authenticate and return YouTube API service."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
    except ImportError:
        log.error("Install: pip install google-api-python-client google-auth-oauthlib")
        return None

    creds = None

    # Load existing token
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), YOUTUBE_SCOPES)
        except Exception:
            pass

    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not CLIENT_SECRETS_FILE.exists():
                log.error(f"client_secret.json not found at {CLIENT_SECRETS_FILE}")
                log.error("Download from Google Cloud Console → APIs → Credentials")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=8090)

        # Save token
        TOKEN_FILE.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path: str, title: str, description: str,
                 tags: list[str] = None, category_id: str = "28",
                 privacy: str = "public", is_short: bool = True) -> dict | None:
    """
    Upload a video to YouTube.

    Args:
        video_path: Path to the video file
        title: Video title (max 100 chars)
        description: Video description
        tags: List of tags
        category_id: YouTube category (28 = Science & Technology)
        privacy: public, private, or unlisted
        is_short: If True, adds #Shorts to title

    Returns:
        Upload result dict with video ID and URL
    """
    service = get_youtube_service()
    if not service:
        return None

    if not Path(video_path).exists():
        log.error(f"Video file not found: {video_path}")
        return None

    # Ensure #Shorts tag for Shorts
    if is_short and "#Shorts" not in title:
        if len(title) + 8 <= 100:
            title = f"{title} #Shorts"

    # Add default tags
    if tags is None:
        tags = config.DEFAULT_TAGS
    tags = list(set(tags + ["Shorts"] if is_short else tags))

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id,
            "defaultLanguage": "hi" if config.LANGUAGE in ["hindi", "hinglish"] else "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
        },
    }

    try:
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024 * 10,  # 10MB chunks
        )

        log.info(f"Uploading to YouTube: {title[:50]}...")
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                log.info(f"Upload progress: {int(status.progress() * 100)}%")

        video_id = response.get("id", "")
        result = {
            "video_id": video_id,
            "url": f"https://youtube.com/shorts/{video_id}" if is_short else f"https://youtu.be/{video_id}",
            "title": title,
            "status": "uploaded",
            "platform": "YouTube",
            "uploaded_at": datetime.now().isoformat(),
        }

        log.info(f"✅ YouTube upload complete: {result['url']}")
        return result

    except Exception as e:
        log.error(f"YouTube upload failed: {e}")
        return None


def set_thumbnail(video_id: str, thumbnail_path: str) -> bool:
    """Set custom thumbnail for a video."""
    service = get_youtube_service()
    if not service:
        return False

    try:
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
        service.thumbnails().set(videoId=video_id, media_body=media).execute()
        log.info(f"Thumbnail set for video {video_id}")
        return True
    except Exception as e:
        log.error(f"Thumbnail upload failed: {e}")
        return False


def get_channel_stats() -> dict | None:
    """Get channel statistics."""
    service = get_youtube_service()
    if not service:
        return None

    try:
        response = service.channels().list(part="statistics,snippet", mine=True).execute()
        if response.get("items"):
            channel = response["items"][0]
            stats = channel.get("statistics", {})
            return {
                "channel_name": channel.get("snippet", {}).get("title", ""),
                "subscribers": int(stats.get("subscriberCount", 0)),
                "total_views": int(stats.get("viewCount", 0)),
                "total_videos": int(stats.get("videoCount", 0)),
            }
    except Exception as e:
        log.error(f"Failed to get channel stats: {e}")
    return None


if __name__ == "__main__":
    print("YouTube Upload Module")
    print("=" * 40)
    stats = get_channel_stats()
    if stats:
        print(f"Channel: {stats['channel_name']}")
        print(f"Subscribers: {stats['subscribers']}")
        print(f"Total Views: {stats['total_views']}")
    else:
        print("Not authenticated. Run this script to authenticate first.")
        print("Make sure client_secret.json is in the backend/ folder.")
