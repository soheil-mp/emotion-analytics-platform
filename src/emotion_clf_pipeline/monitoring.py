"""
File-based monitoring system for emotion classification pipeline.

Tracks and stores comprehensive metrics to local files for later visualization:
- Model performance metrics (accuracy, precision, recall, F1-score)
- Data drift detection using statistical analysis
- Concept drift monitoring via prediction distributions
- Prediction latency and throughput metrics
- System resource usage and API performance
- Error tracking and categorization

All metrics are saved to JSON files in the results/monitoring/ directory
for easy analysis and frontend visualization.
"""

import functools
import json
import logging
import os
import pickle
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import psutil

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Comprehensive file-based metrics collection for ML pipeline monitoring.

    Saves all metrics to JSON files for analysis and frontend visualization:
    - Real-time API performance tracking
    - Model performance and drift detection
    - System resource monitoring
    - Error analysis and categorization
    """

    def __init__(self, window_size: int = 1000, drift_threshold: float = 0.05):
        """
        Initialize metrics collector with file-based storage.

        Args:
            window_size: Number of recent predictions to keep for drift detection
            drift_threshold: Statistical significance threshold for drift detection
        """
        self.window_size = window_size
        self.drift_threshold = drift_threshold

        # Create monitoring directory
        self.monitoring_dir = Path("results/monitoring")
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)

        # Data storage for drift detection
        self.prediction_history = deque(maxlen=window_size)
        self.feature_history = deque(maxlen=window_size)
        self.performance_history = deque(maxlen=100)

        # Real-time counters for Prometheus-style metrics
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)

        # Load baseline statistics for drift detection
        self.baseline_stats = self._load_baseline_stats()

        # Threading lock for thread-safe operations
        self._lock = threading.Lock()

        # Performance tracking
        self.active_requests = 0
        self.total_predictions = 0
        self.total_errors = 0
        self.start_time = datetime.now()

        # Initialize file structure
        self._initialize_monitoring_files()

        logger.info(
            f"File-based MetricsCollector initialized - saving to {self.monitoring_dir}"
        )

    def _initialize_monitoring_files(self):
        """Initialize monitoring file structure."""
        files_to_create = [
            "api_metrics.json",  # API performance metrics
            "model_performance.json",  # Model accuracy, F1, etc.
            "drift_detection.json",  # Data and concept drift
            "system_metrics.json",  # CPU, memory, disk usage
            "error_tracking.json",  # Error logs and analysis
            "prediction_logs.json",  # Individual prediction records
            "daily_summary.json",  # Daily aggregated metrics
        ]

        for filename in files_to_create:
            filepath = self.monitoring_dir / filename
            if not filepath.exists():
                with open(filepath, "w") as f:
                    json.dump([], f)

    def _load_baseline_stats(self) -> Dict[str, Any]:
        """Load baseline statistics from training data."""
        baseline_paths = [
            "models/baseline_stats.pkl",
            "/models/baseline_stats.pkl",
            os.path.join(os.path.dirname(__file__), "../../models/baseline_stats.pkl"),
        ]

        for baseline_path in baseline_paths:
            if os.path.exists(baseline_path):
                try:
                    with open(baseline_path, "rb") as f:
                        logger.info(f"Loaded baseline stats from: {baseline_path}")
                        return pickle.load(f)
                except (pickle.UnpicklingError, EOFError, ValueError) as e:
                    logger.warning(
                        f"Failed to load baseline stats from {baseline_path}: {e}"
                    )
                    logger.warning(
                        "File may be corrupted, attempting to delete and recreate..."
                    )
                    try:
                        os.remove(baseline_path)
                        logger.info(f"Removed corrupted file: {baseline_path}")
                    except OSError:
                        logger.warning(
                            f"Could not remove corrupted file: {baseline_path}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to load baseline stats from {baseline_path}: {e}"
                    )

        logger.warning("No baseline stats file found - using defaults")
        return {
            "feature_means": {},
            "feature_stds": {},
            "prediction_distribution": {
                "happiness": 0.35,
                "neutral": 0.25,
                "sadness": 0.15,
                "anger": 0.10,
                "surprise": 0.08,
                "fear": 0.04,
                "disgust": 0.03,
            },
            "performance_baseline": {"accuracy": 0.85, "f1": 0.83},
        }

    def record_prediction(
        self,
        prediction_data: Dict[str, Any],
        features: Optional[Dict[str, float]] = None,
        latency: float = 0.0,
        confidence: float = 0.0,
    ):
        """
        Record a prediction event with comprehensive metrics.

        Args:
            prediction_data: Dictionary containing prediction results
            features: Input features for drift detection
            latency: Prediction latency in seconds
            confidence: Model confidence score
        """
        with self._lock:
            timestamp = datetime.now()

            # Extract prediction details
            emotion = prediction_data.get("emotion", "unknown")
            sub_emotion = prediction_data.get("sub_emotion", "unknown")
            intensity = prediction_data.get("intensity", "unknown")

            # Update counters
            self.counters[f"prediction_total_{emotion}"] += 1
            self.counters["predictions_total"] += 1
            self.total_predictions += 1

            # Update histograms
            self.histograms["prediction_latency"].append(latency)
            self.histograms["model_confidence"].append(confidence)

            # Store for drift detection
            prediction_record = {
                "timestamp": timestamp.isoformat(),
                "emotion": emotion,
                "sub_emotion": sub_emotion,
                "intensity": intensity,
                "confidence": confidence,
                "latency": latency,
            }
            self.prediction_history.append(prediction_record)

            if features:
                feature_record = {
                    "timestamp": timestamp.isoformat(),
                    "features": features,
                }
                self.feature_history.append(feature_record)

            # Save prediction log
            self._save_prediction_log(prediction_record)

            # Update API metrics
            self._update_api_metrics()

            # Check for drift periodically
            if self.total_predictions % 100 == 0:
                self._detect_and_save_drift()

    def record_transcription(
        self,
        transcript_data: Dict[str, Any],
        latency: float = 0.0,
        audio_quality: float = 0.0,
        confidence: float = 0.0,
    ):
        """Record transcription event with metrics."""
        with self._lock:
            # Update histograms
            self.histograms["transcription_latency"].append(latency)
            self.histograms["audio_quality"].append(audio_quality)
            self.histograms["transcription_confidence"].append(confidence)

            # Update API metrics
            self._update_api_metrics()

    def record_error(self, error_type: str, endpoint: str, error_details: str = ""):
        """Record error event with comprehensive context."""
        with self._lock:
            timestamp = datetime.now()
            self.total_errors += 1
            self.counters[f"error_{error_type}"] += 1
            self.counters["errors_total"] += 1

            # Save error log
            error_record = {
                "timestamp": timestamp.isoformat(),
                "error_type": error_type,
                "endpoint": endpoint,
                "error_details": error_details,
                "total_errors": self.total_errors,
                "error_rate": self.total_errors / max(self.total_predictions, 1) * 100,
            }

            self._save_error_log(error_record)

    def update_model_performance(self, performance_metrics: Dict[str, float]):
        """Update model performance metrics."""
        with self._lock:
            timestamp = datetime.now()

            # Store performance history
            performance_record = {
                "timestamp": timestamp.isoformat(),
                **performance_metrics,
            }
            self.performance_history.append(performance_record)

            # Update gauges
            for metric, value in performance_metrics.items():
                self.gauges[f"model_{metric}"] = value

            # Save to file
            self._save_model_performance(performance_record)

    def start_request(self) -> str:
        """Start tracking a new request. Returns request ID."""
        with self._lock:
            self.active_requests += 1
            request_id = f"req_{int(time.time() * 1000)}_{self.active_requests}"
            self.gauges["active_requests"] = self.active_requests
        return request_id

    def end_request(self, request_id: str):
        """End tracking a request."""
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)
            self.gauges["active_requests"] = self.active_requests

    def record_system_metrics(self):
        """Record current system resource usage."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            timestamp = datetime.now()

            system_record = {
                "timestamp": timestamp.isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
            }

            # Update gauges
            self.gauges.update(
                {
                    "system_cpu_percent": cpu_percent,
                    "system_memory_percent": memory.percent,
                    "system_disk_percent": disk.percent,
                }
            )

            self._save_system_metrics(system_record)

        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")

    def _detect_and_save_drift(self):
        """Detect drift and save results to file."""
        try:
            data_drift_score = self._calculate_data_drift()
            concept_drift_score = self._calculate_concept_drift()

            timestamp = datetime.now()
            drift_record = {
                "timestamp": timestamp.isoformat(),
                "data_drift_score": float(data_drift_score),
                "concept_drift_score": float(concept_drift_score),
                "data_drift_alert": bool(data_drift_score > self.drift_threshold),
                "concept_drift_alert": bool(concept_drift_score > self.drift_threshold),
                "drift_threshold": float(self.drift_threshold),
            }

            # Update gauges
            self.gauges["data_drift_score"] = data_drift_score
            self.gauges["concept_drift_score"] = concept_drift_score

            # Save drift detection results
            self._save_drift_detection(drift_record)

            # Log warnings for significant drift
            if data_drift_score > self.drift_threshold:
                logger.warning(f"Data drift detected: {data_drift_score:.4f}")

            if concept_drift_score > self.drift_threshold:
                logger.warning(f"Concept drift detected: {concept_drift_score:.4f}")

        except Exception as e:
            logger.error(f"Drift detection failed: {e}")

    def _calculate_data_drift(self) -> float:
        """Calculate data drift score using feature distributions."""
        if len(self.feature_history) < 50:
            return 0.0

        try:
            # Get recent features
            recent_features = list(self.feature_history)[-50:]

            # Calculate feature means
            feature_means = {}
            for record in recent_features:
                for feature, value in record["features"].items():
                    if feature not in feature_means:
                        feature_means[feature] = []
                    feature_means[feature].append(value)

            # Compare with baseline
            drift_scores = []
            baseline_means = self.baseline_stats.get("feature_means", {})

            for feature, values in feature_means.items():
                if feature in baseline_means:
                    recent_mean = np.mean(values)
                    baseline_mean = baseline_means[feature]

                    # Simple drift score based on relative change
                    if baseline_mean != 0:
                        drift_score = abs(recent_mean - baseline_mean) / abs(
                            baseline_mean
                        )
                        drift_scores.append(drift_score)

            return np.mean(drift_scores) if drift_scores else 0.0

        except Exception as e:
            logger.error(f"Data drift calculation failed: {e}")
            return 0.0

    def _calculate_concept_drift(self) -> float:
        """Calculate concept drift score using prediction distributions."""
        if len(self.prediction_history) < 50:
            return 0.0

        try:
            # Get recent predictions
            recent_predictions = list(self.prediction_history)[-50:]

            # Calculate current emotion distribution
            current_dist = {}
            for pred in recent_predictions:
                emotion = pred["emotion"]
                current_dist[emotion] = current_dist.get(emotion, 0) + 1

            # Normalize
            total = sum(current_dist.values())
            current_dist = {k: v / total for k, v in current_dist.items()}

            # Compare with baseline distribution
            baseline_dist = self.baseline_stats.get("prediction_distribution", {})

            if baseline_dist:
                return self._jensen_shannon_divergence(current_dist, baseline_dist)

            return 0.0

        except Exception as e:
            logger.error(f"Concept drift calculation failed: {e}")
            return 0.0

    def _jensen_shannon_divergence(self, dist1: Dict, dist2: Dict) -> float:
        """Calculate Jensen-Shannon divergence between two distributions."""
        all_keys = set(dist1.keys()) | set(dist2.keys())

        p = np.array([dist1.get(k, 0) for k in all_keys])
        q = np.array([dist2.get(k, 0) for k in all_keys])

        # Add small epsilon to avoid log(0)
        p = p + 1e-10
        q = q + 1e-10

        # Normalize
        p = p / np.sum(p)
        q = q / np.sum(q)

        m = 0.5 * (p + q)

        kl_pm = np.sum(p * np.log(p / m))
        kl_qm = np.sum(q * np.log(q / m))

        js_divergence = 0.5 * kl_pm + 0.5 * kl_qm
        return js_divergence

    def _save_prediction_log(self, prediction_record: Dict[str, Any]):
        """Save individual prediction to log file."""
        try:
            filepath = self.monitoring_dir / "prediction_logs.json"
            self._append_to_json_file(filepath, prediction_record)
        except Exception as e:
            logger.error(f"Failed to save prediction log: {e}")

    def _save_error_log(self, error_record: Dict[str, Any]):
        """Save error to log file."""
        try:
            filepath = self.monitoring_dir / "error_tracking.json"
            self._append_to_json_file(filepath, error_record)
        except Exception as e:
            logger.error(f"Failed to save error log: {e}")

    def _save_model_performance(self, performance_record: Dict[str, Any]):
        """Save model performance metrics."""
        try:
            filepath = self.monitoring_dir / "model_performance.json"
            self._append_to_json_file(filepath, performance_record)
        except Exception as e:
            logger.error(f"Failed to save model performance: {e}")

    def _save_drift_detection(self, drift_record: Dict[str, Any]):
        """Save drift detection results."""
        try:
            filepath = self.monitoring_dir / "drift_detection.json"
            self._append_to_json_file(filepath, drift_record)
        except Exception as e:
            logger.error(f"Failed to save drift detection: {e}")

    def _save_system_metrics(self, system_record: Dict[str, Any]):
        """Save system metrics."""
        try:
            filepath = self.monitoring_dir / "system_metrics.json"
            self._append_to_json_file(filepath, system_record)
        except Exception as e:
            logger.error(f"Failed to save system metrics: {e}")

    def _update_api_metrics(self):
        """Update and save API performance metrics."""
        try:
            timestamp = datetime.now()
            uptime = (timestamp - self.start_time).total_seconds()

            # Calculate rates
            prediction_rate = self.total_predictions / max(uptime, 1) * 60  # per minute
            error_rate = self.total_errors / max(self.total_predictions, 1) * 100

            # Calculate latency statistics
            latencies = self.histograms.get("prediction_latency", [])
            if latencies:
                p50_latency = np.percentile(
                    latencies[-100:], 50
                )  # Last 100 predictions
                p95_latency = np.percentile(latencies[-100:], 95)
                p99_latency = np.percentile(latencies[-100:], 99)
            else:
                p50_latency = p95_latency = p99_latency = 0.0

            api_record = {
                "timestamp": timestamp.isoformat(),
                "total_predictions": self.total_predictions,
                "total_errors": self.total_errors,
                "active_requests": self.active_requests,
                "prediction_rate_per_minute": prediction_rate,
                "error_rate_percent": error_rate,
                "uptime_seconds": uptime,
                "latency_p50": p50_latency,
                "latency_p95": p95_latency,
                "latency_p99": p99_latency,
            }

            filepath = self.monitoring_dir / "api_metrics.json"
            self._append_to_json_file(filepath, api_record)

        except Exception as e:
            logger.error(f"Failed to update API metrics: {e}")

    def _append_to_json_file(self, filepath: Path, record: Dict[str, Any]):
        """Append a record to a JSON file."""
        try:
            # Read existing data
            if filepath.exists() and filepath.stat().st_size > 0:
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                except json.JSONDecodeError:
                    # File is corrupted, start fresh
                    logger.warning(f"Corrupted JSON file {filepath}, reinitializing")
                    data = []
            else:
                data = []

            # Add new record
            data.append(record)

            # Keep only last 1000 records to prevent files from growing too large
            if len(data) > 1000:
                data = data[-1000:]

            # Write back to file
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2, default=self._json_serializer)

        except Exception as e:
            logger.error(f"Failed to append to {filepath}: {e}")
            # Try to reinitialize the file
            try:
                with open(filepath, "w") as f:
                    json.dump([record], f, indent=2, default=self._json_serializer)
                logger.info(f"Reinitialized corrupted file {filepath}")
            except Exception as e2:
                logger.error(f"Failed to reinitialize {filepath}: {e2}")

    def generate_daily_summary(self):
        """Generate and save daily summary statistics."""
        try:
            timestamp = datetime.now()
            today = timestamp.date()

            # Filter today's data
            today_predictions = [
                p
                for p in self.prediction_history
                if datetime.fromisoformat(p["timestamp"]).date() == today
            ]

            if not today_predictions:
                return

            # Calculate summary statistics
            emotion_counts = {}
            confidence_scores = []
            latencies = []

            for pred in today_predictions:
                emotion = pred["emotion"]
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                confidence_scores.append(pred["confidence"])
                latencies.append(pred["latency"])

            summary = {
                "date": today.isoformat(),
                "timestamp": timestamp.isoformat(),
                "total_predictions": len(today_predictions),
                "total_errors": self.total_errors,  # TODO: Filter by date
                "emotion_distribution": emotion_counts,
                "avg_confidence": (
                    np.mean(confidence_scores) if confidence_scores else 0
                ),
                "avg_latency": np.mean(latencies) if latencies else 0,
                "max_latency": np.max(latencies) if latencies else 0,
                "data_drift_score": self.gauges.get("data_drift_score", 0),
                "concept_drift_score": self.gauges.get("concept_drift_score", 0),
            }

            filepath = self.monitoring_dir / "daily_summary.json"
            self._append_to_json_file(filepath, summary)

        except Exception as e:
            logger.error(f"Failed to generate daily summary: {e}")

    def _json_serializer(self, obj):
        """Custom JSON serializer for numpy types and other objects."""
        if hasattr(obj, "item"):  # numpy scalars
            return obj.item()
        elif hasattr(obj, "tolist"):  # numpy arrays
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, (np.integer, int)):
            return int(obj)
        elif isinstance(obj, (np.floating, float)):
            return float(obj)
        else:
            return str(obj)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary for API endpoint."""
        with self._lock:
            # Record current system metrics
            self.record_system_metrics()

            # Calculate current statistics
            uptime = (datetime.now() - self.start_time).total_seconds()

            # Get recent latency statistics
            recent_latencies = self.histograms.get("prediction_latency", [])[-100:]
            if recent_latencies:
                avg_latency = np.mean(recent_latencies)
                p95_latency = np.percentile(recent_latencies, 95)
            else:
                avg_latency = p95_latency = 0.0

            return {
                # Core metrics
                "total_predictions": self.total_predictions,
                "total_errors": self.total_errors,
                "error_rate_percent": self.total_errors
                / max(self.total_predictions, 1)
                * 100,
                "active_requests": self.active_requests,
                "uptime_seconds": uptime,
                # Performance metrics
                "avg_latency_seconds": avg_latency,
                "p95_latency_seconds": p95_latency,
                "prediction_rate_per_minute": self.total_predictions
                / max(uptime, 1)
                * 60,
                # Drift detection
                "data_drift_score": self.gauges.get("data_drift_score", 0.0),
                "concept_drift_score": self.gauges.get("concept_drift_score", 0.0),
                "drift_threshold": self.drift_threshold,
                # System metrics
                "cpu_percent": self.gauges.get("system_cpu_percent", 0.0),
                "memory_percent": self.gauges.get("system_memory_percent", 0.0),
                "disk_percent": self.gauges.get("system_disk_percent", 0.0),
                # History sizes
                "prediction_history_size": len(self.prediction_history),
                "feature_history_size": len(self.feature_history),
                "performance_history_size": len(self.performance_history),
                # Status
                "monitoring_enabled": True,
                "monitoring_directory": str(self.monitoring_dir),
                "last_updated": datetime.now().isoformat(),
            }

    # Prometheus-style metric properties for backward compatibility
    @property
    def prediction_counter(self):
        """Backward compatibility for prediction counter."""
        return MockCounter(self, "predictions_total")

    @property
    def prediction_latency(self):
        """Backward compatibility for prediction latency."""
        return MockHistogram(self, "prediction_latency")

    @property
    def transcription_latency(self):
        """Backward compatibility for transcription latency."""
        return MockHistogram(self, "transcription_latency")

    @property
    def model_confidence(self):
        """Backward compatibility for model confidence."""
        return MockHistogram(self, "model_confidence")


class MockCounter:
    """Mock counter for Prometheus-style API compatibility."""

    def __init__(self, collector: MetricsCollector, metric_name: str):
        self.collector = collector
        self.metric_name = metric_name

    def labels(self, **kwargs):
        return self

    def inc(self, amount: float = 1):
        self.collector.counters[self.metric_name] += amount


class MockHistogram:
    """Mock histogram for Prometheus-style API compatibility."""

    def __init__(self, collector: MetricsCollector, metric_name: str):
        self.collector = collector
        self.metric_name = metric_name

    def labels(self, **kwargs):
        return self

    def observe(self, value: float):
        self.collector.histograms[self.metric_name].append(value)


class RequestTracker:
    """Context manager for tracking API requests."""

    def __init__(self, collector: Optional[MetricsCollector] = None):
        self.collector = collector or metrics_collector
        self.request_id = None

    def __enter__(self):
        self.request_id = self.collector.start_request()
        return self.request_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.request_id:
            self.collector.end_request(self.request_id)

        if exc_type:
            self.collector.record_error(
                error_type=exc_type.__name__,
                endpoint="unknown",
                error_details=str(exc_val) if exc_val else "",
            )


def monitoring_trace(operation_name: str):
    """Decorator for tracking operation performance."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                metrics_collector.record_error(
                    error_type=type(e).__name__,
                    endpoint=operation_name,
                    error_details=str(e),
                )
                raise
            finally:
                duration = time.time() - start_time
                metrics_collector.histograms[f"{operation_name}_duration"].append(
                    duration
                )

        return wrapper

    return decorator


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Schedule periodic tasks
def _periodic_tasks():
    """Periodic maintenance tasks."""
    try:
        # Generate daily summary
        metrics_collector.generate_daily_summary()

        # Clean up old files (keep last 7 days)
        # This could be implemented later for log rotation

    except Exception as e:
        logger.error(f"Periodic tasks failed: {e}")


# Run periodic tasks every hour
periodic_timer = threading.Timer(3600.0, _periodic_tasks)
periodic_timer.daemon = True
periodic_timer.start()
