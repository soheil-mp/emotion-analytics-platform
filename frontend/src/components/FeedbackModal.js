import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Select,
  MenuItem,
  FormControl,
  Typography,
  Box,
  IconButton,
  Chip,
  useTheme,
  useMediaQuery,
  Snackbar,
  Alert,
  CircularProgress
} from '@mui/material';
import { styled } from '@mui/material/styles';
import CloseIcon from '@mui/icons-material/Close';
import SaveIcon from '@mui/icons-material/Save';
import FeedbackIcon from '@mui/icons-material/Feedback';
import { motion, AnimatePresence } from 'framer-motion';
import { getEmotionColor } from '../utils';
import { saveFeedback } from '../api';
import customTheme from '../theme';

// Styled components for better design with dark theme
const StyledDialog = styled(Dialog)(({ theme }) => ({
  '& .MuiDialog-paper': {
    borderRadius: 20,
    maxWidth: '95vw',
    maxHeight: '90vh',
    width: '1200px',
    background: customTheme.colors.surface.glass,
    backdropFilter: 'blur(20px)',
    border: `1px solid ${customTheme.colors.borderActive}`,
    boxShadow: '0 25px 80px rgba(0, 0, 0, 0.4)',
    color: customTheme.colors.text.primary,
  },
  '& .MuiDialogTitle-root': {
    backgroundColor: customTheme.colors.surface.elevated,
    color: customTheme.colors.text.primary,
    borderBottom: `2px solid ${customTheme.colors.primary.main}`,
  },
  '& .MuiDialogContent-root': {
    backgroundColor: 'transparent',
    color: customTheme.colors.text.primary,
  },
  '& .MuiDialogActions-root': {
    backgroundColor: customTheme.colors.surface.elevated,
    borderTop: `1px solid ${customTheme.colors.border}`,
  },
}));

const StyledTableContainer = styled(TableContainer)(({ theme }) => ({
  maxHeight: '60vh',
  borderRadius: 12,
  border: `1px solid ${customTheme.colors.border}`,
  backgroundColor: customTheme.colors.surface.card,
  '&::-webkit-scrollbar': {
    width: '8px',
  },
  '&::-webkit-scrollbar-track': {
    background: customTheme.colors.surface.glass,
    borderRadius: '4px',
  },
  '&::-webkit-scrollbar-thumb': {
    background: customTheme.colors.primary.main,
    borderRadius: '4px',
    '&:hover': {
      background: customTheme.colors.primary.light,
    },
  },
}));

const StyledTableHead = styled(TableHead)(({ theme }) => ({
  '& .MuiTableCell-head': {
    backgroundColor: customTheme.colors.primary.main,
    fontWeight: 700,
    fontSize: '0.95rem',
    color: customTheme.colors.text.primary,
    borderBottom: `2px solid ${customTheme.colors.primary.dark}`,
    position: 'sticky',
    top: 0,
    zIndex: 1,
  },
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  '& .MuiTableCell-root': {
    color: customTheme.colors.text.primary,
    borderBottom: `1px solid ${customTheme.colors.border}`,
  },
  '&:nth-of-type(even)': {
    backgroundColor: customTheme.colors.surface.glass,
  },
  '&:hover': {
    backgroundColor: customTheme.colors.primary.main + '20', // 20% opacity
    transform: 'scale(1.002)',
    transition: 'all 0.2s ease',
  },
}));

const StyledSelect = styled(Select)(({ theme }) => ({
  minWidth: 120,
  fontSize: '0.875rem',
  color: customTheme.colors.text.primary,
  '& .MuiOutlinedInput-notchedOutline': {
    borderColor: customTheme.colors.border,
  },
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: customTheme.colors.borderHover,
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: customTheme.colors.primary.main,
  },
  '& .MuiSvgIcon-root': {
    color: customTheme.colors.text.secondary,
  },
  '& .MuiSelect-select': {
    backgroundColor: 'transparent',
    color: customTheme.colors.text.primary,
  },
}));

const TextCell = styled(TableCell)(({ theme }) => ({
  maxWidth: '300px',
  wordWrap: 'break-word',
  whiteSpace: 'pre-wrap',
  fontSize: '0.875rem',
  lineHeight: 1.4,
  color: customTheme.colors.text.primary,
  backgroundColor: 'transparent',
}));

// Dark theme MenuProps for Select components
const darkMenuProps = {
  PaperProps: {
    sx: {
      backgroundColor: customTheme.colors.surface.elevated,
      border: `1px solid ${customTheme.colors.border}`,
      borderRadius: 2,
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
      '& .MuiMenuItem-root': {
        color: customTheme.colors.text.primary,
        '&:hover': {
          backgroundColor: customTheme.colors.primary.main + '20',
        },
        '&.Mui-selected': {
          backgroundColor: customTheme.colors.primary.main + '30',
          '&:hover': {
            backgroundColor: customTheme.colors.primary.main + '40',
          },
        },
      },
    },
  },
};

// Available options for dropdowns
const EMOTION_OPTIONS = [
  'happiness',
  'sadness',
  'anger',
  'fear',
  'disgust',
  'surprise',
  'neutral'
];

const SUB_EMOTION_OPTIONS = [
  'neutral',
  'joy', 'excitement', 'curiosity', 'satisfaction', 'pride', 'relief', 'admiration',
  'amusement', 'approval', 'caring', 'desire', 'gratitude', 'love', 'optimism',
  'grief', 'melancholy', 'disappointment', 'despair', 'sorrow', 'remorse',
  'rage', 'annoyance', 'frustration', 'irritation', 'resentment', 'anger',
  'anxiety', 'panic', 'worry', 'nervousness', 'terror', 'fear', 'confusion',
  'revulsion', 'contempt', 'aversion', 'distaste', 'disgust', 'embarrassment',
  'amazement', 'shock', 'wonder', 'astonishment', 'bewilderment', 'surprise', 'realization'
];

const INTENSITY_OPTIONS = [
  'neutral',
  'mild',
  'moderate',
  'intense'
];

/**
 * Format time value (number or string) to HH:MM:SS format
 */
const formatTimeValue = (timeValue) => {
  // If it's already a formatted string, return as is
  if (typeof timeValue === 'string' && timeValue.includes(':')) {
    return timeValue;
  }

  // Convert number to formatted time string
  const seconds = typeof timeValue === 'number' ? timeValue : parseFloat(timeValue) || 0;
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
};

/**
 * Robust field mapping with multiple fallback strategies
 * Ensures no empty values by providing smart defaults
 */
