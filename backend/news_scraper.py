"""
AutoNews AI - News Scraper
Detects trending news from multiple free sources.
Sources: Google Trends, NewsAPI, Reddit RSS, Google News RSS
"""
import json
import time
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path

import requests
import feedparser

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "scraper.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ── Seen articles cache (avoid duplicates) ───────────────────
SEEN_FILE = config.DATA_DIR / "seen_articles.json"


def _load_seen() -> set:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
    return set()


def _save_seen(seen: set):
    # Keep only last 500 entries
    items = list(seen)[-500:]
    SEEN_FILE.write_text(json.dumps(items), encoding="utf-8")


def _article_id(title: str) -> str:
    return hashlib.md5(title.lower().strip().encode()).hexdigest()


# ── Google Trends (via RSS — no API key needed) ─────────────
def fetch_google_trends(region: str = "IN", count: int = 10) -> list[dict]:
    """Fetch trending searches from Google Trends RSS feed."""
    url = f"https://trends.google.com/trending/rss?geo={region}"
    log.info(f"Fetching Google Trends for region={region}")

    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:count]:
            results.append({
                "title": entry.get("title", ""),
                "source": "Google Trends",
                "url": entry.get("link", ""),
                "traffic": entry.get("ht_approx_traffic", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
            })
        log.info(f"Google Trends: found {len(results)} trends")
        return results
    except Exception as e:
        log.error(f"Google Trends error: {e}")
        return []


# ── NewsAPI.org (100 req/day free) ───────────────────────────
def fetch_newsapi(query: str = None, category: str = "technology",
                  country: str = "in", count: int = 10) -> list[dict]:
    """Fetch top headlines from NewsAPI."""
    if not config.NEWS_API_KEY:
        log.warning("NEWS_API_KEY not set, skipping NewsAPI")
        return []

    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": config.NEWS_API_KEY,
        "country": country,
        "pageSize": count,
    }
    if query:
        params["q"] = query
    elif category:
        params["category"] = category

    try:
        log.info(f"Fetching NewsAPI: category={category}, query={query}")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for article in data.get("articles", []):
            results.append({
                "title": article.get("title", ""),
                "source": article.get("source", {}).get("name", "NewsAPI"),
                "url": article.get("url", ""),
                "description": article.get("description", ""),
                "published": article.get("publishedAt", ""),
                "image": article.get("urlToImage", ""),
            })
        log.info(f"NewsAPI: found {len(results)} articles")
        return results
    except Exception as e:
        log.error(f"NewsAPI error: {e}")
        return []


# ── Google News RSS (free, no API key) ───────────────────────
def fetch_google_news_rss(query: str = "technology India",
                          count: int = 10) -> list[dict]:
    """Fetch news from Google News RSS feed."""
    query_encoded = requests.utils.quote(query)
    url = f"https://news.google.com/rss/search?q={query_encoded}&hl=en-IN&gl=IN&ceid=IN:en"

    try:
        log.info(f"Fetching Google News RSS: query={query}")
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:count]:
            results.append({
                "title": entry.get("title", ""),
                "source": entry.get("source", {}).get("title", "Google News"),
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
            })
        log.info(f"Google News RSS: found {len(results)} articles")
        return results
    except Exception as e:
        log.error(f"Google News RSS error: {e}")
        return []


# ── Reddit RSS (free, no API key) ────────────────────────────
def fetch_reddit_trending(subreddits: list[str] = None,
                          count: int = 10) -> list[dict]:
    """Fetch trending posts from Reddit RSS feeds."""
    if subreddits is None:
        subreddits = ["technology", "artificial", "india", "worldnews"]

    results = []
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/hot.rss"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:count // len(subreddits)]:
                results.append({
                    "title": entry.get("title", ""),
                    "source": f"r/{sub}",
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", "")[:300],
                })
        except Exception as e:
            log.error(f"Reddit r/{sub} error: {e}")
    log.info(f"Reddit: found {len(results)} posts")
    return results


# ── Aggregate & Rank ─────────────────────────────────────────
def get_trending_news(max_results: int = 20) -> list[dict]:
    """
    Aggregate news from all sources, deduplicate, and rank by relevance.
    Returns list of news items sorted by virality score.
    """
    seen = _load_seen()
    all_news = []

    # Fetch from all sources
    all_news.extend(fetch_google_trends())
    for cat in config.NEWS_CATEGORIES:
        all_news.extend(fetch_newsapi(category=cat, count=5))
    for kw in config.NEWS_KEYWORDS[:3]:
        all_news.extend(fetch_google_news_rss(query=kw, count=5))
    all_news.extend(fetch_reddit_trending())

    # Deduplicate
    unique = []
    for item in all_news:
        aid = _article_id(item["title"])
        if aid not in seen and item["title"]:
            seen.add(aid)
            # Calculate simple virality score
            score = 0
            title_lower = item["title"].lower()
            for kw in config.NEWS_KEYWORDS:
                if kw.lower() in title_lower:
                    score += 10
            if item.get("traffic"):
                try:
                    score += int(item["traffic"].replace(",", "").replace("+", "")) // 1000
                except (ValueError, AttributeError):
                    pass
            item["virality_score"] = score
            item["fetched_at"] = datetime.now().isoformat()
            unique.append(item)

    # Sort by virality score
    unique.sort(key=lambda x: x.get("virality_score", 0), reverse=True)
    result = unique[:max_results]

    _save_seen(seen)

    # Save to file
    output_file = config.DATA_DIR / f"news_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    output_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Saved {len(result)} trending news items to {output_file}")

    return result


if __name__ == "__main__":
    news = get_trending_news()
    print(f"\n{'='*60}")
    print(f"Found {len(news)} trending news items:")
    print(f"{'='*60}")
    for i, item in enumerate(news, 1):
        print(f"\n{i}. [{item.get('virality_score', 0)}] {item['title']}")
        print(f"   Source: {item['source']}")
        if item.get("url"):
            print(f"   URL: {item['url']}")
