import React, { memo } from 'react';
import { Box, Typography } from '@mui/material';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { motion } from 'framer-motion';
import { getEmotionColor, analyzeEmotionRelationships } from '../utils';
import customTheme from '../theme';
import PaletteIcon from '@mui/icons-material/Palette';

// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

/**
 * SubEmotionDistributionChart Component
 *
 * Displays the distribution of sub-emotions from the analysis data.
 * Sub-emotions provide more granular emotional insights beyond primary categories.
 *
 * Features:
 * - Vertical bar chart with rotated labels for readability
 * - Color-coded by primary emotion category
 * - Animated rendering with staggered bars
 * - Responsive design with scrollable content for many sub-emotions
 */
const SubEmotionDistributionChart = memo(({ analysisData }) => {
    // Process sub-emotion data
  const processSubEmotionData = (data) => {
    if (!data || !data.transcript) return {};

    const subEmotionCounts = {};
    let totalCount = 0;

    // Debug: log first few transcript entries to see data structure
    console.log('Sample transcript entries:', data.transcript.slice(0, 3));

    data.transcript.forEach(item => {
      if (item.sub_emotion) {
        subEmotionCounts[item.sub_emotion] = (subEmotionCounts[item.sub_emotion] || 0) + 1;
        totalCount++;
      }
    });

    // Convert to percentages
    const subEmotionDistribution = {};
    Object.entries(subEmotionCounts).forEach(([subEmotion, count]) => {
      subEmotionDistribution[subEmotion] = totalCount > 0 ? count / totalCount : 0;
    });

    console.log('Sub-emotion counts found:', subEmotionCounts);
    return subEmotionDistribution;
  };
  // Get actual parent emotions from the transcript data
  const getActualParentEmotions = (data) => {
    if (!data || !data.transcript) return {};

    const parentEmotions = {};
    data.transcript.forEach(item => {
      if (item.emotion) {
        parentEmotions[item.emotion] = getEmotionColor(item.emotion);
      }
    });

    console.log('Actual parent emotions in data with colors:', parentEmotions);
    return parentEmotions;
  };

  // Analyze actual emotion-subemotion relationships in the data
  const analyzeDataRelationships = (data) => {
    if (!data || !data.transcript) return {};

    const relationships = {};
    data.transcript.forEach(item => {
      if (item.emotion && item.sub_emotion) {
        if (!relationships[item.sub_emotion]) {
          relationships[item.sub_emotion] = {
            parentEmotions: new Set(),
            count: 0
          };
        }
        relationships[item.sub_emotion].parentEmotions.add(item.emotion);
        relationships[item.sub_emotion].count++;
      }
    });

    // Convert Sets to Arrays and log relationships
    Object.keys(relationships).forEach(subEmotion => {
      relationships[subEmotion].parentEmotions = Array.from(relationships[subEmotion].parentEmotions);
    });

    console.log('🔍 Actual emotion-subemotion relationships in data:', relationships);
    return relationships;
  };  const subEmotionDistribution = processSubEmotionData(analysisData);
  const actualParentEmotions = getActualParentEmotions(analysisData);
  const { subEmotionParentMap } = analyzeEmotionRelationships(analysisData);
  const dataRelationships = analyzeDataRelationships(analysisData);
  const hasData = Object.keys(subEmotionDistribution).length > 0;

  // Debug: log comprehensive analysis
  console.log('📊 Sub-emotion Analysis Summary:');
  console.log('  - Sub-emotions found:', Object.keys(subEmotionDistribution));
  console.log('  - Parent emotions available:', Object.keys(actualParentEmotions));
  console.log('  - Direct relationships:', subEmotionParentMap);
  console.log('  - Data relationships:', dataRelationships);

  // Enhanced color mapping that prioritizes actual data relationships
  const getSubEmotionColor = (subEmotion) => {
    // FIRST PRIORITY: Use direct relationship from the actual transcript data
    if (subEmotionParentMap[subEmotion]) {
      const parentEmotion = subEmotionParentMap[subEmotion];
      const color = getEmotionColor(parentEmotion);
      console.log(`✓ Sub-emotion "${subEmotion}" found with actual parent "${parentEmotion}" in data -> color: ${color}`);
      return color;
    }

    // SECOND PRIORITY: Look for relationship in transcript segments
    if (analysisData?.transcript) {
      const correspondingSegment = analysisData.transcript.find(item =>
        item.sub_emotion === subEmotion && item.emotion
      );

      if (correspondingSegment && correspondingSegment.emotion) {
        const parentColor = getEmotionColor(correspondingSegment.emotion);
        console.log(`✓ Sub-emotion "${subEmotion}" found with parent "${correspondingSegment.emotion}" in segment -> color: ${parentColor}`);
        return parentColor;
      }
    }

    // THIRD PRIORITY: Use predefined mapping, but only with available parent emotions
    const availableParentColors = Object.keys(actualParentEmotions);
    console.log('Available parent emotions for fallback:', availableParentColors);

    // Comprehensive sub-emotion to parent emotion mapping
    const subEmotionToParent = {
      // Happiness family
      'joy': 'happiness', 'delight': 'happiness', 'bliss': 'happiness',
      'contentment': 'happiness', 'satisfaction': 'happiness', 'elation': 'happiness',
      'cheerfulness': 'happiness', 'happiness': 'happiness', 'pleased': 'happiness',
      'glad': 'happiness', 'cheerful': 'happiness', 'content': 'happiness',
      'satisfied': 'happiness', 'happy': 'happiness', 'excited': 'happiness',
      'enthusiastic': 'happiness', 'positive': 'happiness',

      // Sadness family
      'sorrow': 'sadness', 'melancholy': 'sadness', 'grief': 'sadness',
      'disappointment': 'sadness', 'despair': 'sadness', 'gloom': 'sadness',
      'dejection': 'sadness', 'sadness': 'sadness', 'sad': 'sadness',
      'down': 'sadness', 'blue': 'sadness', 'disappointed': 'sadness',
      'depressed': 'sadness', 'unhappy': 'sadness', 'negative': 'sadness',

      // Anger family
      'rage': 'anger', 'fury': 'anger', 'irritation': 'anger',
      'annoyance': 'anger', 'resentment': 'anger', 'outrage': 'anger',
      'hostility': 'anger', 'anger': 'anger', 'mad': 'anger',
      'angry': 'anger', 'furious': 'anger', 'annoyed': 'anger',
      'irritated': 'anger', 'frustrated': 'anger',

      // Fear family
      'anxiety': 'fear', 'terror': 'fear', 'worry': 'fear',
      'nervousness': 'fear', 'dread': 'fear', 'panic': 'fear',
      'apprehension': 'fear', 'fear': 'fear', 'afraid': 'fear',
      'scared': 'fear', 'nervous': 'fear', 'worried': 'fear',
      'anxious': 'fear', 'terrified': 'fear',

      // Surprise family
      'amazement': 'surprise', 'astonishment': 'surprise', 'wonder': 'surprise',
      'bewilderment': 'surprise', 'shock': 'surprise', 'awe': 'surprise',
      'surprise': 'surprise', 'surprised': 'surprise', 'amazed': 'surprise',
      'astonished': 'surprise', 'shocked': 'surprise', 'startled': 'surprise',

      // Disgust family
      'revulsion': 'disgust', 'repugnance': 'disgust', 'distaste': 'disgust',
      'aversion': 'disgust', 'loathing': 'disgust', 'contempt': 'disgust',
      'disgust': 'disgust', 'disgusted': 'disgust', 'revolted': 'disgust',

      // Neutral family
      'calm': 'neutral', 'indifference': 'neutral', 'composure': 'neutral',
      'boredom': 'neutral', 'apathy': 'neutral', 'neutral': 'neutral',
      'composed': 'neutral', 'peaceful': 'neutral', 'relaxed': 'neutral'
    };

    const subEmotionLower = subEmotion.toLowerCase();

    // Try direct mapping first, but only if that parent emotion exists in our data
    const mappedParent = subEmotionToParent[subEmotionLower];
    if (mappedParent && availableParentColors.includes(mappedParent)) {
      const color = getEmotionColor(mappedParent);
      console.log(`→ Sub-emotion "${subEmotion}" mapped to available parent "${mappedParent}" -> color: ${color}`);
      return color;
    }

    // FOURTH PRIORITY: Keyword matching with available parents
    const emotionKeywords = {
      'happiness': ['happy', 'joy', 'glad', 'pleased', 'cheerful', 'delight', 'bliss', 'content', 'satisfied', 'elated', 'positive', 'excited'],
      'sadness': ['sad', 'sorrow', 'grief', 'melancholy', 'despair', 'dejected', 'gloomy', 'disappointed', 'blue', 'down', 'negative', 'depressed'],
      'anger': ['angry', 'mad', 'rage', 'fury', 'irritated', 'annoyed', 'resentful', 'outraged', 'hostile', 'furious', 'frustrated'],
      'fear': ['afraid', 'scared', 'anxious', 'terrified', 'worried', 'nervous', 'dread', 'panic', 'apprehensive', 'fearful'],
      'surprise': ['surprised', 'amazed', 'astonished', 'wonder', 'bewildered', 'shocked', 'awe', 'startled'],
      'disgust': ['disgusted', 'revolted', 'repugnant', 'distaste', 'aversion', 'loathing', 'contempt', 'repulsed'],
      'neutral': ['calm', 'neutral', 'indifferent', 'composed', 'bored', 'apathetic', 'peaceful', 'relaxed']
    };

    // Find parent emotion based on keywords, but only use if available in our data
    for (const [parentEmotion, keywords] of Object.entries(emotionKeywords)) {
      if (availableParentColors.includes(parentEmotion) &&
          keywords.some(keyword => subEmotionLower.includes(keyword))) {
        const color = getEmotionColor(parentEmotion);
        console.log(`→ Sub-emotion "${subEmotion}" matched keyword "${parentEmotion}" -> color: ${color}`);
        return color;
      }
    }

    // FINAL FALLBACK: Use the first available parent emotion or neutral
    const fallbackEmotion = availableParentColors[0] || 'neutral';
    const fallbackColor = getEmotionColor(fallbackEmotion);
    console.log(`⚠ No match found for sub-emotion "${subEmotion}", using fallback "${fallbackEmotion}" -> color: ${fallbackColor}`);
    return fallbackColor;
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
          top: '30%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '90px',
          height: '90px',
          borderRadius: '50%',
          background: `
            radial-gradient(circle,
              ${customTheme.colors.secondary.main}12 0%,
              ${customTheme.colors.primary.main}08 50%,
              transparent 100%
            )
          `,
          animation: 'subChartGlow 3.5s ease-in-out infinite',
          '@keyframes subChartGlow': {
            '0%, 100%': { transform: 'translateX(-50%) scale(1)', opacity: 0.3 },
            '50%': { transform: 'translateX(-50%) scale(1.15)', opacity: 0.6 }
          }
        }} />

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          style={{ position: 'relative', zIndex: 2 }}
        >
          <Box sx={{
            width: 65,
            height: 65,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${customTheme.colors.secondary.main}30, ${customTheme.colors.primary.main}20)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
            position: 'relative',
            border: `1px solid ${customTheme.colors.secondary.main}45`,
            boxShadow: `
              0 0 20px ${customTheme.colors.secondary.main}25,
              0 4px 12px ${customTheme.colors.secondary.main}20
            `,
            animation: 'subChartIconFloat 2.8s ease-in-out infinite',
            '@keyframes subChartIconFloat': {
              '0%, 100%': { transform: 'translateY(0px) rotate(0deg)', filter: 'brightness(1)' },
              '50%': { transform: 'translateY(-3px) rotate(2deg)', filter: 'brightness(1.1)' }
            }
          }}>
            <PaletteIcon sx={{
              fontSize: '1.6rem',
              color: customTheme.colors.secondary.main,
              filter: `drop-shadow(0 2px 4px ${customTheme.colors.secondary.main}30)`
            }} />
          </Box>
          <Typography variant="body2" sx={{
            color: customTheme.colors.text.primary,
            fontSize: '0.8rem',
            fontWeight: 600,
            opacity: 0.85
          }}>
            Awaiting sub-emotion data
          </Typography>
        </motion.div>
      </Box>
    );
  }

  // Prepare data for chart (sorted by frequency)
  const sortedSubEmotions = Object.entries(subEmotionDistribution)
    .sort((a, b) => b[1] - a[1])
    .map(([subEmotion, value]) => ({ subEmotion, value }));

  const labels = sortedSubEmotions.map(item =>
    item.subEmotion.charAt(0).toUpperCase() + item.subEmotion.slice(1)
  );
  const values = sortedSubEmotions.map(item => item.value);
  const colors = sortedSubEmotions.map(item => getSubEmotionColor(item.subEmotion));

  // Chart configuration for horizontal bar chart
  const chartData = {
    labels,
    datasets: [{
      label: 'Sub-emotion Distribution',
      data: values,
      backgroundColor: colors.map(color => `${color}80`),
      borderColor: colors,
      borderWidth: 2,
      borderRadius: 4,
      borderSkipped: false,
    }]
  };
  const chartOptions = {
    // Removed indexAxis to make it a vertical bar chart
    responsive: true,
    maintainAspectRatio: false,    animation: {
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
          label: (context) => `${Math.round(context.parsed.y * 100)}%`
        }
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          color: customTheme.colors.text.secondary,
          font: { size: 9, weight: '500' },
          maxRotation: 45, // Allow rotation for better label readability
        },
        border: { display: false }
      },
      y: {
        beginAtZero: true,
        max: Math.max(...values) * 1.1, // Add some padding
        grid: {
          color: `${customTheme.colors.secondary.main}20`,
        },
        ticks: {
          color: customTheme.colors.text.tertiary,
          font: { size: 10 },
          callback: (value) => `${Math.round(value * 100)}%`
        },
        border: { display: false }
      },
    },
    layout: {
      padding: { top: 5, right: 5, bottom: 5, left: 5 }
    }
  };

  return (    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chart Container */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ height: '100%' }}
      >
        <Box sx={{
          height: '100%',
          background: `linear-gradient(135deg, ${customTheme.colors.secondary.main}05, transparent)`,
          borderRadius: customTheme.borderRadius.lg,
          border: `1px solid ${customTheme.colors.secondary.main}20`,
          p: 1
        }}>
          <Box sx={{
            height: '100%',
            overflow: 'hidden'
          }}>
            <Bar
              key="subemotion-bar-chart"
              data={chartData}
              options={chartOptions}
            />
          </Box></Box>
      </motion.div>
    </Box>
  );
});

SubEmotionDistributionChart.displayName = 'SubEmotionDistributionChart';

export default SubEmotionDistributionChart;
