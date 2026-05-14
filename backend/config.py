"""
AutoNews AI - Configuration v2.2
Centralized, type-safe configuration using Pydantic Settings with validation.
"""

from pathlib import Path
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main configuration class for AutoNews AI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
    )

    # ====================== BASE PATHS ======================
    BASE_DIR: Path = Path(__file__).parent.parent

    DATA_DIR: Path = BASE_DIR / "data"
    VIDEOS_DIR: Path = BASE_DIR / "output" / "videos"
    THUMBNAILS_DIR: Path = BASE_DIR / "output" / "thumbnails"
    SCRIPTS_DIR: Path = BASE_DIR / "output" / "scripts"
    LOGS_DIR: Path = BASE_DIR / "logs"
    CACHE_DIR: Path = BASE_DIR / "cache"

    # ====================== API KEYS ======================
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_API_KEY: str = ""          # optional, for read‑only operations
    GEMINI_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    META_ACCESS_TOKEN: str = ""
    INSTAGRAM_ACCOUNT_ID: str = ""

    # ====================== CHANNEL SETTINGS ======================
    CHANNEL_NAME: str = "AutoNewsAI"
    CHANNEL_HANDLE: str = "@AutoNewsAI"
    LANGUAGE: str = "hinglish"          # hindi, english, hinglish
    NICHE: str = "Tech & AI News"

    # ====================== SCHEDULER ======================
    SCHEDULE_SLOTS: List[str] = ["06:00", "12:00", "17:00", "19:00"]
    VIDEOS_PER_DAY: int = 2
    MAX_VIDEOS_PER_RUN: int = 1

    # ====================== NEWS FILTERING ======================
    NEWS_CATEGORIES: List[str] = ["technology", "science", "business", "ai"]
    NEWS_KEYWORDS: List[str] = [
        "AI", "artificial intelligence", "tech", "India", "startup",
        "Google", "OpenAI", "ISRO", "Tesla", "crypto"
    ]
    GOOGLE_TRENDS_REGION: str = "IN"
    NEWS_MAX_RESULTS: int = 20
    NEWS_FRESHNESS_DAYS: int = 1

    # ====================== VIDEO SETTINGS ======================
    VIDEO_WIDTH: int = 1080
    VIDEO_HEIGHT: int = 1920
    VIDEO_FPS: int = 30
    DEFAULT_FRAME_DURATION: float = 4.5

    # TTS Settings
    TTS_VOICE: str = "hi-IN-SwaraNeural"
    TTS_FALLBACK_VOICE: str = "en-US-JennyNeural"

    # ====================== RETRY & TIMEOUT ======================
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30

    # ====================== DEFAULT SEO ======================
    DEFAULT_TAGS: List[str] = [
        "news", "tech news", "AI news", "trending",
        "shorts", "reels", "breaking news", "AutoNewsAI"
    ]

    # ====================== VALIDATORS ======================
    @field_validator("LANGUAGE")
    @classmethod
    def validate_language(cls, v: str) -> str:
        allowed = {"hinglish", "hindi", "english"}
        if v.lower() not in allowed:
            raise ValueError(f"LANGUAGE must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("SCHEDULE_SLOTS", mode="before")
    @classmethod
    def parse_schedule_slots(cls, v):
        if isinstance(v, str):
            return [slot.strip() for slot in v.split(",")]
        return v

    @field_validator("NEWS_CATEGORIES", "NEWS_KEYWORDS", "DEFAULT_TAGS", mode="before")
    @classmethod
    def parse_list_fields(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v

    # ====================== DERIVED PROPERTIES ======================
    @property
    def is_async_mode(self) -> bool:
        """Return True if running in async mode (for future use)."""
        return False   # Can be set via environment in the future

    @property
    def video_resolution(self) -> tuple[int, int]:
        """Return (width, height) as tuple."""
        return (self.VIDEO_WIDTH, self.VIDEO_HEIGHT)

    @property
    def is_instagram_configured(self) -> bool:
        """Check if Instagram credentials are present."""
        return bool(self.META_ACCESS_TOKEN and self.INSTAGRAM_ACCOUNT_ID)

    @property
    def is_youtube_configured(self) -> bool:
        """Check if YouTube OAuth credentials are present."""
        return bool(self.YOUTUBE_CLIENT_ID and self.YOUTUBE_CLIENT_SECRET)


# ========================== INSTANCE ==========================
settings = Settings()

# ========================== DIRECTORY CREATION ==========================
def _create_directories():
    """Create all required directories, ignoring permission errors."""
    dirs = [
        settings.DATA_DIR,
        settings.VIDEOS_DIR,
        settings.THUMBNAILS_DIR,
        settings.SCRIPTS_DIR,
        settings.LOGS_DIR,
        settings.CACHE_DIR,
    ]
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print(f"⚠️ Warning: Could not create directory {d} (permission denied)")
        except Exception as e:
            print(f"⚠️ Warning: Failed to create {d}: {e}")

_create_directories()


# ========================== HELPER FUNCTIONS ==========================
def get_base_url() -> str:
    """Return base URL for the project (overridable via env)."""
    return "http://localhost:8000"


def print_config_summary():
    """Print configuration summary for debugging."""
    print("\n" + "=" * 60)
    print("🚀 AutoNews AI Configuration Loaded")
    print("=" * 60)
    print(f"Channel       : {settings.CHANNEL_NAME} ({settings.CHANNEL_HANDLE})")
    print(f"Language      : {settings.LANGUAGE}")
    print(f"Schedule      : {settings.SCHEDULE_SLOTS}")
    print(f"Videos/Day    : {settings.VIDEOS_PER_DAY}")
    print(f"Gemini Key    : {'✅ Set' if settings.GEMINI_API_KEY else '❌ Missing'}")
    print(f"NewsAPI Key   : {'✅ Set' if settings.NEWS_API_KEY else '❌ Missing'}")
    print(f"YouTube OAuth : {'✅ Configured' if settings.is_youtube_configured else '❌ Not Configured'}")
    print(f"Instagram     : {'✅ Configured' if settings.is_instagram_configured else '❌ Not Configured'}")
    print(f"Video Size    : {settings.video_resolution[0]}x{settings.video_resolution[1]}")
    print("=" * 60)


if __name__ == "__main__":
    print_config_summary()

def __getattr__(name):
    """Fallback to settings instance for module-level attribute access."""
    if hasattr(settings, name):
        return getattr(settings, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")