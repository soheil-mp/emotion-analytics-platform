import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Button from '@mui/material/Button';
import EditNoteIcon from '@mui/icons-material/EditNote';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import PsychologyAltIcon from '@mui/icons-material/PsychologyAlt';
import TimelineIcon from '@mui/icons-material/Timeline';
import './App.css';
import { motion } from 'framer-motion';
import * as XLSX from 'xlsx';

// Import Chart.js components for sub-emotion bar chart
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

// Import components
import Sidebar from './components/Sidebar';
import AddVideoModal from './components/AddVideoModal';
import SettingsModal from './components/SettingsModal';
import FeedbackModal from './components/FeedbackModal';
import EmotionDistributionAnalytics from './components/InsightsLab';
import EmotionCurrent from './components/EmotionCurrent';
import VideoSummary from './components/VideoSummary';
import MonitoringDashboard from './components/MonitoringDashboard';
import MonitoringErrorBoundary from './components/MonitoringErrorBoundary';


import EmotionTimeline from './components/EmotionTimeline';
import VideoPlayer from './components/VideoPlayer';

// Import context and utilities
import { VideoProvider, useVideo } from './VideoContext';
import { processEmotionData } from './utils';
import customTheme from './theme';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

// Create Sophisticated MUI Theme - Minimalist Navy Design
const muiTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: customTheme.colors.primary.main, // Sophisticated indigo
      light: customTheme.colors.primary.light,
      dark: customTheme.colors.primary.dark,
    },
    secondary: {
      main: customTheme.colors.secondary.main, // Navy slate
      light: customTheme.colors.secondary.light,
      dark: customTheme.colors.secondary.dark,
    },
    background: {
      default: 'transparent', // Let CSS handle the navy gradient
      paper: customTheme.colors.surface.glass,
    },
    text: {
      primary: customTheme.colors.text.primary,
      secondary: customTheme.colors.text.secondary,
    },
  },
  typography: {
    fontFamily: customTheme.typography.fontFamily.primary,
    h1: {
      fontFamily: customTheme.typography.fontFamily.heading,
      fontWeight: customTheme.typography.fontWeight.bold,
      letterSpacing: customTheme.typography.letterSpacing.tight,
    },
    h2: {
      fontFamily: customTheme.typography.fontFamily.heading,
      fontWeight: customTheme.typography.fontWeight.semibold,
      letterSpacing: customTheme.typography.letterSpacing.tight,
    },
    h3: {
      fontFamily: customTheme.typography.fontFamily.heading,
      fontWeight: customTheme.typography.fontWeight.semibold,
    },
    h4: {
      fontFamily: customTheme.typography.fontFamily.heading,
      fontWeight: customTheme.typography.fontWeight.medium,
    },
    h5: {
      fontFamily: customTheme.typography.fontFamily.heading,
      fontWeight: customTheme.typography.fontWeight.medium,
    },
    h6: {
      fontFamily: customTheme.typography.fontFamily.heading,
      fontWeight: customTheme.typography.fontWeight.medium,
    },
    body1: {
      fontWeight: customTheme.typography.fontWeight.normal,
      lineHeight: customTheme.typography.lineHeight.relaxed,
    },
    body2: {
      fontWeight: customTheme.typography.fontWeight.normal,
      lineHeight: customTheme.typography.lineHeight.normal,
    },
  },
  shape: {
    borderRadius: 16, // More refined border radius
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {        body: {
          background: 'transparent', // Let CSS handle the navy gradient
          overflow: 'hidden',
          fontSmooth: 'always',
          WebkitFontSmoothing: 'antialiased',
          MozOsxFontSmoothing: 'grayscale',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: customTheme.borderRadius.xl,
          fontWeight: customTheme.typography.fontWeight.semibold,
          padding: '12px 24px',
          fontSize: '1rem',
          transition: `all ${customTheme.animation.duration.normal} ${customTheme.animation.easing.premium}`,
          '&:hover': {
            transform: 'translateY(-2px)',
          },
        },
        contained: {
          boxShadow: customTheme.shadows.lg,
          '&:hover': {
            boxShadow: customTheme.shadows.xl,
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          transition: `all ${customTheme.animation.duration.normal} ${customTheme.animation.easing.premium}`,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: customTheme.typography.fontWeight.medium,
          fontSize: '0.95rem',
          minHeight: '48px',
          transition: `all ${customTheme.animation.duration.fast} ${customTheme.animation.easing.premium}`,
        },
      },
    },
  },
});

