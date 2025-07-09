import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Button,
  IconButton,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Visibility as VisibilityIcon,
  Analytics as AnalyticsIcon,
  EditNote as EditNoteIcon,
  FileDownload as FileDownloadIcon,
  Fullscreen as FullscreenIcon,
} from '@mui/icons-material';
import VideoPlayer from './VideoPlayer';
import Transcript from './Transcript';
import theme from '../theme';

// Styled Components
const CenterContainer = styled(Box)(() => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
  overflow: 'hidden',
}));

const TabContainer = styled(Box)(() => ({
  borderBottom: `1px solid ${theme.colors.border}`,
  background: theme.colors.surface.glass,
  backdropFilter: 'blur(8px)',
}));

const StyledTabs = styled(Tabs)(() => ({
  minHeight: '48px',
  '& .MuiTabs-indicator': {
    background: `linear-gradient(90deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
    height: 3,
    borderRadius: theme.borderRadius.full,
  },
  '& .MuiTab-root': {
    color: theme.colors.text.secondary,
    fontWeight: theme.typography.fontWeight.medium,
    fontSize: theme.typography.fontSize.sm,
    textTransform: 'none',
    minHeight: '48px',
    transition: `all ${theme.animation.duration.normal} ${theme.animation.easing.easeOut}`,
    '&:hover': {
      color: theme.colors.text.primary,
      background: theme.colors.surface.glass,
    },
    '&.Mui-selected': {
      color: theme.colors.primary.main,
      fontWeight: theme.typography.fontWeight.semibold,
    },
  },
}));

const VideoContainer = styled(Box)(() => ({
  borderRadius: theme.borderRadius.xl,
  overflow: 'hidden',
  background: '#000',
  boxShadow: theme.shadows.xl,
  marginBottom: theme.spacing.lg,
  position: 'relative',

  '&:hover .video-controls': {
    opacity: 1,
  },
}));

const VideoControls = styled(Box)(() => ({
  position: 'absolute',
  top: theme.spacing.md,
  right: theme.spacing.md,
  display: 'flex',
  gap: theme.spacing.sm,
  opacity: 0,
  transition: `opacity ${theme.animation.duration.normal} ${theme.animation.easing.easeOut}`,
  zIndex: 10,
}));

const ControlButton = styled(IconButton)(() => ({
  width: 40,
  height: 40,
  background: theme.colors.surface.overlay,
  backdropFilter: 'blur(8px)',
  color: theme.colors.text.primary,
  border: `1px solid ${theme.colors.border}`,
  '&:hover': {
    background: theme.colors.surface.glass,
    transform: 'scale(1.05)',
  },
}));

const ActionButtonsContainer = styled(Box)(() => ({
  display: 'flex',
  gap: theme.spacing.md,
  justifyContent: 'center',
  flexWrap: 'wrap',
  padding: theme.spacing.md,
  borderTop: `1px solid ${theme.colors.border}`,
  background: theme.colors.surface.glass,
}));

const ActionButton = styled(Button)(() => ({
  borderRadius: theme.borderRadius.lg,
  padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
  fontSize: theme.typography.fontSize.sm,
  fontWeight: theme.typography.fontWeight.medium,
  textTransform: 'none',
  border: `1px solid ${theme.colors.border}`,
  color: theme.colors.text.secondary,
  background: 'transparent',
  transition: `all ${theme.animation.duration.normal} ${theme.animation.easing.easeOut}`,

  '&:hover': {
    borderColor: theme.colors.primary.main,
    background: `${theme.colors.primary.main}08`,
    color: theme.colors.primary.main,
    transform: 'translateY(-1px)',
  },

  '&:disabled': {
    borderColor: theme.colors.border,
    color: theme.colors.text.tertiary,
    background: 'transparent',
  },
}));

// Tab Panel Component
const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`center-tabpanel-${index}`}
    aria-labelledby={`center-tab-${index}`}
    {...other}
    style={{ height: '100%', overflow: 'hidden' }}
  >
    <AnimatePresence mode="wait">
      {value === index && (
        <motion.div
          key={`tab-content-${index}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          style={{ height: '100%' }}
        >
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {children}
          </Box>
        </motion.div>
      )}
    </AnimatePresence>
  </div>
);

/**
 * VideoCenter Module
 * Main center module containing video player, transcript, and controls
 * Handles video playback, transcript display, and analysis actions
 */
const VideoCenter = ({
  videoUrl,
  currentTime = 0,
  onProgress,
  analysisData,
  onFeedback,
  onExport,
  onSentenceClick,
  isLoading = false,
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <CenterContainer>
      {/* Header */}
      <Box sx={{
        p: 3,
        borderBottom: `1px solid ${theme.colors.border}`,
        background: `linear-gradient(135deg, ${theme.colors.primary.main}08, ${theme.colors.secondary.main}04)`,
      }}>
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Typography variant="h5" sx={{
            color: theme.colors.text.primary,
            fontWeight: theme.typography.fontWeight.bold,
            background: `linear-gradient(135deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            mb: 1,
          }}>
            Video Analysis Center
          </Typography>

          <Typography variant="body2" sx={{
            color: theme.colors.text.secondary,
            fontSize: theme.typography.fontSize.sm,
          }}>
            {analysisData?.title || 'No video loaded'}
            {currentTime > 0 && (
              <Box component="span" sx={{ ml: 2, color: theme.colors.text.tertiary }}>
                • {formatTime(currentTime)}
              </Box>
            )}
          </Typography>
        </motion.div>
      </Box>

      {/* Video Player */}
      {videoUrl ? (
        <Box sx={{ p: 3, pb: 0 }}>
          <VideoContainer>
            <VideoControls className="video-controls">
              <ControlButton onClick={handlePlayPause}>
                {isPlaying ? <PauseIcon fontSize="small" /> : <PlayIcon fontSize="small" />}
              </ControlButton>
              <ControlButton onClick={handleFullscreen}>
                <FullscreenIcon fontSize="small" />
              </ControlButton>
            </VideoControls>

            <VideoPlayer
              url={videoUrl}
              onProgress={onProgress}
              currentTime={currentTime}
            />
          </VideoContainer>
        </Box>
      ) : (
        <Box sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          p: 4,
          textAlign: 'center',
        }}>
          <motion.div
            animate={{
              scale: [1, 1.05, 1],
              opacity: [0.7, 1, 0.7],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          >
            <Box sx={{
              width: 120,
              height: 120,
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${theme.colors.primary.main}20, ${theme.colors.secondary.main}15)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 3,
              border: `2px dashed ${theme.colors.border}`,
            }}>
              <PlayIcon sx={{
                fontSize: '3rem',
                color: theme.colors.text.tertiary
              }} />
            </Box>
          </motion.div>

          <Typography variant="h6" sx={{
            color: theme.colors.text.primary,
            fontWeight: theme.typography.fontWeight.semibold,
            mb: 1,
          }}>
            Ready to Analyze
          </Typography>

          <Typography variant="body2" sx={{
            color: theme.colors.text.secondary,
            maxWidth: 300,
          }}>
            Load a video from the sidebar or add a new YouTube URL to begin emotion analysis
          </Typography>
        </Box>
      )}

      {/* Tabs for Content */}
      {analysisData && (
        <>
          <TabContainer>
            <StyledTabs
              value={tabValue}
              onChange={handleTabChange}
              variant="fullWidth"
            >
              <Tab
                icon={<VisibilityIcon fontSize="small" />}
                label="Live View"
                iconPosition="start"
              />
              <Tab
                icon={<AnalyticsIcon fontSize="small" />}
                label="Transcript"
                iconPosition="start"
              />
            </StyledTabs>
          </TabContainer>

          {/* Tab Content */}
          <Box sx={{ flex: 1, overflow: 'hidden' }}>
            <TabPanel value={tabValue} index={0}>
              <Box sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                p: 4,
                textAlign: 'center',
              }}>
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5 }}
                >
                  <Typography variant="h6" sx={{
                    color: theme.colors.text.primary,
                    mb: 2,
                  }}>
                    Live Analysis View
                  </Typography>
                  <Typography variant="body2" sx={{
                    color: theme.colors.text.secondary,
                  }}>
                    Real-time emotion analysis appears here
                  </Typography>
                </motion.div>
              </Box>
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <Box sx={{
                flex: 1,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
              }}>
                <Transcript
                  data={analysisData?.transcript || []}
                  currentTime={currentTime}
                  onSentenceClick={onSentenceClick}
                />
              </Box>
            </TabPanel>
          </Box>

          {/* Action Buttons */}
          <ActionButtonsContainer>
            <ActionButton
              startIcon={<EditNoteIcon />}
              onClick={onFeedback}
              disabled={!analysisData}
            >
              Give Feedback
            </ActionButton>

            <ActionButton
              startIcon={<FileDownloadIcon />}
              onClick={onExport}
              disabled={!analysisData}
            >
              Export Results
            </ActionButton>
          </ActionButtonsContainer>
        </>
      )}

      {/* Loading Overlay */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: theme.colors.surface.overlay,
              backdropFilter: 'blur(8px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 100,
            }}
          >
            <Box sx={{ textAlign: 'center' }}>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                style={{
                  width: 40,
                  height: 40,
                  border: `3px solid ${theme.colors.primary.main}40`,
                  borderTop: `3px solid ${theme.colors.primary.main}`,
                  borderRadius: '50%',
                  margin: '0 auto 16px',
                }}
              />
              <Typography variant="body2" sx={{
                color: theme.colors.text.primary,
                fontWeight: theme.typography.fontWeight.medium,
              }}>
                Processing video...
              </Typography>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </CenterContainer>
  );
};

export default VideoCenter;
