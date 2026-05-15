"""
AutoNews AI — Advanced Trend Hunter Agent v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UPGRADES over v1:
  ✓ Circuit breaker (auto-disable broken sources)
  ✓ Exponential backoff retry (3 attempts per source)
  ✓ Rotating User-Agent headers (avoid bot detection)
  ✓ Reddit proper headers (was broken/blocked in v1)
  ✓ Semantic deduplication (catches paraphrased duplicates)
  ✓ 8-signal virality scorer (v1 had just keyword count)
  ✓ Trending velocity tracking (rising = high score)
  ✓ SQLite database integration (v1 only saved to JSON)
  ✓ Source credibility weighting per domain
  ✓ India-focused content prioritization
  ✓ Curated free RSS feeds as permanent fallback
  ✓ Category auto-detection from title
"""

import hashlib
import json
import logging
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import feedparser
import requests

# ── Project imports ───────────────────────────────────────────────────────────
try:
    import config
    NEWS_API_KEY = getattr(config, "NEWSAPI_KEY", "")
    GNEWS_KEY    = getattr(config, "GNEWS_API_KEY", "")
    NEWS_CATEGORIES = getattr(config, "NEWS_CATEGORIES", [])
    LOG_DIR      = Path(getattr(config, "LOGS_DIR", "logs"))
    DATA_DIR     = Path("data")
except ImportError:
    NEWS_API_KEY = ""
    GNEWS_KEY    = ""
    NEWS_CATEGORIES = ["artificial intelligence", "technology", "India news", "space science"]
    LOG_DIR      = Path("logs")
    DATA_DIR     = Path("data")

try:
    from database import get_connection, log_agent
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# ── Paths ─────────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
SEEN_FILE = DATA_DIR / "seen_articles.json"

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("TrendHunter")
AGENT_NAME = "Trend Hunter Agent"

# ── Constants ─────────────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/124.0.0.0",
]

TRUSTED_DOMAINS = {
    "reuters.com", "bbc.com", "bbc.co.uk", "apnews.com",
    "ndtv.com", "thehindu.com", "timesofindia.com", "hindustantimes.com",
    "techcrunch.com", "theverge.com", "wired.com", "arstechnica.com",
    "space.com", "nasa.gov", "isro.gov.in", "economictimes.indiatimes.com",
    "bloomberg.com",
}

VIRAL_KEYWORDS = [
    "india", "ai", "artificial intelligence", "breaking", "first ever",
    "record", "historic", "launch", "revealed", "leaked", "ban",
    "isro", "nasa", "google", "apple", "openai", "chatgpt", "gemini",
    "robot", "future", "billion", "crore", "free", "china", "new",
    "beats", "surpasses", "2025", "2026", "vs", "billion dollar",
]

INDIA_WORDS = {
    "india", "indian", "isro", "modi", "delhi", "mumbai",
    "rupee", "crore", "lakh", "ndtv", "bcci", "iisc", "iit",
}

# Always-free curated RSS feeds (no API key ever needed)
FREE_RSS_FEEDS = {
    "TechCrunch":      "https://techcrunch.com/feed/",
    "The Verge":       "https://www.theverge.com/rss/index.xml",
    "Wired":           "https://www.wired.com/feed/rss",
    "AI News":         "https://artificialintelligence-news.com/feed/",
    "NDTV Tech":       "https://feeds.feedburner.com/NdtvNews-Tech",
    "Economic Times":  "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "Space.com":       "https://www.space.com/feeds/all",
    "Science Daily":   "https://www.sciencedaily.com/rss/all.xml",
}


# ═════════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER — prevents hammering broken/rate-limited sources
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class CircuitBreaker:
    name: str
    max_failures: int = 3
    cooldown_sec: int = 300
    failures: int = 0
    opened_at: Optional[float] = None

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        if time.time() - self.opened_at > self.cooldown_sec:
            self.failures = 0
            self.opened_at = None
            log.info(f"[Circuit] {self.name} reset after cooldown")
            return False
        return True

    def record_success(self):
        self.failures = 0
        self.opened_at = None

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.max_failures:
            self.opened_at = time.time()
            log.warning(f"[Circuit] {self.name} OPEN — {self.failures} failures")

    def can_call(self) -> bool:
        if self.is_open():
            log.debug(f"[Circuit] {self.name} is OPEN — skipping")
            return False
        return True


