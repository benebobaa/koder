"""Cost tracking and budget management for embedding API calls."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import structlog

from koder.config.settings import get_settings

logger = structlog.get_logger(__name__)


class BudgetExceededError(Exception):
    """Raised when embedding budget is exceeded."""
    pass


class CostTracker:
    """
    Tracks embedding API usage and enforces budget limits.

    Features:
    - Persistent storage of API call counts
    - Daily and monthly budget enforcement
    - Cost estimation based on Google Gemini pricing
    - Usage analytics and reporting
    """

    # Google Gemini text-embedding-004 pricing (as of 2024)
    # Free tier: 1500 requests/day
    # Paid tier: $0.00001 per 1k characters (approximately)
    # Approximate cost per embedding call (assuming 1000 chars avg)
    COST_PER_QUERY_USD = 0.00001
    COST_PER_DOCUMENT_USD = 0.00001
    FREE_TIER_DAILY_LIMIT = 1500

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize cost tracker.

        Args:
            db_path: Path to SQLite database for persistent storage.
                    If None, uses settings.storage.cache_path
        """
        settings = get_settings()

        if db_path is None:
            cache_dir = Path(settings.storage.cache_path)
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "cost_tracker.db"

        self.db_path = db_path
        self.max_monthly_cost = settings.embeddings.max_monthly_cost_usd
        self.max_daily_calls = settings.embeddings.max_daily_api_calls

        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    call_type TEXT NOT NULL,  -- 'query' or 'document'
                    num_calls INTEGER NOT NULL DEFAULT 1,
                    estimated_cost_usd REAL NOT NULL,
                    mode TEXT,  -- 'off', 'lexical', 'primary', 'reranker'
                    metadata TEXT  -- JSON for additional info
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON api_calls(timestamp)
            """)

            conn.commit()

    def record_query_call(self, mode: str = "unknown", num_queries: int = 1):
        """
        Record a query embedding API call.

        Args:
            mode: Retrieval mode used ('off', 'lexical', 'primary', 'reranker')
            num_queries: Number of queries embedded in this call
        """
        cost = self.COST_PER_QUERY_USD * num_queries

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_calls
                (timestamp, call_type, num_calls, estimated_cost_usd, mode)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "query",
                num_queries,
                cost,
                mode
            ))
            conn.commit()

        logger.debug(
            "api_call_recorded",
            call_type="query",
            num_queries=num_queries,
            cost_usd=cost,
            mode=mode
        )

    def record_document_call(self, mode: str = "unknown", num_documents: int = 1):
        """
        Record a document embedding API call.

        Args:
            mode: Retrieval mode used
            num_documents: Number of documents embedded in this call
        """
        cost = self.COST_PER_DOCUMENT_USD * num_documents

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_calls
                (timestamp, call_type, num_calls, estimated_cost_usd, mode)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                "document",
                num_documents,
                cost,
                mode
            ))
            conn.commit()

        logger.debug(
            "api_call_recorded",
            call_type="document",
            num_documents=num_documents,
            cost_usd=cost,
            mode=mode
        )

    def check_budget_before_call(self, num_calls: int = 1) -> bool:
        """
        Check if budget allows this API call.

        Args:
            num_calls: Number of API calls to be made

        Returns:
            True if within budget, False otherwise

        Raises:
            BudgetExceededError: If budget would be exceeded
        """
        daily_calls = self.get_daily_call_count()
        monthly_cost = self.get_monthly_cost()

        # Check daily call limit
        if daily_calls + num_calls > self.max_daily_calls:
            logger.warning(
                "daily_budget_exceeded",
                daily_calls=daily_calls,
                max_daily_calls=self.max_daily_calls,
                attempted_calls=num_calls
            )
            raise BudgetExceededError(
                f"Daily API call limit exceeded: {daily_calls}/{self.max_daily_calls}. "
                f"Attempted to make {num_calls} more calls."
            )

        # Check monthly cost limit
        estimated_additional_cost = self.COST_PER_QUERY_USD * num_calls
        if monthly_cost + estimated_additional_cost > self.max_monthly_cost:
            logger.warning(
                "monthly_budget_exceeded",
                monthly_cost_usd=monthly_cost,
                max_monthly_cost_usd=self.max_monthly_cost,
                estimated_additional_cost_usd=estimated_additional_cost
            )
            raise BudgetExceededError(
                f"Monthly cost budget exceeded: ${monthly_cost:.2f}/${self.max_monthly_cost:.2f}. "
                f"Attempted call would cost ${estimated_additional_cost:.5f}."
            )

        # Warn at 80% threshold
        if daily_calls >= self.max_daily_calls * 0.8:
            logger.warning(
                "daily_budget_warning",
                daily_calls=daily_calls,
                max_daily_calls=self.max_daily_calls,
                percent_used=(daily_calls / self.max_daily_calls) * 100
            )

        if monthly_cost >= self.max_monthly_cost * 0.8:
            logger.warning(
                "monthly_budget_warning",
                monthly_cost_usd=monthly_cost,
                max_monthly_cost_usd=self.max_monthly_cost,
                percent_used=(monthly_cost / self.max_monthly_cost) * 100
            )

        return True

    def get_daily_call_count(self, date: Optional[datetime] = None) -> int:
        """
        Get total API calls for a specific day.

        Args:
            date: Date to query (defaults to today)

        Returns:
            Total number of API calls
        """
        if date is None:
            date = datetime.now()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COALESCE(SUM(num_calls), 0)
                FROM api_calls
                WHERE timestamp >= ? AND timestamp < ?
            """, (start_of_day.isoformat(), end_of_day.isoformat()))

            return cursor.fetchone()[0]

    def get_monthly_cost(self, year: Optional[int] = None, month: Optional[int] = None) -> float:
        """
        Get total estimated cost for a specific month.

        Args:
            year: Year to query (defaults to current year)
            month: Month to query (defaults to current month)

        Returns:
            Total estimated cost in USD
        """
        now = datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month

        start_of_month = datetime(year, month, 1)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1)
        else:
            end_of_month = datetime(year, month + 1, 1)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COALESCE(SUM(estimated_cost_usd), 0.0)
                FROM api_calls
                WHERE timestamp >= ? AND timestamp < ?
            """, (start_of_month.isoformat(), end_of_month.isoformat()))

            return cursor.fetchone()[0]

    def get_usage_stats(self, days: int = 7) -> dict:
        """
        Get usage statistics for the past N days.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with usage statistics
        """
        cutoff = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            # Total calls and cost
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_requests,
                    COALESCE(SUM(num_calls), 0) as total_calls,
                    COALESCE(SUM(estimated_cost_usd), 0.0) as total_cost
                FROM api_calls
                WHERE timestamp >= ?
            """, (cutoff.isoformat(),))

            total_requests, total_calls, total_cost = cursor.fetchone()

            # Calls by mode
            cursor = conn.execute("""
                SELECT mode, COALESCE(SUM(num_calls), 0) as calls
                FROM api_calls
                WHERE timestamp >= ?
                GROUP BY mode
            """, (cutoff.isoformat(),))

            calls_by_mode = dict(cursor.fetchall())

            # Daily breakdown
            cursor = conn.execute("""
                SELECT
                    DATE(timestamp) as date,
                    COALESCE(SUM(num_calls), 0) as calls,
                    COALESCE(SUM(estimated_cost_usd), 0.0) as cost
                FROM api_calls
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """, (cutoff.isoformat(),))

            daily_breakdown = [
                {"date": row[0], "calls": row[1], "cost_usd": row[2]}
                for row in cursor.fetchall()
            ]

        return {
            "period_days": days,
            "total_requests": total_requests,
            "total_calls": total_calls,
            "total_cost_usd": total_cost,
            "avg_daily_calls": total_calls / max(days, 1),
            "avg_daily_cost_usd": total_cost / max(days, 1),
            "calls_by_mode": calls_by_mode,
            "daily_breakdown": daily_breakdown,
            "budget": {
                "max_daily_calls": self.max_daily_calls,
                "max_monthly_cost_usd": self.max_monthly_cost,
                "today_calls": self.get_daily_call_count(),
                "month_cost_usd": self.get_monthly_cost(),
            }
        }

    def reset_stats(self):
        """Delete all tracking data (use with caution)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM api_calls")
            conn.commit()

        logger.info("cost_tracker_reset")


# Singleton instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
