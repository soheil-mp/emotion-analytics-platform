# 🔍 Emotion AI Monitoring System - Complete Technical Guide

## 📊 Overview

The Emotion AI Monitoring System provides real-time insights into your emotion classification pipeline's performance, system health, and prediction quality. This guide explains exactly what each metric means and how it's calculated.

---

## 🛡️ Data Sources & Reliability

### **Primary Data Source (Real Data)**
- **Source**: Backend API at `http://localhost:3120/monitoring/*`
- **Files**: Real monitoring data from `results/monitoring/*.json`
- **Update Frequency**: Real-time as your system processes emotions
- **Data Types**: Actual API calls, model predictions, system metrics, errors

### **Fallback Data Source (Demo Data)**
- **When Used**: Only when the backend API is unavailable (network issues, server down)
- **Purpose**: Ensures dashboard remains functional for demonstrations
- **Indicator**: Console warning message: `"⚠️ Failed to fetch [filename], using enhanced fallback"`

### **How to Verify You're Using Real Data**
1. Check browser console - no "fallback" warnings = real data
2. Data timestamps match your actual usage patterns
3. Sub-emotions and predictions match your actual model outputs

---

## 🏠 Health Status Overview - Detailed Calculations

### **Overall Health Score (0-100)**
**Formula:**
```
Health Score = (System Health × 0.4) + (API Health × 0.35) + (Model Health × 0.25)
```

**Component Calculations:**

#### **System Health (40% weight)**
```javascript
systemHealth = 100 - (
  (avgCpuUsage × 0.4) +
  (avgMemoryUsage × 0.4) +
  (avgDiskUsage × 0.2)
)
```
- **CPU Weight**: 40% (most critical for real-time processing)
- **Memory Weight**: 40% (critical for model inference)
- **Disk Weight**: 20% (less critical for short-term operation)

#### **API Health (35% weight)**
```javascript
apiHealth = 100 - (
  (errorRatePercent × 2) +
  (latencyP95 > 0.5 ? 30 : latencyP95 × 60) +
  (uptimeScore)
)
```
- **Error Rate Impact**: Each 1% error rate reduces health by 2 points
- **Latency Impact**: P95 latency >500ms = 30 point penalty
- **Uptime Score**: Based on successful requests ratio

#### **Model Health (25% weight)**
```javascript
modelHealth = (
  (emotionF1Score × 0.4) +
  (subEmotionF1Score × 0.3) +
  (intensityF1Score × 0.3)
) × 100
```

### **Health Status Indicators**
- **🟢 Excellent (90-100)**: `score >= 90`
- **🟡 Good (70-89)**: `70 <= score < 90`
- **🟠 Warning (50-69)**: `50 <= score < 70`
- **🔴 Critical (<50)**: `score < 50`

---

## 📊 Performance Metrics - Detailed Explanations

### **🎯 Model Performance Metrics**

#### **F1 Score Calculation**
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)

Where:
Precision = True Positives / (True Positives + False Positives)
Recall = True Positives / (True Positives + False Negatives)
```

**What it means:**
- **Range**: 0.0 to 1.0 (higher = better)
- **Interpretation**: Harmonic mean of precision and recall
- **Good Performance**: F1 > 0.80 for emotions, F1 > 0.75 for sub-emotions

#### **Accuracy Calculation**
```
Accuracy = (True Positives + True Negatives) / Total Predictions
```

#### **Task-Specific Metrics**
1. **Emotion Classification**: Predicting primary emotions (happy, sad, angry, etc.)
2. **Sub-Emotion Classification**: Predicting emotion variants (joy, frustration, curiosity)
3. **Intensity Prediction**: Predicting emotion strength (mild, moderate, strong)

---

### **⚡ API Performance Metrics**

#### **Latency Percentiles**
**Calculation:**
```javascript
// Sort all response times
sortedLatencies = latencies.sort((a, b) => a - b)