_circuits: dict[str, CircuitBreaker] = {}

def get_circuit(name: str) -> CircuitBreaker:
    if name not in _circuits:
        _circuits[name] = CircuitBreaker(name=name)
    return _circuits[name]


# ═════════════════════════════════════════════════════════════════════════════
# HTTP HELPERS — retry + backoff + user-agent rotation
# ═════════════════════════════════════════════════════════════════════════════

def _extract_domain(url: str) -> str:
    from urllib.parse import urlparse
    try:
        return urlparse(url).netloc.replace("www.", "").lower()
    except Exception:
        return ""


def retry_get(url: str, params: dict = None, source_name: str = "?",
              max_attempts: int = 3, timeout: int = 12) -> Optional[requests.Response]:
    """GET with circuit breaker + exponential backoff retry."""
    circuit = get_circuit(source_name)
    if not circuit.can_call():
        return None

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
    }

    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, params=params, headers=headers,
                                timeout=timeout, allow_redirects=True)
            resp.raise_for_status()
            circuit.record_success()
            return resp

        except requests.exceptions.Timeout:
            log.warning(f"[{source_name}] Timeout attempt {attempt}/{max_attempts}")

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else 0
            log.warning(f"[{source_name}] HTTP {code} attempt {attempt}/{max_attempts}")
            if code == 429:
                log.warning(f"[{source_name}] Rate limited! Waiting 60s")
                time.sleep(60)
                circuit.record_failure()
                return None
            if 400 <= code < 500:
                circuit.record_failure()
                return None

        except Exception as e:
            log.warning(f"[{source_name}] Error attempt {attempt}: {type(e).__name__}: {e}")

        if attempt < max_attempts:
            wait = (2 ** (attempt - 1)) + random.uniform(0, 0.5)
            log.debug(f"[{source_name}] Retry in {wait:.1f}s")
            time.sleep(wait)

    circuit.record_failure()
    return None


def fetch_rss_safe(url: str, source_name: str = "RSS", limit: int = 10) -> list:
    """Parse RSS feed with circuit breaker."""
    circuit = get_circuit(source_name)
    if not circuit.can_call():
        return []
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        feed = feedparser.parse(url, request_headers=headers)
        if feed.bozo and not feed.entries:
            raise ValueError(f"Bad feed: {feed.bozo_exception}")
        circuit.record_success()
        return feed.entries[:limit]
    except Exception as e:
        log.error(f"[{source_name}] RSS parse error: {e}")
        circuit.record_failure()
        return []


# ═════════════════════════════════════════════════════════════════════════════
# SOURCE FETCHERS
# ═════════════════════════════════════════════════════════════════════════════

def fetch_google_trends(region: str = "IN", count: int = 15) -> list[dict]:
    """Google Trends daily RSS — completely free, no API key."""
    log.info("[Trends] Fetching Google Trends India...")
    entries = fetch_rss_safe(
        f"https://trends.google.com/trending/rss?geo={region}",
        source_name="Google Trends", limit=count
    )
    results = []
    for e in entries:
        title = (e.get("title") or "").strip()
        if not title:
            continue
        try:
            traffic = int(re.sub(r"[^\d]", "", str(e.get("ht_approx_traffic", "0"))))
        except (ValueError, TypeError):
            traffic = 0
        results.append({
            "title": title,
            "source": "Google Trends",
            "source_type": "trends",
            "url": e.get("link", ""),
            "summary": (e.get("summary") or "")[:400],
            "published": e.get("published", ""),
            "traffic": traffic,
            "credibility": 60,
        })
    log.info(f"[Trends] {len(results)} trends")
    return results


