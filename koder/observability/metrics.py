"""Simple metrics collection."""

import time
from collections import defaultdict
from typing import Any, Optional


class MetricsCollector:
    """Simple in-memory metrics collector."""

    def __init__(self):
        """Initialize metrics collector."""
        self.counters: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = {}
        self.timings: dict[str, list[float]] = defaultdict(list)

    def increment(self, name: str, value: int = 1) -> None:
        """
        Increment a counter.

        Args:
            name: Counter name
            value: Value to increment by
        """
        self.counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        """
        Set a gauge value.

        Args:
            name: Gauge name
            value: Gauge value
        """
        self.gauges[name] = value

    def record_timing(self, name: str, duration: float) -> None:
        """
        Record a timing measurement.

        Args:
            name: Timing name
            duration: Duration in seconds
        """
        self.timings[name].append(duration)

    def get_stats(self) -> dict[str, Any]:
        """
        Get all metrics statistics.

        Returns:
            Dictionary of metrics
        """
        stats = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timings": {},
        }

        # Calculate timing statistics
        for name, durations in self.timings.items():
            if durations:
                stats["timings"][name] = {
                    "count": len(durations),
                    "total": sum(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                }

        return stats

    def reset(self) -> None:
        """Reset all metrics."""
        self.counters.clear()
        self.gauges.clear()
        self.timings.clear()


class Timer:
    """Context manager for timing operations."""

    def __init__(self, metrics: MetricsCollector, name: str):
        """
        Initialize timer.

        Args:
            metrics: Metrics collector
            name: Timer name
        """
        self.metrics = metrics
        self.name = name
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and record duration."""
        if self.start_time is not None:
            duration = time.time() - self.start_time
            self.metrics.record_timing(self.name, duration)


# Global metrics instance
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