// Calculate percentiles
P50 = sortedLatencies[Math.floor(0.50 * length)]  // Median
P95 = sortedLatencies[Math.floor(0.95 * length)]  // 95th percentile
P99 = sortedLatencies[Math.floor(0.99 * length)]  // 99th percentile
```

**What they mean:**
- **P50 (Median)**: 50% of requests complete faster than this time
- **P95**: 95% of requests complete faster than this time (excludes outliers)
- **P99**: 99% of requests complete faster than this time (includes most outliers)

#### **Request Rate (Predictions per Minute)**
```javascript
requestRate = totalRequests / timeWindowMinutes
```

#### **Error Rate Percentage**
```javascript
errorRate = (totalErrors / totalRequests) × 100
```
**Healthy Range**: <5% (preferably <2%)

#### **Uptime Calculation**
```javascript
uptime = (successfulRequests / totalRequests) × 100
```

---

### **💻 System Resource Metrics**

#### **CPU Usage Percentage**
```javascript
cpuUsage = (cpuTimeUsed / totalCpuTime) × 100
```
**Calculation Method**: Average over 1-minute windows
**Healthy Range**: <80% sustained usage

#### **Memory Usage Calculation**
```javascript
memoryUsage = (usedMemory / totalMemory) × 100
memoryUsedGB = usedMemory / (1024^3)  // Convert bytes to GB
memoryAvailableGB = (totalMemory - usedMemory) / (1024^3)
```
**Healthy Range**: <85% utilization

#### **Disk Usage Calculation**
```javascript
diskUsage = (usedDisk / totalDisk) × 100
diskUsedGB = usedSpace / (1024^3)
diskFreeGB = freeSpace / (1024^3)
```
**Healthy Range**: <90% capacity

#### **Network I/O Metrics**
- **Bytes Sent**: Total outbound network traffic
- **Bytes Received**: Total inbound network traffic
- **Calculation**: Accumulated over monitoring period

---

## 🎭 Emotion Analysis Metrics

### **Emotion Distribution Calculation**
```javascript
emotionDistribution = emotions.reduce((acc, emotion) => {
  acc[emotion] = (acc[emotion] || 0) + 1
  return acc
}, {})