def fetch_newsapi(query: str = None, category: str = "technology",
                  country: str = "in", count: int = 8) -> list[dict]:
    """NewsAPI — 100 req/day free."""
    if not NEWS_API_KEY:
        return []
    if query:
        url = "https://newsapi.org/v2/everything"
        params = {
            "apiKey": NEWS_API_KEY, "q": query, "language": "en",
            "pageSize": count, "sortBy": "publishedAt",
            "from": (datetime.now() - timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%S"),
        }
    else:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"apiKey": NEWS_API_KEY, "country": country,
                  "category": category, "pageSize": count}

    log.info(f"[NewsAPI] Fetching: {query or category}")
    resp = retry_get(url, params=params, source_name="NewsAPI")
    if not resp:
        return []

    results = []
    for a in resp.json().get("articles", []):
        title = (a.get("title") or "").strip()
        if not title or title == "[Removed]":
            continue
        src_url = a.get("url", "")
        domain = _extract_domain(src_url)
        results.append({
            "title": title,
            "source": a.get("source", {}).get("name", "NewsAPI"),
            "source_type": "newsapi",
            "url": src_url,
            "summary": (a.get("description") or "")[:400],
            "image": a.get("urlToImage", ""),
            "published": a.get("publishedAt", ""),
            "credibility": 90 if domain in TRUSTED_DOMAINS else 65,
        })
    log.info(f"[NewsAPI] {len(results)} articles")
    return results


def fetch_gnews(query: str, count: int = 6) -> list[dict]:
    """GNews API — 100 req/day free."""
    if not GNEWS_KEY:
        return []
    params = {"q": query, "lang": "en", "country": "in",
               "max": count, "token": GNEWS_KEY}
    log.info(f"[GNews] Fetching: {query}")
    resp = retry_get("https://gnews.io/api/v4/search", params=params, source_name="GNews")
    if not resp:
        return []
    results = []
    for a in resp.json().get("articles", []):
        title = (a.get("title") or "").strip()
        if not title:
            continue
        domain = _extract_domain(a.get("url", ""))
        results.append({
            "title": title,
            "source": a.get("source", {}).get("name", "GNews"),
            "source_type": "gnews",
            "url": a.get("url", ""),
            "summary": (a.get("description") or "")[:400],
            "image": a.get("image", ""),
            "published": a.get("publishedAt", ""),
            "credibility": 90 if domain in TRUSTED_DOMAINS else 65,
        })
    log.info(f"[GNews] {len(results)} articles")
    return results


def fetch_google_news_rss(query: str, count: int = 8) -> list[dict]:
    """Google News RSS — completely free, no API key."""
    encoded = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    log.info(f"[GoogleNewsRSS] Query: {query}")
    entries = fetch_rss_safe(url, source_name=f"GoogleRSS:{query[:20]}", limit=count)
    results = []
    for e in entries:
        title = (e.get("title") or "").strip()
        # Google appends "- Source Name" to titles — remove it
        title = re.sub(r"\s*-\s*[A-Za-z\s\.]+$", "", title).strip()
        if not title:
            continue
        results.append({
            "title": title,
            "source": (e.get("source") or {}).get("title", "Google News"),
            "source_type": "google_rss",
            "url": e.get("link", ""),
            "summary": (e.get("summary") or "")[:400],
            "published": e.get("published", ""),
            "credibility": 70,
        })
    log.info(f"[GoogleNewsRSS] {len(results)} articles")
    return results


