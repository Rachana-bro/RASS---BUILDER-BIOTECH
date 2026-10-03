"""
RASS-BUILDER: Stage 10 Observability & Operational Metrics
Provides lightweight in-memory metrics collection for system requests,
durations, job outcomes, and operational failure modes.
"""

import time
import threading
from typing import Dict, Any, List


class OperationalMetricsCollector:
    """
    Thread-safe operational telemetry collector.
    Collects request volume, HTTP status distribution, latencies,
    and background worker pipeline metrics.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.start_time = time.time()
        self.total_requests = 0
        self.failed_requests = 0
        self.status_codes: Dict[int, int] = {}
        self.route_hits: Dict[str, int] = {}
        self.latencies: List[float] = []

        # Job / Pipeline metrics
        self.jobs_enqueued = 0
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.jobs_cancelled = 0

        # Error counts
        self.database_errors = 0
        self.worker_errors = 0
        self.rate_limit_hits = 0

    def record_request(self, method: str, path: str, status_code: int, duration_ms: float):
        """Records an HTTP request outcome and latency."""
        with self._lock:
            self.total_requests += 1
            if status_code >= 400:
                self.failed_requests += 1
            if status_code == 429:
                self.rate_limit_hits += 1

            self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
            route_key = f"{method.upper()} {path}"
            self.route_hits[route_key] = self.route_hits.get(route_key, 0) + 1

            # Keep last 500 latencies for rolling average
            if len(self.latencies) >= 500:
                self.latencies.pop(0)
            self.latencies.append(duration_ms)

    def record_job_lifecycle(self, status: str):
        """Records job lifecycle transitions."""
        with self._lock:
            s = status.upper()
            if s == "QUEUED":
                self.jobs_enqueued += 1
            elif s == "COMPLETED":
                self.jobs_completed += 1
            elif s == "FAILED":
                self.jobs_failed += 1
            elif s == "CANCELLED":
                self.jobs_cancelled += 1

    def record_database_error(self):
        with self._lock:
            self.database_errors += 1

    def record_worker_error(self):
        with self._lock:
            self.worker_errors += 1

    def get_summary(self) -> Dict[str, Any]:
        """Returns structured, safe metrics summary."""
        with self._lock:
            uptime = time.time() - self.start_time
            avg_latency = (sum(self.latencies) / len(self.latencies)) if self.latencies else 0.0
            max_latency = max(self.latencies) if self.latencies else 0.0

            return {
                "uptime_seconds": round(uptime, 2),
                "http_metrics": {
                    "total_requests": self.total_requests,
                    "failed_requests": self.failed_requests,
                    "rate_limit_blocks": self.rate_limit_hits,
                    "status_distribution": dict(self.status_codes),
                    "avg_latency_ms": round(avg_latency, 2),
                    "max_latency_ms": round(max_latency, 2),
                },
                "job_pipeline_metrics": {
                    "enqueued": self.jobs_enqueued,
                    "completed": self.jobs_completed,
                    "failed": self.jobs_failed,
                    "cancelled": self.jobs_cancelled,
                },
                "system_errors": {
                    "database_errors": self.database_errors,
                    "worker_errors": self.worker_errors,
                },
            }

    def reset(self):
        """Resets counters for unit testing."""
        with self._lock:
            self.total_requests = 0
            self.failed_requests = 0
            self.status_codes.clear()
            self.route_hits.clear()
            self.latencies.clear()
            self.jobs_enqueued = 0
            self.jobs_completed = 0
            self.jobs_failed = 0
            self.jobs_cancelled = 0
            self.database_errors = 0
            self.worker_errors = 0
            self.rate_limit_hits = 0


# Global metrics collector instance
metrics_collector = OperationalMetricsCollector()