// Convert to percentages
const total = emotions.length
emotionPercentages = Object.entries(emotionDistribution).map(([emotion, count]) => ({
  emotion,
  count,
  percentage: (count / total) × 100
}))
```

### **Sub-Emotion Processing**
```javascript
// Extract and normalize sub-emotions
processSubEmotions = (data) => {
  const counts = {}
  let validCount = 0

  data.forEach(item => {
    const subEmotion = item.sub_emotion || item.subEmotion || item['sub-emotion']
    if (subEmotion && typeof subEmotion === 'string' && subEmotion.trim()) {
      const cleanName = subEmotion.trim().toLowerCase()
      counts[cleanName] = (counts[cleanName] || 0) + 1
      validCount++
    }
  })

  return Object.entries(counts)
    .map(([name, count]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value: count,
      percentage: validCount > 0 ? ((count / validCount) * 100).toFixed(1) : 0
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8) // Top 8 sub-emotions
}
```

### **Confidence Score Analysis**
```javascript
averageConfidence = predictions.reduce((sum, pred) => sum + pred.confidence, 0) / predictions.length

confidenceDistribution = {
  high: predictions.filter(p => p.confidence >= 0.8).length,
  medium: predictions.filter(p => p.confidence >= 0.6 && p.confidence < 0.8).length,
  low: predictions.filter(p => p.confidence < 0.6).length
}
```

---

## 📈 Trend Analysis Calculations

### **Moving Average Calculation**
```javascript
calculateMovingAverage = (values, windowSize = 5) => {
  return values.map((value, index) => {
    if (index < windowSize - 1) return value

    const window = values.slice(index - windowSize + 1, index + 1)
    return window.reduce((sum, val) => sum + val, 0) / windowSize
  })
}
```

### **Trend Direction Calculation**
```javascript
calculateTrend = (values) => {
  if (values.length < 2) return 'stable'

  const recent = values.slice(-5) // Last 5 values
  const older = values.slice(-10, -5) // Previous 5 values

  const recentAvg = recent.reduce((sum, val) => sum + val, 0) / recent.length
  const olderAvg = older.reduce((sum, val) => sum + val, 0) / older.length

  const change = ((recentAvg - olderAvg) / olderAvg) * 100

  if (change > 5) return 'increasing'
  if (change < -5) return 'decreasing'
  return 'stable'
}
```

---

## 🚨 Drift Detection Calculations

### **Data Drift Score**
```javascript
dataDriftScore = calculateKLDivergence(currentDataDistribution, referenceDataDistribution)

// KL Divergence calculation
calculateKLDivergence = (P, Q) => {
  return P.reduce((sum, p, i) => {
    const q = Q[i]
    if (p === 0) return sum
    if (q === 0) return Infinity
    return sum + p * Math.log(p / q)
  }, 0)
}
```

### **Concept Drift Score**
```javascript
conceptDriftScore = compareModelPerformance(currentWindow, referenceWindow)

compareModelPerformance = (current, reference) => {
  const currentF1 = current.f1Score
  const referenceF1 = reference.f1Score

  return Math.abs(currentF1 - referenceF1) / referenceF1
}
```

### **Alert Thresholds**
- **Data Drift Alert**: `dataDriftScore > 0.05`
- **Concept Drift Alert**: `conceptDriftScore > 0.10`
- **Performance Drop Alert**: `f1Score < (baseline - 0.05)`

---

## 📊 Chart Data Preparation

### **Time-Series Data Bucketing**
```javascript
// Group data by hour for latency trends
groupByHour = (data) => {
  const hourlyBuckets = {}

  data.forEach(item => {
    const hour = new Date(item.timestamp).getHours()
    if (!hourlyBuckets[hour]) {
      hourlyBuckets[hour] = { hour, values: [] }
    }
    hourlyBuckets[hour].values.push(item)
  })

  return Object.values(hourlyBuckets).map(bucket => ({
    hour: `${bucket.hour}:00`,
    avgValue: bucket.values.reduce((sum, v) => sum + v.value, 0) / bucket.values.length,
    count: bucket.values.length
  }))
}
```

### **Percentile Calculation for Charts**
```javascript
calculatePercentile = (arr, percentile) => {
  const sorted = arr.sort((a, b) => a - b)
  const index = Math.floor((percentile / 100) * sorted.length)
  return sorted[index] || 0
}
```

---

## 🎨 Status Color Mapping

### **Health Score Colors**
```javascript
getHealthColor = (score) => {
  if (score >= 90) return '#4CAF50'      // Green - Excellent
  if (score >= 70) return '#FFC107'      // Yellow - Good
  if (score >= 50) return '#FF9800'      // Orange - Warning
  return '#F44336'                       // Red - Critical
}
```

### **Performance Status Colors**
```javascript
getPerformanceColor = (metric, type) => {
  switch(type) {
    case 'latency':
      if (metric < 0.1) return '#4CAF50'     // <100ms - Excellent
      if (metric < 0.3) return '#FFC107'     // <300ms - Good
      if (metric < 0.5) return '#FF9800'     // <500ms - Warning
      return '#F44336'                       // >500ms - Critical

    case 'errorRate':
      if (metric < 1) return '#4CAF50'       // <1% - Excellent
      if (metric < 3) return '#FFC107'       // <3% - Good
      if (metric < 5) return '#FF9800'       // <5% - Warning
      return '#F44336'                       // >5% - Critical
  }
}
```

---

## 🔄 Auto-Refresh & Caching

### **Cache Management**
```javascript
// 10-second cache to prevent excessive API calls
getCachedData = (key) => {
  const cached = cache.get(key)
  const isValid = cached && (Date.now() - cached.timestamp < 10000)
  return isValid ? cached.data : null
}
```

### **Retry Logic**
```javascript
// 3 attempts with exponential backoff
withRetry = async (fn, attempts = 3) => {
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn()
    } catch (error) {
      if (i === attempts - 1) throw error
      await new Promise(resolve =>
        setTimeout(resolve, 1000 * (i + 1)) // 1s, 2s, 3s delays
      )
    }
  }
}
```

---

## 📋 Data File Structure Examples

### **`api_metrics.json` Structure**
```json
{
  "timestamp": "2025-01-16T10:30:00Z",
  "total_predictions": 1500,
  "total_errors": 3,
  "active_requests": 8,
  "prediction_rate_per_minute": 25.5,
  "error_rate_percent": 0.2,
  "uptime_seconds": 86400,
  "latency_p50": 0.12,
  "latency_p95": 0.28,
  "latency_p99": 0.45
}
```

### **`prediction_logs.json` Structure**
```json
{
  "timestamp": "2025-01-16T10:30:00Z",
  "emotion": "happiness",
  "sub_emotion": "joy",
  "intensity": "moderate",
  "confidence": 0.87,
  "latency": 0.15
}
```

### **`model_performance.json` Structure**
```json
{
  "timestamp": "2025-01-16T10:30:00Z",
  "emotion": {
    "f1": 0.85,
    "accuracy": 0.88,
    "precision": 0.84,
    "recall": 0.86
  },
  "sub_emotion": {
    "f1": 0.78,
    "accuracy": 0.81,
    "precision": 0.77,
    "recall": 0.79
  },
  "intensity": {
    "f1": 0.82,
    "accuracy": 0.84,
    "precision": 0.81,
    "recall": 0.83
  }
}
```

### **`system_metrics.json` Structure**
```json
{
  "timestamp": "2025-01-16T10:30:00Z",
  "cpu_percent": 45.2,
  "memory_percent": 68.1,
  "memory_used_gb": 13.6,
  "memory_available_gb": 6.4,
  "disk_percent": 23.5,
  "disk_used_gb": 47.0,
  "disk_free_gb": 153.0,
  "network_io_bytes_sent": 1024000,
  "network_io_bytes_recv": 2048000
}
```

---

## 🚨 Alert Thresholds & Formulas

### **System Resource Alerts**
```javascript
// CPU Alert Threshold
cpuAlert = cpuUsage > 85 && sustainedFor > 300000 // 5 minutes

