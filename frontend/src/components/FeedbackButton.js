import React from 'react';
import { Button, Box, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
import FeedbackIcon from '@mui/icons-material/Feedback';
import EditNoteIcon from '@mui/icons-material/EditNote';
import { motion } from 'framer-motion';

// Styled feedback button with modern design
const StyledFeedbackButton = styled(motion.div)(({ theme }) => ({
  width: '100%',
  marginTop: theme.spacing(2),
}));

const GradientButton = styled(Button)(({ theme }) => ({
  width: '100%',
  padding: theme.spacing(1.5, 3),
  borderRadius: 16,
  textTransform: 'none',
  fontSize: '0.95rem',
  fontWeight: 600,
  background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%)',
  color: 'white',
  border: 'none',
  boxShadow: '0 4px 15px rgba(99, 102, 241, 0.3)',
  position: 'relative',
  overflow: 'hidden',

  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: '-100%',
    width: '100%',
    height: '100%',
    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
    transition: 'left 0.5s ease',
  },

  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: '0 8px 25px rgba(99, 102, 241, 0.4)',
    background: 'linear-gradient(135deg, #5A5AC7 0%, #7B4AC9 50%, #D946EF 100%)',

    '&::before': {
      left: '100%',
    },
  },

  '&:active': {
    transform: 'translateY(-1px)',
  },

  '&:disabled': {
    background: 'rgba(0, 0, 0, 0.12)',
    color: 'rgba(0, 0, 0, 0.26)',
    boxShadow: 'none',
    transform: 'none',
  },
}));

/**
 * FeedbackButton Component
 *
 * A beautifully designed button to trigger the feedback modal.
 * Features hover animations and gradient styling consistent with the app theme.
 */
const FeedbackButton = ({ onClick, disabled = false, transcriptLength = 0 }) => {
  const buttonText = transcriptLength > 0
    ? `Give Feedback (${transcriptLength} segments)`
    : 'Give Feedback for Predictions';

  const tooltipText = disabled
    ? 'No prediction data available'
    : 'Help improve predictions by providing feedback on emotion classifications';

  return (
    <StyledFeedbackButton
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <Tooltip
        title={tooltipText}
        placement="top"
        arrow
        enterDelay={500}
      >
        <Box>
          <GradientButton
            onClick={onClick}
            disabled={disabled}
            startIcon={<EditNoteIcon />}
            endIcon={<FeedbackIcon />}
            fullWidth
          >
            {buttonText}
          </GradientButton>
        </Box>
      </Tooltip>
    </StyledFeedbackButton>
  );
};

export default FeedbackButton;