const mapSegmentData = (item, index) => {
  // Helper function to get text content with multiple field name attempts
  const getText = (segment) => {
    const textFields = ['sentence', 'text', 'content', 'transcript', 'speech'];
    for (const field of textFields) {
      if (segment[field] && typeof segment[field] === 'string' && segment[field].trim()) {
        return segment[field].trim();
      }
    }
    return ''; // Return empty string if no text found
  };

  // Helper function to get emotion with validation and fallbacks
  const getEmotion = (segment) => {
    const emotionFields = ['emotion', 'primary_emotion', 'predicted_emotion', 'main_emotion'];
    const invalidValues = ['unknown', 'undefined', 'null', '', null, undefined];

    for (const field of emotionFields) {
      const value = segment[field];
      if (value && !invalidValues.includes(value) && typeof value === 'string') {
        const cleanValue = value.toLowerCase().trim();
        // Validate against known emotions
        if (EMOTION_OPTIONS.includes(cleanValue)) {
          return cleanValue;
        }
      }
    }
    return 'neutral'; // Default fallback
  };

  // Helper function to get sub-emotion with validation and fallbacks
  const getSubEmotion = (segment) => {
    const subEmotionFields = ['sub_emotion', 'subEmotion', 'secondary_emotion', 'detailed_emotion'];
    const invalidValues = ['unknown', 'undefined', 'null', '', null, undefined, 'neutral'];

    for (const field of subEmotionFields) {
      const value = segment[field];
      if (value && !invalidValues.includes(value) && typeof value === 'string') {
        const cleanValue = value.toLowerCase().trim();
        // Validate against known sub-emotions
        if (SUB_EMOTION_OPTIONS.includes(cleanValue)) {
          return cleanValue;
        }
      }
    }

    // Smart fallback based on primary emotion
    const primaryEmotion = getEmotion(segment);
    const emotionToSubEmotionMap = {
      'happiness': 'joy',
      'sadness': 'melancholy',
      'anger': 'frustration',
      'fear': 'anxiety',
      'surprise': 'amazement',
      'disgust': 'aversion',
      'neutral': 'neutral'
    };

    return emotionToSubEmotionMap[primaryEmotion] || 'neutral';
  };

  // Helper function to get intensity with validation and fallbacks
  const getIntensity = (segment) => {
    const intensityFields = ['intensity', 'confidence', 'strength', 'magnitude', 'score'];
    const invalidValues = ['unknown', 'undefined', 'null', '', null, undefined];

    for (const field of intensityFields) {
      const value = segment[field];
      if (value && !invalidValues.includes(value)) {
        // Handle string values
        if (typeof value === 'string') {
          const cleanValue = value.toLowerCase().trim();
          if (INTENSITY_OPTIONS.includes(cleanValue)) {
            return cleanValue;
          }
          // Try to parse as number
          const numValue = parseFloat(value);
          if (!isNaN(numValue)) {
            if (numValue >= 0 && numValue <= 0.3) return 'mild';
            if (numValue > 0.3 && numValue <= 0.6) return 'moderate';
            if (numValue > 0.6) return 'intense';
          }
        }
        // Handle numeric values
        if (typeof value === 'number' && !isNaN(value)) {
          if (value >= 0 && value <= 0.3) return 'mild';
          if (value > 0.3 && value <= 0.6) return 'moderate';
          if (value > 0.6 && value <= 1.0) return 'intense';
          if (value > 1 && value <= 30) return 'mild';
          if (value > 30 && value <= 60) return 'moderate';
          if (value > 60) return 'intense';
        }
      }
    }

    // Smart fallback based on emotion type
    const emotion = getEmotion(segment);
    const emotionToIntensityMap = {
      'anger': 'intense',
      'fear': 'moderate',
      'happiness': 'moderate',
      'sadness': 'moderate',
      'surprise': 'mild',
      'disgust': 'mild',
      'neutral': 'mild'
    };

    return emotionToIntensityMap[emotion] || 'mild';
  };

  return {
    id: index,
    start_time: formatTimeValue(item.start_time ?? item.start ?? 0),
    end_time: formatTimeValue(item.end_time ?? item.end ?? (item.start_time ?? item.start ?? 0) + 2),
    text: getText(item),
    emotion: getEmotion(item),
    sub_emotion: getSubEmotion(item),
    intensity: getIntensity(item)
  };
};

/**
 * FeedbackModal Component
 *
 * A comprehensive modal for editing emotion predictions with dropdown selections.
 * Features responsive design, data validation, and Azure integration for saving training data.
 */