// Memory Alert Threshold
memoryAlert = memoryUsage > 90

// Disk Alert Threshold
diskAlert = diskUsage > 95
```

### **Performance Alerts**
```javascript
// High Latency Alert
latencyAlert = latencyP95 > 500 // milliseconds

// High Error Rate Alert
errorRateAlert = errorRate > 5 // percent

// Low Confidence Alert
confidenceAlert = averageConfidence < 0.6
```

### **Model Performance Alerts**
```javascript
// Model Degradation Alert
modelAlert = currentF1 < (baselineF1 - 0.05) // 5% drop

// Drift Alert
driftAlert = driftScore > 0.10 // 10% threshold
```

---

## 🛠️ Troubleshooting Guide

### **Common Calculation Issues**

#### **Health Score Showing 0**
**Possible Causes:**
```javascript
// Check if data is available
if (!systemMetrics || !apiMetrics) {
  console.log('Missing data for health calculation')
}

// Check for division by zero
if (totalRequests === 0) {
  console.log('No requests found for API health calculation')
}
```

#### **Percentiles Showing NaN**
**Fix:**
```javascript
// Ensure array has values before calculating percentiles
const validLatencies = latencies.filter(l => !isNaN(l) && l > 0)
if (validLatencies.length === 0) {
  return { p50: 0, p95: 0, p99: 0 }
}
```

#### **Trend Calculation Errors**
**Fix:**
```javascript
// Ensure sufficient data points
if (values.length < 10) {
  return 'insufficient_data'
}
```

---

## 🎯 Performance Benchmarks

### **Target Metrics**
- **API Latency P95**: <200ms
- **Error Rate**: <2%
- **CPU Usage**: <80%
- **Memory Usage**: <85%
- **Model F1 Score**: >0.80 (emotions), >0.75 (sub-emotions)
- **Uptime**: >99.5%

### **Alert Escalation**
1. **Warning Level**: Metrics exceed 80% of threshold
2. **Critical Level**: Metrics exceed threshold
3. **Emergency Level**: Multiple critical alerts or system failure

---

## 📞 Technical Support

**For metric calculation issues:**
1. Check browser console for calculation errors
2. Verify data format matches expected structure
3. Ensure all required fields are present in JSON files
4. Check for null/undefined values in calculations

**Remember**: All calculations use **real data** from your emotion AI system. The formulas provide accurate insights into your actual system performance! 🎉
