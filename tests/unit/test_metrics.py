"""
Unit tests for metrics collection system.
"""
import pytest
from omni_channel_ai_servicing.monitoring.metrics import MetricsCollector, MetricsTimer


class TestMetricsCollector:
    """Test the MetricsCollector class"""
    
    def setup_method(self):
        """Create a fresh metrics collector for each test"""
        self.metrics = MetricsCollector()
    
    def test_counter_increment(self):
        """Test basic counter increment"""
        self.metrics.increment_counter("test_counter")
        assert self.metrics.get_counter("test_counter") == 1
        
        self.metrics.increment_counter("test_counter", 5)
        assert self.metrics.get_counter("test_counter") == 6
    
    def test_counter_with_labels(self):
        """Test counters with labels"""
        self.metrics.increment_counter("emails_total", labels={"intent": "address"})
        self.metrics.increment_counter("emails_total", labels={"intent": "fraud"})
        self.metrics.increment_counter("emails_total", labels={"intent": "address"})
        
        # Base counter should track all
        assert self.metrics.get_counter("emails_total") == 3
    
    def test_histogram_recording(self):
        """Test histogram value recording"""
        self.metrics.record_histogram("response_time", 0.5)
        self.metrics.record_histogram("response_time", 1.0)
        self.metrics.record_histogram("response_time", 1.5)
        
        stats = self.metrics.get_histogram_stats("response_time")
        assert stats is not None
        assert stats["count"] == 3
        assert stats["min"] == 0.5
        assert stats["max"] == 1.5
        assert stats["mean"] == 1.0
    
    def test_histogram_percentiles(self):
        """Test histogram percentile calculations"""
        # Add 100 values from 1 to 100
        for i in range(1, 101):
            self.metrics.record_histogram("test_metric", float(i))
        
        stats = self.metrics.get_histogram_stats("test_metric")
        assert stats["p50"] == 50.0  # Median
        assert stats["p95"] == 95.0  # 95th percentile
        assert stats["p99"] == 99.0  # 99th percentile
    
    def test_gauge_set_get(self):
        """Test gauge setting and retrieval"""
        self.metrics.set_gauge("active_connections", 42.0)
        assert self.metrics.get_gauge("active_connections") == 42.0
        
        self.metrics.set_gauge("active_connections", 10.0)
        assert self.metrics.get_gauge("active_connections") == 10.0
    
    def test_nonexistent_metrics(self):
        """Test accessing non-existent metrics"""
        assert self.metrics.get_counter("nonexistent") == 0
        assert self.metrics.get_gauge("nonexistent") is None
        assert self.metrics.get_histogram_stats("nonexistent") is None
    
    def test_get_all_metrics(self):
        """Test retrieving all metrics"""
        self.metrics.increment_counter("counter1", 5)
        self.metrics.record_histogram("hist1", 1.5)
        self.metrics.set_gauge("gauge1", 10.0)
        
        all_metrics = self.metrics.get_all_metrics()
        
        assert "timestamp" in all_metrics
        assert all_metrics["counters"]["counter1"] == 5
        assert all_metrics["histograms"]["hist1"]["count"] == 1
        assert all_metrics["gauges"]["gauge1"] == 10.0
    
    def test_prometheus_format(self):
        """Test Prometheus text format export"""
        self.metrics.increment_counter("emails_total", 10)
        self.metrics.set_gauge("active_workflows", 3.0)
        
        prom_text = self.metrics.get_prometheus_format()
        
        assert "# TYPE emails_total counter" in prom_text
        assert "emails_total 10" in prom_text
        assert "# TYPE active_workflows gauge" in prom_text
        assert "active_workflows 3.0" in prom_text
    
    def test_reset(self):
        """Test metrics reset"""
        self.metrics.increment_counter("test", 5)
        self.metrics.set_gauge("test_gauge", 10.0)
        
        self.metrics.reset()
        
        assert self.metrics.get_counter("test") == 0
        assert self.metrics.get_gauge("test_gauge") is None


class TestMetricsTimer:
    """Test the MetricsTimer context manager"""
    
    def test_timer_context_manager(self):
        """Test timing with context manager"""
        metrics = MetricsCollector()
        
        import time
        with MetricsTimer(metrics, "test_duration"):
            time.sleep(0.01)  # Sleep 10ms
        
        stats = metrics.get_histogram_stats("test_duration")
        assert stats is not None
        assert stats["count"] == 1
        assert stats["min"] >= 0.01  # At least 10ms
        assert stats["max"] < 0.1   # Less than 100ms (with some tolerance)
    
    def test_timer_multiple_calls(self):
        """Test multiple timed operations"""
        metrics = MetricsCollector()
        
        import time
        for _ in range(3):
            with MetricsTimer(metrics, "operation_time"):
                time.sleep(0.05)
        
        stats = metrics.get_histogram_stats("operation_time")
        assert stats["count"] == 3


def test_global_metrics_instance():
    """Test the global metrics singleton"""
    from omni_channel_ai_servicing.monitoring.metrics import get_metrics
    
    metrics1 = get_metrics()
    metrics2 = get_metrics()
    
    # Should be the same instance
    assert metrics1 is metrics2
    
    # Modifications should be visible across instances
    metrics1.increment_counter("shared_counter")
    assert metrics2.get_counter("shared_counter") == 1
