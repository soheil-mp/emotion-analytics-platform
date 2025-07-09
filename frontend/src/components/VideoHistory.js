import React from 'react';
import {
  Avatar,
  Typography,
  Box,
  IconButton
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { motion } from 'framer-motion';
import CloseIcon from '@mui/icons-material/Close';
import { useVideo } from '../VideoContext';
import { getEmotionColor } from '../utils';
import HistoryIcon from '@mui/icons-material/History';
import SentimentSatisfiedAltIcon from '@mui/icons-material/SentimentSatisfiedAlt';


const DeleteButton = styled(IconButton)(({ theme }) => ({
  position: 'absolute',
  top: 8,
  right: 8,
  opacity: 0.6, // Made more visible by default
  transition: 'all 0.2s ease',
  padding: '6px',
  background: 'rgba(239, 68, 68, 0.08)',
  borderRadius: '6px',
  zIndex: 10,
  border: '1px solid rgba(239, 68, 68, 0.15)',
  '&:hover': {
    opacity: 1,
    background: 'rgba(239, 68, 68, 0.15)',
    color: '#EF4444',
    transform: 'scale(1.05)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  '& .MuiSvgIcon-root': {
    fontSize: '1.1rem',
    color: '#EF4444',
  },
}));

// Enhanced styled components
const HistoryItemContainer = styled(motion.div)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  borderRadius: '12px',
  overflow: 'hidden',
  cursor: 'pointer',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  border: '1px solid rgba(0, 0, 0, 0.06)',
  backgroundColor: 'rgba(255, 255, 255, 0.7)',
  position: 'relative',
  '&:hover': {
    transform: 'translateY(-3px)',
    boxShadow: '0 10px 20px rgba(0, 0, 0, 0.08), 0 5px 10px rgba(0, 0, 0, 0.04)',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    '& .delete-icon': {
      opacity: 1,
      transform: 'scale(1.1)',
    },
  },
}));

const EmotionAvatar = styled(Avatar)(({ theme, emotion }) => {
  const emotionColor = getEmotionColor(emotion || 'neutral');

  return {
    backgroundColor: `${emotionColor}25`,
    border: `1px solid ${emotionColor}50`,
    color: emotionColor,
    '& svg': {
      fontSize: '1.2rem',
    },
  };
});

const VideoTitle = styled(Typography)(({ theme }) => ({
  fontWeight: 600,
  fontSize: '0.95rem',
  lineHeight: 1.3,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  display: '-webkit-box',
  WebkitLineClamp: 2,
  WebkitBoxOrient: 'vertical',
}));

const DateText = styled(Typography)(({ theme }) => ({
  fontSize: '0.75rem',
  color: theme.palette.text.secondary,
  fontWeight: 500,
}));

const EmotionBar = styled(Box)(({ theme }) => ({
  height: '5px',
  borderRadius: '3px',
  marginTop: theme.spacing(1),
  overflow: 'hidden',
  background: 'rgba(229, 231, 235, 0.5)',
}));

const EmotionBarItem = styled(Box)(({ width, color }) => ({
  height: '100%',
  backgroundColor: color,
  display: 'inline-block',
}));

const EmotionalIcon = ({ emotion }) => {
  switch(emotion) {
    case 'happiness':
      return <SentimentSatisfiedAltIcon />;
    default:
      return <HistoryIcon />;
  }
};

// Helper function to format date
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const currentDate = new Date();
  const isToday = date.toDateString() === currentDate.toDateString();

  // Format: Today or MM-DD-YY
  if (isToday) {
    return 'Today';
  } else {
    return date.toLocaleDateString('en-US', {
      month: '2-digit',
      day: '2-digit',
      year: '2-digit'
    });
  }
};

// Function to create color bar from emotional data
const createEmotionBar = (videoData) => {
  // Example emotions and their proportion in the video
  // In a real implementation, this would come from the videoData
  const emotions = [
    { emotion: 'happiness', proportion: 0.3 },
    { emotion: 'sadness', proportion: 0.2 },
    { emotion: 'anger', proportion: 0.1 },
    { emotion: 'surprise', proportion: 0.15 },
    { emotion: 'neutral', proportion: 0.25 },
  ];

  return emotions.map((item, index) => (
    <EmotionBarItem
      key={index}
      width={`${item.proportion * 100}%`}
      color={getEmotionColor(item.emotion)}
      sx={{ width: `${item.proportion * 100}%` }}
    />
  ));
};

// Get the dominant emotion from a video
const getDominantEmotion = (video) => {
  return video.dominant_emotion || 'neutral';
};

const VideoHistory = ({ videos = [], onVideoSelect }) => {
  const { removeFromHistory } = useVideo();

  // Maintain local storage for persistence between sessions
  React.useEffect(() => {
    if (videos.length > 0) {
      try {
        localStorage.setItem('videoAnalysisHistory', JSON.stringify(videos));
      } catch (error) {
        console.error("Failed to save video history to localStorage:", error);
      }
    }  }, [videos]);

  // Handle delete with stopPropagation to prevent selection
  const handleDelete = (e, videoId) => {
    e.stopPropagation();
    e.preventDefault();

    // Add some visual feedback
    const button = e.currentTarget;
    button.style.transform = 'scale(0.9)';

    setTimeout(() => {
      removeFromHistory(videoId);
    }, 150); // Small delay for visual feedback
  };

  if (!videos.length) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          py: 4,
          textAlign: 'center',
        }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Box sx={{
            width: 70,
            height: 70,
            borderRadius: '50%',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 2,
            mx: 'auto',  // Added margin auto for horizontal centering
          }}>
            <HistoryIcon sx={{ fontSize: '2rem', color: '#6366F1', opacity: 0.6 }} />
          </Box>

          <Typography variant="body1" color="textSecondary" sx={{ fontWeight: 500 }}>
            No Video History
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, maxWidth: 220 }}>
            Analyzed videos will appear here
          </Typography>
        </motion.div>
      </Box>
    );
  }

  const container = {
    hidden: { opacity: 1 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
    >
      {videos.map((video) => {
        const dominantEmotion = getDominantEmotion(video);

        return (
          <motion.div key={video.id} variants={item}>
            <HistoryItemContainer onClick={() => onVideoSelect(video)}>
              <Box sx={{ p: 2, position: 'relative' }}>
                <DeleteButton
                  className="delete-icon"
                  onClick={(e) => handleDelete(e, video.id)}
                  aria-label={`Remove ${video.title} from history`}
                  size="small"
                  title="Remove from history"
                >
                  <CloseIcon fontSize="inherit" />
                </DeleteButton>

                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <EmotionAvatar emotion={dominantEmotion} variant="rounded">
                    <EmotionalIcon emotion={dominantEmotion} />
                  </EmotionAvatar>
                  <Box sx={{ ml: 1.5 }}>
                    <VideoTitle>{video.title}</VideoTitle>
                    <DateText>{formatDate(video.date)}</DateText>
                  </Box>
                </Box>

                <EmotionBar>
                  {createEmotionBar(video)}
                </EmotionBar>
              </Box>
            </HistoryItemContainer>
          </motion.div>
        );
      })}
    </motion.div>
  );
};

export default VideoHistory;
