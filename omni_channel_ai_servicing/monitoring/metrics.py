"""
Metrics collection and monitoring for the omni-channel AI servicing platform.

Tracks:
- Email processing (received, processed, responses sent)
- Intent classification (distribution, confidence)
- Workflow execution (counts, duration, success/failure)
- API requests (endpoint usage, latency)
- Errors and exceptions
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
from threading import Lock
import statistics


class MetricsCollector:
    """
    Thread-safe metrics collector for tracking system performance.
    
    Supports three metric types:
    - Counters: Monotonically increasing values (e.g., total emails processed)
    - Histograms: Distribution of values (e.g., response times)
    - Gauges: Point-in-time values (e.g., active connections)
    """
    
    def __init__(self):
        self._lock = Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._gauges: Dict[str, float] = {}
        self._labels: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
    # ============= Counter Methods =============
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.
        
        Args:
            name: Metric name (e.g., 'emails_received_total')
            value: Amount to increment (default: 1)
            labels: Optional labels for categorization (e.g., {'intent': 'update_address'})
        """
        with self._lock:
            self._counters[name] += value
            
            if labels:
                label_key = f"{name}_{self._serialize_labels(labels)}"
                self._labels[name][label_key] += value
    
    def get_counter(self, name: str) -> int:
        """Get current counter value."""
        with self._lock:
            return self._counters.get(name, 0)
    
    # ============= Histogram Methods =============
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Record a value in a histogram for distribution analysis.
        
        Args:
            name: Metric name (e.g., 'email_processing_duration_seconds')
            value: Value to record (e.g., 1.5 seconds)
            labels: Optional labels
        """
        with self._lock:
            self._histograms[name].append(value)
            
            # Keep only last 10000 values to prevent memory bloat
            if len(self._histograms[name]) > 10000:
                self._histograms[name] = self._histograms[name][-10000:]
    
    def get_histogram_stats(self, name: str) -> Optional[Dict[str, float]]:
        """
        Get statistical summary of a histogram.
        
        Returns:
            Dict with min, max, mean, median, p50, p95, p99, count
        """
        with self._lock:
            values = self._histograms.get(name, [])
            
            if not values:
                return None
            
            sorted_values = sorted(values)
            count = len(sorted_values)
            
            return {
                "count": count,
                "min": min(sorted_values),
                "max": max(sorted_values),
                "mean": statistics.mean(sorted_values),
                "median": statistics.median(sorted_values),
                "p50": self._percentile(sorted_values, 0.50),
                "p95": self._percentile(sorted_values, 0.95),
                "p99": self._percentile(sorted_values, 0.99),
            }
    
    # ============= Gauge Methods =============
    
    def set_gauge(self, name: str, value: float):
        """
        Set a gauge to a specific value.
        
        Args:
            name: Metric name (e.g., 'active_workflows')
            value: Current value
        """
        with self._lock:
            self._gauges[name] = value
    
    def get_gauge(self, name: str) -> Optional[float]:
        """Get current gauge value."""
        with self._lock:
            return self._gauges.get(name)
    
    # ============= Summary Methods =============
    
    def get_all_metrics(self) -> Dict:
        """
        Get all metrics in a structured format.
        
        Returns:
            Dict with counters, histograms, and gauges
        """
        with self._lock:
            # Calculate histogram stats inline to avoid lock re-entry
            histogram_stats = {}
            for name, values in self._histograms.items():
                if values:
                    sorted_values = sorted(values)
                    histogram_stats[name] = {
                        "count": len(sorted_values),
                        "min": min(sorted_values),
                        "max": max(sorted_values),
                        "mean": statistics.mean(sorted_values),
                        "median": statistics.median(sorted_values),
                        "p50": self._percentile(sorted_values, 0.50),
                        "p95": self._percentile(sorted_values, 0.95),
                        "p99": self._percentile(sorted_values, 0.99),
                    }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "counters": dict(self._counters),
                "histograms": histogram_stats,
                "gauges": dict(self._gauges),
            }
    
    def get_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            String in Prometheus exposition format
        """
        lines = []
        
        with self._lock:
            # Counters
            for name, value in self._counters.items():
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")
            
            # Histograms
            for name, values in self._histograms.items():
                if values:
                    sorted_values = sorted(values)
                    lines.append(f"# TYPE {name} histogram")
                    lines.append(f"{name}_sum {sum(values)}")
                    lines.append(f"{name}_count {len(values)}")
                    lines.append(f"{name}_min {min(sorted_values)}")
                    lines.append(f"{name}_max {max(sorted_values)}")
                    lines.append(f"{name}_mean {statistics.mean(sorted_values)}")
            
            # Gauges
            for name, value in self._gauges.items():
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")
        
        return "\n".join(lines)
    
    def reset(self):
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()
            self._labels.clear()
    
    # ============= Helper Methods =============
    
    @staticmethod
    def _percentile(sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        
        # Calculate index for percentile (0-indexed)
        # For p50 of 100 values: (100-1) * 0.50 = 49.5 -> 49 (50th value, 0-indexed)
        index = int((len(sorted_values) - 1) * percentile)
        return sorted_values[index]
    
    @staticmethod
    def _serialize_labels(labels: Dict[str, str]) -> str:
        """Serialize labels dict to string for use as key."""
        return "_".join(f"{k}={v}" for k, v in sorted(labels.items()))


# ============= Context Manager for Timing =============

class MetricsTimer:
    """Context manager for timing operations and recording to histogram."""
    
    def __init__(self, metrics: MetricsCollector, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.metrics = metrics
        self.metric_name = metric_name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.metrics.record_histogram(self.metric_name, duration, self.labels)
        return False


# ============= Global Metrics Instance =============

# Singleton instance for application-wide metrics
_metrics_instance = None


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance
