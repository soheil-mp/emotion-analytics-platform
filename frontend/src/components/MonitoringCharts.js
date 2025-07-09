import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  useTheme,
  alpha
} from '@mui/material';
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Legend,
  ComposedChart,
  ScatterChart,
  Scatter
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Warning,
  CheckCircle,
  Error as ErrorIcon
} from '@mui/icons-material';

// Enhanced color palette
const COLORS = {
  primary: ['#4F46E5', '#6366f1', '#8B5CF6', '#A855F7'],
  performance: ['#10B981', '#059669', '#047857', '#065F46'],
  warning: ['#F59E0B', '#D97706', '#B45309', '#92400E'],
  danger: ['#EF4444', '#DC2626', '#B91C1C', '#991B1B'],
  info: ['#3B82F6', '#2563EB', '#1D4ED8', '#1E40AF'],
  emotions: [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD',
    '#FF9F43', '#70A1FF', '#5352ED', '#FF3838'
  ],
  gradients: {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    success: 'linear-gradient(135deg, #48BB78 0%, #38A169 100%)',
    warning: 'linear-gradient(135deg, #ED8936 0%, #D69E2E 100%)',
    danger: 'linear-gradient(135deg, #F56565 0%, #E53E3E 100%)'
  }
};

// Custom tooltip component
const CustomTooltip = ({ active, payload, label, labelFormatter, valueFormatter }) => {
  if (active && payload && payload.length) {
    return (
      <Box sx={{
        background: 'rgba(0,0,0,0.9)',
        color: 'white',
        p: 2,
        borderRadius: 2,
        border: '1px solid rgba(255,255,255,0.2)',
        backdropFilter: 'blur(10px)'
      }}>
        <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
          {labelFormatter ? labelFormatter(label) : label}
        </Typography>
        {payload.map((entry, index) => (
          <Typography key={index} variant="body2" sx={{ color: entry.color }}>
            {entry.name}: {valueFormatter ? valueFormatter(entry.value) : entry.value}
          </Typography>
        ))}
      </Box>
    );
  }
  return null;
};

// Trend indicator component
const TrendIndicator = ({ trend, value, unit = '' }) => {
  const getIcon = () => {
    switch (trend) {
      case 'improving':
      case 'increasing':
        return <TrendingUp sx={{ color: COLORS.performance[0] }} />;
      case 'declining':
      case 'decreasing':
        return <TrendingDown sx={{ color: COLORS.danger[0] }} />;
      default:
        return <TrendingFlat sx={{ color: COLORS.info[0] }} />;
    }
  };

  return (
    <Box display="flex" alignItems="center" gap={1}>
      {getIcon()}
      <Typography variant="body2" color="rgba(255,255,255,0.8)">
        {value}{unit}
      </Typography>
    </Box>
  );
};

