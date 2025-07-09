import React, { memo } from 'react';
import { Box, Typography } from '@mui/material';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { motion } from 'framer-motion';
import { getEmotionColor, processEmotionData } from '../utils';
import customTheme from '../theme';
import InsightsIcon from '@mui/icons-material/Insights';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);

/**
 * EmotionDistributionChart Component
 *
 * Displays the distribution of primary emotions using both bar and doughnut charts
 * for comprehensive data visualization.
 *
 * Features:
 * - Dual chart view (bar and doughnut)
 * - Animated rendering
 * - Responsive design
 * - Empty state handling
 */
const EmotionDistributionChart = memo(({ analysisData }) => {
  // Process emotion data
  const { emotionDistribution } = analysisData ? processEmotionData(analysisData) : { emotionDistribution: {} };

  // Check if we have data
  const hasData = Object.keys(emotionDistribution).length > 0;

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
          top: '30%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '100px',
          height: '100px',
          borderRadius: '50%',
          background: `
            radial-gradient(circle,
              ${customTheme.colors.primary.main}10 0%,
              ${customTheme.colors.secondary.main}08 50%,
              transparent 100%
            )
          `,
          animation: 'chartGlow 3s ease-in-out infinite',
          '@keyframes chartGlow': {
            '0%, 100%': { transform: 'translateX(-50%) scale(1)', opacity: 0.4 },
            '50%': { transform: 'translateX(-50%) scale(1.2)', opacity: 0.7 }
          }
        }} />

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          style={{ position: 'relative', zIndex: 2 }}
        >
          <Box sx={{
            width: 70,
            height: 70,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${customTheme.colors.primary.main}25, ${customTheme.colors.secondary.main}20)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
            position: 'relative',
            border: `1px solid ${customTheme.colors.primary.main}40`,
            boxShadow: `
              0 0 20px ${customTheme.colors.primary.main}20,
              0 4px 12px ${customTheme.colors.primary.main}15
            `,
            animation: 'chartIconFloat 2.5s ease-in-out infinite',
            '@keyframes chartIconFloat': {
              '0%, 100%': { transform: 'translateY(0px)', filter: 'brightness(1)' },
              '50%': { transform: 'translateY(-4px)', filter: 'brightness(1.1)' }
            }
          }}>
            <InsightsIcon sx={{
              fontSize: '1.8rem',
              color: customTheme.colors.primary.main,
              filter: `drop-shadow(0 2px 4px ${customTheme.colors.primary.main}30)`
            }} />
          </Box>
          <Typography variant="body2" sx={{
            color: customTheme.colors.text.primary,
            fontSize: '0.85rem',
            fontWeight: 600,
            opacity: 0.9
          }}>
            Awaiting emotion data
          </Typography>
        </motion.div>
      </Box>
    );
  }

  // Prepare data for charts
  const sortedEmotions = Object.entries(emotionDistribution)
    .sort((a, b) => b[1] - a[1])
    .map(([emotion, value]) => ({ emotion, value }));

  const labels = sortedEmotions.map(item =>
    item.emotion.charAt(0).toUpperCase() + item.emotion.slice(1)
  );
  const values = sortedEmotions.map(item => item.value);
  const colors = sortedEmotions.map(item => getEmotionColor(item.emotion));

  // Bar chart configuration
  const barChartData = {
    labels,
    datasets: [{
      label: 'Distribution',
      data: values,
      backgroundColor: colors.map(color => `${color}80`),
      borderColor: colors,
      borderWidth: 2,
      borderRadius: 6,
      borderSkipped: false,
    }]
  };
  const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 800,
      easing: 'easeOutQuart',
      loop: false,
      animateRotate: false,
      animateScale: false,
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
          label: (context) => `${Math.round(context.parsed.y * 100)}%`
        }
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: customTheme.colors.text.tertiary,
          font: { size: 10, weight: '500' }
        },
        border: { display: false }
      },
      y: {
        beginAtZero: true,
        max: 1,
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
    }
  };
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
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
                key="emotion-bar-chart"
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

EmotionDistributionChart.displayName = 'EmotionDistributionChart';

export default EmotionDistributionChart;
