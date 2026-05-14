"""
AutoNews AI - Script Writer v3.0 (Advanced)
High-reliability Gemini script generator with structured output, smart caching,
retries, content safety, and async support.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Union, Any

import config
from pydantic import BaseModel, Field, ValidationError

# Optional: Use tenacity for powerful retries
try:
    from tenacity import (
        retry, stop_after_attempt, wait_exponential,
        retry_if_exception_type, before_sleep_log
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    from functools import wraps
    import time

log = logging.getLogger(__name__)

# ========================== CONFIGURATION ==========================
CACHE_TTL_HOURS = int(os.getenv("SCRIPT_CACHE_TTL_HOURS", "2"))
CACHE_TTL = timedelta(hours=CACHE_TTL_HOURS)
CACHE_DIR = Path(config.DATA_DIR) / "script_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS_DIR = Path(config.SCRIPTS_DIR)
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_RETRIES = int(os.getenv("SCRIPT_MAX_RETRIES", "3"))
INITIAL_DELAY = float(os.getenv("SCRIPT_INITIAL_DELAY", "1.0"))
MAX_DELAY = float(os.getenv("SCRIPT_MAX_DELAY", "10.0"))

# Safety settings: BLOCK_NONE, BLOCK_ONLY_HIGH, BLOCK_MEDIUM_AND_ABOVE
SAFETY_SETTING = os.getenv("GEMINI_SAFETY_SETTING", "BLOCK_MEDIUM_AND_ABOVE")

# ========================== PYDANTIC MODEL ==========================
class ScriptData(BaseModel):
    hook: str = Field(..., min_length=5, max_length=180)
    script: str = Field(..., min_length=30, max_length=1800)
    title_youtube: str = Field(..., max_length=60)
    title_instagram: str = Field(..., max_length=2200)
    description: str = Field(..., max_length=5000)
    tags: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)

    # Metadata added by system
    source_title: Optional[str] = None
    source_name: Optional[str] = None
    generated_at: Optional[str] = None
    is_fallback: bool = False
    language: Optional[str] = None
    token_count: Optional[int] = None

    class Config:
        extra = "allow"


# ========================== GEMINI CLIENT ==========================
def _get_safety_settings():
    """Map string setting to Google's SafetySetting dict."""
    mapping = {
        "BLOCK_NONE": "BLOCK_NONE",
        "BLOCK_ONLY_HIGH": "BLOCK_ONLY_HIGH",
        "BLOCK_MEDIUM_AND_ABOVE": "BLOCK_MEDIUM_AND_ABOVE",
        "BLOCK_LOW_AND_ABOVE": "BLOCK_LOW_AND_ABOVE",
    }
    harm_categories = [
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
    ]
    threshold = mapping.get(SAFETY_SETTING, "BLOCK_MEDIUM_AND_ABOVE")
    return [{"category": cat, "threshold": threshold} for cat in harm_categories]


def _get_gemini_model():
    try:
        import google.generativeai as genai

        if not getattr(config, "GEMINI_API_KEY", None):
            log.error("GEMINI_API_KEY is not set in config")
            return None

        genai.configure(api_key=config.GEMINI_API_KEY)

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.75,
                "max_output_tokens": 900,
                "response_mime_type": "application/json",
            },
            safety_settings=_get_safety_settings(),
            system_instruction="""You are an expert short-form video script writer for Indian audience.
Focus on energetic yet trustworthy Hinglish delivery. Never use clickbait or misinformation.
Keep scripts concise, under 150 words. Use [PAUSE] for pacing.""",
        )
        return model
    except ImportError:
        log.error("google-generativeai not installed. Run: pip install google-generativeai")
        return None
    except Exception as e:
        log.error(f"Failed to initialize Gemini model: {e}")
        return None


# ========================== CACHE ==========================
def _get_cache_key(news_item: dict) -> str:
    content = (
        f"{news_item.get('title')}|"
        f"{news_item.get('description') or news_item.get('summary')}|"
        f"{config.LANGUAGE}"
    )
    return hashlib.md5(content.encode("utf-8")).hexdigest()[:20]


