// Enhanced API service for Emotion Classification Pipeline
const API_BASE = 'http://localhost:3120';

class EmotionAPI {
  constructor() {
    this.baseURL = API_BASE;
    this.cache = new Map();
    this.cacheTimeout = 30000; // 30 seconds
  }

  // Existing methods...
  async predictEmotion(url, method = 'local') {
    const response = await fetch(`${this.baseURL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url, method }),
    });

    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.statusText}`);
    }

    return response.json();
  }

  async saveFeedback(feedbackData) {
    const response = await fetch(`${this.baseURL}/save-feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedbackData),
    });

    if (!response.ok) {
      throw new Error(`Feedback submission failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Enhanced monitoring methods
  async getMonitoringFile(fileName) {
    try {
      const cacheKey = `monitoring_${fileName}`;
      const cached = this.getCachedData(cacheKey);
      if (cached) return cached;

      const response = await fetch(`${this.baseURL}/monitoring/${fileName}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch ${fileName}: ${response.statusText}`);
      }

      const data = await response.json();
      this.setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      console.warn(`⚠️ Error fetching ${fileName}:`, error.message);
      throw error;
    }
  }

  async getLiveMonitoringSummary() {
    try {
      const response = await fetch(`${this.baseURL}/monitoring/summary/live`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch live summary: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error fetching live monitoring summary:', error);
      throw error;
    }
  }

  async getMonitoringTrends() {
    try {
      const response = await fetch(`${this.baseURL}/monitoring/analytics/trends`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch trends: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('❌ Error fetching monitoring trends:', error);
      throw error;
    }
  }

  async getAllMonitoringData() {
    try {
      console.log('🔄 Fetching comprehensive monitoring data...');

      const [
        apiMetrics,
        modelPerformance,
        systemMetrics,
        predictionLogs,
        driftDetection,
        errorTracking,
        dailySummary,
        liveSummary,
        trends
      ] = await Promise.all([
        this.getMonitoringFile('api_metrics.json'),
        this.getMonitoringFile('model_performance.json'),
        this.getMonitoringFile('system_metrics.json'),
        this.getMonitoringFile('prediction_logs.json'),
        this.getMonitoringFile('drift_detection.json'),
        this.getMonitoringFile('error_tracking.json'),
        this.getMonitoringFile('daily_summary.json'),
        this.getLiveMonitoringSummary(),
        this.getMonitoringTrends()
      ]);

      console.log('✅ Successfully fetched comprehensive monitoring data');

      return {
        apiMetrics,
        modelPerformance,
        systemMetrics,
        predictionLogs,
        driftDetection,
        errorTracking,
        dailySummary,
        liveSummary,
        trends,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('❌ Error fetching all monitoring data:', error);
      throw new Error(`Failed to fetch monitoring data: ${error.message}`);
    }
  }

  async getSystemHealth() {
    try {
      const liveSummary = await this.getLiveMonitoringSummary();
      return {
        score: liveSummary.health_score || 0,
        status: liveSummary.status || 'unknown',
        timestamp: liveSummary.timestamp,
        details: {
          system: liveSummary.system || {},
          api: liveSummary.api || {},
          model: liveSummary.model || {},
          predictions: liveSummary.predictions || {},
          errors: liveSummary.errors || {}
        }
      };
    } catch (error) {
      console.error('❌ Error fetching system health:', error);
      return {
        score: 0,
        status: 'unknown',
        timestamp: new Date().toISOString(),
        details: {}
      };
    }
  }

  async checkBackendStatus() {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        timeout: 5000 // 5 second timeout
      });

      if (response.ok) {
        return { status: 'online', timestamp: new Date().toISOString() };
      } else {
        return { status: 'error', timestamp: new Date().toISOString() };
      }
    } catch (error) {
      console.warn('Backend health check failed:', error.message);
      return { status: 'offline', timestamp: new Date().toISOString() };
    }
  }

  // Cache management
  getCachedData(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  setCachedData(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  clearCache() {
    this.cache.clear();
  }

  // Analytics helpers
  analyzeApiMetrics(data) {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return { avgLatency: 0, totalPredictions: 0, errorRate: 0 };
    }

    const latest = data[data.length - 1] || {};
    const recent = data.slice(-10);

    return {
      avgLatency: Math.round((latest.latency_p50 || 0) * 1000),
      totalPredictions: latest.total_predictions || 0,
      errorRate: latest.error_rate_percent || 0,
      throughput: latest.prediction_rate_per_minute || 0,
      uptime: latest.uptime_seconds || 0,
      trend: this.calculateTrend(recent.map(d => d.latency_p50 || 0))
    };
  }

  analyzeSystemMetrics(data) {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return { avgCpu: 0, avgMemory: 0, avgDisk: 0 };
    }

    const recent = data.slice(-20);

    return {
      avgCpu: Math.round(recent.reduce((sum, d) => sum + (d.cpu_percent || 0), 0) / recent.length),
      avgMemory: Math.round(recent.reduce((sum, d) => sum + (d.memory_percent || 0), 0) / recent.length),
      avgDisk: Math.round(recent.reduce((sum, d) => sum + (d.disk_percent || 0), 0) / recent.length),
      latest: recent[recent.length - 1] || {}
    };
  }

  analyzeModelPerformance(data) {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return { averageF1: 0, trend: 'stable' };
    }

    const latest = data[data.length - 1] || {};
    const emotionF1 = latest.emotion?.f1 || 0;
    const subEmotionF1 = latest.sub_emotion?.f1 || 0;
    const intensityF1 = latest.intensity?.f1 || 0;

    const averageF1 = (emotionF1 + subEmotionF1 + intensityF1) / 3;
    const f1Values = data.slice(-10).map(d => d.emotion?.f1 || 0);

    return {
      averageF1: Number(averageF1.toFixed(3)),
      emotionF1: Number(emotionF1.toFixed(3)),
      subEmotionF1: Number(subEmotionF1.toFixed(3)),
      intensityF1: Number(intensityF1.toFixed(3)),
      trend: this.calculateTrend(f1Values),
      performanceScore: Math.round(averageF1 * 100)
    };
  }

  calculateTrend(values) {
    if (values.length < 3) return 'stable';

    const recent = values.slice(-5);
    const older = values.slice(-10, -5);

    if (recent.length === 0 || older.length === 0) return 'stable';

    const recentAvg = recent.reduce((sum, v) => sum + v, 0) / recent.length;
    const olderAvg = older.reduce((sum, v) => sum + v, 0) / older.length;

    const change = (recentAvg - olderAvg) / olderAvg;

    if (change > 0.05) return 'improving';
    if (change < -0.05) return 'declining';
    return 'stable';
  }

  calculateOverallHealth(systemMetrics, apiMetrics, modelPerformance) {
    let score = 100;
    let issues = [];

    // System health (40% weight)
    if (systemMetrics.avgCpu > 80) {
      score -= 15;
      issues.push('High CPU usage');
    } else if (systemMetrics.avgCpu > 60) {
      score -= 8;
    }

    if (systemMetrics.avgMemory > 85) {
      score -= 15;
      issues.push('High memory usage');
    } else if (systemMetrics.avgMemory > 70) {
      score -= 8;
    }

    // API performance (35% weight)
    if (apiMetrics.avgLatency > 500) {
      score -= 12;
      issues.push('High latency');
    } else if (apiMetrics.avgLatency > 300) {
      score -= 6;
    }

    if (apiMetrics.errorRate > 5) {
      score -= 12;
      issues.push('High error rate');
    } else if (apiMetrics.errorRate > 2) {
      score -= 6;
    }

    // Model performance (25% weight)
    if (modelPerformance.performanceScore < 60) {
      score -= 10;
      issues.push('Low model performance');
    } else if (modelPerformance.performanceScore < 75) {
      score -= 5;
    }

    score = Math.max(0, Math.min(100, score));

    let status = 'Excellent';
    if (score < 60) status = 'Critical';
    else if (score < 75) status = 'Warning';
    else if (score < 90) status = 'Good';

    return {
      score: Math.round(score),
      status,
      issues,
      timestamp: new Date().toISOString()
    };
  }
}

// Export singleton instance
const emotionAPI = new EmotionAPI();
export default emotionAPI;
