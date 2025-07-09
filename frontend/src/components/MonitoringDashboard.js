import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Paper,
  CircularProgress,
  Fab,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  AppBar,
  useTheme,
  alpha
} from '@mui/material';
import {
  Home as HomeIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Psychology as PsychologyIcon,
  Error as ErrorIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Computer as ComputerIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Dashboard as DashboardIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  BugReport as BugReportIcon
} from '@mui/icons-material';
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
  Tooltip as RechartsTooltip,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Legend,
  ComposedChart
} from 'recharts';

// Import enhanced chart components
import {
  ModelPerformanceChart,
  SystemMetricsChart,
  EmotionDistributionChart,
  SubEmotionDistributionChart,
  LatencyTrendsChart,
  DriftDetectionChart,
  ErrorTrackingChart,
  ApiPerformanceChart
} from './MonitoringCharts';

import realMonitoringService from '../services/realMonitoringService';

// Enhanced color scheme with theme support
const COLORS = {
  primary: '#4F46E5',
  secondary: '#6366f1',
  accent: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  success: '#10B981',
  info: '#3B82F6',
  emotions: [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD'
  ],
  gradients: {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    success: 'linear-gradient(135deg, #48BB78 0%, #38A169 100%)',
    warning: 'linear-gradient(135deg, #ED8936 0%, #D69E2E 100%)',
    danger: 'linear-gradient(135deg, #F56565 0%, #E53E3E 100%)',
    info: 'linear-gradient(135deg, #4299E1 0%, #3182CE 100%)'
  }
};