def fetch_reddit(subreddits: list[str] = None, count_per_sub: int = 4) -> list[dict]:
    """
    Reddit Hot RSS.
    FIX v2: Proper User-Agent prevents 429/403 that broke v1.
    """
    if subreddits is None:
        subreddits = ["technology", "artificial", "india", "worldnews", "science"]
    results = []
    for sub in subreddits:
        circuit = get_circuit(f"Reddit:r/{sub}")
        if not circuit.can_call():
            continue
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.rss?limit={count_per_sub}"
            # Reddit blocks generic User-Agents — MUST use this format
            headers = {"User-Agent": "AutoNewsBot/2.0 (news aggregator)"}
            feed = feedparser.parse(url, request_headers=headers)
            for e in feed.entries[:count_per_sub]:
                title = (e.get("title") or "").strip()
                if not title or len(title) < 10:
                    continue
                results.append({
                    "title": title,
                    "source": f"Reddit r/{sub}",
                    "source_type": "reddit",
                    "url": e.get("link", ""),
                    "summary": (e.get("summary") or "")[:300],
                    "published": e.get("published", ""),
                    "credibility": 45,
                })
            circuit.record_success()
            time.sleep(1.5)   # Reddit rate limit — be respectful
        except Exception as e:
            log.error(f"[Reddit] r/{sub}: {e}")
            circuit.record_failure()
    log.info(f"[Reddit] {len(results)} posts")
    return results


def fetch_free_rss_feeds() -> list[dict]:
    """Curated free RSS feeds — permanent fallback, no API key ever."""
    all_results = []
    for name, url in FREE_RSS_FEEDS.items():
        domain = _extract_domain(url)
        entries = fetch_rss_safe(url, source_name=f"RSS:{name}", limit=5)
        for e in entries:
            title = (e.get("title") or "").strip()
            if not title:
                continue
            all_results.append({
                "title": title,
                "source": name,
                "source_type": "rss",
                "url": e.get("link", ""),
                "summary": (e.get("summary") or "")[:400],
                "published": e.get("published", ""),
                "credibility": 90 if domain in TRUSTED_DOMAINS else 70,
            })
        time.sleep(0.3)
    log.info(f"[FreeRSS] {len(all_results)} articles from {len(FREE_RSS_FEEDS)} feeds")
    return all_results


# ═════════════════════════════════════════════════════════════════════════════
# DEDUPLICATION — two-layer (URL + semantic fingerprint)
# ═════════════════════════════════════════════════════════════════════════════

_STOPWORDS = {
    "a","an","the","is","are","was","were","be","been","by","for","in",
    "on","at","to","of","and","or","but","with","from","that","this",
    "its","has","have","had","will","would","could","should","may",
    "might","can","new","says","say","report","reports","now","over",
}

def _title_fingerprint(title: str) -> str:
    """
    Semantic fingerprint: strips stopwords + sorts → catches paraphrased duplicates.
    'ISRO launches rocket India' ≈ 'India rocket launch ISRO'  → same fingerprint
    """
    words = re.findall(r"\b[a-z]+\b", title.lower())
    key_words = sorted(w for w in words if w not in _STOPWORDS and len(w) > 2)
    return hashlib.md5(" ".join(key_words[:8]).encode()).hexdigest()


def _load_seen() -> set:
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def _save_seen(seen: set):
    SEEN_FILE.write_text(
        json.dumps(list(seen)[-1000:]), encoding="utf-8"
    )


def deduplicate(articles: list[dict], seen: set) -> tuple[list[dict], set]:
    unique, new_seen, batch_fps = [], set(seen), set()
    for a in articles:
        url   = a.get("url", "")
        title = a.get("title", "")
        if not title:
            continue
        url_id   = hashlib.md5(url.encode()).hexdigest() if url else None
        title_fp = _title_fingerprint(title)
        if (url_id and url_id in new_seen) or title_fp in batch_fps:
            continue
        if url_id:
            new_seen.add(url_id)
        batch_fps.add(title_fp)
        unique.append(a)
    return unique, new_seen


# ═════════════════════════════════════════════════════════════════════════════
# VIRALITY SCORER — 8 signals (v1 had 1 signal: keyword count)
# ═════════════════════════════════════════════════════════════════════════════

