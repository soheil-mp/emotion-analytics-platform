import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { ErrorOutline as ErrorIcon, Refresh as RefreshIcon } from '@mui/icons-material';

class MonitoringErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Monitoring Dashboard Error:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            minHeight: '100vh',
            background: `
              linear-gradient(145deg,
                #020617 0%,
                #0f172a 30%,
                #1e293b 70%,
                #334155 100%
              )
            `,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3
          }}
        >
          <Paper
            sx={{
              p: 4,
              maxWidth: 600,
              textAlign: 'center',
              background: 'rgba(255, 255, 255, 0.02)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(220, 38, 38, 0.2)',
              borderRadius: '16px',
            }}
          >
            <ErrorIcon sx={{ fontSize: 64, color: '#dc2626', mb: 2 }} />

            <Typography variant="h4" fontWeight="bold" color="white" gutterBottom>
              Monitoring Dashboard Error
            </Typography>

            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              There was an error loading the monitoring dashboard. This is likely due to a missing dependency or configuration issue.
            </Typography>

            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={this.handleRetry}
              sx={{
                background: 'linear-gradient(135deg, #4F46E5 0%, #3730a3 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #3730a3 0%, #4F46E5 100%)',
                },
                mb: 2
              }}
            >
              Retry Loading
            </Button>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              If the problem persists, check the browser console for more details.
            </Typography>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(220, 38, 38, 0.1)', borderRadius: 1 }}>
                <Typography variant="caption" color="error.main" component="pre" sx={{ fontSize: '0.75rem' }}>
                  {this.state.error.toString()}
                </Typography>
              </Box>
            )}
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default MonitoringErrorBoundary;