// Tab panel component
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`monitoring-tabpanel-${index}`}
      aria-labelledby={`monitoring-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const MonitoringDashboard = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  // State management
  const [data, setData] = useState(null);
  const [analyzedData, setAnalyzedData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [overallHealth, setOverallHealth] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Enhanced data fetching with better error handling
  const fetchData = useCallback(async () => {
    try {
      setError(null);
      setBackendStatus('checking');

      console.log('🔄 Fetching comprehensive monitoring data...');
      const monitoringData = await realMonitoringService.getAllMonitoringData();

      if (!monitoringData) {
        throw new Error('No monitoring data received from backend');
      }

      console.log('📊 Raw monitoring data:', monitoringData);
      setData(monitoringData);
      setBackendStatus('online');

      // Enhanced data analysis
      const analyzed = {
        modelPerformance: realMonitoringService.analyzeModelPerformance(monitoringData.modelPerformance),
        systemMetrics: realMonitoringService.analyzeSystemMetrics(monitoringData.systemMetrics),
        apiMetrics: realMonitoringService.analyzeApiMetrics(monitoringData.apiMetrics),
        predictionLogs: realMonitoringService.analyzePredictionLogs(monitoringData.predictionLogs),
        driftDetection: realMonitoringService.analyzeDriftDetection(monitoringData.driftDetection),
        errorTracking: realMonitoringService.analyzeErrorTracking(monitoringData.errorTracking)
      };

      console.log('📈 Analyzed data:', analyzed);
      setAnalyzedData(analyzed);

      // Calculate comprehensive health metrics
      const health = realMonitoringService.calculateOverallHealth(
        analyzed.systemMetrics,
        analyzed.apiMetrics,
        analyzed.driftDetection
      );
      setOverallHealth(health);

      setLastUpdated(new Date().toLocaleTimeString());
      setLoading(false);

    } catch (err) {
      console.error('❌ Error fetching monitoring data:', err);
      setError(`Failed to load monitoring data: ${err.message}`);
      setBackendStatus('offline');
      setLoading(false);
    }
  }, []);

  // Auto-refresh functionality
  useEffect(() => {
    fetchData();

    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchData, autoRefresh]);

  // Tab change handler
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Manual refresh handler
  const handleRefresh = () => {
    setLoading(true);
    fetchData();
  };

  // Status utility functions
  const getStatusIcon = (status) => {
    switch (status) {
      case 'online': return <CheckCircleIcon sx={{ color: COLORS.success, mr: 1 }} />;
      case 'offline': return <ErrorIcon sx={{ color: COLORS.danger, mr: 1 }} />;
      default: return <CircularProgress size={16} sx={{ mr: 1 }} />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'online': return 'Backend Online';
      case 'offline': return 'Backend Offline';
      default: return 'Checking Status...';
    }
  };

  const getHealthColor = (score) => {
    if (score >= 80) return COLORS.success;
    if (score >= 60) return COLORS.warning;
    return COLORS.danger;
  };

  // Memoized health status component
  const HealthStatusCard = useMemo(() => {
    if (!overallHealth) return null;

    return (
      <Card sx={{
        background: COLORS.gradients.primary,
        color: 'white',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {overallHealth.score}%
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                {overallHealth.status}
              </Typography>
            </Box>
            <Box sx={{
              width: 80,
              height: 80,
              position: 'relative'
            }}>
              <CircularProgress
                variant="determinate"
                value={100}
                size={80}
                thickness={4}
                sx={{ color: 'rgba(255,255,255,0.2)', position: 'absolute' }}
              />
              <CircularProgress
                variant="determinate"
                value={overallHealth.score}
                size={80}
                thickness={4}
                sx={{ color: 'white' }}
              />
              <Box sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Typography variant="caption" sx={{ color: 'white', fontWeight: 'bold' }}>
                  {overallHealth.score}%
                </Typography>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>
    );
  }, [overallHealth]);

  // Loading state
  if (loading && !data) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white'
        }}
      >
        <Box textAlign="center">
          <CircularProgress size={60} sx={{ color: COLORS.accent, mb: 2 }} />
          <Typography variant="h6">Loading Monitoring Dashboard...</Typography>
          <Typography variant="body2" color="rgba(255,255,255,0.7)" sx={{ mt: 1 }}>
            Fetching real-time system metrics, model performance, and analytics
          </Typography>
        </Box>
      </Box>
    );
  }

  // Error state
  if (error && backendStatus === 'offline') {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          p: 3
        }}
      >
        <Card sx={{
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 3,
          p: 4,
          textAlign: 'center',
          maxWidth: 600
        }}>
          <ErrorIcon sx={{ fontSize: 80, color: COLORS.danger, mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            Monitoring Service Unavailable
          </Typography>
          <Typography variant="body1" color="rgba(255,255,255,0.7)" sx={{ mb: 3 }}>
            {error}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <IconButton
              onClick={handleRefresh}
              sx={{
                background: COLORS.gradients.primary,
                color: 'white',
                '&:hover': { background: COLORS.gradients.primary }
              }}
            >
              <RefreshIcon />
            </IconButton>
            <IconButton
              onClick={() => navigate('/')}
              sx={{
                background: COLORS.gradients.info,
                color: 'white',
                '&:hover': { background: COLORS.gradients.info }
              }}
            >
              <HomeIcon />
            </IconButton>
          </Box>
        </Card>
      </Box>
    );
  }

  // Main dashboard render
  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
      color: 'white',
      pb: 4
    }}>
      {/* Header */}
      <AppBar position="static" sx={{
        background: 'rgba(255,255,255,0.05)',
        backdropFilter: 'blur(10px)',
        boxShadow: 'none',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <Box sx={{ p: 2 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center">
              <DashboardIcon sx={{ mr: 2, fontSize: 32 }} />
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                  Monitoring Dashboard
                </Typography>
                <Box display="flex" alignItems="center" sx={{ mt: 0.5 }}>
                  {getStatusIcon(backendStatus)}
                  <Typography variant="body2" sx={{ opacity: 0.8 }}>
                    {getStatusText(backendStatus)}
                  </Typography>
                  {lastUpdated && (
                    <Typography variant="body2" sx={{ ml: 2, opacity: 0.6 }}>
                      Last updated: {lastUpdated}
                    </Typography>
                  )}
                </Box>
              </Box>
            </Box>

            <Box display="flex" alignItems="center" gap={2}>
              <Tooltip title="Toggle Auto Refresh">
                <Chip
                  icon={<RefreshIcon />}
                  label={`Auto Refresh: ${autoRefresh ? 'ON' : 'OFF'}`}
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  color={autoRefresh ? 'success' : 'default'}
                  variant={autoRefresh ? 'filled' : 'outlined'}
                />
              </Tooltip>

              <Tooltip title="Manual Refresh">
                <IconButton
                  onClick={handleRefresh}
                  disabled={loading}
                  sx={{
                    background: loading ? 'rgba(255,255,255,0.1)' : COLORS.gradients.primary,
                    color: 'white',
                    '&:hover': { background: COLORS.gradients.primary }
                  }}
                >
                  {loading ? <CircularProgress size={20} /> : <RefreshIcon />}
                </IconButton>
              </Tooltip>

              <Tooltip title="Back to Home">
                <IconButton
                  onClick={() => navigate('/')}
                  sx={{
                    background: COLORS.gradients.info,
                    color: 'white',
                    '&:hover': { background: COLORS.gradients.info }
                  }}
                >
                  <HomeIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </Box>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ p: 3 }}>
        {/* Health Status Overview */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            {HealthStatusCard}
          </Grid>

          {/* Quick Stats */}
          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              {analyzedData.apiMetrics && (
                <>
                  <Grid item xs={6} md={3}>
                    <Card sx={{
                      background: COLORS.gradients.success,
                      color: 'white',
                      textAlign: 'center'
                    }}>
                      <CardContent sx={{ py: 2 }}>
                        <SpeedIcon sx={{ fontSize: 32, mb: 1 }} />
                        <Typography variant="h6">
                          {analyzedData.apiMetrics.avgLatency || 0}ms
                        </Typography>
                        <Typography variant="caption">
                          Avg Latency
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={6} md={3}>
                    <Card sx={{
                      background: COLORS.gradients.info,
                      color: 'white',
                      textAlign: 'center'
                    }}>
                      <CardContent sx={{ py: 2 }}>
                        <TrendingUpIcon sx={{ fontSize: 32, mb: 1 }} />
                        <Typography variant="h6">
                          {analyzedData.apiMetrics.totalPredictions || 0}
                        </Typography>
                        <Typography variant="caption">
                          Total Predictions
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </>
              )}

              {analyzedData.systemMetrics && (
                <>
                  <Grid item xs={6} md={3}>
                    <Card sx={{
                      background: COLORS.gradients.warning,
                      color: 'white',
                      textAlign: 'center'
                    }}>
                      <CardContent sx={{ py: 2 }}>
                        <MemoryIcon sx={{ fontSize: 32, mb: 1 }} />
                        <Typography variant="h6">
                          {Math.round(analyzedData.systemMetrics.avgCpu || 0)}%
                        </Typography>
                        <Typography variant="caption">
                          CPU Usage
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid item xs={6} md={3}>
                    <Card sx={{
                      background: COLORS.gradients.danger,
                      color: 'white',
                      textAlign: 'center'
                    }}>
                      <CardContent sx={{ py: 2 }}>
                        <StorageIcon sx={{ fontSize: 32, mb: 1 }} />
                        <Typography variant="h6">
                          {Math.round(analyzedData.systemMetrics.avgMemory || 0)}%
                        </Typography>
                        <Typography variant="caption">
                          Memory Usage
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </>
              )}
            </Grid>
          </Grid>
        </Grid>

        {/* Tabbed Content */}
        <Paper sx={{
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: 2
        }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            sx={{
              borderBottom: '1px solid rgba(255,255,255,0.1)',
              '& .MuiTab-root': {
                color: 'rgba(255,255,255,0.7)',
                '&.Mui-selected': {
                  color: 'white'
                }
              }
            }}
          >
            <Tab icon={<AssessmentIcon />} label="Performance" />
            <Tab icon={<ComputerIcon />} label="System" />
            <Tab icon={<PsychologyIcon />} label="Emotions" />
            <Tab icon={<TimelineIcon />} label="Analytics" />
            <Tab icon={<BugReportIcon />} label="Errors" />
          </Tabs>

          {/* Tab Panels */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} lg={6}>
                <ModelPerformanceChart data={data?.modelPerformance} />
              </Grid>
              <Grid item xs={12} lg={6}>
                <ApiPerformanceChart data={data?.apiMetrics} />
              </Grid>
              <Grid item xs={12}>
                <LatencyTrendsChart data={data?.predictionLogs} />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <SystemMetricsChart data={data?.systemMetrics} />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <EmotionDistributionChart data={data?.predictionLogs} />
              </Grid>
              <Grid item xs={12} md={6}>
                <SubEmotionDistributionChart data={data?.predictionLogs} />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <DriftDetectionChart data={data?.driftDetection} />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={4}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <ErrorTrackingChart data={data?.errorTracking} />
              </Grid>
            </Grid>
          </TabPanel>
        </Paper>
      </Box>
    </Box>
  );
};

export default MonitoringDashboard;