def _load_from_cache(key: str) -> Optional[dict]:
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(data["cached_at"])
        if datetime.now() - cached_at > CACHE_TTL:
            cache_file.unlink(missing_ok=True)
            return None
        return data["script_data"]
    except Exception as e:
        log.warning(f"Cache read failed for key {key}: {e}")
        return None


def _save_to_cache(key: str, script_data: dict):
    cache_file = CACHE_DIR / f"{key}.json"
    try:
        payload = {
            "cached_at": datetime.now().isoformat(),
            "script_data": script_data
        }
        cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning(f"Failed to write cache: {e}")


# ========================== RETRY DECORATOR ==========================
if TENACITY_AVAILABLE:
    def gemini_retry(func):
        @retry(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=INITIAL_DELAY, min=INITIAL_DELAY, max=MAX_DELAY),
            retry=retry_if_exception_type((Exception)),
            before_sleep=before_sleep_log(log, logging.WARNING),
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
else:
    # Simple retry fallback
    def gemini_retry(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = INITIAL_DELAY
            last_exception = None
            for attempt in range(MAX_RETRIES):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == MAX_RETRIES - 1:
                        break
                    log.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, MAX_DELAY)
            raise last_exception
        return wrapper


# ========================== PROMPTS ==========================
def _build_script_prompt(news_item: dict) -> str:
    title = news_item.get("title", "")
    details = news_item.get("description") or news_item.get("summary") or ""

    # Few-shot example to guide format
    example = """
Example output:
{
  "hook": "🔥 OpenAI just dropped a BOMBSHELL!",
  "script": "OpenAI just confirmed...[PAUSE] GPT-5 is coming in 2026! [PAUSE] Follow for more!",
  "title_youtube": "GPT-5 RELEASE DATE CONFIRMED! 🔥",
  "title_instagram": "GPT-5 coming in 2026! 🚀 #technews",
  "description": "OpenAI officially announces GPT-5 release... #ai #gpt5",
  "tags": ["GPT5", "OpenAI", "AInews"],
  "hashtags": ["#GPT5", "#OpenAI"]
}
"""

    return f"""Write a 45-60 second video script for this news:

Title: {title}
Source: {news_item.get('source', 'Unknown')}
Details: {details[:700]}

Rules:
- Use {config.LANGUAGE} (Hinglish preferred for Indian audience)
- Strong hook in first 3 seconds
- Conversational, energetic, friend-like tone
- 2-3 key facts only
- Add [PAUSE] for pacing
- End with CTA: Follow @{config.CHANNEL_HANDLE.replace('@', '')}
- Strictly factual, no clickbait
- Output MUST be valid JSON only, no other text.

{example}

Now generate JSON only:"""


# ========================== CORE GENERATION (ASYNC) ==========================
@gemini_retry
async def _generate_with_gemini_async(prompt: str) -> dict:
    """Async Gemini call with retry."""
    model = _get_gemini_model()
    if not model:
        raise RuntimeError("Gemini model unavailable")

    response = await model.generate_content_async(prompt)
    text = response.text.strip()

    # Extract token usage if available
    token_count = None
    if hasattr(response, 'usage_metadata'):
        token_count = response.usage_metadata.total_token_count

    # Extract JSON safely
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    parsed = json.loads(text)
    # Add token count to result
    if token_count:
        parsed["token_count"] = token_count
    return parsed


