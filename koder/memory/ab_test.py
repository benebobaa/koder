"""A/B testing framework for comparing retrieval modes.

This module provides functionality to:
1. Deterministically assign tasks to test variants
2. Track success metrics per variant
3. Generate comparison reports
4. Enable data-driven decisions about embedding usage
"""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Literal

import structlog

from koder.config.settings import get_settings

logger = structlog.get_logger(__name__)


class ABTestManager:
    """
    Manages A/B testing for retrieval mode comparisons.

    Features:
    - Deterministic variant assignment (consistent for same task_id)
    - Tracks success metrics per variant
    - Statistical analysis of results
    - Comparison reports
    """

    def __init__(self, db_path: Path | None = None):
        """
        Initialize A/B test manager.

        Args:
            db_path: Path to SQLite database for persistent storage
        """
        settings = get_settings()

        if db_path is None:
            cache_dir = Path(settings.storage.cache_path)
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "ab_test.db"

        self.db_path = db_path
        self.enabled = settings.embeddings.ab_test_enabled
        self.ratio = settings.embeddings.ab_test_ratio

        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    variant TEXT NOT NULL,  -- 'control' or 'treatment'
                    mode TEXT NOT NULL,     -- 'off', 'lexical', 'primary', 'reranker'
                    task_description TEXT,
                    success BOOLEAN,
                    duration_seconds REAL,
                    context_provided BOOLEAN,
                    context_helpful BOOLEAN,
                    error_occurred BOOLEAN,
                    error_message TEXT,
                    metadata TEXT  -- JSON for additional info
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_variant
                ON ab_test_results(variant)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mode
                ON ab_test_results(mode)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON ab_test_results(timestamp)
            """)

            conn.commit()

    def get_variant(self, task_id: str) -> Literal["control", "treatment"]:
        """
        Deterministically assign task to control or treatment variant.

        Uses hash of task_id to ensure:
        1. Same task always gets same variant (reproducibility)
        2. Distribution matches configured ratio
        3. No bias in assignment

        Args:
            task_id: Unique identifier for the task

        Returns:
            'control' or 'treatment'
        """
        # Hash task_id to get consistent assignment
        hash_value = int(
            hashlib.md5(task_id.encode(), usedforsecurity=False).hexdigest(), 16
        )
        normalized = (hash_value % 1000) / 1000.0  # Value between 0 and 1

        # Assign based on ratio threshold
        if normalized < self.ratio:
            return "treatment"  # Use embeddings
        else:
            return "control"  # No embeddings (or baseline)

    def get_mode_for_variant(
        self, variant: Literal["control", "treatment"], default_mode: str = "reranker"
    ) -> str:
        """
        Get retrieval mode for a given variant.

        Args:
            variant: 'control' or 'treatment'
            default_mode: Mode to use for treatment group

        Returns:
            Retrieval mode string
        """
        if variant == "control":
            # Control group: no embeddings (lexical only or off)
            return "lexical"
        else:
            # Treatment group: use configured embedding mode
            return default_mode

    def record_result(
        self,
        task_id: str,
        variant: str,
        mode: str,
        success: bool,
        duration_seconds: float,
        task_description: str | None = None,
        context_provided: bool = False,
        context_helpful: bool | None = None,
        error_occurred: bool = False,
        error_message: str | None = None,
    ):
        """
        Record A/B test result for analysis.

        Args:
            task_id: Unique task identifier
            variant: 'control' or 'treatment'
            mode: Retrieval mode used
            success: Whether task completed successfully
            duration_seconds: Task execution time
            task_description: Optional task description
            context_provided: Whether context was provided
            context_helpful: Whether context was helpful (if known)
            error_occurred: Whether an error occurred
            error_message: Error message if applicable
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ab_test_results
                (timestamp, task_id, variant, mode, task_description,
                 success, duration_seconds, context_provided, context_helpful,
                 error_occurred, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    task_id,
                    variant,
                    mode,
                    task_description,
                    success,
                    duration_seconds,
                    context_provided,
                    context_helpful,
                    error_occurred,
                    error_message,
                ),
            )
            conn.commit()

        logger.debug(
            "ab_test_result_recorded",
            task_id=task_id,
            variant=variant,
            mode=mode,
            success=success,
        )

    def get_summary_stats(self, days: int = 7) -> dict:
        """
        Get summary statistics for A/B test.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with summary statistics
        """
        cutoff = datetime.now().timestamp() - (days * 86400)
        cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Overall stats by variant
            cursor = conn.execute(
                """
                SELECT
                    variant,
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END)
                        as successful_tasks,
                    AVG(duration_seconds) as avg_duration,
                    SUM(CASE WHEN context_provided THEN 1 ELSE 0 END)
                        as context_provided_count,
                    SUM(CASE WHEN context_helpful THEN 1 ELSE 0 END)
                        as context_helpful_count,
                    SUM(CASE WHEN error_occurred THEN 1 ELSE 0 END)
                        as error_count
                FROM ab_test_results
                WHERE timestamp >= ?
                GROUP BY variant
            """,
                (cutoff_iso,),
            )

            variant_stats = {}
            for row in cursor.fetchall():
                variant = row[0]
                total = row[1]
                successful = row[2]
                variant_stats[variant] = {
                    "total_tasks": total,
                    "successful_tasks": successful,
                    "success_rate": successful / max(total, 1),
                    "avg_duration_seconds": row[3],
                    "context_provided": row[4],
                    "context_helpful": row[5],
                    "error_count": row[6],
                    "error_rate": row[6] / max(total, 1),
                }

            # Stats by mode
            cursor = conn.execute(
                """
                SELECT
                    mode,
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_tasks,
                    AVG(duration_seconds) as avg_duration
                FROM ab_test_results
                WHERE timestamp >= ?
                GROUP BY mode
            """,
                (cutoff_iso,),
            )

            mode_stats = {}
            for row in cursor.fetchall():
                mode = row[0]
                total = row[1]
                successful = row[2]
                mode_stats[mode] = {
                    "total_tasks": total,
                    "successful_tasks": successful,
                    "success_rate": successful / max(total, 1),
                    "avg_duration_seconds": row[3],
                }

        return {
            "period_days": days,
            "variant_stats": variant_stats,
            "mode_stats": mode_stats,
            "enabled": self.enabled,
            "ratio": self.ratio,
        }

    def generate_comparison_report(self, days: int = 7) -> str:
        """
        Generate human-readable comparison report.

        Args:
            days: Number of days to analyze

        Returns:
            Formatted report string
        """
        stats = self.get_summary_stats(days)

        lines = [f"A/B Test Comparison Report ({days} days)", "=" * 50, ""]

        if not self.enabled:
            lines.append("⚠️  A/B testing is currently DISABLED")
            lines.append("")

        # Variant comparison
        lines.append("Variant Comparison:")
        lines.append("-" * 50)

        for variant, vstats in stats["variant_stats"].items():
            lines.append(f"\n{variant.upper()}:")
            lines.append(f"  Total tasks: {vstats['total_tasks']}")
            lines.append(f"  Success rate: {vstats['success_rate']:.1%}")
            lines.append(f"  Avg duration: {vstats['avg_duration_seconds']:.2f}s")
            lines.append(f"  Context provided: {vstats['context_provided']}")
            lines.append(f"  Context helpful: {vstats['context_helpful']}")
            lines.append(f"  Error rate: {vstats['error_rate']:.1%}")

        # Mode comparison
        lines.append("\n\nMode Comparison:")
        lines.append("-" * 50)

        for mode, mstats in stats["mode_stats"].items():
            lines.append(f"\n{mode.upper()}:")
            lines.append(f"  Total tasks: {mstats['total_tasks']}")
            lines.append(f"  Success rate: {mstats['success_rate']:.1%}")
            lines.append(f"  Avg duration: {mstats['avg_duration_seconds']:.2f}s")

        # Calculate uplift (if both variants exist)
        if (
            "control" in stats["variant_stats"]
            and "treatment" in stats["variant_stats"]
        ):
            control = stats["variant_stats"]["control"]
            treatment = stats["variant_stats"]["treatment"]

            success_uplift = (
                (treatment["success_rate"] - control["success_rate"])
                / max(control["success_rate"], 0.01)
            ) * 100

            duration_change = (
                (treatment["avg_duration_seconds"] - control["avg_duration_seconds"])
                / max(control["avg_duration_seconds"], 0.01)
            ) * 100

            lines.append("\n\nTreatment vs Control:")
            lines.append("-" * 50)
            lines.append(f"Success rate uplift: {success_uplift:+.1f}%")
            lines.append(f"Duration change: {duration_change:+.1f}%")

            # Recommendation
            lines.append("\n\nRecommendation:")
            lines.append("-" * 50)

            if success_uplift > 5 and duration_change < 20:
                lines.append("✅ Treatment (embeddings) shows clear benefit")
                lines.append("   Consider enabling embeddings in production")
            elif success_uplift < -5:
                lines.append("❌ Treatment (embeddings) performs worse")
                lines.append("   Consider disabling embeddings or investigating issues")
            else:
                lines.append("⚠️  Results are inconclusive")
                lines.append("   Continue testing or increase sample size")

        return "\n".join(lines)

    def reset_results(self):
        """Delete all A/B test results (use with caution)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM ab_test_results")
            conn.commit()

        logger.info("ab_test_results_reset")


# Singleton instance
_ab_test_manager: ABTestManager | None = None


def get_ab_test_manager() -> ABTestManager:
    """Get or create global A/B test manager instance."""
    global _ab_test_manager
    if _ab_test_manager is None:
        _ab_test_manager = ABTestManager()
    return _ab_test_manager
