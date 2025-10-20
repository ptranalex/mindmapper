"""SQLite-based caching for enrichment results."""

import hashlib
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class EnrichmentCache:
    """SQLite cache for storing enrichment results per row hash."""

    def __init__(self, cache_dir: str = ".cache") -> None:
        """Initialize the cache.

        Args:
            cache_dir: Directory to store the cache database
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "enrichment.db"
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "PRAGMA journal_mode=WAL"
        )  # Write-Ahead Logging for better concurrency
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS enrichment_cache (
                row_hash TEXT PRIMARY KEY,
                tldr TEXT NOT NULL,
                challenge TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
        conn.close()
        logger.debug(f"Initialized cache database at {self.db_path}")

    def compute_hash(
        self, category: str, subcategory: str, topic: str, description: str
    ) -> str:
        """Compute MD5 hash for a row.

        Args:
            category: Category name
            subcategory: Subcategory name
            topic: Topic name
            description: Description text

        Returns:
            MD5 hash string
        """
        content = f"{category}|{subcategory}|{topic}|{description}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def get(self, row_hash: str) -> Optional[Tuple[str, str]]:
        """Get cached enrichment result.

        Args:
            row_hash: MD5 hash of the row

        Returns:
            Tuple of (tldr, challenge) if cached, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT tldr, challenge FROM enrichment_cache WHERE row_hash = ?",
            (row_hash,),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            logger.debug(f"Cache hit for hash {row_hash[:8]}...")
            return (result[0], result[1])

        logger.debug(f"Cache miss for hash {row_hash[:8]}...")
        return None

    def set(self, row_hash: str, tldr: str, challenge: str) -> None:
        """Store enrichment result in cache.

        Args:
            row_hash: MD5 hash of the row
            tldr: Generated TLDR summary
            challenge: Challenge level (practice or expert)
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT OR REPLACE INTO enrichment_cache 
               (row_hash, tldr, challenge, created_at) 
               VALUES (?, ?, ?, ?)""",
            (row_hash, tldr, challenge, datetime.now()),
        )
        conn.commit()
        conn.close()
        logger.debug(f"Cached result for hash {row_hash[:8]}...")

    def exists(self, row_hash: str) -> bool:
        """Check if a row hash exists in cache.

        Args:
            row_hash: MD5 hash of the row

        Returns:
            True if cached, False otherwise
        """
        return self.get(row_hash) is not None

    def stats(self) -> Tuple[int, Optional[datetime]]:
        """Get cache statistics.

        Returns:
            Tuple of (total_entries, latest_update)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*), MAX(created_at) FROM enrichment_cache")
        result = cursor.fetchone()
        conn.close()

        count = result[0] if result else 0
        latest = datetime.fromisoformat(result[1]) if result and result[1] else None
        return (count, latest)
