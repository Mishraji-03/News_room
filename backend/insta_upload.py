"""
AutoNews AI - Instagram Upload
Posts Reels to Instagram using Meta Graph API (free).

SETUP:
1. Go to https://developers.facebook.com
2. Create an app → Business type
3. Add Instagram Graph API product
4. Generate a Page Access Token (long-lived)
5. Get your Instagram Business Account ID
6. Set META_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in config.py

NOTE: Instagram Graph API requires:
- A Facebook Page connected to an Instagram Business/Creator account
- The video must be hosted on a public URL (or uploaded to a server first)
"""
import json
import logging
import time
from datetime import datetime

import requests
import config

log = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


def upload_reel(video_url: str, caption: str,
                share_to_feed: bool = True) -> dict | None:
    """
    Upload a Reel to Instagram.

    Args:
        video_url: Public URL of the video file
        caption: Post caption with hashtags
        share_to_feed: Also share to main feed

    Returns:
        Upload result dict
    """
    if not config.META_ACCESS_TOKEN or not config.INSTAGRAM_ACCOUNT_ID:
        log.error("META_ACCESS_TOKEN or INSTAGRAM_ACCOUNT_ID not set!")
        return None

    account_id = config.INSTAGRAM_ACCOUNT_ID
    token = config.META_ACCESS_TOKEN

    try:
        # Step 1: Create media container
        log.info(f"Creating Instagram Reel container...")
        container_url = f"{GRAPH_API_BASE}/{account_id}/media"
        container_data = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "share_to_feed": share_to_feed,
            "access_token": token,
        }

        resp = requests.post(container_url, data=container_data, timeout=30)
        resp.raise_for_status()
        container_id = resp.json().get("id")

        if not container_id:
            log.error("Failed to create media container")
            return None

        log.info(f"Container created: {container_id}")

        # Step 2: Wait for processing
        status_url = f"{GRAPH_API_BASE}/{container_id}"
        for attempt in range(30):  # Wait up to 5 minutes
            time.sleep(10)
            status_resp = requests.get(
                status_url,
                params={"fields": "status_code", "access_token": token},
                timeout=10,
            )
            status = status_resp.json().get("status_code")
            log.info(f"Processing status: {status} (attempt {attempt + 1})")

            if status == "FINISHED":
                break
            elif status == "ERROR":
                log.error("Instagram processing failed")
                return None

        # Step 3: Publish
        log.info("Publishing Reel...")
        publish_url = f"{GRAPH_API_BASE}/{account_id}/media_publish"
        publish_data = {
            "creation_id": container_id,
            "access_token": token,
        }

        pub_resp = requests.post(publish_url, data=publish_data, timeout=30)
        pub_resp.raise_for_status()
        media_id = pub_resp.json().get("id")

        result = {
            "media_id": media_id,
            "container_id": container_id,
            "platform": "Instagram",
            "status": "published",
            "caption": caption[:100] + "...",
            "uploaded_at": datetime.now().isoformat(),
        }

        log.info(f"✅ Instagram Reel published: {media_id}")
        return result

    except requests.exceptions.HTTPError as e:
        log.error(f"Instagram API error: {e.response.text[:500]}")
        return None
    except Exception as e:
        log.error(f"Instagram upload failed: {e}")
        return None


def get_account_insights() -> dict | None:
    """Get Instagram account insights."""
    if not config.META_ACCESS_TOKEN or not config.INSTAGRAM_ACCOUNT_ID:
        return None

    try:
        url = f"{GRAPH_API_BASE}/{config.INSTAGRAM_ACCOUNT_ID}"
        params = {
            "fields": "username,followers_count,media_count,biography",
            "access_token": config.META_ACCESS_TOKEN,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        return {
            "username": data.get("username", ""),
            "followers": data.get("followers_count", 0),
            "posts": data.get("media_count", 0),
            "bio": data.get("biography", ""),
        }
    except Exception as e:
        log.error(f"Instagram insights error: {e}")
        return None


def upload_local_video(video_path: str, caption: str,
                       hosting_url: str = None) -> dict | None:
    """
    Upload a local video to Instagram.

    Since Instagram API requires a public URL, you need either:
    1. A hosting service URL (provide hosting_url)
    2. A simple file server (we'll log instructions)

    For production, use a free hosting like:
    - Cloudinary (free: 25 credits/month)
    - Firebase Storage (free: 5GB)
    - Railway.app static hosting
    """
    if hosting_url:
        return upload_reel(hosting_url, caption)

    log.warning("Instagram API requires video on a public URL.")
    log.warning("Options:")
    log.warning("  1. Upload to Cloudinary/Firebase first")
    log.warning("  2. Use a simple Python HTTP server with ngrok")
    log.warning(f"  Video: {video_path}")

    return None


if __name__ == "__main__":
    print("Instagram Upload Module")
    print("=" * 40)
    insights = get_account_insights()
    if insights:
        print(f"Username: @{insights['username']}")
        print(f"Followers: {insights['followers']}")
        print(f"Posts: {insights['posts']}")
    else:
        print("Not configured. Set META_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID.")