// Model Performance Chart
export const ModelPerformanceChart = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        height: 400
      }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>📈 Model Performance</Typography>
          <Alert severity="info">No model performance data available</Alert>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.slice(-20).map(item => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString(),
    emotion: Number((item.emotion?.f1 || 0).toFixed(3)),
    subEmotion: Number((item.sub_emotion?.f1 || 0).toFixed(3)),
    intensity: Number((item.intensity?.f1 || 0).toFixed(3))
  }));

  const latest = data[data.length - 1] || {};
  const avgF1 = (
    (latest.emotion?.f1 || 0) +
    (latest.sub_emotion?.f1 || 0) +
    (latest.intensity?.f1 || 0)
  ) / 3;

  return (
    <Card sx={{
      background: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255,255,255,0.1)',
      height: 400
    }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">📈 Model Performance</Typography>
        <Chip
            label={`Avg F1: ${(avgF1 * 100).toFixed(1)}%`}
            color={avgF1 > 0.8 ? 'success' : avgF1 > 0.6 ? 'warning' : 'error'}
          />
        </Box>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="timestamp"
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
            <YAxis
              stroke="rgba(255,255,255,0.6)"
              domain={[0, 1]}
              fontSize={12}
            />
            <Tooltip
              content={<CustomTooltip
                valueFormatter={(value) => `${(value * 100).toFixed(1)}%`}
              />}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="emotion"
              stroke={COLORS.performance[0]}
              strokeWidth={2}
              name="Emotion F1"
              dot={{ fill: COLORS.performance[0], strokeWidth: 2, r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="subEmotion"
              stroke={COLORS.info[0]}
              strokeWidth={2}
              name="Sub-Emotion F1"
              dot={{ fill: COLORS.info[0], strokeWidth: 2, r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="intensity"
              stroke={COLORS.warning[0]}
              strokeWidth={2}
              name="Intensity F1"
              dot={{ fill: COLORS.warning[0], strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
    </CardContent>
  </Card>
  );
};

// System Metrics Chart
export const SystemMetricsChart = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        height: 400
      }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>🖥️ System Metrics</Typography>
          <Alert severity="info">No system metrics data available</Alert>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.slice(-50).map(item => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString(),
    cpu: Math.round(item.cpu_percent || 0),
    memory: Math.round(item.memory_percent || 0),
    disk: Math.round(item.disk_percent || 0)
  }));

  const latest = data[data.length - 1] || {};

  return (
    <Card sx={{
      background: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255,255,255,0.1)',
      height: 400
    }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>🖥️ System Metrics</Typography>

        {/* Current Usage Stats */}
        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid item xs={4}>
            <Box textAlign="center">
              <Typography variant="h6" color={COLORS.info[0]}>
                {Math.round(latest.cpu_percent || 0)}%
              </Typography>
              <Typography variant="caption">CPU</Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box textAlign="center">
              <Typography variant="h6" color={COLORS.warning[0]}>
                {Math.round(latest.memory_percent || 0)}%
              </Typography>
              <Typography variant="caption">Memory</Typography>
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box textAlign="center">
              <Typography variant="h6" color={COLORS.danger[0]}>
                {Math.round(latest.disk_percent || 0)}%
              </Typography>
              <Typography variant="caption">Disk</Typography>
            </Box>
          </Grid>
        </Grid>

        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="timestamp"
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
            <YAxis
              stroke="rgba(255,255,255,0.6)"
              domain={[0, 100]}
              fontSize={12}
            />
          <Tooltip
              content={<CustomTooltip
                valueFormatter={(value) => `${value}%`}
              />}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="cpu"
            stackId="1"
              stroke={COLORS.info[0]}
              fill={alpha(COLORS.info[0], 0.3)}
            name="CPU %"
          />
          <Area
            type="monotone"
            dataKey="memory"
            stackId="2"
              stroke={COLORS.warning[0]}
              fill={alpha(COLORS.warning[0], 0.3)}
            name="Memory %"
          />
          <Area
            type="monotone"
            dataKey="disk"
            stackId="3"
              stroke={COLORS.danger[0]}
              fill={alpha(COLORS.danger[0], 0.3)}
            name="Disk %"
          />
        </AreaChart>
      </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// API Performance Chart
export const ApiPerformanceChart = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        height: 400
      }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>🚀 API Performance</Typography>
          <Alert severity="info">No API performance data available</Alert>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.slice(-30).map(item => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString(),
    latency: Math.round((item.latency_p50 || 0) * 1000),
    throughput: Math.round(item.prediction_rate_per_minute || 0),
    errors: item.total_errors || 0
  }));

  const latest = data[data.length - 1] || {};
  const avgLatency = Math.round((latest.latency_p50 || 0) * 1000);

  return (
    <Card sx={{
      background: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255,255,255,0.1)',
      height: 400
    }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">🚀 API Performance</Typography>
        <Chip
            label={`${avgLatency}ms avg`}
            color={avgLatency < 200 ? 'success' : avgLatency < 500 ? 'warning' : 'error'}
        />
      </Box>

        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="timestamp"
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
            <YAxis
              yAxisId="left"
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
            <Tooltip
              content={<CustomTooltip
                valueFormatter={(value, name) => {
                  if (name === 'Latency') return `${value}ms`;
                  if (name === 'Throughput') return `${value}/min`;
                  return value;
                }}
              />}
            />
            <Legend />
            <Bar
              yAxisId="left"
              dataKey="latency"
              fill={COLORS.info[0]}
              name="Latency (ms)"
              radius={[4, 4, 0, 0]}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="throughput"
              stroke={COLORS.performance[0]}
              strokeWidth={2}
              name="Throughput (/min)"
              dot={{ fill: COLORS.performance[0], strokeWidth: 2, r: 4 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="errors"
              stroke={COLORS.danger[0]}
              strokeWidth={2}
              name="Errors"
              dot={{ fill: COLORS.danger[0], strokeWidth: 2, r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Emotion Distribution Chart
export const EmotionDistributionChart = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        height: 400
      }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>😊 Emotion Distribution</Typography>
          <Alert severity="info">No emotion data available</Alert>
        </CardContent>
      </Card>
    );
  }

  // Analyze emotion distribution
  const emotionCounts = {};
  data.forEach(item => {
    if (item.emotion) {
      emotionCounts[item.emotion] = (emotionCounts[item.emotion] || 0) + 1;
    }
  });

  const chartData = Object.entries(emotionCounts)
    .map(([emotion, count]) => ({
      name: emotion,
      value: count,
      percentage: ((count / data.length) * 100).toFixed(1)
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <Card sx={{
      background: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255,255,255,0.1)',
      height: 400
    }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>😊 Emotion Distribution</Typography>

        <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie
              data={chartData}
            cx="50%"
            cy="50%"
              labelLine={false}
              label={({ name, percentage }) => `${name}: ${percentage}%`}
              outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS.emotions[index % COLORS.emotions.length]}
                />
            ))}
          </Pie>
          <Tooltip
              content={<CustomTooltip
                valueFormatter={(value, name) => `${value} predictions`}
              />}
            />
            <Legend />
        </PieChart>
      </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Sub-Emotion Distribution Chart - Completely Rewritten for Reliability
export const SubEmotionDistributionChart = ({ data }) => {
  // Simple custom tooltip that doesn't break
  const SimpleTooltip = ({ active, payload }) => {
    if (active && payload && payload.length > 0) {
      const data = payload[0].payload;
      return (
        <Box sx={{
          background: 'rgba(0,0,0,0.9)',
          border: '1px solid rgba(255,255,255,0.2)',
          borderRadius: 1,
          p: 1.5,
          color: 'white',
          fontSize: '12px'
        }}>
          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
            {data.name}
          </div>
          <div>Count: {data.value}</div>
          <div>Percentage: {data.percentage}%</div>
        </Box>
      );
    }
    return null;
  };

  // Validate input data
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        height: 400
      }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>🎭 Top Sub-Emotions</Typography>
          <Alert severity="info">No data available for sub-emotions analysis</Alert>
        </CardContent>
      </Card>
    );
  }

  // Process the data to extract sub-emotions
  const processData = () => {
    const counts = {};
    let validCount = 0;

    data.forEach(item => {
      if (item && typeof item === 'object') {
        const subEmotion = item.sub_emotion || item.subEmotion || item['sub-emotion'];
        if (subEmotion && typeof subEmotion === 'string' && subEmotion.trim()) {
          const cleanName = subEmotion.trim().toLowerCase();
          counts[cleanName] = (counts[cleanName] || 0) + 1;
          validCount++;
        }
      }
    });

    // Convert to chart data format
    const chartData = Object.entries(counts)
      .map(([name, count]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value: count,
        percentage: validCount > 0 ? Number(((count / validCount) * 100).toFixed(1)) : 0
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);

    return { chartData, validCount, totalTypes: Object.keys(counts).length };
  };

  const { chartData, validCount, totalTypes } = processData();

  // Handle case where no sub-emotions are found
  if (chartData.length === 0) {
    return (
      <Card sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        height: 400
      }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>🎭 Top Sub-Emotions</Typography>
          <Alert severity="warning">
            No valid sub-emotion data found in {data.length} records
          </Alert>
          <Box sx={{ mt: 2, p: 1, background: 'rgba(255,255,255,0.02)', borderRadius: 1 }}>
            <Typography variant="caption" sx={{ opacity: 0.7 }}>
              Data should contain 'sub_emotion' field with string values
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  // Color palette for bars
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
    '#FF9FF3', '#54A0FF', '#5F27CD', '#00D2D3', '#FF9F43'
  ];

  return (
    <Card sx={{
      background: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255,255,255,0.1)',
      height: 400
    }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          🎭 Top Sub-Emotions ({totalTypes} total)
        </Typography>

        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              type="number"
              stroke="rgba(255,255,255,0.6)"
              fontSize={11}
            />
            <YAxis
              type="category"
              dataKey="name"
              stroke="rgba(255,255,255,0.6)"
              fontSize={11}
              width={75}
            />
            <Tooltip content={<SimpleTooltip />} />
            <Bar
              dataKey="value"
              radius={[0, 3, 3, 0]}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={colors[index % colors.length]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <Box sx={{ mt: 1 }}>
          <Typography variant="caption" sx={{ opacity: 0.7 }}>
            Showing top {chartData.length} of {totalTypes} sub-emotions ({validCount} valid records)
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

// Latency Trends Chart
export const LatencyTrendsChart = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        height: 400
      }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>⚡ Latency Trends</Typography>
          <Alert severity="info">No latency data available</Alert>
        </CardContent>
      </Card>
    );
  }

  // Group data by time buckets
  const hourlyData = {};
  data.forEach(item => {
    const hour = new Date(item.timestamp).getHours();
    if (!hourlyData[hour]) {
      hourlyData[hour] = { hour, latencies: [], confidences: [] };
    }
    if (item.latency) hourlyData[hour].latencies.push(item.latency);
    if (item.confidence) hourlyData[hour].confidences.push(item.confidence);
  });

  const chartData = Object.values(hourlyData).map(bucket => ({
    hour: `${bucket.hour}:00`,
    avgLatency: bucket.latencies.length > 0
      ? Math.round((bucket.latencies.reduce((sum, l) => sum + l, 0) / bucket.latencies.length) * 1000)
      : 0,
    count: bucket.latencies.length,
    avgConfidence: bucket.confidences.length > 0
      ? (bucket.confidences.reduce((sum, c) => sum + c, 0) / bucket.confidences.length).toFixed(2)
      : 0
  })).sort((a, b) => parseInt(a.hour) - parseInt(b.hour));

  return (
    <Card sx={{
      background: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255,255,255,0.1)',
      height: 400
    }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>⚡ Latency & Confidence Trends</Typography>

        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="hour"
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
            <YAxis
              yAxisId="left"
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
          <Tooltip
              content={<CustomTooltip
                valueFormatter={(value, name) => {
                  if (name === 'Avg Latency') return `${value}ms`;
                  if (name === 'Avg Confidence') return `${value}`;
                  return value;
                }}
              />}
            />
            <Legend />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="avgLatency"
              stroke={COLORS.warning[0]}
              fill={alpha(COLORS.warning[0], 0.3)}
              name="Avg Latency (ms)"
          />
          <Line
              yAxisId="right"
            type="monotone"
              dataKey="avgConfidence"
              stroke={COLORS.performance[0]}
            strokeWidth={2}
              name="Avg Confidence"
              dot={{ fill: COLORS.performance[0], strokeWidth: 2, r: 4 }}
          />
          </ComposedChart>
      </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Drift Detection Chart
export const DriftDetectionChart = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        height: 400
      }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>📊 Drift Detection</Typography>
          <Alert severity="info">No drift detection data available</Alert>
        </CardContent>
      </Card>
    );
  }

  const chartData = data.map(item => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString(),
    dataDrift: Number((item.data_drift_score || 0).toFixed(4)),
    conceptDrift: Number((item.concept_drift_score || 0).toFixed(4)),
    threshold: item.drift_threshold || 0.05
  }));

  const latest = data[data.length - 1] || {};
  const hasAlert = latest.data_drift_alert || latest.concept_drift_alert;

  return (
    <Card sx={{
      background: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255,255,255,0.1)',
      height: 400
    }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">📊 Model Drift Detection</Typography>
          {hasAlert ? (
            <Chip
              icon={<Warning />}
              label="Drift Detected"
              color="warning"
            />
          ) : (
            <Chip
              icon={<CheckCircle />}
              label="Stable"
              color="success"
            />
          )}
        </Box>

      <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="timestamp"
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
            <YAxis
              stroke="rgba(255,255,255,0.6)"
              fontSize={12}
            />
          <Tooltip
              content={<CustomTooltip
                valueFormatter={(value) => value.toFixed(4)}
              />}
          />
          <Legend />
          <Line
            type="monotone"
              dataKey="dataDrift"
              stroke={COLORS.info[0]}
            strokeWidth={2}
            name="Data Drift"
              dot={{ fill: COLORS.info[0], strokeWidth: 2, r: 4 }}
          />
          <Line
            type="monotone"
              dataKey="conceptDrift"
              stroke={COLORS.warning[0]}
            strokeWidth={2}
            name="Concept Drift"
              dot={{ fill: COLORS.warning[0], strokeWidth: 2, r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="threshold"
              stroke={COLORS.danger[0]}
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Threshold"
              dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

// Error Tracking Chart
export const ErrorTrackingChart = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        height: 400
      }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>🚨 Error Tracking</Typography>
          <Alert severity="success">No errors detected</Alert>
        </CardContent>
      </Card>
    );
  }

  // Group errors by type
  const errorTypeCounts = {};
  const severityCounts = { low: 0, medium: 0, high: 0 };

  data.forEach(error => {
    if (error.error_type) {
      errorTypeCounts[error.error_type] = (errorTypeCounts[error.error_type] || 0) + 1;
    }
    if (error.severity) {
      severityCounts[error.severity] = (severityCounts[error.severity] || 0) + 1;
    }
  });

  const errorTypeData = Object.entries(errorTypeCounts)
    .map(([type, count]) => ({ name: type, value: count }))
    .sort((a, b) => b.value - a.value);

  const severityData = Object.entries(severityCounts)
    .map(([severity, count]) => ({ name: severity, value: count }));

  return (
    <Card sx={{
      background: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(10px)',
      border: '1px solid rgba(255,255,255,0.1)',
      height: 400
    }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">🚨 Error Analysis</Typography>
          <Chip
            label={`${data.length} total errors`}
            color={data.length > 50 ? 'error' : data.length > 20 ? 'warning' : 'info'}
          />
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
          <Typography variant="subtitle2" gutterBottom>Error Types</Typography>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={errorTypeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis
                  dataKey="name"
                  stroke="rgba(255,255,255,0.6)"
                  fontSize={10}
                  angle={-45}
                  textAnchor="end"
                />
                <YAxis stroke="rgba(255,255,255,0.6)" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" fill={COLORS.danger[0]} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>Severity Distribution</Typography>
            <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                  data={severityData}
                cx="50%"
                cy="50%"
                  outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                  {severityData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS.danger[index % COLORS.danger.length]}
                    />
                ))}
              </Pie>
                <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
