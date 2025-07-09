import React, { memo } from 'react';
import { Box, Typography } from '@mui/material';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { motion } from 'framer-motion';
import customTheme from '../theme';
import BoltIcon from '@mui/icons-material/Bolt';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

/**
 * IntensityDistributionChart Component
 *
 * Displays the distribution of emotional intensity levels from the analysis data.
 * Shows patterns in emotional intensity across different categories (mild, moderate, intense).
 *
 * Features:
 * - Dual visualization: Bar chart and Polar area chart
 * - Intensity-based color gradients
 * - Animated rendering
 * - Statistical summary
 */
const IntensityDistributionChart = memo(({ analysisData }) => {

  // Process intensity data
  const processIntensityData = (data) => {
    if (!data || !data.transcript) return {};

    const intensityCounts = {
      mild: 0,
      moderate: 0,
      intense: 0
    };

    let totalCount = 0;

    data.transcript.forEach(item => {
      if (item.intensity) {
        const intensity = item.intensity.toLowerCase();
        if (intensityCounts.hasOwnProperty(intensity)) {
          intensityCounts[intensity]++;
          totalCount++;
        }
      }
    });

    // Convert to percentages
    const intensityDistribution = {};
    Object.entries(intensityCounts).forEach(([intensity, count]) => {
      intensityDistribution[intensity] = totalCount > 0 ? count / totalCount : 0;
    });

    return {
      distribution: intensityDistribution,
      totalCount,
      rawCounts: intensityCounts
    };
  };

  const intensityData = processIntensityData(analysisData);
  const { distribution: intensityDistribution, totalCount, rawCounts } = intensityData;
  const hasData = totalCount > 0;

  // Color mapping for intensity levels
  const getIntensityColor = (intensity) => {
    const intensityColors = {
      mild: '#10B981',      // Emerald green
      moderate: '#F59E0B',  // Amber      intense: '#EF4444'    // Red
    };
    return intensityColors[intensity] || '#6B7280';
  };

  if (!hasData) {
    return (
      <Box sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: customTheme.colors.text.secondary,
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Background Glow */}
        <Box sx={{
          position: 'absolute',
          top: '25%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '95px',
          height: '95px',
          borderRadius: '50%',
          background: `
            radial-gradient(circle,
              #F59E0B15 0%,
              #EF444410 40%,
              #10B98110 80%,
              transparent 100%
            )
          `,
          animation: 'intensityGlow 4s ease-in-out infinite',
          '@keyframes intensityGlow': {
            '0%, 100%': { transform: 'translateX(-50%) scale(1)', opacity: 0.4 },
            '50%': { transform: 'translateX(-50%) scale(1.25)', opacity: 0.7 }
          }
        }} />

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          style={{ position: 'relative', zIndex: 2 }}
        >
          <Box sx={{
            width: 68,
            height: 68,
            borderRadius: '50%',
            background: `linear-gradient(135deg, #F59E0B25, #EF444420, #10B98115)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
            position: 'relative',
            border: `1px solid #F59E0B40`,
            boxShadow: `
              0 0 20px #F59E0B20,
              0 4px 12px #F59E0B15
            `,
            animation: 'intensityIconFloat 3s ease-in-out infinite',
            '@keyframes intensityIconFloat': {
              '0%, 100%': {
                transform: 'translateY(0px) rotate(0deg)',
                filter: 'brightness(1)',
                boxShadow: `0 0 20px #F59E0B20, 0 4px 12px #F59E0B15`
              },
              '50%': {
                transform: 'translateY(-5px) rotate(-5deg)',
                filter: 'brightness(1.15)',
                boxShadow: `0 0 25px #EF444425, 0 6px 16px #EF444420`
              }
            }
          }}>
            <BoltIcon sx={{
              fontSize: '1.7rem',
              color: '#F59E0B',
              filter: `drop-shadow(0 2px 4px #F59E0B30)`
            }} />
          </Box>
          <Typography variant="body2" sx={{
            color: customTheme.colors.text.primary,
            fontSize: '0.8rem',
            fontWeight: 600,
            opacity: 0.9
          }}>
            Awaiting intensity data
          </Typography>
        </motion.div>
      </Box>
    );
  }

  // Prepare data for charts
  const intensityLevels = ['mild', 'moderate', 'intense'];
  const labels = intensityLevels.map(level => level.charAt(0).toUpperCase() + level.slice(1));
  const values = intensityLevels.map(level => intensityDistribution[level] || 0);
  const colors = intensityLevels.map(level => getIntensityColor(level));

  // Bar chart configuration
  const barChartData = {
    labels,
    datasets: [{
      label: 'Intensity Distribution',
      data: values,
      backgroundColor: colors.map(color => `${color}80`),
      borderColor: colors,
      borderWidth: 2,
      borderRadius: 8,
      borderSkipped: false,
    }]
  };  const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 400,
      easing: 'easeOutQuart'
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: customTheme.colors.surface.glass,
        titleColor: customTheme.colors.text.primary,
        bodyColor: customTheme.colors.text.secondary,
        borderColor: customTheme.colors.border,
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        callbacks: {
          label: (context) => `${Math.round(context.parsed.y * 100)}% (${rawCounts[intensityLevels[context.dataIndex]]} occurrences)`
        }
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: customTheme.colors.text.secondary,
          font: { size: 11, weight: '600' }
        },
        border: { display: false }
      },
      y: {
        beginAtZero: true,
        max: Math.max(...values) * 1.2,
        grid: {
          color: `${customTheme.colors.secondary.main}20`,
        },
        ticks: {
          color: customTheme.colors.text.tertiary,
          font: { size: 10 },
          callback: (value) => `${Math.round(value * 100)}%`
        },
        border: { display: false }
      },    },    layout: {
      padding: { top: 5, right: 5, bottom: 5, left: 5 }
    }};

  return (<Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Single Chart Container */}
      <Box sx={{
        flex: 1,
        minHeight: 0
      }}>
        {/* Bar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          style={{ height: '100%' }}
        >
          <Box sx={{
            height: '100%',            background: `linear-gradient(135deg, ${customTheme.colors.secondary.main}05, transparent)`,
            borderRadius: customTheme.borderRadius.lg,
            border: `1px solid ${customTheme.colors.secondary.main}20`,
            p: 1
          }}>            <Box sx={{
              height: '100%',
              overflow: 'hidden'
            }}>
              <Bar
                key="intensity-bar-chart"
                data={barChartData}
                options={barChartOptions}
              />
            </Box>
          </Box>
        </motion.div>
      </Box>
    </Box>
  );
});

IntensityDistributionChart.displayName = 'IntensityDistributionChart';

export default IntensityDistributionChart;
