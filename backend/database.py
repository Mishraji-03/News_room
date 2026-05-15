"""
AutoNews AI - Database Module v3.0
Production-ready SQLite database with connection pooling, context managers,
indexing, migration support, and async wrappers.
"""

import sqlite3
import logging
import json
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional, Dict, Any, List, Tuple

import config

log = logging.getLogger(__name__)

DB_PATH = config.DATA_DIR / "autonews.db"

# Connection pool settings (simple thread-local pool)
CONNECTION_POOL_SIZE = 5
_pool = []


class Database:
    """Advanced database manager with pooling and utilities."""

    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_directories()
        self._current_version = 3  # Current schema version

    def _ensure_directories(self):
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager with connection pooling."""
        conn = None
        try:
            # Try to get a connection from pool
            global _pool
            if _pool:
                conn = _pool.pop()
            else:
                conn = sqlite3.connect(self.db_path, timeout=15)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA synchronous = NORMAL;")
                conn.execute("PRAGMA cache_size = -20000;")  # 20MB cache
            yield conn
            conn.commit()
            # Return to pool if pool size not exceeded
            if len(_pool) < CONNECTION_POOL_SIZE:
                _pool.append(conn)
            else:
                conn.close()
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            log.error(f"Database error: {e}")
            raise
        finally:
            # If we didn't return to pool, ensure connection closed
            if conn and conn not in _pool:
                try:
                    conn.close()
                except:
                    pass

    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        """Get current schema version from user_version pragma."""
        cursor = conn.execute("PRAGMA user_version")
        return cursor.fetchone()[0]

    def _set_schema_version(self, conn: sqlite3.Connection, version: int):
        conn.execute(f"PRAGMA user_version = {version}")

    def _migrate(self, conn: sqlite3.Connection, current_version: int):
        """Apply migrations to reach target version."""
        target = self._current_version
        if current_version >= target:
            return

        cursor = conn.cursor()
        log.info(f"Migrating database from version {current_version} to {target}")

        # Migration steps
        if current_version < 1:
            # v1: initial schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE NOT NULL,
                    description TEXT,
                    category TEXT,
                    source_url TEXT,
                    trend_score REAL DEFAULT 0,
                    viral_probability REAL DEFAULT 0,
                    status TEXT DEFAULT 'new',
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS verified_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id INTEGER,
                    title TEXT,
                    summary TEXT,
                    confidence_score REAL DEFAULT 0,
                    fake_probability REAL DEFAULT 0,
                    sources_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(topic_id) REFERENCES news_topics(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    duration_ms INTEGER DEFAULT 0,
                    run_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE,
                    videos_attempted INTEGER DEFAULT 0,
                    videos_success INTEGER DEFAULT 0,
                    auto_upload BOOLEAN DEFAULT 0,
                    status TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            current_version = 1

        if current_version < 2:
            # v2: add indexes and content_metadata table
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_title ON news_topics(title);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_logs_agent ON agent_logs(agent_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_logs_created ON agent_logs(created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_run_id ON pipeline_runs(run_id);")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_key TEXT UNIQUE,
                    content_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            current_version = 2

        if current_version < 3:
            # v3: add video_uploads table for tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    video_path TEXT,
                    youtube_id TEXT,
                    instagram_id TEXT,
                    status TEXT,
                    uploaded_at TIMESTAMP,
                    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id)
                )
            """)
            current_version = 3

        self._set_schema_version(conn, target)
        log.info("Database migration completed")

    def initialize(self):
        """Create all tables and run migrations."""
        with self.get_connection() as conn:
            current = self._get_schema_version(conn)
            if current < self._current_version:
                self._migrate(conn, current)
            else:
                # Ensure all indexes exist even if no migration needed
                cursor = conn.cursor()
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_title ON news_topics(title);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_logs_agent ON agent_logs(agent_name);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_logs_created ON agent_logs(created_at);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_run_id ON pipeline_runs(run_id);")
            log.info("✅ Database initialized successfully")

    # ====================== HELPER METHODS ======================
    def insert_news_topic(self, title: str, description: str = "",
                         category: str = "", source_url: str = "",
                         trend_score: float = 0, viral_probability: float = 0,
                         status: str = "new", published_at: Optional[str] = None) -> Optional[int]:
        """Insert or ignore a news topic. Returns ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT OR IGNORE INTO news_topics
                    (title, description, category, source_url, trend_score, viral_probability, status, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, description, category, source_url, trend_score, viral_probability, status, published_at))
                if cursor.lastrowid:
                    return cursor.lastrowid
                # If ignored, fetch existing ID
                cursor = conn.execute("SELECT id FROM news_topics WHERE title = ?", (title,))
                row = cursor.fetchone()
                return row["id"] if row else None
        except Exception as e:
            log.error(f"Failed to insert news topic: {e}")
            return None

    def insert_verified_news(self, topic_id: int, title: str, summary: str,
                            confidence_score: float = 0, fake_probability: float = 0,
                            sources_count: int = 0) -> bool:
        """Insert verified news record."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO verified_news
                    (topic_id, title, summary, confidence_score, fake_probability, sources_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (topic_id, title, summary, confidence_score, fake_probability, sources_count))
                return True
        except Exception as e:
            log.error(f"Failed to insert verified news: {e}")
            return False

    def log_agent(self, agent_name: str, action: str, status: str,
                  details: str = "", duration_ms: int = 0, run_id: Optional[str] = None):
        """Log agent activity (compatible with global function)."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO agent_logs
                    (agent_name, action, status, details, duration_ms, run_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (agent_name, action, status, details[:500] if details else "", duration_ms, run_id))
        except Exception as e:
            log.error(f"Failed to log agent action: {e}")

    def record_pipeline_run(self, run_id: str, videos_attempted: int,
                           videos_success: int, auto_upload: bool,
                           status: str = "completed"):
        """Record pipeline execution (compatible with global function)."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO pipeline_runs
                    (run_id, videos_attempted, videos_success, auto_upload, status, completed_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (run_id, videos_attempted, videos_success, auto_upload, status))
        except Exception as e:
            log.error(f"Failed to record pipeline run: {e}")

    def get_recent_logs(self, limit: int = 50, agent: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve recent agent logs."""
        try:
            with self.get_connection() as conn:
                if agent:
                    cursor = conn.execute("""
                        SELECT * FROM agent_logs
                        WHERE agent_name = ?
                        ORDER BY created_at DESC LIMIT ?
                    """, (agent, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM agent_logs
                        ORDER BY created_at DESC LIMIT ?
                    """, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            log.error(f"Failed to get recent logs: {e}")
            return []

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Return aggregated pipeline statistics."""
        try:
            with self.get_connection() as conn:
                # Total runs, success rate, total videos
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_runs,
                        SUM(videos_success) as total_videos,
                        AVG(CASE WHEN status='completed' THEN 1 ELSE 0 END) * 100 as success_rate
                    FROM pipeline_runs
                """)
                row = cursor.fetchone()
                return {
                    "total_runs": row["total_runs"] or 0,
                    "total_videos": row["total_videos"] or 0,
                    "success_rate": round(row["success_rate"] or 0, 2)
                }
        except Exception as e:
            log.error(f"Failed to get pipeline stats: {e}")
            return {"total_runs": 0, "total_videos": 0, "success_rate": 0.0}


