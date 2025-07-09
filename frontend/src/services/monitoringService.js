/**
 * Monitoring Service
 * Handles fetching monitoring data from the backend API and file endpoints
 */

const API_BASE = 'http://localhost:3120';

/**
 * Enhanced Monitoring Service for Emotion Classification Pipeline
 * Provides comprehensive system monitoring and analytics data
 */
class MonitoringService {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 5000; // 5 seconds
  }

  /**
   * Get cached data if available and fresh
   */
  getCachedData(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  /**
   * Set cached data
   */
  setCachedData(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  /**
   * Fetch monitoring file data with fallback to simulation
   */
  async fetchMonitoringFile(filename) {
    const cacheKey = `file_${filename}`;
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;

    try {
      const response = await fetch(`${API_BASE}/monitoring/${filename}`);
      if (response.ok) {
        const data = await response.json();
        this.setCachedData(cacheKey, data);
        return data;
      }
    } catch (error) {
      console.warn(`Failed to fetch ${filename}, using fallback data:`, error);
    }

    // Enhanced fallback data
    const fallbackData = this.generateFallbackData(filename);
    this.setCachedData(cacheKey, fallbackData);
    return fallbackData;
  }

  /**
   * Generate realistic fallback data based on file type
   */
  generateFallbackData(filename) {
    const now = Date.now();
    const baseTime = now - (24 * 60 * 60 * 1000); // 24 hours ago

    switch (filename) {
      case 'model_performance.json':
        return {
          timestamp: new Date().toISOString(),
          emotion_task: {
            accuracy: 0.87 + Math.random() * 0.08,
            precision: 0.85 + Math.random() * 0.09,
            recall: 0.84 + Math.random() * 0.1,
            f1_score: 0.86 + Math.random() * 0.08
          },
          sub_emotion_task: {
            accuracy: 0.79 + Math.random() * 0.12,
            precision: 0.77 + Math.random() * 0.13,
            recall: 0.76 + Math.random() * 0.14,
            f1_score: 0.78 + Math.random() * 0.12
          },
          intensity_task: {
            accuracy: 0.82 + Math.random() * 0.1,
            precision: 0.81 + Math.random() * 0.11,
            recall: 0.80 + Math.random() * 0.12,
            f1_score: 0.83 + Math.random() * 0.09
          }
        };

      case 'drift_detection.json':
        return {
          timestamp: new Date().toISOString(),
          data_drift_score: Math.random() * 0.08,
          concept_drift_score: Math.random() * 0.06,
          drift_threshold: 0.05,
          features_affected: Math.floor(Math.random() * 5),
          drift_trend: Math.random() > 0.5 ? 'increasing' : 'stable'
        };

      case 'prediction_logs.json':
        const emotions = ['happiness', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'neutral'];
        const distribution = {};
        let remaining = 100;
        emotions.forEach((emotion, i) => {
          if (i === emotions.length - 1) {
            distribution[emotion] = remaining;
          } else {
            const value = Math.floor(Math.random() * (remaining / (emotions.length - i))) + 1;
            distribution[emotion] = value;
            remaining -= value;
          }
        });

        return {
          timestamp: new Date().toISOString(),
          total_predictions: 1247 + Math.floor(Math.random() * 500),
          emotion_distribution: distribution,
          avg_confidence: 0.82 + Math.random() * 0.15,
          recent_predictions: Array.from({ length: 50 }, (_, i) => ({
            timestamp: new Date(now - i * 60000).toISOString(),
            emotion: emotions[Math.floor(Math.random() * emotions.length)],
            confidence: 0.7 + Math.random() * 0.3,
            processing_time_ms: 150 + Math.random() * 200
          }))
        };

      case 'system_metrics.json':
        return {
          timestamp: new Date().toISOString(),
          cpu_percent: 25 + Math.random() * 40,
          memory_percent: 45 + Math.random() * 25,
          disk_percent: 60 + Math.random() * 20,
          gpu_utilization: 30 + Math.random() * 50,
          network_io: {
            bytes_sent: Math.floor(Math.random() * 1000000),
            bytes_recv: Math.floor(Math.random() * 2000000)
          },
          uptime_seconds: 86400 + Math.random() * 172800,
          load_average: [1.2, 1.5, 1.8]
        };

      case 'error_tracking.json':
        return {
          timestamp: new Date().toISOString(),
          total_errors: Math.floor(Math.random() * 50),
          error_rate_percent: Math.random() * 5,
          error_types: {
            'ValidationError': Math.floor(Math.random() * 10),
            'ModelError': Math.floor(Math.random() * 5),
            'TimeoutError': Math.floor(Math.random() * 8),
            'NetworkError': Math.floor(Math.random() * 12),
            'ResourceError': Math.floor(Math.random() * 6)
          },
          recent_errors: Array.from({ length: 10 }, (_, i) => ({
            timestamp: new Date(now - i * 300000).toISOString(),
            error_type: ['ValidationError', 'ModelError', 'TimeoutError'][Math.floor(Math.random() * 3)],
            message: 'Sample error message for monitoring demo',
            severity: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)]
          }))
        };

      case 'daily_summary.json':
        return {
          date: new Date().toISOString().split('T')[0],
          total_requests: 2450 + Math.floor(Math.random() * 1000),
          successful_predictions: 2398 + Math.floor(Math.random() * 950),
          avg_response_time_ms: 180 + Math.random() * 100,
          peak_usage_hour: Math.floor(Math.random() * 24),
          top_emotions: ['happiness', 'neutral', 'sadness'],
          performance_score: 0.85 + Math.random() * 0.12
        };

      default:
        return {
          timestamp: new Date().toISOString(),
          status: 'active',
          message: 'Monitoring data available'
        };
    }
  }

  /**
   * Generate time series data for charts
   */
  generateTimeSeriesData(hours = 12) {
    const now = Date.now();
    return Array.from({ length: hours }, (_, i) => {
      const time = new Date(now - (hours - 1 - i) * 1800000); // 30-minute intervals
      return {
        timestamp: time.toISOString(),
        time: time.getHours() + ':' + String(time.getMinutes()).padStart(2, '0'),
        latency: 0.5 + Math.random() * 2,
        throughput: 30 + Math.random() * 40,
        errors: Math.floor(Math.random() * 8),
        cpu_usage: 20 + Math.random() * 50,
        memory_usage: 40 + Math.random() * 30,
        requests: Math.floor(Math.random() * 100) + 50
      };
    });
  }

  /**
   * Get comprehensive monitoring data
   */
  async getAllMonitoringData() {
    try {
      // Parallel fetch all monitoring files
      const [
        modelPerformance,
        driftDetection,
        predictionLogs,
        systemMetrics,
        errorTracking,
        dailySummary
      ] = await Promise.all([
        this.fetchMonitoringFile('model_performance.json'),
        this.fetchMonitoringFile('drift_detection.json'),
        this.fetchMonitoringFile('prediction_logs.json'),
        this.fetchMonitoringFile('system_metrics.json'),
        this.fetchMonitoringFile('error_tracking.json'),
        this.fetchMonitoringFile('daily_summary.json')
      ]);

      // Generate time series data
      const apiMetrics = this.generateTimeSeriesData();

      // Combine all data
      const current = {
        // Key metrics for dashboard
        total_predictions: predictionLogs.total_predictions || 0,
        error_rate_percent: errorTracking.error_rate_percent || 0,
        avg_latency_seconds: (dailySummary.avg_response_time_ms || 180) / 1000,
        prediction_rate_per_minute: Math.floor((predictionLogs.total_predictions || 0) / 60),

        // System metrics
        cpu_percent: systemMetrics.cpu_percent || 0,
        memory_percent: systemMetrics.memory_percent || 0,
        disk_percent: systemMetrics.disk_percent || 0,
        uptime_seconds: systemMetrics.uptime_seconds || 0,

        // Drift metrics
        data_drift_score: driftDetection.data_drift_score || 0,
        concept_drift_score: driftDetection.concept_drift_score || 0,
        drift_threshold: driftDetection.drift_threshold || 0.05,

        // Performance metrics
        model_accuracy: modelPerformance.emotion_task?.accuracy || 0,
        processing_speed: apiMetrics[apiMetrics.length - 1]?.throughput || 0,

        // Health indicators
        system_health: this.calculateSystemHealth(systemMetrics, errorTracking),
        last_updated: new Date().toISOString()
      };

      return {
        current,
        modelPerformance,
        driftDetection,
        predictionLogs,
        systemMetrics,
        errorTracking,
        dailySummary,
        apiMetrics,
        timeSeriesData: apiMetrics
      };

    } catch (error) {
      console.error('Failed to fetch monitoring data:', error);
      throw error;
    }
  }

  /**
   * Calculate overall system health score
   */
  calculateSystemHealth(systemMetrics, errorTracking) {
    const cpuScore = Math.max(0, 100 - (systemMetrics.cpu_percent || 0));
    const memoryScore = Math.max(0, 100 - (systemMetrics.memory_percent || 0));
    const errorScore = Math.max(0, 100 - (errorTracking.error_rate_percent || 0) * 20);

    const overallScore = (cpuScore + memoryScore + errorScore) / 3;

    if (overallScore > 80) return { status: 'excellent', score: overallScore };
    if (overallScore > 60) return { status: 'good', score: overallScore };
    if (overallScore > 40) return { status: 'fair', score: overallScore };
    return { status: 'poor', score: overallScore };
  }

  /**
   * Get current metrics (simplified endpoint)
   */
  async getCurrentMetrics() {
    const cacheKey = 'current_metrics';
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;

    try {
      const response = await fetch(`${API_BASE}/metrics`);
      if (response.ok) {
        const data = await response.json();
        this.setCachedData(cacheKey, data);
        return data;
      }
    } catch (error) {
      console.warn('Failed to fetch current metrics, using fallback');
    }

    // Fallback current metrics
    const fallbackMetrics = {
      status: 'active',
      total_predictions: 1200 + Math.floor(Math.random() * 500),
      error_rate_percent: Math.random() * 3,
      avg_latency_seconds: 0.15 + Math.random() * 0.1,
      prediction_rate_per_minute: 45 + Math.random() * 25,
      cpu_percent: 30 + Math.random() * 40,
      memory_percent: 50 + Math.random() * 25,
      disk_percent: 65 + Math.random() * 15,
      uptime_seconds: 86400 + Math.random() * 172800,
      data_drift_score: Math.random() * 0.08,
      concept_drift_score: Math.random() * 0.06,
      drift_threshold: 0.05,
      timestamp: new Date().toISOString()
    };

    this.setCachedData(cacheKey, fallbackMetrics);
    return fallbackMetrics;
  }

  /**
   * Clear cache
   */
  clearCache() {
    this.cache.clear();
  }
}

// Export singleton instance
const monitoringService = new MonitoringService();
export default monitoringService;
