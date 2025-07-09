import React from 'react';
import { Box, Typography } from '@mui/material';
import { Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';
import 'chartjs-adapter-date-fns';
import { getEmotionColor } from '../utils';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  annotationPlugin
);

// Add CSS animation for pulsing cursor effect
if (typeof document !== 'undefined' && !document.querySelector('#timeline-animations')) {
  const style = document.createElement('style');
  style.id = 'timeline-animations';
  style.textContent = `
    @keyframes timelinePulse {
      0% { opacity: 0.7; }
      50% { opacity: 1; }
      100% { opacity: 0.7; }
    }
  `;
  document.head.appendChild(style);
}

const EmotionTimeline = ({ data, currentTime }) => {
  // Format timestamp display for x-axis
  const formatTimestamp = (seconds) => {
    if (seconds === undefined || seconds === null || isNaN(seconds)) {
      return "0:00";
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const isValidData = data && data.datasets && data.datasets.length > 0;
  const emotionLabels = isValidData ? data.emotionLabels : [];
  const modifiedChartData = React.useMemo(() => {
    if (!isValidData) {
      // Return a structure that matches what Scatter expects, even if empty
      return { datasets: [], emotionLabels: [] };
    }

    return {
      ...data, // Spreads other properties from data, like emotionLabels
      datasets: data.datasets.map(dataset => {
        const originalBackgroundColor = dataset.backgroundColor;
        const originalBorderColor = dataset.borderColor;
        const originalPointRadius = dataset.pointRadius !== undefined ? dataset.pointRadius : 7;
        const originalHoverRadius = dataset.pointHoverRadius !== undefined ? dataset.pointHoverRadius : 10;

        return {
          ...dataset,
          pointRadius: function(context) {
            const xValue = context.raw?.x ?? context.parsed?.x;
            if (xValue === undefined) return originalPointRadius;
            // Always show all points, but make future ones slightly smaller
            return xValue > currentTime ? originalPointRadius * 0.8 : originalPointRadius;
          },
          pointBackgroundColor: function(context) {
            const xValue = context.raw?.x ?? context.parsed?.x;
            if (xValue === undefined) return originalBackgroundColor;
            // Future points are slightly dimmed but always visible
            if (xValue > currentTime) {
              // Convert color to rgba with reduced opacity for future points
              const color = originalBackgroundColor;
              if (typeof color === 'string' && color.startsWith('#')) {
                const r = parseInt(color.slice(1, 3), 16);
                const g = parseInt(color.slice(3, 5), 16);
                const b = parseInt(color.slice(5, 7), 16);
                return `rgba(${r}, ${g}, ${b}, 0.4)`;
              }
              return color;
            }
            return originalBackgroundColor;
          },
          pointBorderColor: function(context) {
            const xValue = context.raw?.x ?? context.parsed?.x;
            if (xValue === undefined) return originalBorderColor;
            // Future points have dimmed borders
            if (xValue > currentTime) {
              const color = originalBorderColor;
              if (typeof color === 'string' && color.startsWith('#')) {
                const r = parseInt(color.slice(1, 3), 16);
                const g = parseInt(color.slice(3, 5), 16);
                const b = parseInt(color.slice(5, 7), 16);
                return `rgba(${r}, ${g}, ${b}, 0.3)`;
              }
              return color;
            }
            return originalBorderColor;
          },
          pointHoverRadius: originalHoverRadius,
          pointBorderWidth: function(context) {
            const xValue = context.raw?.x ?? context.parsed?.x;
            if (xValue === undefined) return 2;
            // Current and past points have thicker borders
            return xValue > currentTime ? 1 : 2;
          }
        };
      })
    };
  }, [data, currentTime, isValidData]);
  // Chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 300, // Smooth animation for luxury feel
      easing: 'easeOutCubic',
    },
    interaction: {
      mode: 'nearest',
      intersect: false,
      axis: 'x'
    },
    plugins: {
      legend: {
        display: false,
        position: 'top',
        labels: {
          usePointStyle: true,
          pointStyle: 'circle',
          font: {
            size: 11,
            family: "'Inter', sans-serif",
            weight: 500
          },
          boxWidth: 10,
          boxHeight: 10
        }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.95)', // Navy background
        titleColor: '#f8fafc',
        bodyColor: '#e2e8f0',
        bodyFont: {
          family: "'Inter', sans-serif",
          size: 13
        },
        titleFont: {
          family: "'Inter', sans-serif",
          size: 14,
          weight: 600
        },
        padding: 16,
        borderColor: 'rgba(148, 163, 184, 0.2)',
        borderWidth: 1,
        cornerRadius: 12,
        boxPadding: 6,
        usePointStyle: true,
        boxWidth: 12,
        boxHeight: 12,
        callbacks: {
          title: (items) => {
            if (!items.length) return '';
            const seconds = parseFloat(items[0].parsed.x);
            return `Time: ${formatTimestamp(seconds)}`;
          },
          label: (context) => {
            const dataset = context.dataset;
            const emotion = dataset.label;
            return emotion;
          }
        },
        mode: 'nearest',
        intersect: false,
      },
      annotation: {
        annotations: {}
      }
    },    scales: {
      x: {
        type: 'linear',
        title: {
          display: true,
          text: 'Timeline',
          color: 'rgba(148, 163, 184, 0.8)',
          font: {
            weight: 600,
            size: 12,
            family: "'Inter', sans-serif"
          }
        },
        ticks: {
          callback: (value) => formatTimestamp(value),
          maxRotation: 0,
          autoSkip: true,
          color: 'rgba(148, 163, 184, 0.7)',
          font: {
            size: 11,
            family: "'Inter', sans-serif",
            weight: 500
          }
        },
        grid: {
          display: true,
          color: 'rgba(148, 163, 184, 0.1)',
          lineWidth: 1,
        },
        border: {
          display: false,
        }
      },
      y: {
        type: 'category',
        labels: emotionLabels,
        offset: true,
        position: 'left',
        title: {
          display: true,
          text: 'Emotions',
          color: 'rgba(148, 163, 184, 0.8)',
          font: {
            weight: 600,
            size: 12,
            family: "'Inter', sans-serif"
          }
        },
        ticks: {
          font: {
            size: 12,
            family: "'Inter', sans-serif",
            weight: 500
          },
          color: (context) => {
            if (context.tick && typeof context.tick.label === 'string') {
              return getEmotionColor(context.tick.label.toLowerCase());
            }
            return 'rgba(148, 163, 184, 0.8)';
          },
          padding: 12
        },
        grid: {
          display: true,
          color: 'rgba(148, 163, 184, 0.08)',
          lineWidth: 1,
          z: 1
        },
        border: {
          display: false,
        }
      }
    },    elements: {
      point: {
        pointStyle: 'circle', // Changed to circle for a more modern look
        borderWidth: 2,
      },
    },
    parsing: {
      xAxisKey: 'x',
      yAxisKey: 'y'
    }
  };
  // Add beautiful animated cursor for current time position when available
  if (currentTime !== undefined && currentTime !== null) {
    // Main cursor line with gradient and glow effect
    options.plugins.annotation.annotations.currentTimeLine = {
      type: 'line',
      scaleID: 'x',
      value: currentTime,
      borderColor: '#3b82f6', // Beautiful blue
      borderWidth: 3,
      borderDash: [],
      label: {
        content: '● NOW',
        enabled: true,
        position: 'top',
        backgroundColor: 'rgba(59, 130, 246, 0.95)',
        color: '#ffffff',
        font: {
          size: 10,
          weight: 'bold',
          family: "'Inter', sans-serif"
        },
        padding: {
          x: 8,
          y: 4
        },
        cornerRadius: 6,
        borderColor: 'rgba(59, 130, 246, 0.3)',
        borderWidth: 1,
      },
      z: 10 // Ensure it's above other elements
    };

    // Add a subtle glow line behind the main cursor for depth
    options.plugins.annotation.annotations.currentTimeGlow = {
      type: 'line',
      scaleID: 'x',
      value: currentTime,
      borderColor: 'rgba(59, 130, 246, 0.2)',
      borderWidth: 8,
      borderDash: [],
      z: 9 // Behind the main line
    };

    // Add animated pulse at the current time position (top)
    options.plugins.annotation.annotations.currentTimePulse = {
      type: 'point',
      xValue: currentTime,
      yValue: emotionLabels.length > 0 ? emotionLabels[emotionLabels.length - 1] : 0,
      backgroundColor: 'rgba(59, 130, 246, 0.8)',
      borderColor: '#3b82f6',
      borderWidth: 2,
      radius: 6,
      z: 11
    };
  }

  // Add horizontal lines to separate emotions more clearly
  // This section is removed as drawing lines precisely between string-based categories
  // with the annotation plugin is complex and might not render as expected.
  // The default y-axis grid lines will provide some separation.
  /*
  if (emotionLabels.length > 0) {
    emotionLabels.forEach((label, index) => {
      if (index < emotionLabels.length - 1) {
        options.plugins.annotation.annotations[`line${index}`] = {
          type: 'line',
          scaleID: 'y',
          value: label,
          yMax: label,
          yMin: label,
          borderColor: 'rgba(0, 0, 0, 0.1)',
          borderWidth: 1,
          borderDash: [3, 3],
        };
      }
    });
  }
  */
  return (
    <Box sx={{
      width: '100%',
      height: 320,
      position: 'relative',
      pb: 3,
      pt: 2,
      px: 2,
      background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.02) 0%, rgba(30, 41, 59, 0.02) 100%)',
      borderRadius: 3,
      border: '1px solid rgba(148, 163, 184, 0.1)',
      backdropFilter: 'blur(10px)',
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.03) 0%, rgba(139, 92, 246, 0.03) 100%)',
        borderRadius: 3,
        pointerEvents: 'none',
        zIndex: 1,
      },
      '& > *': {
        position: 'relative',
        zIndex: 2,
      }
    }}>
      {isValidData ? (
        <Scatter
          options={options}
          data={modifiedChartData}
        />
      ) : (
        <Box sx={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'rgba(148, 163, 184, 0.8)',
          fontSize: '0.9rem',
          opacity: 0.8,
          fontStyle: 'italic'
        }}>
          <Typography variant="body2" sx={{
            mb: 1,
            color: 'rgba(148, 163, 184, 0.9)',
            fontWeight: 500
          }}>
            No timeline data available
          </Typography>
          <Typography variant="caption" sx={{
            color: 'rgba(148, 163, 184, 0.7)'
          }}>
            Process a video to see emotion analysis over time
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default EmotionTimeline;