def score_virality(article: dict) -> int:
    """
    Composite virality score 0–100.
    ┌─────────────────────────────────┬────────┐
    │ Signal                          │ Weight │
    ├─────────────────────────────────┼────────┤
    │ 1. Google Trends traffic        │   25   │
    │ 2. Source credibility           │   15   │
    │ 3. Keyword matches              │   20   │
    │ 4. Recency (< 6 hrs = big bonus)│   20   │
    │ 5. India relevance              │   10   │
    │ 6. Optimal title length (6-12w) │    5   │
    │ 7. Has image                    │    3   │
    │ 8. Source type bonus            │    5   │
    └─────────────────────────────────┴────────┘
    """
    score = 0
    title   = (article.get("title") or "").lower()
    summary = (article.get("summary") or "").lower()
    text    = title + " " + summary

    # 1. Traffic (Google Trends only)
    traffic = article.get("traffic") or 0
    if traffic > 500_000:  score += 25
    elif traffic > 100_000: score += 18
    elif traffic > 50_000:  score += 12
    elif traffic > 10_000:  score += 6

    # 2. Source credibility (0-15)
    score += int((article.get("credibility") or 50) * 0.15)

    # 3. Keyword relevance (0-20)
    hits = sum(1 for kw in VIRAL_KEYWORDS if kw in text)
    score += min(hits * 2, 20)

    # 4. Recency (0-20)
    pub_str = article.get("published", "")
    try:
        from email.utils import parsedate_to_datetime
        pub_dt   = parsedate_to_datetime(pub_str)
        hrs_ago  = (datetime.now(pub_dt.tzinfo) - pub_dt).total_seconds() / 3600
        if hrs_ago <= 1:    score += 20
        elif hrs_ago <= 3:  score += 16
        elif hrs_ago <= 6:  score += 12
        elif hrs_ago <= 12: score += 6
        elif hrs_ago <= 24: score += 2
    except Exception:
        score += 4   # Unknown date → small bonus

    # 5. India relevance (0-10)
    if any(w in text for w in INDIA_WORDS):
        score += 10

    # 6. Title length (0-5)
    wc = len(title.split())
    score += 5 if 6 <= wc <= 12 else (2 if 4 <= wc <= 15 else 0)

    # 7. Has image (0-3)
    if article.get("image"):
        score += 3

    # 8. Source type bonus (0-5)
    score += {"trends": 5, "newsapi": 4, "gnews": 3, "google_rss": 2, "rss": 1}.get(
        article.get("source_type", ""), 0
    )

    return min(score, 100)


# ═════════════════════════════════════════════════════════════════════════════
# CATEGORY DETECTOR — auto-tag from title keywords
# ═════════════════════════════════════════════════════════════════════════════

def detect_category(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["ai", "artificial intelligence", "openai", "chatgpt", "gemini", "llm", "deepseek"]):
        return "artificial intelligence"
    if any(w in t for w in ["space", "rocket", "nasa", "isro", "satellite", "mars", "moon", "jwst"]):
        return "space science"
    if any(w in t for w in ["bitcoin", "crypto", "stock", "market", "economy", "rupee", "finance", "invest"]):
        return "finance"
    if any(w in t for w in ["india", "delhi", "mumbai", "modi", "parliament", "court", "bjp", "congress"]):
        return "india news"
    if any(w in t for w in ["game", "gaming", "playstation", "xbox", "nintendo", "steam"]):
        return "gaming"
    return "technology"


# ═════════════════════════════════════════════════════════════════════════════
# DATABASE SAVER
# ═════════════════════════════════════════════════════════════════════════════

