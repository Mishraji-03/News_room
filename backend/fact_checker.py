"""
AutoNews AI - Fact Checker
Basic fact checking using free APIs and heuristics.
Filters unreliable sources and flags suspicious content.
"""
import logging
import requests
import config

log = logging.getLogger(__name__)

# Known reliable sources
RELIABLE_SOURCES = {
    "reuters", "associated press", "ap news", "bbc", "the hindu",
    "ndtv", "indian express", "hindustan times", "times of india",
    "economic times", "mint", "moneycontrol", "techcrunch", "the verge",
    "wired", "ars technica", "espncricinfo", "cricbuzz",
    "google news", "google trends", "nature", "science",
}

# Known unreliable / clickbait patterns
CLICKBAIT_PATTERNS = [
    "you won't believe", "shocking", "exposed", "secret revealed",
    "100% true", "must watch", "gone wrong", "gone viral",
    "scam alert", "fraud", "ponzi",
]

# Misinformation keywords to flag
FLAG_KEYWORDS = [
    "cure for cancer", "free money", "government giving",
    "whatsapp forward", "as per whatsapp",
]


def check_source_reliability(source: str) -> dict:
    """Check if the news source is known and reliable."""
    source_lower = source.lower().strip()

    is_reliable = any(rs in source_lower for rs in RELIABLE_SOURCES)
    is_reddit = "reddit" in source_lower or "r/" in source_lower

    return {
        "source": source,
        "is_reliable": is_reliable,
        "is_social_media": is_reddit,
        "confidence": 0.9 if is_reliable else (0.5 if is_reddit else 0.6),
    }


def check_clickbait(title: str) -> dict:
    """Check if the title contains clickbait patterns."""
    title_lower = title.lower()

    found_patterns = [p for p in CLICKBAIT_PATTERNS if p in title_lower]
    is_clickbait = len(found_patterns) > 0

    # Check excessive caps
    words = title.split()
    caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 2) / max(len(words), 1)
    if caps_ratio > 0.5:
        is_clickbait = True
        found_patterns.append("excessive_caps")

    # Check excessive punctuation
    if title.count("!") > 2 or title.count("?") > 2:
        is_clickbait = True
        found_patterns.append("excessive_punctuation")

    return {
        "is_clickbait": is_clickbait,
        "patterns_found": found_patterns,
        "score": 0.3 if is_clickbait else 0.9,
    }


def check_misinformation_flags(title: str, description: str = "") -> dict:
    """Check for common misinformation patterns."""
    combined = f"{title} {description}".lower()

    flags = [kw for kw in FLAG_KEYWORDS if kw in combined]

    return {
        "has_flags": len(flags) > 0,
        "flags": flags,
        "score": 0.2 if flags else 1.0,
    }


def check_claim_buster(text: str) -> dict:
    """
    Use ClaimBuster API for fact-checking (free tier).
    Returns a score of how likely the claim is check-worthy.
    """
    url = "https://idir.uta.edu/claimbuster/api/v2/score/text/"
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, json={"input_text": text}, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                avg_score = sum(r.get("score", 0) for r in results) / len(results)
                return {
                    "claim_score": round(avg_score, 3),
                    "is_check_worthy": avg_score > 0.5,
                    "details": results[:3],
                }
        return {"claim_score": 0, "is_check_worthy": False, "details": []}
    except Exception as e:
        log.warning(f"ClaimBuster API error: {e}")
        return {"claim_score": 0, "is_check_worthy": False, "error": str(e)}


def verify_news(news_item: dict) -> dict:
    """
    Run all fact-checking steps on a news item.
    Returns a verdict with overall trust score.
    """
    title = news_item.get("title", "")
    source = news_item.get("source", "Unknown")
    description = news_item.get("description", "") or news_item.get("summary", "")

    # Run all checks
    source_check = check_source_reliability(source)
    clickbait_check = check_clickbait(title)
    misinfo_check = check_misinformation_flags(title, description)

    # Calculate overall trust score (0-100)
    trust_score = (
        source_check["confidence"] * 40 +
        clickbait_check["score"] * 30 +
        misinfo_check["score"] * 30
    )

    verdict = "approved"
    if trust_score < 40:
        verdict = "rejected"
    elif trust_score < 65:
        verdict = "needs_review"

    result = {
        "title": title,
        "source": source,
        "trust_score": round(trust_score, 1),
        "verdict": verdict,
        "checks": {
            "source": source_check,
            "clickbait": clickbait_check,
            "misinformation": misinfo_check,
        },
    }

    log.info(f"Fact check: [{verdict}] score={trust_score:.0f} | {title[:60]}")
    return result


def filter_news(news_list: list[dict], min_score: float = 50) -> list[dict]:
    """Filter a list of news items, keeping only verified ones."""
    verified = []
    for item in news_list:
        check = verify_news(item)
        item["fact_check"] = check
        if check["trust_score"] >= min_score:
            verified.append(item)
        else:
            log.warning(f"Filtered out: {item['title'][:60]} (score={check['trust_score']})")
    log.info(f"Fact check: {len(verified)}/{len(news_list)} passed (min_score={min_score})")
    return verified


if __name__ == "__main__":
    # Test with sample data
    test_news = [
        {"title": "OpenAI releases GPT-5 with major improvements", "source": "TechCrunch"},
        {"title": "YOU WON'T BELIEVE what Modi said!!!", "source": "RandomBlog.com"},
        {"title": "ISRO successfully launches Chandrayaan-4", "source": "NDTV"},
        {"title": "FREE MONEY! Government giving Rs 50000 to everyone", "source": "WhatsApp Forward"},
    ]

    print("="*60)
    for item in test_news:
        result = verify_news(item)
        print(f"\n[{result['verdict'].upper()}] Score: {result['trust_score']}")
        print(f"  Title: {item['title']}")
        print(f"  Source: {item['source']}")
    print("\n" + "="*60)