const FeedbackModal = ({ open, onClose, transcriptData, videoTitle }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    // State management for feedback data and UI
  const [feedbackData, setFeedbackData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');  /**
   * Initialize feedback data when modal opens
   * Converts transcript data to editable format with robust field mapping
   */
  useEffect(() => {
    if (open && transcriptData) {
      setIsDataLoading(true);

      // DEBUG: Log what we're receiving from the API
      console.log("=== FRONTEND DEBUG: Raw transcriptData ===");
      console.log("transcriptData:", transcriptData);
      console.log("transcriptData length:", transcriptData?.length);
      if (transcriptData && transcriptData.length > 0) {
        console.log("First item:", transcriptData[0]);
        console.log("First item keys:", Object.keys(transcriptData[0]));
        console.log("start_time value:", transcriptData[0].start_time, "type:", typeof transcriptData[0].start_time);
        console.log("end_time value:", transcriptData[0].end_time, "type:", typeof transcriptData[0].end_time);
        console.log("sentence value:", transcriptData[0].sentence);
        console.log("emotion value:", transcriptData[0].emotion);
        console.log("sub_emotion value:", transcriptData[0].sub_emotion);
        console.log("intensity value:", transcriptData[0].intensity);
      }
      console.log("=== END FRONTEND DEBUG ===");

      // Process data with robust field mapping
      const processData = () => {
        try {
          const initialData = transcriptData.map((item, index) => {
            const mappedData = mapSegmentData(item, index);

            // Log any data mapping issues for debugging
            if (!mappedData.text || mappedData.text.trim() === '') {
              console.warn(`No text found for segment ${index}:`, item);
            }

            console.log(`Mapped segment ${index}:`, {
              original: {
                emotion: item.emotion,
                sub_emotion: item.sub_emotion,
                intensity: item.intensity
              },
              mapped: {
                emotion: mappedData.emotion,
                sub_emotion: mappedData.sub_emotion,
                intensity: mappedData.intensity
              }
            });

            return mappedData;
          });

          console.log("=== PROCESSED FEEDBACK DATA ===");
          console.log("Total segments processed:", initialData.length);
          console.log("Sample processed data:", initialData.slice(0, 3));
          console.log("=== END PROCESSED DATA ===");

          setFeedbackData(initialData);
          setIsDataLoading(false);
        } catch (error) {
          console.error("Error processing feedback data:", error);
          setSnackbarMessage("Error processing feedback data. Please try again.");
          setSnackbarSeverity("error");
          setSnackbarOpen(true);
          setIsDataLoading(false);
        }
      };

      // Add small delay to show loading state
      setTimeout(processData, 500);
    } else if (!open) {
      // Reset loading state when modal closes
      setIsDataLoading(true);
      setFeedbackData([]);
    }
  }, [open, transcriptData]);

  /**
   * Handle dropdown value changes
   * Updates specific field for a given row
   */
  const handleValueChange = (id, field, value) => {
    setFeedbackData(prev =>
      prev.map(item =>
        item.id === id ? { ...item, [field]: value } : item
      )
    );
  };
  /**
   * Validate feedback data before submission
   * Ensures all required emotion fields are filled (text can be empty for some segments)
   */
  const validateData = () => {
    const invalidRows = feedbackData.filter(item =>
      !item.emotion ||
      !item.sub_emotion ||
      !item.intensity ||
      item.emotion === '' ||
      item.sub_emotion === '' ||
      item.intensity === ''
    );

    if (invalidRows.length > 0) {
      console.warn("Invalid rows found:", invalidRows);
      setSnackbarMessage(`Please ensure emotion, sub-emotion, and intensity are selected for all ${invalidRows.length} row(s)`);
      setSnackbarSeverity('warning');
      setSnackbarOpen(true);
      return false;
    }

    return true;
  };
  /**
   * Submit feedback data to backend
   * Saves as CSV file to Azure training data assets
   */
  const handleSubmit = async () => {
    if (!validateData()) return;

    setIsLoading(true);

    try {
      const result = await saveFeedback({
        videoTitle: videoTitle || 'Unknown Video',
        feedbackData: feedbackData
      });

      setSnackbarMessage(`Feedback saved successfully as ${result.filename}!`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);

      // Close modal after short delay
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Error saving feedback:', error);
      setSnackbarMessage('Failed to save feedback. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Close modal with confirmation if data has been modified
   */
  const handleClose = () => {
    // Could add dirty check here if needed
    onClose();
  };

  /**
   * Render emotion chip with appropriate color
   */
  const renderEmotionChip = (emotion) => (
    <Chip
      label={emotion}
      size="small"
      sx={{
        backgroundColor: `${getEmotionColor(emotion)}20`,
        color: getEmotionColor(emotion),
        fontWeight: 600,
        fontSize: '0.75rem',
        textTransform: 'capitalize',
      }}
    />
  );

  return (
    <>
      <StyledDialog
        open={open}
        onClose={handleClose}
        fullScreen={isMobile}
        maxWidth={false}
        aria-labelledby="feedback-dialog-title"
      >        <DialogTitle
          id="feedback-dialog-title"
          sx={{
            pb: 2,
            borderBottom: `1px solid ${customTheme.colors.border}`,
            background: `linear-gradient(90deg, ${customTheme.colors.primary.main}, ${customTheme.colors.primary.light})`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: customTheme.colors.surface.elevated,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FeedbackIcon sx={{ color: customTheme.colors.primary.main }} />
            <Typography
              variant="h6"
              component="span"
              sx={{
                fontWeight: 700,
                color: customTheme.colors.text.primary,
                background: `linear-gradient(90deg, ${customTheme.colors.primary.main}, ${customTheme.colors.primary.light})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Give Feedback for Predictions
            </Typography>
          </Box>

          <IconButton
            onClick={handleClose}
            size="small"
            sx={{
              color: customTheme.colors.text.secondary,
              '&:hover': {
                backgroundColor: customTheme.colors.primary.main + '20',
                color: customTheme.colors.primary.main,
              }
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>        <DialogContent sx={{ p: 0, backgroundColor: 'transparent' }}>
          <Box sx={{ p: 3, pb: 2 }}>
            <Typography
              variant="body2"
              sx={{
                mb: 2,
                color: customTheme.colors.text.secondary,
              }}
            >
              Review and adjust the emotion predictions below. Your feedback will be saved as training data
              to improve future predictions.
            </Typography>
            <Typography
              variant="body2"
              sx={{
                mb: 3,
                fontWeight: 500,
                color: customTheme.colors.text.primary,
              }}
            >
              Video: <strong style={{ color: customTheme.colors.primary.main }}>
                {videoTitle || 'Unknown Video'}
              </strong> |
              Total Segments: <strong style={{ color: customTheme.colors.primary.main }}>
                {isDataLoading ? '...' : feedbackData.length}
              </strong>
            </Typography>
          </Box><StyledTableContainer component={Paper} elevation={0}>
            {isDataLoading ? (              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  py: 8,
                  gap: 2
                }}
              >
                <CircularProgress
                  size={40}
                  sx={{ color: customTheme.colors.primary.main }}
                />
                <Typography
                  variant="body1"
                  sx={{ color: customTheme.colors.text.secondary }}
                >
                  Loading feedback data...
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: customTheme.colors.text.tertiary,
                    opacity: 0.7,
                  }}
                >
                  Preparing {transcriptData?.length || 0} transcript segments for review
                </Typography>
              </Box>
            ) : (
              <Table stickyHeader>
                <StyledTableHead>
                  <TableRow>
                    <TableCell sx={{ width: '15%' }}>Time Range</TableCell>
                    <TableCell sx={{ width: '35%' }}>Text</TableCell>
                    <TableCell sx={{ width: '15%' }}>Emotion</TableCell>
                    <TableCell sx={{ width: '20%' }}>Sub-Emotion</TableCell>
                    <TableCell sx={{ width: '15%' }}>Intensity</TableCell>
                  </TableRow>
                </StyledTableHead>

                <TableBody>
                  <AnimatePresence>
                    {feedbackData.map((row) => (
                    <motion.tr
                      key={row.id}
                      component={StyledTableRow}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.2, delay: row.id * 0.02 }}
                    >                      <TableCell sx={{
                        fontSize: '0.875rem',
                        fontFamily: 'monospace',
                        color: customTheme.colors.text.primary,
                      }}>
                        <Box>
                          <Typography
                            variant="caption"
                            display="block"
                            sx={{ color: customTheme.colors.text.primary }}
                          >
                            {row.start_time}
                          </Typography>
                          <Typography
                            variant="caption"
                            display="block"
                            sx={{ color: customTheme.colors.text.secondary }}
                          >
                            {row.end_time}
                          </Typography>
                        </Box>
                      </TableCell>

                      <TextCell>
                        {row.text ||
                          <em style={{ color: customTheme.colors.text.tertiary }}>
                            No text
                          </em>
                        }
                      </TextCell>
                        <TableCell>
                        <FormControl size="small" fullWidth>
                          <StyledSelect
                            value={row.emotion || 'neutral'}
                            onChange={(e) => handleValueChange(row.id, 'emotion', e.target.value)}
                            displayEmpty
                            MenuProps={darkMenuProps}
                          >
                            {EMOTION_OPTIONS.map(option => (
                              <MenuItem key={option} value={option}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  {renderEmotionChip(option)}
                                </Box>
                              </MenuItem>
                            ))}
                          </StyledSelect>
                        </FormControl>
                      </TableCell>

                      <TableCell>
                        <FormControl size="small" fullWidth>
                          <StyledSelect
                            value={row.sub_emotion || 'neutral'}
                            onChange={(e) => handleValueChange(row.id, 'sub_emotion', e.target.value)}
                            displayEmpty
                            MenuProps={darkMenuProps}
                          >
                            {SUB_EMOTION_OPTIONS.map(option => (
                              <MenuItem key={option} value={option} sx={{ textTransform: 'capitalize' }}>
                                {option}
                              </MenuItem>
                            ))}
                          </StyledSelect>
                        </FormControl>
                      </TableCell>

                      <TableCell>
                        <FormControl size="small" fullWidth>
                          <StyledSelect
                            value={row.intensity || 'mild'}
                            onChange={(e) => handleValueChange(row.id, 'intensity', e.target.value)}
                            displayEmpty
                            MenuProps={darkMenuProps}
                          >
                            {INTENSITY_OPTIONS.map(option => (
                              <MenuItem key={option} value={option} sx={{ textTransform: 'capitalize' }}>
                                {option}
                              </MenuItem>
                            ))}
                          </StyledSelect>
                        </FormControl>
                      </TableCell>
                    </motion.tr>                  ))}
                </AnimatePresence>
              </TableBody>
            </Table>
            )}
          </StyledTableContainer>
        </DialogContent>        <DialogActions sx={{
          p: 3,
          borderTop: `1px solid ${customTheme.colors.border}`,
          backgroundColor: customTheme.colors.surface.elevated,
        }}>
          <Button
            onClick={handleClose}
            variant="outlined"
            sx={{
              textTransform: 'none',
              borderRadius: 10,
              px: 3,
              color: customTheme.colors.text.secondary,
              borderColor: customTheme.colors.border,
              '&:hover': {
                borderColor: customTheme.colors.borderHover,
                backgroundColor: customTheme.colors.primary.main + '10',
                color: customTheme.colors.text.primary,
              }
            }}
          >
            Cancel
          </Button>

          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={isLoading}
            startIcon={isLoading ?
              <CircularProgress size={16} sx={{ color: customTheme.colors.text.primary }} /> :
              <SaveIcon />
            }
            sx={{
              textTransform: 'none',
              borderRadius: 10,
              px: 4,
              background: `linear-gradient(90deg, ${customTheme.colors.primary.main}, ${customTheme.colors.primary.light})`,
              color: customTheme.colors.text.primary,
              '&:hover': {
                background: `linear-gradient(90deg, ${customTheme.colors.primary.dark}, ${customTheme.colors.primary.main})`,
              },
              '&:disabled': {
                background: customTheme.colors.surface.glass,
                color: customTheme.colors.text.disabled,
              }
            }}
          >
            {isLoading ? 'Saving...' : 'Save Feedback'}
          </Button>
        </DialogActions>
      </StyledDialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity={snackbarSeverity}
          sx={{ borderRadius: 2 }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default FeedbackModal;