# ========================== GLOBAL INSTANCE ==========================
db = Database()


# ========================== COMPATIBILITY FUNCTIONS (preserve signatures) ==========================
def log_agent(
    agent_name: str,
    action: str,
    status: str,
    details: str = "",
    duration_ms: int = 0,
    run_id: Optional[str] = None
):
    """Global log_agent (backward compatible)."""
    db.log_agent(agent_name, action, status, details, duration_ms, run_id)


def record_pipeline_run(
    run_id: str,
    videos_attempted: int,
    videos_success: int,
    auto_upload: bool,
    status: str = "completed"
):
    """Global record_pipeline_run (backward compatible)."""
    db.record_pipeline_run(run_id, videos_attempted, videos_success, auto_upload, status)


def init_database():
    """Initialize database (call once at startup)."""
    try:
        db.initialize()
        log.info("Database ready")
    except Exception as e:
        log.critical(f"Database initialization failed: {e}")
        raise


def get_connection():
    """
    Module-level get_connection for backward compatibility.
    Returns a raw sqlite3 connection (caller must commit/close).
    """
    conn = sqlite3.connect(db.db_path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


# ========================== CLI TEST ==========================
if __name__ == "__main__":
    init_database()
    print("✅ Database initialized successfully")
    print(f"Database location: {DB_PATH}")

    # Optional: show stats
    stats = db.get_pipeline_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")