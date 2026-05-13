"""
AutoNews AI - Configuration
Fill in your API keys after creating accounts.
"""
import os
from pathlib import Path

# ============================================================
# BASE PATHS
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VIDEOS_DIR = BASE_DIR / "output" / "videos"
THUMBNAILS_DIR = BASE_DIR / "output" / "thumbnails"
SCRIPTS_DIR = BASE_DIR / "output" / "scripts"
LOGS_DIR = BASE_DIR / "logs"

for d in [DATA_DIR, VIDEOS_DIR, THUMBNAILS_DIR, SCRIPTS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# API KEYS  (set these as environment variables or fill here)
# ============================================================

# Google / YouTube
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")

# NewsAPI.org  (free: 100 requests/day)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Google Gemini  (free: 1500 requests/day)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Instagram / Meta Graph API
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

# ============================================================
# CHANNEL SETTINGS
# ============================================================
CHANNEL_NAME = "AutoNewsAI"
CHANNEL_HANDLE = "@AutoNewsAI-03"
LANGUAGE = "hinglish"  # hindi, english, hinglish
NICHE = "Tech & AI News"

# ============================================================
# SCHEDULE  (IST times)
# ============================================================
SCHEDULE_SLOTS = ["06:00", "12:00", "17:00", "19:00"]
VIDEOS_PER_DAY = 4
TIMEZONE = "Asia/Kolkata"

# ============================================================
# NEWS SOURCES
# ============================================================
NEWS_CATEGORIES = ["technology", "science", "business"]
NEWS_KEYWORDS = ["AI", "artificial intelligence", "tech", "India", "startup",
                  "Google", "OpenAI", "ISRO", "Tesla", "crypto", "gaming"]
GOOGLE_TRENDS_REGION = "IN"

# ============================================================
# VIDEO SETTINGS
# ============================================================
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # 9:16 for shorts/reels
VIDEO_FPS = 30
VIDEO_DURATION_MAX = 60  # seconds (shorts)
VOICE_LANGUAGE = "hi-IN"  # Google TTS
VOICE_SPEED = 1.1

# ============================================================
# SEO DEFAULTS
# ============================================================
DEFAULT_TAGS = ["news", "hindi", "tech news", "AI news", "trending",
                CHANNEL_NAME, "shorts", "reels", "breaking news"]