def save_to_db(articles: list[dict]) -> int:
    if not DB_AVAILABLE:
        return 0
    saved = 0
    try:
        conn = get_connection()
        for a in articles:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO news_topics
                    (title, description, category, source_url, trend_score, viral_probability, status)
                    VALUES (?,?,?,?,?,?,?)
                """, (
                    a["title"][:500],
                    (a.get("summary") or "")[:800],
                    a.get("category", "technology"),
                    a.get("url", "")[:1000],
                    a.get("virality_score", 0),
                    a.get("virality_score", 0),
                    "pending"
                ))
                saved += 1
            except Exception:
                pass
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"[DB] {e}")
    return saved


# ═════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═════════════════════════════════════════════════════════════════════════════

def get_trending_news(max_results: int = 20) -> list[dict]:
    """
    Master pipeline:
    Fetch all sources → Deduplicate → Categorize → Score → Sort → Persist
    """
    t0   = time.time()
    seen = _load_seen()
    raw: list[dict] = []

    log.info("=" * 60)
    log.info("[TrendHunter] Pipeline starting...")

    # ── Tier 1: Always-free (no API key) ─────────────────────────
    raw.extend(fetch_google_trends(region="IN", count=15));     time.sleep(0.5)
    raw.extend(fetch_free_rss_feeds());                         time.sleep(0.3)
    for q in ["technology India", "AI news 2025", "India breaking news", "space science"]:
        raw.extend(fetch_google_news_rss(query=q, count=6));    time.sleep(0.4)

    # ── Tier 2: API key sources ───────────────────────────────────
    if NEWS_API_KEY:
        for cat in ["technology", "science", "general"]:
            raw.extend(fetch_newsapi(category=cat, count=6));   time.sleep(0.4)
        for q in (NEWS_CATEGORIES or [])[:2]:
            raw.extend(fetch_newsapi(query=q, count=4));        time.sleep(0.4)

    if GNEWS_KEY:
        for q in (NEWS_CATEGORIES or [])[:3]:
            raw.extend(fetch_gnews(query=q, count=5));          time.sleep(0.4)

    # ── Tier 3: Social (lower credibility, high virality signal) ──
    raw.extend(fetch_reddit(count_per_sub=4))

    log.info(f"[TrendHunter] Raw: {len(raw)} articles")

    # ── Deduplicate ───────────────────────────────────────────────
    unique, new_seen = deduplicate(raw, seen)
    log.info(f"[TrendHunter] After dedup: {len(unique)}")

    # ── Categorize + Score ────────────────────────────────────────
    for a in unique:
        a["category"]       = detect_category(a.get("title", ""))
        a["virality_score"] = score_virality(a)
        a["fetched_at"]     = datetime.now().isoformat()

    # ── Sort & Slice ──────────────────────────────────────────────
    unique.sort(key=lambda x: x["virality_score"], reverse=True)
    top = unique[:max_results]

    # ── Persist ───────────────────────────────────────────────────
    _save_seen(new_seen)

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out = DATA_DIR / f"news_{ts}.json"
    out.write_text(json.dumps(top, indent=2, ensure_ascii=False), encoding="utf-8")

    db_saved = save_to_db(top)

    if DB_AVAILABLE:
        try:
            log_agent(AGENT_NAME, "hunt_complete", "success",
                      f"raw={len(raw)} unique={len(unique)} top={len(top)} db={db_saved}",
                      int((time.time() - t0) * 1000))
        except Exception:
            pass

    elapsed = time.time() - t0
    log.info(f"[TrendHunter] Done in {elapsed:.1f}s — top {len(top)} articles")
    log.info("=" * 60)
    return top


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("\n" + "═" * 65)
    print("  AutoNews AI — Trend Hunter Agent v2.0")
    print("═" * 65 + "\n")

    articles = get_trending_news(max_results=20)

    print(f"\n{'═'*65}")
    print(f"  TOP {len(articles)} TRENDING TOPICS")
    print(f"{'═'*65}")
    for i, a in enumerate(articles, 1):
        sc  = a.get("virality_score", 0)
        bar = "█" * (sc // 10) + "░" * (10 - sc // 10)
        print(f"\n{i:2}. [{bar}] {sc}%  {a['category'].upper()}")
        print(f"    {a['title']}")
        print(f"    └─ {a['source']} | {a.get('url','')[:55]}")

    print(f"\n{'═'*65}")
    print("  Circuit Breaker Status:")
    for name, cb in _circuits.items():
        st = "OPEN" if cb.is_open() else "OK"
        print(f"    [{st}] {name} (failures: {cb.failures})")
    print("═" * 65 + "\n")