// Main App Content
function AppContent() {
  const {
    videoUrl,
    currentTime,
    setCurrentTime,
    isLoading,
    analysisData,
    videoHistory,
    loadFromHistory,
    getCurrentEmotion,
    processVideo  } = useVideo();
  // Current emotion state
  const currentEmotion = getCurrentEmotion();

  // UI State Management - organized for clarity and maintainability
  const [searchTerm, setSearchTerm] = useState('');

  // Modal State Management - centralized modal controls
  const [modalStates, setModalStates] = useState({
    feedback: false,
    addVideo: false,
    settings: false
  });

  // Refs for DOM manipulation and performance optimization
  const transcriptContainerRef = useRef(null);

  // Modal Management Utilities - centralized modal control system
  const openModal = useCallback((modalName) => {
    setModalStates(prev => ({ ...prev, [modalName]: true }));
  }, []);

  const closeModal = useCallback((modalName) => {
    setModalStates(prev => ({ ...prev, [modalName]: false }));
  }, []);

  // Legacy compatibility - maintaining backward compatibility during refactor
  const feedbackModalOpen = modalStates.feedback;
  const addVideoModalOpen = modalStates.addVideo;
  const settingsModalOpen = modalStates.settings;
  const setAddVideoModalOpen = useCallback((open) => setModalStates(prev => ({ ...prev, addVideo: open })), []);
  const setSettingsModalOpen = useCallback((open) => setModalStates(prev => ({ ...prev, settings: open })), []);

  // Process analyzed data for visualizations - memoized for performance
  const { intensityTimeline } = useMemo(() =>
    analysisData ? processEmotionData(analysisData) : { emotionDistribution: {}, intensityTimeline: [] },
    [analysisData]
  );

  // Event Handlers - organized and documented for maintainability

  /**
   * Handles video timeline navigation when user clicks on transcript segment
   * @param {number} time - Target timestamp in seconds
   */
  const handleSentenceClick = useCallback((time) => {
    setCurrentTime(time);
    // VideoPlayer will automatically update through context
  }, [setCurrentTime]);

  /**
   * Modal Management Handlers - centralized modal control
   */
  const handleOpenFeedback = useCallback(() => openModal('feedback'), [openModal]);
  const handleCloseFeedback = useCallback(() => closeModal('feedback'), [closeModal]);

  // Enhanced Auto-scroll Effect - optimized for performance and smooth UX
  useEffect(() => {
    // Early return for performance - avoid unnecessary computations
    if (!analysisData?.transcript || !transcriptContainerRef.current || currentTime <= 0) {
      return;
    }

    // Find active segment with optimized search
    const activeSegment = analysisData.transcript.find(segment => {
      const startTime = segment.start_time ?? segment.start ?? 0;
      const endTime = segment.end_time ?? segment.end ?? (startTime + 2);
      return currentTime >= startTime && currentTime <= endTime;
    });

    // Perform smooth scroll to active segment
    if (activeSegment) {
      const segmentIndex = analysisData.transcript.indexOf(activeSegment);
      const segmentElement = transcriptContainerRef.current.children[segmentIndex];

      if (segmentElement) {
        segmentElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
          inline: 'nearest'
        });
      }
    }
  }, [currentTime, analysisData?.transcript]);

  // Enhanced Theme Safety Check - elegant error handling with beautiful fallback
  if (!customTheme?.colors) {
    console.error('Theme object is not properly loaded');
    return (
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        color: '#f8fafc'
      }}>
        <Box sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 3,
          textAlign: 'center',
          maxWidth: 400,
          px: 4
        }}>
          {/* Animated Loading Icon */}
          <Box sx={{
            width: 64,
            height: 64,
            border: '4px solid rgba(248, 250, 252, 0.1)',
            borderTop: '4px solid #6366f1',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            '@keyframes spin': {
              '0%': { transform: 'rotate(0deg)' },
              '100%': { transform: 'rotate(360deg)' }
            }
          }} />

          <Typography variant="h5" sx={{
            fontWeight: 600,
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Loading Theme
          </Typography>

          <Typography variant="body1" sx={{
            color: 'rgba(248, 250, 252, 0.7)',
            lineHeight: 1.6
          }}>
            Preparing your beautiful emotion analysis experience...
          </Typography>
        </Box>
      </Box>
    );
  }

  // Helper function to format time from seconds to HH:MM:SS
  const formatTimeToHHMMSS = (seconds) => {
    if (seconds === undefined || seconds === null || isNaN(seconds)) {
      return "00:00:00";
    }

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Helper function to calculate dominant emotion from transcript data
  const calculateDominantEmotion = (transcriptData) => {
    if (!transcriptData || transcriptData.length === 0) return 'Unknown';

    const emotionCounts = {};
    transcriptData.forEach(segment => {
      const emotion = segment.emotion || 'neutral';
      emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
    });

    return Object.entries(emotionCounts)
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'Unknown';
  };

  // Helper function to get analysis date with fallbacks
  const getAnalysisDate = (analysisData) => {
    // Try different possible date field names
    const possibleDateFields = [
      'createdAt', 'created_at', 'analysisDate', 'analysis_date',
      'timestamp', 'dateProcessed', 'date_processed'
    ];

    for (const field of possibleDateFields) {
      if (analysisData[field]) {
        try {
          return new Date(analysisData[field]).toLocaleString();
        } catch (e) {
          // Continue to next field if date parsing fails
        }
      }
    }

    // If no date field found, use current date as fallback
    return new Date().toLocaleString();
  };

  // Handle export predictions to Excel
  const handleExportPredictions = () => {
    if (!analysisData) return;

    try {

      // Create a new workbook
      const workbook = XLSX.utils.book_new();

      // Calculate dominant emotion and other summary statistics
      const dominantEmotion = calculateDominantEmotion(analysisData.transcript);
      const totalSegments = analysisData.transcript?.length || 0;
      const totalDuration = analysisData.transcript?.reduce((sum, segment) => {
        const start = segment.start_time ?? segment.start ?? 0;
        const end = segment.end_time ?? segment.end ?? start;
        return sum + (end - start);
      }, 0) || 0;      // 1. Enhanced Summary Sheet
      const summaryData = [
        ['🎬 EMOTION ANALYSIS REPORT'],
        [''],
        ['📊 VIDEO INFORMATION'],
        ['Title', analysisData.title || 'Unknown Video'],
        ['Source URL', videoUrl || 'N/A'],
        ['Export Date', new Date().toLocaleString()],
        ['Analysis Date', getAnalysisDate(analysisData)],
        [''],
        ['📈 ANALYSIS OVERVIEW'],
        ['Total Duration', formatTimeToHHMMSS(totalDuration)],
        ['Total Segments', totalSegments],
        ['Dominant Emotion', dominantEmotion],
        ['Average Segment Length', totalSegments > 0 ? formatTimeToHHMMSS(totalDuration / totalSegments) : 'N/A'],
        [''],
        ['🎭 EMOTION DISTRIBUTION'],
        ['Emotion', 'Count', 'Percentage', 'Duration (approx)']
      ];

      // Calculate enhanced emotion distribution
      const emotionCounts = {};
      const emotionDurations = {};

      if (analysisData.transcript) {
        analysisData.transcript.forEach(segment => {
          const emotion = segment.emotion || 'neutral';
          const start = segment.start_time ?? segment.start ?? 0;
          const end = segment.end_time ?? segment.end ?? start;
          const duration = end - start;

          emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
          emotionDurations[emotion] = (emotionDurations[emotion] || 0) + duration;
        });
      }

      Object.entries(emotionCounts)
        .sort(([,a], [,b]) => b - a) // Sort by count descending
        .forEach(([emotion, count]) => {
          const percentage = totalSegments > 0 ? ((count / totalSegments) * 100).toFixed(1) : '0.0';
          const duration = formatTimeToHHMMSS(emotionDurations[emotion] || 0);
          summaryData.push([emotion, count, `${percentage}%`, duration]);
        });

      // Add quality metrics
      summaryData.push(
        [''],
        ['📊 DATA QUALITY METRICS'],
        ['Segments with Text', analysisData.transcript?.filter(s => (s.text || s.sentence || s.content || '').trim()).length || 0],
        ['Segments with Sub-emotions', analysisData.transcript?.filter(s => s.subEmotion || s.sub_emotion || s.secondary_emotion).length || 0],
        ['Unique Emotions Detected', Object.keys(emotionCounts).length]
      );

      const summarySheet = XLSX.utils.aoa_to_sheet(summaryData);

      // Enhanced styling for summary sheet
      summarySheet['!cols'] = [
        { width: 25 },
        { width: 20 },
        { width: 15 },
        { width: 18 }
      ];

      XLSX.utils.book_append_sheet(workbook, summarySheet, 'Summary');

      // 2. Enhanced Transcript Sheet
      const transcriptData = [
        ['Segment', 'Start Time', 'End Time', 'Duration', 'Text Content', 'Primary Emotion', 'Sub Emotion']
      ];

      if (analysisData.transcript) {
        analysisData.transcript.forEach((segment, index) => {
          // Handle different possible field names for time
          const startTime = segment.start_time ?? segment.start ?? 0;
          const endTime = segment.end_time ?? segment.end ?? startTime + 1; // Default 1 second if no end time
          const duration = endTime - startTime;

          // Handle different possible field names for text
          const text = (segment.text || segment.sentence || segment.content || '').trim() || '[No text available]';

          // Handle emotion data
          const primaryEmotion = segment.emotion || 'neutral';
          const subEmotion = segment.subEmotion || segment.sub_emotion || segment.secondary_emotion || '';

          transcriptData.push([
            index + 1,
            formatTimeToHHMMSS(startTime),
            formatTimeToHHMMSS(endTime),
            formatTimeToHHMMSS(duration),
            text,
            primaryEmotion,
            subEmotion
          ]);
        });
      }

      const transcriptSheet = XLSX.utils.aoa_to_sheet(transcriptData);

      // Enhanced styling for transcript sheet
      transcriptSheet['!cols'] = [
        { width: 8 },   // Segment
        { width: 12 },  // Start Time
        { width: 12 },  // End Time
        { width: 12 },  // Duration
        { width: 70 },  // Text (increased width for better readability)
        { width: 18 },  // Primary Emotion
        { width: 16 }   // Sub Emotion
      ];

      XLSX.utils.book_append_sheet(workbook, transcriptSheet, 'Transcript');

      // 3. Enhanced Emotion Timeline Sheet
      if (analysisData.emotionTimeline && analysisData.emotionTimeline.length > 0) {
        const timelineData = [
          ['Time', 'Happiness', 'Sadness', 'Anger', 'Fear', 'Surprise', 'Disgust', 'Neutral', 'Dominant Emotion']
        ];

        analysisData.emotionTimeline.forEach(point => {
          timelineData.push([
            formatTimeToHHMMSS(point.time || 0),
            (point.happiness || 0).toFixed(3),
            (point.sadness || 0).toFixed(3),
            (point.anger || 0).toFixed(3),
            (point.fear || 0).toFixed(3),
            (point.surprise || 0).toFixed(3),
            (point.disgust || 0).toFixed(3),
            (point.neutral || 0).toFixed(3),
            point.dominant_emotion || point.dominantEmotion || 'Unknown'
          ]);
        });

        const timelineSheet = XLSX.utils.aoa_to_sheet(timelineData);

        // Enhanced styling for timeline sheet
        timelineSheet['!cols'] = [
          { width: 12 },  // Time
          { width: 12 },  // Happiness
          { width: 12 },  // Sadness
          { width: 12 },  // Anger
          { width: 12 },  // Fear
          { width: 12 },  // Surprise
          { width: 12 },  // Disgust
          { width: 12 },  // Neutral
          { width: 18 }   // Dominant Emotion
        ];

        XLSX.utils.book_append_sheet(workbook, timelineSheet, 'Emotion Timeline');
      }

      // 4. Enhanced Analytics Sheet
      const analyticsData = [
        ['📊 ADVANCED EMOTION ANALYTICS'],
        [''],
        ['🔄 EMOTION TRANSITIONS'],
        ['From Emotion', 'To Emotion', 'Frequency', 'Percentage']
      ];

      // Calculate emotion transitions
      const transitions = {};
      if (analysisData.transcript && analysisData.transcript.length > 1) {
        for (let i = 0; i < analysisData.transcript.length - 1; i++) {
          const fromEmotion = analysisData.transcript[i].emotion || 'neutral';
          const toEmotion = analysisData.transcript[i + 1].emotion || 'neutral';
          const key = `${fromEmotion}→${toEmotion}`;
          transitions[key] = (transitions[key] || 0) + 1;
        }
      }

      const totalTransitions = Object.values(transitions).reduce((sum, count) => sum + count, 0) || 1;
      const sortedTransitions = Object.entries(transitions).sort(([,a], [,b]) => b - a);

      sortedTransitions.forEach(([transition, count]) => {
        const [from, to] = transition.split('→');
        const percentage = ((count / totalTransitions) * 100).toFixed(1);
        analyticsData.push([from, to, count, `${percentage}%`]);
      });

      // Add emotion stability analysis
      analyticsData.push(
        [''],
        ['🎭 EMOTION STABILITY ANALYSIS'],
        ['Metric', 'Value', 'Description']
      );

      if (analysisData.transcript && analysisData.transcript.length > 0) {
        const emotions = analysisData.transcript.map(s => s.emotion || 'neutral');
        const uniqueEmotions = [...new Set(emotions)];
        const emotionChanges = emotions.slice(1).filter((emotion, i) => emotion !== emotions[i]).length;
        const stabilityScore = emotions.length > 1 ? ((emotions.length - emotionChanges) / emotions.length * 100).toFixed(1) : '100.0';

        analyticsData.push(
          ['Unique Emotions', uniqueEmotions.length, 'Total different emotions detected'],
          ['Emotion Changes', emotionChanges, 'Number of times emotion switched'],
          ['Stability Score', `${stabilityScore}%`, 'Percentage of time emotion remained same'],
          ['Most Common', dominantEmotion, 'Most frequently occurring emotion'],
          ['Diversity Index', (uniqueEmotions.length / Math.max(1, emotions.length) * 100).toFixed(1) + '%', 'Emotional diversity ratio']
        );
      }

      // Add duration insights
      analyticsData.push(
        [''],
        ['⏱️ TEMPORAL ANALYSIS'],
        ['Metric', 'Value', 'Details']
      );

      if (analysisData.transcript) {
        const durations = analysisData.transcript.map(s => {
          const start = s.start_time ?? s.start ?? 0;
          const end = s.end_time ?? s.end ?? start + 1;
          return end - start;
        }).filter(d => d > 0);

        if (durations.length > 0) {
          const avgDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
          const minDuration = Math.min(...durations);
          const maxDuration = Math.max(...durations);

          analyticsData.push(
            ['Total Duration', formatTimeToHHMMSS(totalDuration), 'Complete video length analyzed'],
            ['Average Segment', formatTimeToHHMMSS(avgDuration), 'Mean length per segment'],
            ['Shortest Segment', formatTimeToHHMMSS(minDuration), 'Minimum segment duration'],
            ['Longest Segment', formatTimeToHHMMSS(maxDuration), 'Maximum segment duration'],
            ['Segments per Minute', (durations.length / (totalDuration / 60)).toFixed(1), 'Segment density']
          );
        }
      }

      const analyticsSheet = XLSX.utils.aoa_to_sheet(analyticsData);

      // Enhanced styling for analytics sheet
      analyticsSheet['!cols'] = [
        { width: 25 },
        { width: 20 },
        { width: 15 },
        { width: 35 }
      ];

      XLSX.utils.book_append_sheet(workbook, analyticsSheet, 'Analytics');

      // Generate enhanced filename with video title
      const videoTitle = (analysisData.title || 'unknown-video')
        .replace(/[^\w\s-]/g, '') // Remove special chars
        .replace(/\s+/g, '-') // Replace spaces with hyphens
        .substring(0, 30); // Limit length

      const timestamp = new Date().toISOString().slice(0, 10); // YYYY-MM-DD format
      const filename = `emotion-analysis-${videoTitle}-${timestamp}.xlsx`;

      // Write and download the file
      XLSX.writeFile(workbook, filename);

      console.log('Enhanced Excel report exported successfully:', filename);
    } catch (error) {
      console.error('Error exporting to Excel:', error);
      // Fallback to JSON export if Excel fails
      try {
        const exportData = {
          videoTitle: analysisData.title || 'Unknown Video',
          videoUrl: videoUrl,
          exportDate: new Date().toISOString(),
          emotionData: analysisData.emotionTimeline || [],
          transcript: analysisData.transcript || [],
          summary: {
            totalSegments: analysisData.transcript?.length || 0,
            dominantEmotion: calculateDominantEmotion(analysisData.transcript),
            totalDuration: analysisData.transcript?.reduce((sum, segment) => {
              const start = segment.start_time ?? segment.start ?? 0;
              const end = segment.end_time ?? segment.end ?? start;
              return sum + (end - start);
            }, 0) || 0
          }
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        const exportFileDefaultName = `emotion-analysis-fallback-${Date.now()}.json`;

        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();

        console.log('Fallback JSON export completed');
      } catch (fallbackError) {
        console.error('Both Excel and JSON export failed:', fallbackError);
      }
    }  };  // Handle URL upload - processes YouTube URLs and file uploads for emotion analysis
  const handleUrlUpload = async (data) => {
    try {
      console.log('Processing video data:', data);

      // Validate input data
      if (!data || typeof data !== 'object') {
        console.error('Invalid data provided to handleUrlUpload');
        return;
      }

      // Close the modal first
      setAddVideoModalOpen(false);

      if (data.type === 'youtube') {
        // Handle YouTube URL processing
        if (!data.url || !data.url.trim()) {
          console.error('Empty YouTube URL provided');
          return;
        }

        console.log('Processing YouTube URL:', data.url);
        await processVideo(data.url.trim());
        console.log('YouTube video processing initiated successfully');

      } else if (data.type === 'file') {
        // Handle file upload processing
        if (!data.file) {
          console.error('No file provided for upload');
          return;
        }

        console.log('Processing video file:', data.file.name);
        // TODO: Implement file upload processing
        // For now, we'll show an info message
        console.info('File upload functionality not yet implemented:', data.file.name);
        // You might want to show a user-friendly message here

      } else {
        console.error('Unknown upload type:', data.type);
      }

    } catch (error) {
      console.error('Error processing video:', error);
      // TODO: Show user-friendly error message (e.g., using a snackbar or alert)
    }
  };
  // Filter history based on search term
  const filteredHistory = videoHistory.filter(video =>
    video.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (<Box
      className="dashboard-layout-fix"
      sx={{
        display: 'flex',
        minHeight: '100vh',
        width: '100vw', // Ensure full viewport width
        maxWidth: '100vw', // Prevent horizontal overflow
        background: customTheme.colors.background.primary, // Navy gradient background
        position: 'relative',
        overflow: 'hidden', // Prevent horizontal scrolling
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: customTheme.colors.gradients.subtle, // Subtle navy effect
          opacity: 0.1,
          zIndex: 0,
        },
      }}>
      <Sidebar
        videoHistory={filteredHistory}
        onVideoSelect={loadFromHistory}
        onAddVideo={() => setAddVideoModalOpen(true)}
        onSettings={() => setSettingsModalOpen(true)}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}      />      {/* Main Content Area with Enhanced Premium Grid Layout */}
      <Box
        className="main-content-area"
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          p: 4,
          pl: '140px', // Enhanced left padding
          minHeight: '100vh',
          width: '100%', // Ensure full width
          maxWidth: '100%', // Prevent overflow
          justifyContent: 'flex-start',
          alignItems: 'stretch',
          position: 'relative',
          zIndex: 1,
          boxSizing: 'border-box', // Include padding in width calculation
        }}>
        <Grid
          container
          spacing={4}
          className="dashboard-grid-container"
          sx={{
            width: '100%',
            minWidth: '100%', // Ensure minimum full width
            height: 'fit-content',
            alignItems: 'flex-start', // Align all columns to top instead of stretch
            justifyContent: 'space-between', // Distribute columns evenly
            py: 2,
            mt: 1,
            flexWrap: 'nowrap', // Prevent wrapping on large screens
            '& > .MuiGrid-item': {
              minWidth: 0, // Allow content to shrink if needed
              flexBasis: '33.333%', // Ensure each column takes exactly 1/3 width
              maxWidth: '33.333%', // Prevent columns from growing too large
              alignSelf: 'flex-start', // Ensure each grid item aligns to top
            }
          }}>          {/* Premium Dashboard Card - Split into Two Equal Parts */}
          <Grid
            item
            xs={12}
            lg={4}
            className="dashboard-grid-item"
            sx={{
              display: 'flex',
              minWidth: 0,
              width: '100%',
              flexShrink: 0, // Prevent shrinking
              alignSelf: 'flex-start', // Ensure this column aligns to top
            }}>
            <Box sx={{
              height: '85vh',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              width: '100%', // Ensure full width within grid item
            }}>
              {/* Upper Half - Hub */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                style={{ height: '50%' }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    height: '100%',
                    p: 2.5,
                    background: customTheme.glassmorphism.luxury.background,
                    backdropFilter: customTheme.glassmorphism.luxury.backdropFilter,
                    border: customTheme.glassmorphism.luxury.border,
                    borderRadius: customTheme.borderRadius['3xl'],
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    position: 'relative',
                    transition: `all ${customTheme.animation.duration.normal} ${customTheme.animation.easing.premium}`,
                    boxShadow: customTheme.shadows.xl,
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: customTheme.shadows['3xl'],
                      border: `1px solid ${customTheme.colors.primary.glow}`,
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '2px',
                      background: customTheme.colors.gradients.primary,
                      borderRadius: customTheme.borderRadius.full,
                    }
                  }}
                >
                  <Typography variant="h5" sx={{
                    mb: 2,
                    fontWeight: 800,
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    fontSize: '1.2rem',
                    letterSpacing: '0.5px'
                  }}>
                    <Box sx={{
                      width: 28,
                      height: 28,
                      borderRadius: '6px',
                      background: `linear-gradient(135deg, ${customTheme.colors.primary.main}, ${customTheme.colors.primary.dark})`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1rem',
                      boxShadow: `0 4px 16px ${customTheme.colors.primary.main}40`,
                      animation: 'iconFloat 3s ease-in-out infinite',
                      '@keyframes iconFloat': {
                        '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
                        '50%': { transform: 'translateY(-2px) rotate(2deg)' }
                      }
                    }}>
                      🧠
                    </Box>
                    Video Summary
                  </Typography>

                  {/* Video Summary Content */}
                  <Box sx={{ flex: 1, overflow: 'hidden' }}>
                    {analysisData ? (
                      <VideoSummary
                        analysisData={analysisData}
                        videoTitle={analysisData?.title || 'Video Analysis'}
                      />
                    ) : (
                      <Box sx={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center', // Keep horizontal centering
                        justifyContent: 'flex-end', // Move content to bottom vertically
                        flexDirection: 'column',
                        gap: 3,
                        color: customTheme.colors.text.secondary,
                        textAlign: 'center',
                        position: 'relative',
                        paddingBottom: 12, // Significantly increased bottom padding (was 8)
                        paddingTop: 12, // Significantly increased top padding (was 6)
                      }}>
                        {/* Animated Background Elements */}
                        <Box sx={{
                          position: 'absolute',
                          bottom: '40%', // Changed from top: '20%' to bottom: '40%'
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: '120px',
                          height: '120px',
                          borderRadius: '50%',
                          background: `
                            radial-gradient(circle at 30% 30%,
                              ${customTheme.colors.primary.main}15 0%,
                              ${customTheme.colors.secondary.main}10 50%,
                              transparent 100%
                            )
                          `,
                          animation: 'hubPulse 4s ease-in-out infinite',
                          '@keyframes hubPulse': {
                            '0%, 100%': { transform: 'translateX(-50%) scale(1)', opacity: 0.6 },
                            '50%': { transform: 'translateX(-50%) scale(1.1)', opacity: 0.9 }
                          }
                        }} />

                        {/* Central Hub Icon */}
                        <Box sx={{
                          width: 80,
                          height: 80,
                          borderRadius: '50%',
                          background: `
                            linear-gradient(135deg,
                              ${customTheme.colors.primary.main}90 0%,
                              ${customTheme.colors.primary.dark}70 50%,
                              ${customTheme.colors.secondary.main}40 100%
                            )
                          `,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '2.2rem',
                          position: 'relative',
                          zIndex: 2,
                          boxShadow: `
                            0 0 30px ${customTheme.colors.primary.main}50,
                            0 8px 24px ${customTheme.colors.primary.main}30,
                            inset 0 1px 0 rgba(255,255,255,0.3)
                          `,
                          border: `1px solid ${customTheme.colors.primary.main}60`,
                          animation: 'hubIconFloat 3s ease-in-out infinite',
                          '@keyframes hubIconFloat': {
                            '0%, 100%': {
                              transform: 'translateY(0px) rotate(0deg)',
                              filter: 'brightness(1)'
                            },
                            '50%': {
                              transform: 'translateY(-6px) rotate(2deg)',
                              filter: 'brightness(1.2)'
                            }
                          }
                        }}>
                          🧠
                        </Box>

                        {/* Hub Content */}
                        <Box sx={{ textAlign: 'center', zIndex: 2 }}>
                          <Typography variant="h6" sx={{
                            fontWeight: 700,
                            color: 'white',
                            mb: 1,
                            fontSize: '1.1rem',
                            letterSpacing: '0.5px',
                            filter: `drop-shadow(0 2px 8px ${customTheme.colors.primary.main}30)`
                          }}>
                            Upload a video to see this section
                          </Typography>
                        </Box>
                      </Box>
                    )}
                  </Box>
                </Paper>
              </motion.div>

              {/* Lower Half - Secondary Section */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
                style={{ height: '50%' }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    height: '100%',
                    p: 2.5,
                    background: customTheme.glassmorphism.luxury.background,
                    backdropFilter: customTheme.glassmorphism.luxury.backdropFilter,
                    border: customTheme.glassmorphism.luxury.border,
                    borderRadius: customTheme.borderRadius['3xl'],
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                    position: 'relative',
                    transition: `all ${customTheme.animation.duration.normal} ${customTheme.animation.easing.premium}`,
                    boxShadow: customTheme.shadows.xl,
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: customTheme.shadows['3xl'],
                      border: `1px solid ${customTheme.colors.secondary.glow}`,
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '2px',
                      background: customTheme.colors.gradients.secondary,
                      borderRadius: customTheme.borderRadius.full,
                    }
                  }}
                >                  <Typography variant="h5" sx={{
                    mb: 2,
                    fontWeight: 800,
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    fontSize: '1.2rem',
                    letterSpacing: '0.5px'
                  }}>
                    <Box sx={{
                      width: 28,
                      height: 28,
                      borderRadius: '6px',
                      background: `linear-gradient(135deg, ${customTheme.colors.secondary.main}, ${customTheme.colors.secondary.dark})`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1rem',
                      boxShadow: `0 4px 16px ${customTheme.colors.secondary.main}40`,
                      animation: 'iconFloat 3s ease-in-out infinite',
                      '@keyframes iconFloat': {
                        '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
                        '50%': { transform: 'translateY(-2px) rotate(2deg)' }
                      }
                    }}>
                      📊
                    </Box>                    Emotion Distribution
                  </Typography>

                  {/* Emotion Distribution Analytics Component */}
                  <Box sx={{ flex: 1, overflow: 'hidden' }}>
                    <EmotionDistributionAnalytics
                      analysisData={analysisData}
                      currentTime={currentTime}
                    />
                  </Box>
                </Paper>
              </motion.div>
            </Box>
          </Grid>          {/* Premium Video Player & Transcript Section */}
          <Grid
            item
            xs={12}
            lg={4}
            className="dashboard-grid-item"
            sx={{
              display: 'flex',
              minWidth: 0,
              width: '100%',
              flexShrink: 0, // Prevent shrinking
              alignSelf: 'flex-start', // Ensure this column aligns to top
            }}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
              style={{ width: '100%', display: 'flex' }} // Ensure motion div takes full width
            >
              <Paper
                elevation={0}
                sx={{
                  height: '85vh',
                  width: '100%', // Ensure paper takes full width
                  p: 4,
                  background: customTheme.glassmorphism.luxury.background,
                  backdropFilter: customTheme.glassmorphism.luxury.backdropFilter,
                  border: customTheme.glassmorphism.luxury.border,
                  borderRadius: customTheme.borderRadius['3xl'],
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  position: 'relative',
                  transition: `all ${customTheme.animation.duration.normal} ${customTheme.animation.easing.premium}`,
                  boxShadow: customTheme.shadows.xl,
                  '&:hover': {
                    transform: 'translateY(-6px)',
                    boxShadow: customTheme.shadows['3xl'],
                    border: `1px solid ${customTheme.colors.primary.glow}`, // Primary accent only
                  },
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,                    right: 0,                    height: '2px',
                    background: customTheme.colors.gradients.primary, // Primary accent only
                    borderRadius: customTheme.borderRadius.full,
                  }
                }}
              >
                {/* Premium Video Player Section */}
                <Box sx={{ mb: 3 }}>                  <Typography variant="h5" sx={{
                    mb: 3,
                    fontWeight: 800,
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    fontSize: '1.4rem',
                    letterSpacing: '0.5px'
                  }}>
                    <Box sx={{
                      width: 32,
                      height: 32,
                      borderRadius: '6px',
                      background: `linear-gradient(135deg, ${customTheme.colors.secondary.main}, ${customTheme.colors.secondary.dark})`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1rem',
                      boxShadow: `0 4px 16px ${customTheme.colors.secondary.main}40`,
                      animation: 'videoIconPulse 2.5s ease-in-out infinite',
                      '@keyframes videoIconPulse': {
                        '0%, 100%': { transform: 'scale(1)', filter: 'brightness(1)' },
                        '50%': { transform: 'scale(1.1)', filter: 'brightness(1.2)' }
                      }
                    }}>
                      🎥
                    </Box>
                    Video Interface
                  </Typography>

                {videoUrl ? (                  <Box sx={{
                    borderRadius: customTheme.borderRadius.lg,
                    overflow: 'hidden',
                    border: `1px solid ${customTheme.colors.border}`,
                    height: '280px' // Restored height for proper video controls
                  }}>
                    <VideoPlayer
                      url={videoUrl}
                      currentTime={currentTime}
                      onProgress={(state) => setCurrentTime(state.playedSeconds)}
                    />
                  </Box>
                ) : (                  <Box sx={{
                    height: '280px',
                    width: '100%', // Ensure full width
                    position: 'relative',
                    border: `2px dashed ${customTheme.colors.primary.main}40`,
                    borderRadius: customTheme.borderRadius.lg,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 3,
                    minWidth: 0, // Allow shrinking if needed
                    flexShrink: 0, // But prevent complete collapse
                    background: `
                      linear-gradient(135deg,
                        ${customTheme.colors.primary.main}08 0%,
                        ${customTheme.colors.secondary.main}05 50%,
                        ${customTheme.colors.primary.main}08 100%
                      )
                    `,
                    overflow: 'hidden',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      background: `
                        radial-gradient(1px 1px at 30px 40px, ${customTheme.colors.primary.main}30, transparent),
                        radial-gradient(1px 1px at 80px 80px, ${customTheme.colors.secondary.main}20, transparent),
                        radial-gradient(1px 1px at 150px 30px, ${customTheme.colors.primary.main}25, transparent)
                      `,
                      backgroundSize: '200px 120px',
                      animation: 'uploadShimmer 8s linear infinite',
                      '@keyframes uploadShimmer': {
                        '0%': { transform: 'translateY(0px)', opacity: 0.6 },
                        '100%': { transform: 'translateY(-120px)', opacity: 0.3 }
                      }
                    }
                  }}>
                    {/* Floating Upload Icon */}
                    <Box sx={{
                      width: 70,
                      height: 70,
                      borderRadius: '50%',
                      background: `linear-gradient(135deg, ${customTheme.colors.primary.main}, ${customTheme.colors.primary.dark})`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '2rem',
                      color: 'white',
                      boxShadow: `
                        0 0 30px ${customTheme.colors.primary.main}50,
                        0 8px 24px ${customTheme.colors.primary.main}30
                      `,
                      animation: 'uploadFloat 3s ease-in-out infinite',
                      zIndex: 2,
                      '@keyframes uploadFloat': {
                        '0%, 100%': {
                          transform: 'translateY(0px) scale(1)',
                          filter: 'brightness(1)'
                        },
                        '50%': {
                          transform: 'translateY(-8px) scale(1.05)',
                          filter: 'brightness(1.2)'
                        }
                      }
                    }}>
                      📹
                    </Box>

                    <Box sx={{ textAlign: 'center', zIndex: 2 }}>                      <Typography variant="h5" sx={{
                        fontWeight: 800,
                        color: '#ffffff',
                        mb: 1,
                        fontSize: '1.4rem',
                        letterSpacing: '0.5px',
                        filter: `drop-shadow(0 4px 16px ${customTheme.colors.primary.main}30)`
                      }}>
                        Neural Video Portal
                      </Typography>
                      <Typography variant="body2" sx={{
                        opacity: 0.9,
                        color: customTheme.colors.text.primary,
                        fontWeight: 500
                      }}>
                        Quantum-ready emotion analysis awaits
                      </Typography>
                    </Box>

                    <Button
                      onClick={() => setAddVideoModalOpen(true)}
                      variant="contained"
                      startIcon={<CloudUploadIcon />}
                      sx={{
                        textTransform: 'none',
                        borderRadius: 3,
                        px: 4,
                        py: 1.8,
                        fontSize: '0.95rem',
                        fontWeight: 700,
                        background: `linear-gradient(135deg, ${customTheme.colors.primary.main}, ${customTheme.colors.primary.dark})`,
                        color: 'white',
                        boxShadow: `
                          0 8px 24px ${customTheme.colors.primary.main}40,
                          0 4px 12px ${customTheme.colors.primary.main}20
                        `,
                        border: `1px solid ${customTheme.colors.primary.main}60`,
                        position: 'relative',
                        overflow: 'hidden',
                        zIndex: 2,
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: '-100%',
                          width: '100%',
                          height: '100%',
                          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                          transition: 'left 0.6s ease',
                        },
                        '&:hover': {
                          background: `linear-gradient(135deg, ${customTheme.colors.primary.dark}, ${customTheme.colors.primary.main})`,
                          transform: 'translateY(-2px) scale(1.02)',
                          boxShadow: `
                            0 12px 32px ${customTheme.colors.primary.main}50,
                            0 6px 16px ${customTheme.colors.primary.main}30
                          `,
                          '&::before': {
                            left: '100%',
                          }
                        },
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                      }}
                    >
                      Initialize Portal                    </Button>
                </Box>
                )}
              </Box>

              {/* Premium Action Buttons */}
              <Box sx={{
                display: 'flex',
                justifyContent: 'center',
                gap: 3,
                mb: 4,
                flexWrap: 'wrap'
              }}>
                <Button
                  onClick={handleOpenFeedback}
                  disabled={!analysisData}
                  variant="contained"
                  startIcon={<EditNoteIcon />}
                  sx={{
                    textTransform: 'none',
                    borderRadius: 3,
                    px: 4,
                    py: 1.8,
                    fontSize: '0.95rem',
                    fontWeight: 700,
                    background: `linear-gradient(135deg, ${customTheme.colors.primary.main}, ${customTheme.colors.primary.dark})`,
                    color: 'white',
                    boxShadow: `
                      0 8px 24px ${customTheme.colors.primary.main}40,
                      0 4px 12px ${customTheme.colors.primary.main}20
                    `,
                    border: `1px solid ${customTheme.colors.primary.main}60`,
                    position: 'relative',
                    overflow: 'hidden',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: '-100%',
                      width: '100%',
                      height: '100%',
                      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                      transition: 'left 0.6s ease',
                    },
                    '&:hover': {
                      background: `linear-gradient(135deg, ${customTheme.colors.primary.dark}, ${customTheme.colors.primary.main})`,
                      transform: 'translateY(-2px) scale(1.02)',
                      boxShadow: `
                        0 12px 32px ${customTheme.colors.primary.main}50,
                        0 6px 16px ${customTheme.colors.primary.main}30
                      `,
                      '&::before': {
                        left: '100%',
                      }
                    },
                    '&:disabled': {
                      background: customTheme.colors.surface.glass,
                      color: customTheme.colors.text.disabled,
                      boxShadow: 'none',
                      transform: 'none'
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                >
                  Feedback
                </Button>

                <Button
                  onClick={handleExportPredictions}
                  disabled={!analysisData}
                  variant="contained"
                  startIcon={<FileDownloadIcon />}
                  sx={{
                    textTransform: 'none',
                    borderRadius: 3,
                    px: 4,
                    py: 1.8,
                    fontSize: '0.95rem',
                    fontWeight: 700,
                    background: `linear-gradient(135deg, ${customTheme.colors.status.success}, #0d9488)`,
                    color: 'white',
                    boxShadow: `
                      0 8px 24px ${customTheme.colors.status.success}40,
                      0 4px 12px ${customTheme.colors.status.success}20
                    `,
                    border: `1px solid ${customTheme.colors.status.success}60`,
                    position: 'relative',
                    overflow: 'hidden',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: '-100%',
                      width: '100%',
                      height: '100%',
                      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                      transition: 'left 0.6s ease',
                    },
                    '&:hover': {
                      background: `linear-gradient(135deg, #0d9488, ${customTheme.colors.status.success})`,
                      transform: 'translateY(-2px) scale(1.02)',
                      boxShadow: `
                        0 12px 32px ${customTheme.colors.status.success}50,
                        0 6px 16px ${customTheme.colors.status.success}30
                      `,
                      '&::before': {
                        left: '100%',
                      }
                    },
                    '&:disabled': {
                      background: customTheme.colors.surface.glass,
                      color: customTheme.colors.text.disabled,
                      boxShadow: 'none',
                      transform: 'none'
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                >
                  Export
                </Button>
              </Box>{/* Controls Section - Only show when no analysis data or loading */}
              {(!analysisData || isLoading) && (
                <Box sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  gap: 2,
                  mt: 2,
                  flexWrap: 'wrap'
                }}>
                  {/* Upload/Analysis controls will go here */}
                </Box>
              )}{analysisData && (
                <Box mt={4} sx={{
                  flexGrow: 1,
                  overflow: 'hidden',
                  minHeight: 0,
                  display: 'flex',
                  flexDirection: 'column',
                }}>
                  {/* Enhanced Transcript Header */}                  <Typography variant="h5" sx={{
                    mb: 2,
                    fontWeight: 800,
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    fontSize: '1.4rem',
                    letterSpacing: '0.5px'
                  }}>
                    📝 Transcript
                    <Typography variant="body2" sx={{
                      ml: 2,
                      color: 'text.secondary',
                      fontWeight: 400
                    }}>
                      {analysisData.transcript?.length || 0} segments
                    </Typography>
                  </Typography>

                  {/* Enhanced Transcript List */}
                  <Box sx={{
                    flexGrow: 1,
                    overflow: 'auto',
                    pr: 1,
                    '&::-webkit-scrollbar': {
                      width: '6px',
                    },
                    '&::-webkit-scrollbar-track': {
                      background: 'rgba(0,0,0,0.05)',
                      borderRadius: '3px',
                    },
                    '&::-webkit-scrollbar-thumb': {
                      background: 'rgba(0,0,0,0.2)',
                      borderRadius: '3px',
                      '&:hover': {
                        background: 'rgba(0,0,0,0.3)',
                      }
                    }
                  }} ref={transcriptContainerRef}>
                    {analysisData.transcript?.map((segment, index) => {
                      const startTime = segment.start_time ?? segment.start ?? 0;
                      const emotion = segment.emotion || 'neutral';
                      const text = segment.text || segment.sentence || segment.content || 'No text available';
                      const isActive = Math.abs(currentTime - startTime) < 2; // Active if within 2 seconds

                      return (
                        <Box
                          key={index}
                          onClick={() => handleSentenceClick(startTime)}
                          sx={{
                            p: 2,
                            mb: 1.5,
                            borderRadius: '12px',
                            cursor: 'pointer',
                            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                            border: '1px solid',
                            borderColor: isActive ?
                              customTheme.colors.emotion[emotion] || customTheme.colors.emotion.neutral :
                              'rgba(0, 0, 0, 0.08)',                            backgroundColor: isActive ?
                              `${customTheme.colors.emotion[emotion] || customTheme.colors.emotion.neutral}15` :
                              'rgba(30, 41, 59, 0.4)',
                            boxShadow: isActive ?
                              `0 4px 20px ${customTheme.colors.emotion[emotion] || customTheme.colors.emotion.neutral}20` :
                              '0 2px 8px rgba(0, 0, 0, 0.04)',
                            transform: isActive ? 'translateY(-2px)' : 'translateY(0px)',
                            '&:hover': {
                              transform: 'translateY(-3px)',
                              boxShadow: `0 6px 25px ${customTheme.colors.emotion[emotion] || customTheme.colors.emotion.neutral}25`,
                              borderColor: customTheme.colors.emotion[emotion] || customTheme.colors.emotion.neutral,
                            }
                          }}
                        >
                          {/* Timestamp and Emotion Badge */}
                          <Box sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            mb: 1.5
                          }}>
                            <Typography variant="caption" sx={{
                              color: 'text.secondary',
                              fontWeight: 500,
                              fontFamily: 'monospace',
                              backgroundColor: 'rgba(0, 0, 0, 0.05)',
                              px: 1,
                              py: 0.5,
                              borderRadius: '4px'
                            }}>
                              {formatTimeToHHMMSS(startTime)}
                            </Typography>


                            <Box sx={{
                              px: 1.5,
                              py: 0.5,
                              borderRadius: '20px',
                              backgroundColor: `${customTheme.colors.emotion[emotion] || customTheme.colors.emotion.neutral}15`,
                              border: `1px solid ${customTheme.colors.emotion[emotion] || customTheme.colors.emotion.neutral}40`,
                            }}>
                              <Typography variant="caption" sx={{
                                color: customTheme.colors.emotion[emotion] || customTheme.colors.emotion.neutral,
                                fontWeight: 600,
                                textTransform: 'capitalize',
                                fontSize: '0.75rem'
                              }}>
                                {emotion}
                              </Typography>
                            </Box>
                          </Box>

                          {/* Text Content */}
                          <Typography variant="body2" sx={{
                            color: 'text.primary',
                            lineHeight: 1.6,
                            fontWeight: isActive ? 500 : 400,
                            fontSize: '0.9rem'
                          }}>
                            {text}
                          </Typography>
                        </Box>                      );
                    })}

                    {/* No transcript message */}
                    {analysisData.transcript?.length === 0 && (
                      <Box sx={{
                        p: 3,
                        borderRadius: '12px',
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        textAlign: 'center',
                        color: 'text.secondary',
                        fontStyle: 'italic',
                        mt: 2,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: 1,
                      }}>
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          No transcript segments found for this video.
                        </Typography>
                        <Typography variant="caption" sx={{ opacity: 0.8 }}>
                          The video may not have any spoken content, or the analysis is still in progress.
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </Box>
              )}
            </Paper>
          </motion.div>
        </Grid>        {/* New Row 1, Column 3 - Emotion Pulse & Emotion Tracker */}
        <Grid
          item
          xs={12}
          lg={4}
          className="dashboard-grid-item"
          sx={{
            display: 'flex',
            minWidth: 0,
            width: '100%',
            flexShrink: 0, // Prevent shrinking
            alignSelf: 'flex-start', // Ensure this column aligns to top
          }}>
          <Box sx={{
            height: '85vh',
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            width: '100%', // Ensure full width within grid item
          }}>
            {/* Emotion Pulse Box */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              style={{ flex: 1, minHeight: 0 }}
            >
              <Paper
                elevation={0}
                sx={{
                  height: '100%',
                  p: 2.5,
                  background: customTheme.glassmorphism.luxury.background,
                  backdropFilter: customTheme.glassmorphism.luxury.backdropFilter,
                  border: customTheme.glassmorphism.luxury.border,
                  borderRadius: customTheme.borderRadius['3xl'],
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  position: 'relative',
                  transition: `all ${customTheme.animation.duration.normal} ${customTheme.animation.easing.premium}`,
                  boxShadow: customTheme.shadows.xl,
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: customTheme.shadows['3xl'],
                    border: `1px solid ${customTheme.colors.primary.glow}`,
                  },
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '2px',
                    background: customTheme.colors.gradients.primary,
                    borderRadius: customTheme.borderRadius.full,
                  }
                }}
              >
                <Typography variant="h5" sx={{
                  mb: 2,
                  fontWeight: 800,
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  fontSize: '1.2rem',
                  letterSpacing: '0.5px'
                }}>
                  <Box sx={{
                    width: 28,
                    height: 28,
                    borderRadius: '6px',
                    background: `linear-gradient(135deg, ${customTheme.colors.primary.main}, ${customTheme.colors.primary.dark})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1rem',
                    boxShadow: `0 4px 16px ${customTheme.colors.primary.main}40`,
                    animation: 'iconFloat 3s ease-in-out infinite',
                    '@keyframes iconFloat': {
                      '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
                      '50%': { transform: 'translateY(-2px) rotate(2deg)' }
                    }
                  }}>
                    <PsychologyAltIcon fontSize="small" />
                  </Box>
                  Emotion Pulse
                </Typography>                  <Box sx={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
                  <EmotionCurrent
                    emotion={currentEmotion?.emotion}
                    subEmotion={currentEmotion?.sub_emotion}
                    intensity={currentEmotion?.intensity || 0.5}
                    compact={true}
                  />
                </Box>
              </Paper>
            </motion.div>            {/* Emotion Tracker Box */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
              style={{ flex: 1, minHeight: 0 }}
            >
              <Paper
                elevation={0}
                sx={{
                  height: '100%',
                  p: 2.5,
                  background: customTheme.glassmorphism.luxury.background,
                  backdropFilter: customTheme.glassmorphism.luxury.backdropFilter,
                  border: customTheme.glassmorphism.luxury.border,
                  borderRadius: customTheme.borderRadius['3xl'],
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  position: 'relative',
                  transition: `all ${customTheme.animation.duration.normal} ${customTheme.animation.easing.premium}`,
                  boxShadow: customTheme.shadows.xl,
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: customTheme.shadows['3xl'],
                    border: `1px solid ${customTheme.colors.secondary.glow}`,
                  },
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '2px',
                    background: customTheme.colors.gradients.secondary,
                    borderRadius: customTheme.borderRadius.full,
                  }
                }}
              >
                <Typography variant="h5" sx={{
                  mb: 2,
                  fontWeight: 800,
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  fontSize: '1.2rem',
                  letterSpacing: '0.5px'
                }}>
                  <Box sx={{
                    width: 28,
                    height: 28,
                    borderRadius: '6px',
                    background: `linear-gradient(135deg, ${customTheme.colors.secondary.main}, ${customTheme.colors.secondary.dark})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1rem',
                    boxShadow: `0 4px 16px ${customTheme.colors.secondary.main}40`,
                    animation: 'iconFloat 3s ease-in-out infinite',
                    '@keyframes iconFloat': {
                      '0%, 100%': { transform: 'translateY(0px) rotate(0deg)' },
                      '50%': { transform: 'translateY(-2px) rotate(2deg)' }
                    }
                  }}>
                    <TimelineIcon fontSize="small" />
                  </Box>
                  Emotion Tracker
                </Typography>
                  <Box sx={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
                  {analysisData ? (
                    <EmotionTimeline
                      data={intensityTimeline}
                      currentTime={currentTime}
                    />
                  ) : (
                    <Box sx={{
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 3,
                      color: customTheme.colors.text.secondary,
                      textAlign: 'center',
                      position: 'relative',
                      overflow: 'hidden'
                    }}>
                      {/* Animated Background Elements */}
                      <Box sx={{
                        position: 'absolute',
                        top: '20%',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        width: '120px',
                        height: '120px',
                        borderRadius: '50%',
                        background: `
                          radial-gradient(circle at 30% 30%,
                            ${customTheme.colors.secondary.main}15 0%,
                            ${customTheme.colors.primary.main}10 50%,
                            transparent 100%
                          )
                        `,
                        animation: 'trackerPulse 4s ease-in-out infinite',
                        '@keyframes trackerPulse': {
                          '0%, 100%': { transform: 'translateX(-50%) scale(1)', opacity: 0.6 },
                          '50%': { transform: 'translateX(-50%) scale(1.1)', opacity: 0.9 }
                        }
                      }} />

                      {/* Central Tracker Icon */}
                      <Box sx={{
                        width: 80,
                        height: 80,
                        borderRadius: '50%',
                        background: `
                          linear-gradient(135deg,
                            ${customTheme.colors.secondary.main}90 0%,
                            ${customTheme.colors.secondary.dark}70 50%,
                            ${customTheme.colors.primary.main}40 100%
                          )
                        `,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '2.2rem',
                        position: 'relative',
                        zIndex: 2,
                        boxShadow: `
                          0 0 30px ${customTheme.colors.secondary.main}50,
                          0 8px 24px ${customTheme.colors.secondary.main}30,
                          inset 0 1px 0 rgba(255,255,255,0.3)
                        `,
                        border: `1px solid ${customTheme.colors.secondary.main}60`,
                        animation: 'trackerIconFloat 3s ease-in-out infinite',
                        '@keyframes trackerIconFloat': {
                          '0%, 100%': {
                            transform: 'translateY(0px) rotate(0deg)',
                            filter: 'brightness(1)'
                          },
                          '50%': {
                            transform: 'translateY(-6px) rotate(2deg)',
                            filter: 'brightness(1.2)'
                          }
                        }
                      }}>
                        📈
                      </Box>

                      {/* Tracker Content */}
                      <Box sx={{ textAlign: 'center', zIndex: 2 }}>
                        <Typography variant="h6" sx={{
                          fontWeight: 700,
                          color: 'white',
                          mb: 1,
                          fontSize: '1.1rem',
                          letterSpacing: '0.5px',
                          filter: `drop-shadow(0 2px 8px ${customTheme.colors.secondary.main}30)`
                        }}>
                          Upload a video to see this section
                        </Typography>
                      </Box>
                    </Box>
                  )}
                </Box>
              </Paper>
            </motion.div>
          </Box>
        </Grid>
      </Grid>

    </Box>

    {isLoading && (
        <Box className="loading-overlay" sx={{
          background: customTheme.colors.background.cosmic,
          backdropFilter: 'blur(40px)',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: customTheme.colors.gradients.glow,
            opacity: 0.4,
            zIndex: 1,
          }
        }}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 30 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              maxWidth: '700px',
              textAlign: 'center',
              padding: '0 30px',
              position: 'relative',
              zIndex: 2,
            }}
          >
            {/* Premium Enhanced Emotion Visualization */}
            <Box sx={{ position: 'relative', width: 320, height: 320, mb: 8 }}>
              {/* Constellation Network */}
              {[...Array(8)].map((_, i) => {
                const angle1 = (i * 45) * (Math.PI / 180);
                const angle2 = ((i + 1) * 45) * (Math.PI / 180);
                const radius = 200;
                const x1 = Math.cos(angle1) * radius;
                const y1 = Math.sin(angle1) * radius;
                const x2 = Math.cos(angle2) * radius;
                const y2 = Math.sin(angle2) * radius;

                return (
                  <motion.div
                    key={`constellation-${i}`}
                    animate={{
                      opacity: [0, 0.4, 0],
                      scaleX: [0.5, 1.2, 0.5],
                    }}
                    transition={{
                      duration: 6 + (i * 0.5),
                      repeat: Infinity,
                      ease: "easeInOut",
                      delay: i * 0.4,
                    }}
                    style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: `translate(-50%, -50%) rotate(${Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI)}deg)`,
                      width: Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2),
                      height: 1,
                      background: `linear-gradient(to right,
                        transparent 0%,
                        ${customTheme.colors.primary.main}60 50%,
                        transparent 100%
                      )`,
                      transformOrigin: 'left center',
                      zIndex: 1,
                    }}
                  />
                );
              })}

              {/* Background Starfield */}
              {[...Array(30)].map((_, i) => {
                const x = (Math.random() - 0.5) * 800;
                const y = (Math.random() - 0.5) * 600;

                return (
                  <motion.div
                    key={`star-${i}`}
                    animate={{
                      opacity: [0.2, 0.8, 0.2],
                      scale: [0.5, 1, 0.5],
                    }}
                    transition={{
                      duration: 3 + Math.random() * 4,
                      repeat: Infinity,
                      ease: "easeInOut",
                      delay: Math.random() * 5,
                    }}
                    style={{
                      position: 'absolute',
                      top: `calc(50% + ${y}px)`,
                      left: `calc(50% + ${x}px)`,
                      transform: 'translate(-50%, -50%)',
                      width: 2 + Math.random() * 2,
                      height: 2 + Math.random() * 2,
                      borderRadius: '50%',
                      background: `radial-gradient(circle,
                        ${Math.random() > 0.5 ? customTheme.colors.primary.main : customTheme.colors.secondary.main}80,
                        transparent
                      )`,
                      filter: 'blur(0.5px)',
                      zIndex: 1,
                    }}
                  />
                );
              })}

              {/* Outermost Orbital Ring */}
              <motion.div
                animate={{
                  rotate: [0, 360],
                }}
                transition={{
                  duration: 40,
                  repeat: Infinity,
                  ease: "linear"
                }}
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: 300,
                  height: 300,
                  borderRadius: '50%',
                  border: `1px solid ${customTheme.colors.primary.main}10`,
                  zIndex: 3,
                }}
              />

              {/* Central Premium Orb */}
              <motion.div
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.7, 1, 0.7],
                  rotate: [0, 360],
                }}
                transition={{
                  duration: 8,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: 180,
                  height: 180,
                  borderRadius: '50%',
                  background: `
                    radial-gradient(circle at 30% 30%,
                      ${customTheme.colors.primary.main}90 0%,
                      ${customTheme.colors.secondary.main}70 40%,
                      ${customTheme.colors.primary.dark}50 70%,
                      transparent 100%
                    )
                  `,
                  boxShadow: `
                    0 0 100px ${customTheme.colors.primary.main}40,
                    0 0 200px ${customTheme.colors.secondary.main}20,
                    0 0 300px ${customTheme.colors.primary.main}10,
                    inset 0 0 60px rgba(255, 255, 255, 0.08)
                  `,
                  filter: 'blur(1px)',
                  zIndex: 7,
                }}
              />

              {/* Inner Crystalline Core */}
              <motion.div
                animate={{
                  scale: [0.8, 1.3, 0.8],
                  opacity: [0.5, 1, 0.5],
                  rotate: [0, -360],
                }}
                transition={{
                  duration: 6,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: 120,
                  height: 120,
                  borderRadius: '50%',
                  background: `
                    linear-gradient(135deg,
                      ${customTheme.colors.primary.main}FF 0%,
                      ${customTheme.colors.secondary.main}DD 50%,
                      ${customTheme.colors.primary.dark}AA 100%
                    )
                  `,
                  boxShadow: `
                    0 0 80px ${customTheme.colors.primary.main}70,
                    inset 0 0 40px rgba(255, 255, 255, 0.15)
                  `,
                  zIndex: 9,
                }}
              />

              {/* Enhanced Cosmic Particles */}
              {Array.from({ length: 20 }, (_, i) => {
                const angle = (i / 20) * Math.PI * 2;
                const radius = 120 + (i % 4) * 25;
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;

                return (
                  <motion.div
                    key={i}
                    animate={{
                      rotate: [0, 360],
                      scale: [0.4, 1.6, 0.4],
                      opacity: [0.2, 1, 0.2],
                      x: [x, x * 1.4, x * 0.6, x],
                      y: [y, y * 1.4, y * 0.6, y],
                    }}
                    transition={{
                      rotate: {
                        duration: 25,
                        repeat: Infinity,
                        ease: "linear"
                      },
                      scale: {
                        duration: 5 + i * 0.8,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 0.25
                      },
                      opacity: {
                        duration: 4 + i * 0.4,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 0.15
                      },
                      x: {
                        duration: 8 + i * 0.6,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 0.1
                      },
                      y: {
                        duration: 8 + i * 0.6,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 0.1
                      }
                    }}
                    style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: 3 + (i % 4) * 2,
                      height: 3 + (i % 4) * 2,
                      borderRadius: '50%',
                      background: i % 4 === 0
                        ? `radial-gradient(circle, ${customTheme.colors.primary.main}FF, transparent)`
                        : i % 3 === 0
                        ? `radial-gradient(circle, ${customTheme.colors.secondary.main}FF, transparent)`
                        : i % 2 === 0
                        ? `radial-gradient(circle, ${customTheme.colors.tertiary.main}FF, transparent)`
                        : `radial-gradient(circle, ${customTheme.colors.primary.light}FF, transparent)`,
                      boxShadow: `0 0 ${15 + (i % 3) * 10}px ${
                        i % 4 === 0
                          ? customTheme.colors.primary.main
                          : i % 3 === 0
                          ? customTheme.colors.secondary.main
                          : i % 2 === 0
                          ? customTheme.colors.tertiary.main
                          : customTheme.colors.primary.light
                      }70`,
                      filter: 'blur(0.5px)',
                      zIndex: 10,
                    }}
                  />
                );
              })}              {/* Orbital Satellites */}
              {[...Array(3)].map((_, i) => {
                const orbitRadius = 180 + (i * 40);
                return (
                  <motion.div
                    key={`satellite-${i}`}
                    animate={{
                      rotate: [0, 360],
                    }}
                    transition={{
                      duration: 15 + (i * 5),
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: orbitRadius * 2,
                      height: orbitRadius * 2,
                      zIndex: 6,
                    }}
                  >
                    <motion.div
                      animate={{
                        scale: [0.8, 1.4, 0.8],
                        opacity: [0.6, 1, 0.6],
                      }}
                      transition={{
                        duration: 3 + (i * 0.8),
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 0.5,
                      }}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        width: 12 + (i * 2),
                        height: 12 + (i * 2),
                        borderRadius: '50%',
                        background: `radial-gradient(circle,
                          ${customTheme.colors.primary.main}FF 0%,
                          ${customTheme.colors.secondary.main}80 50%,
                          transparent 100%
                        )`,
                        boxShadow: `
                          0 0 30px ${customTheme.colors.primary.main}80,
                          0 0 60px ${customTheme.colors.secondary.main}40
                        `,
                        filter: 'blur(0.8px)',
                      }}
                    />
                  </motion.div>
                );
              })}

              {/* Energy Pulses */}
              {[...Array(5)].map((_, i) => (
                <motion.div
                  key={`pulse-${i}`}
                  animate={{
                    scale: [0, 4, 0],
                    opacity: [0, 0.6, 0],
                  }}
                  transition={{
                    duration: 4,
                    repeat: Infinity,
                    ease: "easeOut",
                    delay: i * 0.8,
                  }}
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 100,
                    height: 100,
                    borderRadius: '50%',
                    border: `2px solid ${customTheme.colors.primary.main}60`,
                    background: `radial-gradient(circle, transparent 60%, ${customTheme.colors.primary.main}20 100%)`,
                    zIndex: 3,
                  }}
                />
              ))}

              {/* Simplified rings for depth */}
              <motion.div
                animate={{
                  rotate: [0, 360],
                  scale: [1, 1.02, 1],
                }}
                transition={{
                  rotate: {
                    duration: 20,
                    repeat: Infinity,
                    ease: "linear"
                  },
                  scale: {
                    duration: 4,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }
                }}
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: 200,
                  height: 200,
                  borderRadius: '50%',
                  border: `2px solid ${customTheme.colors.primary.main}30`,
                  zIndex: 5,
                }}
              />
              <motion.div
                animate={{
                  rotate: [0, -360],
                  scale: [1, 1.03, 1],
                }}
                transition={{
                  rotate: {
                    duration: 25,
                    repeat: Infinity,
                    ease: "linear"
                  },
                  scale: {
                    duration: 5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }
                }}
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: 240,
                  height: 240,
                  borderRadius: '50%',
                  border: `1px solid ${customTheme.colors.primary.main}20`,
                  zIndex: 4,
                }}
              />
            </Box>            {/* Quantum Loading Title */}
            <Typography
              variant="h2"
              component="h1"
              gutterBottom
              align="center"
              sx={{
                fontWeight: 900,
                mb: 4,
                color: 'white',
                fontSize: { xs: '2.8rem', md: '4rem' },
                letterSpacing: '-0.02em',
                fontFamily: customTheme.typography.fontFamily.heading,
                textShadow: 'none'
              }}
            >
              Emotion Analysis
            </Typography>

            {/* Enhanced Progress Section */}
            <Box sx={{ mb: 6, width: '100%', maxWidth: '550px' }}>
              <Typography
                align="center"
                sx={{
                  fontWeight: 600,
                  color: customTheme.colors.text.primary,
                  mb: 3,
                  fontSize: '1.2rem',
                  letterSpacing: '0.01em',
                  textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
                }}
              >
                Processing...
              </Typography>

              {/* Enhanced loading spinner with dark theme */}
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  mb: 3,
                }}
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "linear"
                  }}
                  style={{
                    width: 40,
                    height: 40,
                    border: `4px solid ${customTheme.colors.primary.main}30`,
                    borderTop: `4px solid ${customTheme.colors.primary.main}`,
                    borderRadius: '50%',
                    boxShadow: `0 0 20px ${customTheme.colors.primary.main}50`,
                  }}
                />
              </Box>
            </Box>          </motion.div>
        </Box>
      )}

      {/* Feedback Modal */}
      <FeedbackModal
        open={feedbackModalOpen}
        onClose={handleCloseFeedback}
        transcriptData={analysisData?.transcript || []}
        videoTitle={analysisData?.title || 'Unknown Video'}
      />

      {/* Add Video Modal */}
      <AddVideoModal
        open={addVideoModalOpen}
        onClose={() => setAddVideoModalOpen(false)}
        onSubmit={handleUrlUpload}
      />

      {/* Settings Modal */}
      <SettingsModal
        open={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
      />
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={muiTheme}>
      <CssBaseline />
      <VideoProvider>
        <Router>
          <Routes>
            <Route path="/" element={
              <Box sx={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
                <AppContent />
              </Box>
            } />
            <Route path="/monitoring" element={
              <MonitoringErrorBoundary>
                <MonitoringDashboard />
              </MonitoringErrorBoundary>
            } />
          </Routes>
        </Router>
      </VideoProvider>
    </ThemeProvider>
  );
}

export default App;
