import React, { useEffect, useRef, useState } from 'react';
import { Box, Typography, Paper, Chip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { motion, AnimatePresence } from 'framer-motion';
import { getEmotionColor } from '../utils';

const TranscriptContainer = styled(Paper)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
  borderRadius: theme.shape.borderRadius * 2,
  backgroundColor: 'rgba(255, 255, 255, 0.7)',
  backdropFilter: 'blur(8px)',
  border: '1px solid rgba(255, 255, 255, 0.9)',
  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04), 0 2px 10px rgba(0, 0, 0, 0.02)',
}));

const TranscriptHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
}));

const TranscriptList = styled(Box)(({ theme }) => ({
  flex: 1,
  overflowY: 'auto',
  padding: theme.spacing(2),
  '&::-webkit-scrollbar': {
    width: '8px',
  },
  '&::-webkit-scrollbar-track': {
    background: 'rgba(0, 0, 0, 0.03)',
    borderRadius: '4px',
  },
  '&::-webkit-scrollbar-thumb': {
    background: 'rgba(0, 0, 0, 0.12)',
    borderRadius: '4px',
    '&:hover': {
      background: 'rgba(0, 0, 0, 0.18)',
    },
  },
}));

const TranscriptItem = styled(Box)(({ theme, isActive, emotion }) => {
  const emotionColor = getEmotionColor(emotion);

  return {
    padding: theme.spacing(1.5, 2),
    marginBottom: theme.spacing(1.5),
    borderRadius: '12px',
    position: 'relative',
    cursor: 'pointer',
    backgroundColor: isActive
      ? `${emotionColor}15`
      : 'rgba(249, 250, 251, 0.8)',
    border: isActive
      ? `1px solid ${emotionColor}40`
      : '1px solid rgba(0,0,0,0.06)',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    overflow: 'hidden',
    '&:hover': {
      backgroundColor: isActive
        ? `${emotionColor}25`
        : 'rgba(249, 250, 251, 0.95)',
      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
      transform: 'translateY(-2px)',
    },
    '&::before': isActive ? {
      content: '""',
      position: 'absolute',
      left: 0,
      top: 0,
      height: '100%',
      width: '4px',
      backgroundColor: emotionColor,
      borderRadius: '4px 0 0 4px',
    } : {},
  };
});

const EmotionChip = styled(Chip)(({ theme, emotion }) => {
  const emotionColor = getEmotionColor(emotion);

  return {
    marginBottom: theme.spacing(1),
    backgroundColor: `${emotionColor}15`,
    color: emotionColor,
    borderColor: `${emotionColor}30`,
    fontWeight: 600,
    fontSize: '0.75rem',
    height: '26px',
    '& .MuiChip-label': {
      paddingLeft: 10,
      paddingRight: 10,
    },
  };
});

const TimeChip = styled(Box)(({ theme, isActive, emotion }) => {
  const emotionColor = getEmotionColor(emotion);

  return {
    position: 'absolute',
    right: theme.spacing(2),
    top: theme.spacing(1.5),
    color: isActive ? emotionColor : 'rgba(0, 0, 0, 0.5)',
    fontSize: '0.75rem',
    fontWeight: 600,
    padding: theme.spacing(0.5, 1),
    borderRadius: '4px',
    backgroundColor: isActive ? `${emotionColor}10` : 'rgba(0, 0, 0, 0.04)',
    border: isActive ? `1px solid ${emotionColor}20` : '1px solid transparent',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  };
});

const formatTimestamp = (seconds) => {
  if (seconds === undefined || seconds === null || isNaN(seconds)) {
    return "0:00";
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

const Transcript = ({ data, currentTime, onSentenceClick }) => {
  const transcriptRef = useRef(null);
  const [activeId, setActiveId] = useState(null);

  // Find the active sentence based on currentTime
  useEffect(() => {
    if (!data || !data.length) return;

    // Find the sentence that corresponds to the current time
    const activeSentence = data.find((sentence, i) => {
      const nextSentence = data[i + 1];
      const sentenceStart = typeof sentence.start === 'number' ? sentence.start :
                            typeof sentence.start_time === 'number' ? sentence.start_time : 0;
      const nextStart = nextSentence ?
                        (typeof nextSentence.start === 'number' ? nextSentence.start :
                         typeof nextSentence.start_time === 'number' ? nextSentence.start_time : Infinity) :
                        Infinity;

      return currentTime >= sentenceStart && currentTime < nextStart;
    });

    if (activeSentence) {
      const id = activeSentence.id || `sentence-${data.indexOf(activeSentence)}`;
      setActiveId(id);

      // Scroll to the active sentence - now positioned at the top
      if (transcriptRef.current) {
        const activeElement = transcriptRef.current.querySelector(`[data-id="${id}"]`);
        if (activeElement) {
          // Added a small delay to ensure smooth scrolling after state update
          setTimeout(() => {
            activeElement.scrollIntoView({
              behavior: 'smooth',
              block: 'start'  // Changed from 'center' to 'start' to position at top
            });
          }, 100);
        }
      }
    }
  }, [data, currentTime]);

  if (!data || !data.length) {
    return (
      <TranscriptContainer>
        <TranscriptHeader>
          <Typography variant="h6" fontWeight={600}>Transcript</Typography>
        </TranscriptHeader>
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 3,
            textAlign: 'center'
          }}
        >
          <Typography color="text.secondary">No transcript available yet</Typography>
        </Box>
      </TranscriptContainer>
    );
  }

  return (
    <TranscriptContainer>
      <TranscriptHeader>
        <Typography variant="h6" fontWeight={600} sx={{
          background: 'linear-gradient(90deg, #6366F1, #8B5CF6)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}>
          Transcript
          <Chip
            label={`${data?.length || 0} sentences`}
            size="small"
            sx={{
              ml: 1,
              height: 22,
              fontSize: '0.75rem',
              fontWeight: 600,
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              color: '#6366F1',
            }}
          />
        </Typography>
      </TranscriptHeader>
      <TranscriptList ref={transcriptRef}>
        <AnimatePresence>
          {data && data.map((item, index) => {
            const id = item.id || `sentence-${index}`;
            const isActive = id === activeId;
            const emotion = item.emotion || 'neutral';
            const text = item.text || item.sentence || '';
            const startTime = typeof item.start === 'number' ? item.start :
                              typeof item.start_time === 'number' ? item.start_time : 0;

            return (
              <motion.div
                key={id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.01 }}
                data-id={id}
              >
                <TranscriptItem
                  isActive={isActive}
                  emotion={emotion}
                  onClick={() => onSentenceClick(startTime)}
                >
                  <EmotionChip
                    emotion={emotion}
                    label={emotion}
                    size="small"
                    variant="outlined"
                  />
                  <TimeChip isActive={isActive} emotion={emotion}>
                    {formatTimestamp(startTime)}
                  </TimeChip>
                  <Typography variant="body2" sx={{ pt: 0.5, fontWeight: isActive ? 500 : 400 }}>
                    {text}
                  </Typography>
                </TranscriptItem>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </TranscriptList>
    </TranscriptContainer>
  );
};

export default Transcript;
