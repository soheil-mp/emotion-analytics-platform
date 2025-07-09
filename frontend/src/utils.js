// Format timestamp from seconds to MM:SS format
export const formatTimestamp = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
};

// Convert HH:MM:SS time string to seconds
export const timeStringToSeconds = (timeString) => {
  if (typeof timeString === 'number') {
    return timeString; // Already in seconds
  }

  if (typeof timeString !== 'string') {
    return 0; // Invalid input
  }

  // Handle HH:MM:SS, MM:SS, or SS formats
  const parts = timeString.split(':').map(part => parseInt(part, 10) || 0);

  if (parts.length === 3) {
    // HH:MM:SS format
    const [hours, minutes, seconds] = parts;
    return hours * 3600 + minutes * 60 + seconds;
  } else if (parts.length === 2) {
    // MM:SS format
    const [minutes, seconds] = parts;
    return minutes * 60 + seconds;
  } else if (parts.length === 1) {
    // SS format
    return parts[0];
  }

  return 0; // Invalid format
};

// Get color based on emotion
export const getEmotionColor = (emotion) => {
  const emotionColors = {
    happiness: '#FFD700',  // Gold
    sadness: '#4169E1',    // Royal Blue
    anger: '#FF4500',      // Red Orange
    fear: '#800080',       // Purple
    disgust: '#008000',    // Green
    surprise: '#FFA500',   // Orange
    neutral: '#A9A9A9',    // Dark Gray
  };

  return emotionColors[emotion] || '#A9A9A9';
};

// Get intensity value (0-1) from string representation
export const getIntensityValue = (intensity) => {
  const intensityValues = {
    mild: 0.3,
    moderate: 0.6,
    intense: 0.9
  };

  return intensityValues[intensity] || 0.5;
};

// Process emotion data for visualization
export const processEmotionData = (analysisData) => {
  if (!analysisData || !analysisData.transcript) {
    return { emotionDistribution: {}, intensityTimeline: [] };
  }

  // Group by emotion categories for the bar chart
  const emotionCounts = analysisData.transcript.reduce((acc, item) => {
    acc[item.emotion] = (acc[item.emotion] || 0) + 1;
    return acc;
  }, {});

  // Calculate total count to normalize to percentages
  const totalCount = Object.values(emotionCounts).reduce((sum, count) => sum + count, 0);

  // Convert counts to normalized percentages (0-1)
  const emotionDistribution = {};
  Object.entries(emotionCounts).forEach(([emotion, count]) => {
    emotionDistribution[emotion] = totalCount > 0 ? count / totalCount : 0;
  });

  // Get all unique emotions present in the transcript
  const uniqueEmotions = [...new Set(analysisData.transcript.map(item => item.emotion))];

  // Sort emotions in a meaningful order (can be customized as needed)
  const emotionOrder = ['neutral', 'happiness', 'sadness', 'anger', 'fear', 'surprise', 'disgust'];
  uniqueEmotions.sort((a, b) => {
    const indexA = emotionOrder.indexOf(a) !== -1 ? emotionOrder.indexOf(a) : 999;
    const indexB = emotionOrder.indexOf(b) !== -1 ? emotionOrder.indexOf(b) : 999;
    return indexA - indexB;
  });

  // Map emotions to y-axis positions (0 for neutral, 1 for happiness, etc.)
  const emotionPositions = {};
  uniqueEmotions.forEach((emotion, index) => {
    emotionPositions[emotion] = index;
  });

  // Create data for categorical timeline
  const timelineData = {
    datasets: uniqueEmotions.map((emotion) => {
      // Filter transcript items for this emotion
      const emotionSegments = analysisData.transcript
        .filter(item => item.emotion === emotion)
        .map(item => ({
          x: item.start_time,
          y: emotion.charAt(0).toUpperCase() + emotion.slice(1),
          duration: item.end_time - item.start_time,
          intensity: getIntensityValue(item.intensity)
        }));

      return {
        label: emotion.charAt(0).toUpperCase() + emotion.slice(1),
        data: emotionSegments,
        backgroundColor: getEmotionColor(emotion),
        borderColor: getEmotionColor(emotion),
        borderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        showLine: false, // This makes it a scatter plot
      };
    }),
    emotionLabels: uniqueEmotions.map(e => e.charAt(0).toUpperCase() + e.slice(1))
  };

  return { emotionDistribution, intensityTimeline: timelineData };
};

// Process sub-emotion data for distribution analysis
export const processSubEmotionData = (analysisData) => {
  if (!analysisData || !analysisData.transcript) {
    return {};
  }

  const subEmotionCounts = {};
  let totalCount = 0;

  analysisData.transcript.forEach(item => {
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

  return subEmotionDistribution;
};

// Process intensity data for distribution analysis
export const processIntensityData = (analysisData) => {
  if (!analysisData || !analysisData.transcript) {
    return { distribution: {}, totalCount: 0, rawCounts: {} };
  }

  const intensityCounts = {
    mild: 0,
    moderate: 0,
    intense: 0
  };

  let totalCount = 0;

  analysisData.transcript.forEach(item => {
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

// Analyze emotion and sub-emotion relationships in transcript data
export const analyzeEmotionRelationships = (analysisData) => {
  if (!analysisData || !analysisData.transcript) {
    return { emotionSubEmotionMap: {}, subEmotionParentMap: {} };
  }

  const emotionSubEmotionMap = {}; // emotion -> [sub_emotions]
  const subEmotionParentMap = {}; // sub_emotion -> emotion

  analysisData.transcript.forEach(item => {
    if (item.emotion && item.sub_emotion) {
      // Map emotion to its sub-emotions
      if (!emotionSubEmotionMap[item.emotion]) {
        emotionSubEmotionMap[item.emotion] = new Set();
      }
      emotionSubEmotionMap[item.emotion].add(item.sub_emotion);

      // Map sub-emotion to its parent emotion
      subEmotionParentMap[item.sub_emotion] = item.emotion;
    }
  });

  // Convert Sets to Arrays for easier use
  Object.keys(emotionSubEmotionMap).forEach(emotion => {
    emotionSubEmotionMap[emotion] = Array.from(emotionSubEmotionMap[emotion]);
  });

  console.log('Emotion-SubEmotion relationships found in data:', {
    emotionSubEmotionMap,
    subEmotionParentMap
  });

  return { emotionSubEmotionMap, subEmotionParentMap };
};
