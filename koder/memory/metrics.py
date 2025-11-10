"""Embedding metrics and monitoring system."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from koder.config.settings import get_settings
from koder.observability.logging import get_logger

logger = get_logger(__name__)


class EmbeddingMetrics:
    """Tracks and reports embedding system metrics."""

    def __init__(self, workspace_path: str):
        """
        Initialize metrics tracker.

        Args:
            workspace_path: Path to workspace directory
        """
        self.workspace_path = Path(workspace_path).resolve()
        self.settings = get_settings()
        self.metrics_file = (
            Path(self.settings.storage.cache_path) / "embedding_metrics.json"
        )
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing metrics
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from file."""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error("metrics_load_failed", error=str(e))

        # Default metrics structure
        return {
            "workspace": str(self.workspace_path),
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_documents": 0,
            "total_chunks": 0,
            "file_types": {},
            "indexing_stats": {
                "total_indexing_time": 0.0,
                "average_indexing_time": 0.0,
                "files_indexed": 0,
                "files_updated": 0,
                "files_skipped": 0,
                "indexing_errors": 0,
            },
            "search_stats": {
                "total_searches": 0,
                "average_search_time": 0.0,
                "total_search_time": 0.0,
                "failed_searches": 0,
            },
            "daily_stats": {},
            "health": {"status": "unknown", "last_health_check": None, "issues": []},
        }

    def _save_metrics(self):
        """Save metrics to file."""
        try:
            self.metrics["last_updated"] = datetime.now().isoformat()
            with open(self.metrics_file, "w") as f:
                json.dump(self.metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error("metrics_save_failed", error=str(e))

    def record_indexing_operation(
        self,
        operation_type: str,
        files_processed: int = 0,
        files_updated: int = 0,
        files_skipped: int = 0,
        errors: int = 0,
        duration: float = 0.0,
        file_types: Optional[Dict[str, int]] = None,
    ):
        """
        Record an indexing operation.

        Args:
            operation_type: Type of operation (full, incremental, watch)
            files_processed: Number of files processed
            files_updated: Number of files updated/indexed
            files_skipped: Number of files skipped
            errors: Number of errors encountered
            duration: Duration in seconds
            file_types: Dictionary of file types and counts
        """
        try:
            # Update indexing stats
            stats = self.metrics["indexing_stats"]
            stats["total_indexing_time"] += duration
            stats["files_indexed"] += files_processed
            stats["files_updated"] += files_updated
            stats["files_skipped"] += files_skipped
            stats["indexing_errors"] += errors

            if stats["files_indexed"] > 0:
                stats["average_indexing_time"] = (
                    stats["total_indexing_time"] / stats["files_indexed"]
                )

            # Update file types
            if file_types:
                for ext, count in file_types.items():
                    self.metrics["file_types"][ext] = (
                        self.metrics["file_types"].get(ext, 0) + count
                    )

            # Update daily stats
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in self.metrics["daily_stats"]:
                self.metrics["daily_stats"][today] = {
                    "operations": 0,
                    "files_processed": 0,
                    "duration": 0.0,
                    "errors": 0,
                }

            daily = self.metrics["daily_stats"][today]
            daily["operations"] += 1
            daily["files_processed"] += files_processed
            daily["duration"] += duration
            daily["errors"] += errors

            self._save_metrics()

            logger.info(
                "indexing_metrics_recorded",
                operation_type=operation_type,
                files_processed=files_processed,
                duration=duration,
            )

        except Exception as e:
            logger.error("indexing_metrics_record_failed", error=str(e))

    def record_search_operation(
        self, query: str, results_count: int, duration: float, success: bool = True
    ):
        """
        Record a search operation.

        Args:
            query: Search query
            results_count: Number of results returned
            duration: Search duration in seconds
            success: Whether search was successful
        """
        try:
            # Update search stats
            stats = self.metrics["search_stats"]
            stats["total_searches"] += 1
            stats["total_search_time"] += duration

            if stats["total_searches"] > 0:
                stats["average_search_time"] = (
                    stats["total_search_time"] / stats["total_searches"]
                )

            if not success:
                stats["failed_searches"] += 1

            # Update daily stats
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in self.metrics["daily_stats"]:
                self.metrics["daily_stats"][today] = {
                    "searches": 0,
                    "search_duration": 0.0,
                    "search_errors": 0,
                }

            daily = self.metrics["daily_stats"][today]
            daily["searches"] = daily.get("searches", 0) + 1
            daily["search_duration"] = daily.get("search_duration", 0.0) + duration
            if not success:
                daily["search_errors"] = daily.get("search_errors", 0) + 1

            self._save_metrics()

            logger.info(
                "search_metrics_recorded",
                query_length=len(query),
                results_count=results_count,
                duration=duration,
                success=success,
            )

        except Exception as e:
            logger.error("search_metrics_record_failed", error=str(e))

    def update_document_count(
        self, total_chunks: int, file_types: Optional[Dict[str, int]] = None
    ):
        """
        Update document count information.

        Args:
            total_chunks: Total number of chunks in vector store
            file_types: Dictionary of file types and counts
        """
        try:
            self.metrics["total_chunks"] = total_chunks

            if file_types:
                self.metrics["file_types"].update(file_types)

            self._save_metrics()

        except Exception as e:
            logger.error("document_count_update_failed", error=str(e))

    def check_health(self) -> Dict[str, Any]:
        """
        Perform health check of embedding system.

        Returns:
            Health check results
        """
        health_info = {"status": "healthy", "issues": [], "warnings": [], "metrics": {}}

        try:
            # Check if metrics are recent
            last_updated = self.metrics.get("last_updated")
            if last_updated:
                last_update_time = datetime.fromisoformat(last_updated)
                hours_since_update = (
                    datetime.now() - last_update_time
                ).total_seconds() / 3600

                if hours_since_update > 24:
                    health_info["warnings"].append(
                        f"Metrics not updated for {hours_since_update:.1f} hours"
                    )

            # Check error rates
            indexing_stats = self.metrics.get("indexing_stats", {})
            search_stats = self.metrics.get("search_stats", {})

            if indexing_stats.get("files_indexed", 0) > 0:
                error_rate = (
                    indexing_stats.get("indexing_errors", 0)
                    / indexing_stats["files_indexed"]
                )
                if error_rate > 0.1:  # 10% error rate
                    health_info["issues"].append(
                        f"High indexing error rate: {error_rate:.1%}"
                    )

            if search_stats.get("total_searches", 0) > 0:
                search_error_rate = (
                    search_stats.get("failed_searches", 0)
                    / search_stats["total_searches"]
                )
                if search_error_rate > 0.05:  # 5% error rate
                    health_info["issues"].append(
                        f"High search error rate: {search_error_rate:.1%}"
                    )

            # Check performance
            avg_indexing_time = indexing_stats.get("average_indexing_time", 0)
            if avg_indexing_time > 5.0:  # 5 seconds per file
                health_info["warnings"].append(
                    f"Slow indexing performance: {avg_indexing_time:.1f}s per file"
                )

            avg_search_time = search_stats.get("average_search_time", 0)
            if avg_search_time > 2.0:  # 2 seconds per search
                health_info["warnings"].append(
                    f"Slow search performance: {avg_search_time:.1f}s per search"
                )

            # Check document count
            total_chunks = self.metrics.get("total_chunks", 0)
            if total_chunks == 0:
                health_info["warnings"].append("No indexed documents found")
            elif total_chunks < 10:
                health_info["warnings"].append("Very few indexed documents")

            # Determine overall status
            if health_info["issues"]:
                health_info["status"] = "unhealthy"
            elif health_info["warnings"]:
                health_info["status"] = "degraded"

            # Add summary metrics
            health_info["metrics"] = {
                "total_chunks": total_chunks,
                "total_files_indexed": indexing_stats.get("files_indexed", 0),
                "total_searches": search_stats.get("total_searches", 0),
                "average_indexing_time": avg_indexing_time,
                "average_search_time": avg_search_time,
            }

            # Update health in metrics
            self.metrics["health"] = {
                "status": health_info["status"],
                "last_health_check": datetime.now().isoformat(),
                "issues": health_info["issues"],
                "warnings": health_info["warnings"],
            }

            self._save_metrics()

        except Exception as e:
            health_info["status"] = "error"
            health_info["issues"].append(f"Health check failed: {str(e)}")
            logger.error("health_check_failed", error=str(e))

        return health_info

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        try:
            # Perform health check
            health = self.check_health()

            # Calculate recent activity (last 7 days)
            recent_stats = {"indexing": 0, "searching": 0, "errors": 0}
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            for date, daily_stats in self.metrics.get("daily_stats", {}).items():
                if date >= seven_days_ago:
                    recent_stats["indexing"] += daily_stats.get("files_processed", 0)
                    recent_stats["searching"] += daily_stats.get("searches", 0)
                    recent_stats["errors"] += daily_stats.get(
                        "errors", 0
                    ) + daily_stats.get("search_errors", 0)

            return {
                "workspace": self.metrics["workspace"],
                "created_at": self.metrics["created_at"],
                "last_updated": self.metrics["last_updated"],
                "health": health["status"],
                "documents": {
                    "total_chunks": self.metrics.get("total_chunks", 0),
                    "file_types": dict(
                        sorted(
                            self.metrics.get("file_types", {}).items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )[:10]
                    ),
                },
                "performance": {
                    "indexing": {
                        "files_indexed": self.metrics["indexing_stats"][
                            "files_indexed"
                        ],
                        "average_time": self.metrics["indexing_stats"][
                            "average_indexing_time"
                        ],
                        "total_time": self.metrics["indexing_stats"][
                            "total_indexing_time"
                        ],
                    },
                    "searching": {
                        "total_searches": self.metrics["search_stats"][
                            "total_searches"
                        ],
                        "average_time": self.metrics["search_stats"][
                            "average_search_time"
                        ],
                        "failed_searches": self.metrics["search_stats"][
                            "failed_searches"
                        ],
                    },
                },
                "recent_activity": recent_stats,
                "issues": health["issues"],
                "warnings": health["warnings"],
            }

        except Exception as e:
            logger.error("summary_generation_failed", error=str(e))
            return {"error": str(e)}

    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = self._load_metrics()  # Reload defaults
        self.metrics["created_at"] = datetime.now().isoformat()
        self._save_metrics()
        logger.info("metrics_reset")


# Global metrics instances
_metrics_instances: Dict[str, EmbeddingMetrics] = {}


def get_metrics(workspace_path: str) -> EmbeddingMetrics:
    """Get or create metrics instance for a workspace."""
    workspace_key = str(Path(workspace_path).resolve())

    if workspace_key not in _metrics_instances:
        _metrics_instances[workspace_key] = EmbeddingMetrics(workspace_path)

    return _metrics_instances[workspace_key]