async def _generate_script_async(news_item: dict) -> Optional[dict]:
    """Async internal version."""
    if not news_item or not news_item.get("title"):
        log.error("Invalid news item passed to generate_script")
        return None

    if not getattr(config, "GEMINI_API_KEY", None):
        log.error("GEMINI_API_KEY is not set. Using fallback script.")
        return _generate_fallback_script(news_item)

    cache_key = _get_cache_key(news_item)
    cached = _load_from_cache(cache_key)
    if cached:
        log.info(f"✅ Cache hit for: {news_item['title'][:60]}")
        return cached

    log.info(f"✍️ Generating new script: {news_item['title'][:70]}...")

    try:
        prompt = _build_script_prompt(news_item)
        script_data = await _generate_with_gemini_async(prompt)

        # Validate with Pydantic
        validated = ScriptData(**script_data)
        script_dict = validated.dict(exclude_none=True)

        # Enrich with metadata
        script_dict.update({
            "source_title": news_item.get("title"),
            "source_name": news_item.get("source"),
            "generated_at": datetime.now().isoformat(),
            "is_fallback": False,
            "language": config.LANGUAGE,
        })

        # Save to disk
        _save_script_to_disk(script_dict, news_item.get("title", "news"))

        # Cache and return
        _save_to_cache(cache_key, script_dict)
        log.info("✅ Script generated and cached successfully")
        return script_dict

    except Exception as e:
        log.exception(f"Script generation failed for: {news_item.get('title')[:60]}")
        fallback = _generate_fallback_script(news_item)
        _save_to_cache(cache_key, fallback)
        return fallback


# ========================== SYNC WRAPPER (Backward Compatible) ==========================
def generate_script(news_item: dict) -> Optional[dict]:
    """
    Synchronous version of generate_script (backward compatible).
    Uses asyncio.run() internally.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, safe to create new one
        return asyncio.run(_generate_script_async(news_item))
    else:
        # Already in async context – run in thread to avoid event loop conflict
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _generate_script_async(news_item))
            return future.result()


# ========================== DISK SAVE ==========================
def _save_script_to_disk(script_data: dict, title: str):
    safe_title = "".join(c for c in title[:40] if c.isalnum() or c in " -_").strip().replace(" ", "_")
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_title}.json"

    try:
        file_path = SCRIPTS_DIR / filename
        file_path.write_text(
            json.dumps(script_data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception as e:
        log.warning(f"Failed to save script file: {e}")


# ========================== FALLBACK ==========================
def _generate_fallback_script(news_item: dict) -> dict:
    title = news_item.get("title", "Breaking News")
    source = news_item.get("source", "Unknown")
    details = news_item.get("description", "") or news_item.get("summary", "") or ""

    script_text = f"Breaking news! [PAUSE] {title}. [PAUSE] {details[:180]}... [PAUSE] Source: {source}. Follow @{config.CHANNEL_HANDLE.replace('@', '')} for daily updates!"

    return {
        "hook": f"🔥 {title[:55]}...",
        "script": script_text,
        "title_youtube": f"🔥 {title[:58]}",
        "title_instagram": f"🔥 {title}\n\n#shorts #viral #news",
        "description": f"{title}\nSource: {source}\n\nFollow for more daily updates!",
        "tags": getattr(config, "DEFAULT_TAGS", ["news", "tech", "trending", "shorts"])[:10],
        "hashtags": ["#technews", "#breaking", "#shorts", "#viral"],
        "source_title": title,
        "source_name": source,
        "generated_at": datetime.now().isoformat(),
        "is_fallback": True,
        "language": config.LANGUAGE,
        "token_count": 0,
    }


# ========================== SEO METADATA ==========================
async def _generate_seo_metadata_async(script_data: dict) -> dict:
    """Async version for SEO optimization."""
    model = _get_gemini_model()
    if not model:
        return {
            "optimized_title": script_data.get("title_youtube", ""),
            "optimized_description": script_data.get("description", ""),
            "optimized_tags": script_data.get("tags", []),
        }

    # Simple optimization – can be expanded with actual AI call later
    return {
        "optimized_title": script_data.get("title_youtube", "")[:60],
        "optimized_description": script_data.get("description", "")[:400],
        "optimized_tags": script_data.get("tags", [])[:12],
    }


def generate_seo_metadata(script_data: dict) -> dict:
    """Synchronous wrapper for SEO metadata generation."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_generate_seo_metadata_async(script_data))
    else:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _generate_seo_metadata_async(script_data))
            return future.result()


# ========================== CLI TEST ==========================
if __name__ == "__main__":
    test_news = {
        "title": "OpenAI confirms GPT-5 release date for 2026",
        "source": "TechCrunch",
        "description": "OpenAI has officially announced GPT-5 coming in Q3 2026 with major improvements.",
    }
    script = generate_script(test_news)
    if script:
        print(json.dumps(script, indent=2, ensure_ascii=False))