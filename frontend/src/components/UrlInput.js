import React, { useState } from 'react';
import { TextField, Button, Paper, Box, CircularProgress, InputAdornment, Typography } from '@mui/material';
import { styled } from '@mui/material/styles';
import YouTubeIcon from '@mui/icons-material/YouTube';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import { motion } from 'framer-motion';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3.5),
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  borderRadius: 20,
  boxShadow: '0 10px 40px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
  position: 'relative',
  overflow: 'hidden',
  border: '1px solid rgba(255, 255, 255, 0.8)',
  backgroundColor: 'rgba(255, 255, 255, 0.7)',
  backdropFilter: 'blur(15px)',
  [theme.breakpoints.up('md')]: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '3px',
    background: 'linear-gradient(90deg, #6366F1, #EC4899)',
    zIndex: 1,
  }
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: 14,
    background: 'rgba(255, 255, 255, 0.6)',
    transition: 'all 0.35s ease',
    fontWeight: 500,
    '&:hover': {
      background: 'rgba(255, 255, 255, 0.9)',
      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
    },
    '&.Mui-focused': {
      background: 'rgba(255, 255, 255, 1)',
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    }
  },
  '& .MuiInputLabel-root': {
    fontWeight: 500,
    fontSize: '0.95rem',
  },
  '& .MuiInputLabel-root.Mui-focused': {
    color: theme.palette.primary.main,
  }
}));

const StyledButton = styled(Button)(({ theme }) => ({
  borderRadius: 14,
  boxShadow: '0 8px 24px rgba(99,102,241,0.25)',
  textTransform: 'none',
  fontWeight: 600,
  fontSize: '1rem',
  padding: theme.spacing(1.5, 3.5),
  background: 'linear-gradient(90deg, #6366F1, #8B5CF6)',
  transition: 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
  letterSpacing: '0.2px',
  fontFamily: 'Manrope, sans-serif',
  '&:hover': {
    background: 'linear-gradient(90deg, #4F46E5, #7C3AED)',
    boxShadow: '0 10px 30px rgba(99,102,241,0.35)',
    transform: 'translateY(-2px)',
  },
  '&.Mui-disabled': {
    background: 'linear-gradient(90deg, #6366F1CC, #8B5CF6CC)',
  }
}));

const UrlInput = ({ onSubmit, isLoading }) => {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  const validateYoutubeUrl = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$/;
    return youtubeRegex.test(url);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    if (!validateYoutubeUrl(url)) {
      setError('Please enter a valid YouTube URL');
      return;
    }

    setError('');
    onSubmit(url);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.23, 1, 0.32, 1] }}
    >
      <StyledPaper elevation={0}>
        <Box
          component="form"
          onSubmit={handleSubmit}
          sx={{
            width: '100%',
            display: 'flex',
            flexDirection: { xs: 'column', md: 'row' },
            gap: 2.5,
            position: 'relative',
          }}
        >
          <Box sx={{ position: 'relative', width: '100%' }}>
            <StyledTextField
              fullWidth
              label="Enter YouTube Video URL"
              variant="outlined"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              error={!!error}
              helperText={error}
              placeholder="https://www.youtube.com/watch?v=..."
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <YouTubeIcon
                      color="error"
                      sx={{
                        fontSize: '1.5rem',
                        filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.1))'
                      }}
                    />
                  </InputAdornment>
                ),
                sx: {
                  height: 60,
                  pr: 1,
                  typography: {
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 500
                  }
                }
              }}
            />
            {url && !error && !isLoading && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{
                  type: "spring",
                  stiffness: 600,
                  damping: 20
                }}
                style={{
                  position: 'absolute',
                  top: 25,
                  right: 15,
                  width: 12,
                  height: 12,
                  background: '#10B981',
                  borderRadius: '50%',
                  boxShadow: '0 0 10px rgba(16, 185, 129, 0.5)',
                }}
              />
            )}
          </Box>
          <motion.div
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
          >
            <StyledButton
              type="submit"
              variant="contained"
              disabled={isLoading}
              sx={{
                minWidth: { xs: '100%', md: '220px' },
                height: '60px',
                whiteSpace: 'nowrap',
              }}
              startIcon={isLoading ? null :
                <AnalyticsIcon sx={{
                  fontSize: '1.3rem',
                  filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.1))'
                }} />
              }
            >
              {isLoading ? (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CircularProgress size={24} color="inherit" sx={{ mr: 1.5 }} />
                  <Typography variant="body1" fontFamily="Manrope, sans-serif" fontWeight={600}>
                    Analyzing...
                  </Typography>
                </Box>
              ) : (
                'Analyze Emotions'
              )}
            </StyledButton>
          </motion.div>
        </Box>
        {!isLoading && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              position: 'absolute',
              bottom: 8,
              right: 20,
              fontSize: '0.75rem',
              opacity: 0.7,
              fontStyle: 'italic'
            }}
          >
            Processing takes ~30 seconds
          </Typography>
        )}
      </StyledPaper>
    </motion.div>
  );
};

export default UrlInput;
