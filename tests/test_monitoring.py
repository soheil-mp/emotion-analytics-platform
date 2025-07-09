"""
Unit tests for emotion_clf_pipeline.monitoring module.

Tests monitoring functionality including metrics collection and file-based storage.
"""

import unittest
from unittest.mock import MagicMock, mock_open, patch

from emotion_clf_pipeline.monitoring import MetricsCollector, RequestTracker


class TestMetricsCollector(unittest.TestCase):
    """Test cases for MetricsCollector class."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('pathlib.Path.mkdir'):
            with patch.object(MetricsCollector, '_load_baseline_stats'):
                with patch.object(MetricsCollector, '_initialize_monitoring_files'):
                    self.collector = MetricsCollector()

    def test_init(self):
        """Test MetricsCollector initialization."""
        self.assertEqual(self.collector.window_size, 1000)
        self.assertEqual(self.collector.drift_threshold, 0.05)
        self.assertIsNotNone(self.collector.prediction_history)
        self.assertIsNotNone(self.collector.counters)

    def test_record_prediction(self):
        """Test recording a prediction."""
        prediction_data = {
            'emotion': 'happiness',
            'sub_emotion': 'joy',
            'intensity': 'medium'
        }
        
        with patch.object(self.collector, '_save_prediction_log'):
            with patch.object(self.collector, '_update_api_metrics'):
                self.collector.record_prediction(
                    prediction_data=prediction_data,
                    latency=0.1,
                    confidence=0.9
                )
        
        self.assertEqual(self.collector.counters['prediction_total_happiness'], 1)
        self.assertEqual(self.collector.counters['predictions_total'], 1)

    def test_record_error(self):
        """Test recording an error."""
        with patch.object(self.collector, '_save_error_log'):
            self.collector.record_error(
                error_type="ValidationError",
                endpoint="/predict",
                error_details="Invalid input"
            )
        
        self.assertEqual(self.collector.counters['error_ValidationError'], 1)
        self.assertEqual(self.collector.total_errors, 1)

    def test_update_model_performance(self):
        """Test updating model performance metrics."""
        metrics = {
            'accuracy': 0.85,
            'f1_score': 0.82,
            'precision': 0.87
        }
        
        with patch.object(self.collector, '_save_model_performance'):
            self.collector.update_model_performance(metrics)
        
        self.assertEqual(self.collector.gauges['model_accuracy'], 0.85)
        self.assertEqual(self.collector.gauges['model_f1_score'], 0.82)

    def test_start_end_request(self):
        """Test request tracking."""
        request_id = self.collector.start_request()
        
        self.assertIsInstance(request_id, str)
        self.assertEqual(self.collector.active_requests, 1)
        
        with patch.object(self.collector, '_update_api_metrics'):
            self.collector.end_request(request_id)
        
        self.assertEqual(self.collector.active_requests, 0)

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_record_system_metrics(self, mock_disk, mock_memory, mock_cpu):
        """Test recording system metrics."""
        # Mock system metrics
        mock_cpu.return_value = 45.2
        mock_memory.return_value = MagicMock(percent=65.5)
        mock_disk.return_value = MagicMock(percent=75.8)
        
        with patch.object(self.collector, '_save_system_metrics'):
            self.collector.record_system_metrics()
        
        self.assertEqual(self.collector.gauges['system_cpu_percent'], 45.2)
        self.assertEqual(self.collector.gauges['system_memory_percent'], 65.5)

    def test_get_metrics_summary(self):
        """Test getting metrics summary."""
        # Set up some test data
        self.collector.total_predictions = 100
        self.collector.total_errors = 5
        self.collector.gauges['model_accuracy'] = 0.85
        
        summary = self.collector.get_metrics_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('total_predictions', summary)
        self.assertIn('total_errors', summary)
        self.assertEqual(summary['total_predictions'], 100)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_append_to_json_file(self, mock_json_load, mock_file):
        """Test appending record to JSON file."""
        # Mock existing data
        mock_json_load.return_value = [{'old': 'data'}]
        
        test_record = {'new': 'record'}
        test_file = MagicMock()
        test_file.exists.return_value = True
        
        self.collector._append_to_json_file(test_file, test_record)
        
        # Verify file operations
        mock_file.assert_called()

    def test_calculate_data_drift_no_history(self):
        """Test data drift calculation with no history."""
        drift_score = self.collector._calculate_data_drift()
        
        self.assertEqual(drift_score, 0.0)

    def test_calculate_concept_drift_no_history(self):
        """Test concept drift calculation with no history."""
        drift_score = self.collector._calculate_concept_drift()
        
        self.assertEqual(drift_score, 0.0)

    def test_jensen_shannon_divergence(self):
        """Test Jensen-Shannon divergence calculation."""
        dist1 = {'happiness': 0.5, 'sadness': 0.3, 'anger': 0.2}
        dist2 = {'happiness': 0.4, 'sadness': 0.4, 'anger': 0.2}
        
        divergence = self.collector._jensen_shannon_divergence(dist1, dist2)
        
        self.assertIsInstance(divergence, float)
        self.assertGreaterEqual(divergence, 0.0)
        self.assertLessEqual(divergence, 1.0)


class TestRequestTracker(unittest.TestCase):
    """Test cases for RequestTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        mock_collector = MagicMock()
        self.tracker = RequestTracker(collector=mock_collector)

    def test_init(self):
        """Test RequestTracker initialization."""
        self.assertIsNotNone(self.tracker.collector)
        self.assertIsNone(self.tracker.request_id)

    def test_context_manager(self):
        """Test RequestTracker as context manager."""
        with self.tracker as tracker:
            self.assertIsNotNone(tracker.request_id)
            self.tracker.collector.start_request.assert_called_once()
        
        # After exiting context
        self.tracker.collector.end_request.assert_called_once()

    def test_context_manager_with_exception(self):
        """Test RequestTracker context manager with exception."""
        try:
            with self.tracker:
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Should still call end_request even with exception
        self.tracker.collector.end_request.assert_called_once()


if __name__ == '__main__':
    unittest.main() 