import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import customTheme from '../theme';

// Import distribution chart components
import EmotionDistributionChart from './EmotionDistributionChart';
import SubEmotionDistributionChart from './SubEmotionDistributionChart';
import IntensityDistributionChart from './IntensityDistributionChart';

/**
 * EmotionDistributionAnalytics Component - Advanced Data Distribution Analytics
 *
 * Provides comprehensive data distribution visualization across three key dimensions:
 * - Emotion Distribution: Primary emotion categories analysis
 * - Sub-emotion Distribution: Detailed emotional nuances
 * - Intensity Distribution: Emotional intensity patterns
 *
 * Features:
 * - Tabbed interface for organized data exploration
 * - Animated transitions between views
 * - Responsive chart rendering
 * - Empty state handling
 */
const EmotionDistributionAnalytics = ({ analysisData, currentTime = 0 }) => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const tabPanelStyle = {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative'
  };
  const tabData = [
    {
      label: 'Emotions',
      icon: '○',
      description: 'Primary emotion categories distribution',
      component: EmotionDistributionChart
    },
    {
      label: 'Sub-emotions',
      icon: '◇',
      description: 'Detailed emotional nuances analysis',
      component: SubEmotionDistributionChart
    },
    {
      label: 'Intensity',
      icon: '△',
      description: 'Emotional intensity patterns',
      component: IntensityDistributionChart
    }
  ];

  // Show empty state when no data is available
  if (!analysisData || !analysisData.transcript || analysisData.transcript.length === 0) {
    return (
      <Box sx={{
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        gap: 3,
        color: customTheme.colors.text.secondary,
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Animated Background Elements */}
        <Box sx={{
          position: 'absolute',
          top: '15%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '140px',
          height: '140px',
          borderRadius: '50%',
          background: `
            radial-gradient(circle at 40% 40%,
              ${customTheme.colors.secondary.main}12 0%,
              ${customTheme.colors.primary.main}08 60%,
              transparent 100%
            )
          `,
          animation: 'distributionPulse 5s ease-in-out infinite',
          '@keyframes distributionPulse': {
            '0%, 100%': { transform: 'translateX(-50%) scale(1)', opacity: 0.5 },
            '50%': { transform: 'translateX(-50%) scale(1.15)', opacity: 0.8 }
          }
        }} />

        {/* Central Distribution Icon */}
        <Box sx={{
          width: 85,
          height: 85,
          borderRadius: '50%',
          background: `
            linear-gradient(135deg,
              ${customTheme.colors.secondary.main}85 0%,
              ${customTheme.colors.secondary.dark}65 50%,
              ${customTheme.colors.primary.main}35 100%
            )
          `,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '2.4rem',
          position: 'relative',
          zIndex: 2,
          boxShadow: `
            0 0 35px ${customTheme.colors.secondary.main}45,
            0 8px 28px ${customTheme.colors.secondary.main}25,
            inset 0 1px 0 rgba(255,255,255,0.25)
          `,
          border: `1px solid ${customTheme.colors.secondary.main}55`,
          animation: 'distributionIconFloat 3.5s ease-in-out infinite',
          '@keyframes distributionIconFloat': {
            '0%, 100%': {
              transform: 'translateY(0px) rotate(0deg)',
              filter: 'brightness(1) saturate(1)'
            },
            '50%': {
              transform: 'translateY(-8px) rotate(-3deg)',
              filter: 'brightness(1.15) saturate(1.1)'
            }
          }
        }}>
          📊
        </Box>

        {/* Main Content */}
        <Box sx={{ textAlign: 'center', zIndex: 2 }}>
          <Typography variant="h6" sx={{
            fontWeight: 700,
            color: 'white',
            mb: 1.5,
            fontSize: '1.1rem',
            letterSpacing: '0.5px',
            filter: `drop-shadow(0 2px 8px ${customTheme.colors.secondary.main}30)`
          }}>
            Upload a video to see this section
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative'
    }}>      {/* Tabs Navigation */}
      <Box sx={{
        mb: 2
      }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              color: 'text.secondary',
              textTransform: 'none',
              fontSize: '0.75rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              borderRadius: customTheme.borderRadius.md,
              mx: 0.5,
              border: `1px solid ${customTheme.colors.border}`,
              minHeight: '40px',
              '&:hover': {
                backgroundColor: 'rgba(99, 102, 241, 0.2)',
                color: customTheme.colors.primary.main,
              }
            },
            '& .Mui-selected': {
              color: customTheme.colors.primary.main,
              backgroundColor: 'rgba(99, 102, 241, 0.25)',
              fontWeight: 600,
              border: `1px solid ${customTheme.colors.primary.main}40`,
            },
            '& .MuiTabs-indicator': {
              backgroundColor: customTheme.colors.primary.main,
              height: 3,
              borderRadius: '2px',
            }
          }}
        >
          {tabData.map((tab, index) => (
            <Tab
              key={index}
              label={
                <Box sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}>
                  <Box sx={{ fontSize: '1rem' }}>{tab.icon}</Box>
                  <Typography variant="caption" sx={{
                    fontWeight: 600,
                    fontSize: '0.7rem'
                  }}>
                    {tab.label}
                  </Typography>
                </Box>
              }
            />
          ))}
        </Tabs>
      </Box>

      {/* Tab Panels with Animation */}
      <Box sx={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <AnimatePresence mode="wait">
          {tabData.map((tab, index) => {
            if (index !== activeTab) return null;
              const ChartComponent = tab.component;

            return (
              <motion.div
                key={`tab-panel-${index}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}                transition={{
                  duration: 0.3,
                  ease: "easeOut"
                }}
                style={tabPanelStyle}
              >                <Box sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column'
                }}>
                  {/* Chart Container - Maximized */}
                  <Box sx={{
                    flex: 1,
                    height: '100%'
                  }}>
                    <ChartComponent
                      key={`chart-${index}-${activeTab}`}
                      analysisData={analysisData}
                      currentTime={currentTime}
                    />
                  </Box>
                </Box>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </Box>
    </Box>
  );
};

export default EmotionDistributionAnalytics;
