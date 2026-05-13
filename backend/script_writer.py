"""
AutoNews AI - Script Writer
Auto-generates video scripts using Google Gemini (free: 1500 req/day).
Generates in Hinglish for Indian audience.
"""
import json
import logging
from datetime import datetime

import config

log = logging.getLogger(__name__)


def _get_gemini_model():
    """Initialize Gemini model."""
    try:
        import google.generativeai as genai
        if not config.GEMINI_API_KEY:
            log.error("GEMINI_API_KEY not set!")
            return None
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except ImportError:
        log.error("google-generativeai not installed. Run: pip install google-generativeai")
        return None


SCRIPT_PROMPT = """You are a news script writer for a YouTube Shorts / Instagram Reels channel called "{channel}".

Write a 45-60 second video script in {language} about this news:

Title: {title}
Source: {source}
Details: {details}

RULES:
1. Language: {language_rules}
2. Start with a HOOK (first 3 seconds must grab attention)
3. Keep it under 150 words
4. Use simple, conversational tone — like talking to a friend
5. End with a CTA: "Follow @{handle} for daily tech updates"
6. Include 2-3 key facts
7. NO clickbait, NO misinformation, stick to facts
8. Add [PAUSE] markers for dramatic effect

OUTPUT FORMAT (JSON):
{{
  "hook": "Opening hook line (3 seconds)",
  "script": "Full script text with [PAUSE] markers",
  "title_youtube": "YouTube Shorts title (max 60 chars, with emoji)",
  "title_instagram": "Instagram Reels caption (with hashtags)",
  "description": "YouTube description (2-3 lines + hashtags)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"]
}}
"""

LANGUAGE_RULES = {
    "hinglish": "Mix of Hindi and English (Hinglish). Use Roman Hindi script. Example: 'Aaj ki sabse badi tech news ye hai ki...'",
    "hindi": "Pure Hindi in Devanagari script.",
    "english": "Simple English, easy to understand for Indian audience.",
}


def generate_script(news_item: dict) -> dict | None:
    """Generate a video script from a news item using Gemini."""
    model = _get_gemini_model()
    if not model:
        return _generate_fallback_script(news_item)

    title = news_item.get("title", "")
    source = news_item.get("source", "")
    details = news_item.get("description", "") or news_item.get("summary", "") or ""

    prompt = SCRIPT_PROMPT.format(
        channel=config.CHANNEL_NAME,
        language=config.LANGUAGE,
        title=title,
        source=source,
        details=details[:500],
        language_rules=LANGUAGE_RULES.get(config.LANGUAGE, LANGUAGE_RULES["hinglish"]),
        handle=config.CHANNEL_HANDLE.replace("@", ""),
    )

    try:
        log.info(f"Generating script for: {title[:50]}")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Parse JSON from response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        script_data = json.loads(text)
        script_data["source_title"] = title
        script_data["source_name"] = source
        script_data["generated_at"] = datetime.now().isoformat()

        # Save script
        safe_title = "".join(c for c in title[:40] if c.isalnum() or c in " -_").strip().replace(" ", "_")
        script_file = config.SCRIPTS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}.json"
        script_file.write_text(json.dumps(script_data, indent=2, ensure_ascii=False), encoding="utf-8")

        log.info(f"Script generated and saved: {script_file.name}")
        return script_data

    except json.JSONDecodeError:
        log.error(f"Failed to parse Gemini response as JSON")
        return _generate_fallback_script(news_item)
    except Exception as e:
        log.error(f"Gemini error: {e}")
        return _generate_fallback_script(news_item)


def _generate_fallback_script(news_item: dict) -> dict:
    """Fallback template when AI is unavailable."""
    title = news_item.get("title", "Breaking News")
    source = news_item.get("source", "")
    details = news_item.get("description", "") or news_item.get("summary", "") or ""

    script = (
        f"Breaking news! [PAUSE] "
        f"{title}. [PAUSE] "
        f"{details[:200]} [PAUSE] "
        f"Source: {source}. [PAUSE] "
        f"Follow @{config.CHANNEL_HANDLE.replace('@', '')} for daily tech updates!"
    )

    return {
        "hook": f"🔥 {title[:50]}...",
        "script": script,
        "title_youtube": f"🔥 {title[:55]}",
        "title_instagram": f"🔥 {title}\n\n#technews #ainews #trending #shorts",
        "description": f"{title}\n\nSource: {source}\n\n#technews #ainews #trending",
        "tags": config.DEFAULT_TAGS[:5],
        "hashtags": ["#technews", "#ainews", "#trending", "#shorts", "#news"],
        "source_title": title,
        "source_name": source,
        "generated_at": datetime.now().isoformat(),
        "is_fallback": True,
    }


def generate_seo_metadata(script_data: dict) -> dict:
    """Generate optimized SEO metadata for the video."""
    model = _get_gemini_model()
    if not model:
        return {
            "optimized_title": script_data.get("title_youtube", ""),
            "optimized_description": script_data.get("description", ""),
            "optimized_tags": script_data.get("tags", []),
        }

    prompt = f"""Optimize this YouTube Shorts metadata for maximum reach:

Title: {script_data.get('title_youtube', '')}
Description: {script_data.get('description', '')}
Tags: {script_data.get('tags', [])}

Return JSON with:
{{
  "optimized_title": "max 60 chars, emoji, power words",
  "optimized_description": "2 lines + 5 relevant hashtags",
  "optimized_tags": ["10 SEO optimized tags"]
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        log.warning(f"SEO optimization failed: {e}")
        return {
            "optimized_title": script_data.get("title_youtube", ""),
            "optimized_description": script_data.get("description", ""),
            "optimized_tags": script_data.get("tags", []),
        }


if __name__ == "__main__":
    test_news = {
        "title": "OpenAI confirms GPT-5 release date for 2026",
        "source": "TechCrunch",
        "description": "OpenAI has officially announced that GPT-5 will be released in Q3 2026 with major improvements in reasoning, multimodal capabilities, and reduced hallucinations.",
    }
    script = generate_script(test_news)
    if script:
        print(json.dumps(script, indent=2, ensure_ascii=False))
