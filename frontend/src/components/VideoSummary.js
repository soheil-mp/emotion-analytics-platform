import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { styled } from '@mui/material/styles';
import { motion, AnimatePresence } from 'framer-motion';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import geminiSummaryService from '../services/geminiSummaryService';
// Import debug utils for development
import '../utils/geminiDebug';

const SummaryContainer = styled(Box)(({ theme }) => ({
  width: '100%',
  height: '100%', // Take full available height from parent
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
  overflow: 'hidden', // Prevent container from growing
}));

const SummaryContent = styled(Paper)(({ theme }) => ({
  width: '100%',
  height: '100%', // Take full height of container
  padding: theme.spacing(3, 4.5), // Consistent horizontal padding
  paddingTop: theme.spacing(3), // Fixed top padding
  paddingBottom: theme.spacing(3), // Fixed bottom padding
  background: `
    linear-gradient(145deg,
      rgba(15, 23, 42, 0.95) 0%,
      rgba(30, 41, 59, 0.85) 25%,
      rgba(15, 23, 42, 0.9) 50%,
      rgba(20, 25, 45, 0.95) 75%,
      rgba(15, 23, 42, 0.98) 100%
    )
  `,
  backdropFilter: 'blur(32px) saturate(140%) brightness(1.1)',
  border: '1px solid rgba(99, 102, 241, 0.25)',
  borderRadius: '24px',
  position: 'relative',
  overflow: 'hidden',
  transition: 'all 0.5s cubic-bezier(0.23, 1, 0.32, 1)',

  // Fixed height with scrollable content
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'flex-start', // Align content to top
  alignItems: 'stretch',

  // Enhanced Visual Effects with Multiple Layers
  boxShadow: `
    0 12px 40px rgba(0, 0, 0, 0.4),
    0 6px 20px rgba(99, 102, 241, 0.15),
    0 2px 8px rgba(139, 92, 246, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 -1px 0 rgba(99, 102, 241, 0.1)
  `,

  // Animated Multi-Color Border Effect
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: '-100%',
    width: '100%',
    height: '3px',
    background: `linear-gradient(90deg,
      transparent 0%,
      rgba(99, 102, 241, 0.8) 20%,
      rgba(139, 92, 246, 1) 40%,
      rgba(236, 72, 153, 0.9) 60%,
      rgba(251, 146, 60, 0.8) 80%,
      transparent 100%
    )`,
    animation: 'shimmer 5s ease-in-out infinite',
    '@keyframes shimmer': {
      '0%': {
        left: '-100%',
        opacity: 0,
        transform: 'scaleX(0.5)',
      },
      '25%': {
        opacity: 0.7,
        transform: 'scaleX(1)',
      },
      '50%': {
        opacity: 1,
        transform: 'scaleX(1.2)',
      },
      '75%': {
        opacity: 0.7,
        transform: 'scaleX(1)',
      },
      '100%': {
        left: '100%',
        opacity: 0,
        transform: 'scaleX(0.5)',
      }
    }
  },

  // Floating Orb Background Effects with Additional Orb
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '10%',
    right: '15%',
    width: '120px',
    height: '120px',
    background: `
      radial-gradient(circle at 30% 30%,
        rgba(99, 102, 241, 0.15) 0%,
        rgba(139, 92, 246, 0.1) 30%,
        rgba(236, 72, 153, 0.08) 60%,
        transparent 80%
      )
    `,
    borderRadius: '50%',
    filter: 'blur(20px)',
    animation: 'float 8s ease-in-out infinite',
    '@keyframes float': {
      '0%, 100%': {
        transform: 'translateY(0px) translateX(0px) scale(1)',
        opacity: 0.3,
      },
      '25%': {
        transform: 'translateY(-15px) translateX(10px) scale(1.1)',
        opacity: 0.5,
      },
      '50%': {
        transform: 'translateY(-10px) translateX(-15px) scale(0.9)',
        opacity: 0.7,
      },
      '75%': {
        transform: 'translateY(5px) translateX(5px) scale(1.05)',
        opacity: 0.4,
      },
    }
  },

  // Additional Floating Orb (left side)
  '& .secondary-orb': {
    position: 'absolute',
    bottom: '20%',
    left: '10%',
    width: '80px',
    height: '80px',
    background: `
      radial-gradient(circle at 70% 70%,
        rgba(168, 85, 247, 0.12) 0%,
        rgba(251, 146, 60, 0.08) 40%,
        rgba(99, 102, 241, 0.06) 70%,
        transparent 85%
      )
    `,
    borderRadius: '50%',
    filter: 'blur(15px)',
    animation: 'floatSecondary 10s ease-in-out infinite reverse',
    '@keyframes floatSecondary': {
      '0%, 100%': {
        transform: 'translateY(0px) translateX(0px) scale(0.8)',
        opacity: 0.2,
      },
      '33%': {
        transform: 'translateY(12px) translateX(-8px) scale(1.2)',
        opacity: 0.4,
      },
      '66%': {
        transform: 'translateY(-8px) translateX(12px) scale(0.9)',
        opacity: 0.6,
      },
    }
  },

  // Premium Hover Effects
  '&:hover': {
    transform: 'translateY(-4px) scale(1.008) rotateX(2deg)',
    border: '1px solid rgba(99, 102, 241, 0.45)',
    boxShadow: `
      0 20px 60px rgba(0, 0, 0, 0.5),
      0 12px 32px rgba(99, 102, 241, 0.25),
      0 6px 16px rgba(139, 92, 246, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.12),
      inset 0 -1px 0 rgba(99, 102, 241, 0.15)
    `,
    backdropFilter: 'blur(36px) saturate(150%) brightness(1.15)',

    '&::before': {
      height: '4px',
      animationDuration: '3s',
    },

    '&::after': {
      animationDuration: '6s',
      transform: 'translateY(-20px) scale(1.2)',
      opacity: 0.8,
    }
  },

  // Responsive Design
  '@media (max-width: 768px)': {
    padding: theme.spacing(2.5, 3),
    borderRadius: '20px',
    fontSize: '0.95rem',

    '&::after': {
      width: '80px',
      height: '80px',
    }
  },

  // Additional responsive breakpoints for text
  '@media (max-width: 480px)': {
    padding: theme.spacing(2, 2.5),
    fontSize: '0.9rem',
    lineHeight: 1.7,
  },
}));

// Scrollable Text Container for handling overflow
const ScrollableTextContainer = styled(Box)(({ theme }) => ({
  flex: 1,
  overflow: 'auto',
  paddingRight: theme.spacing(1),

  // Custom Scrollbar Styling
  '&::-webkit-scrollbar': {
    width: '6px',
    backgroundColor: 'transparent',
  },
  '&::-webkit-scrollbar-track': {
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
    borderRadius: '3px',
    margin: '8px 0',
  },
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: 'rgba(99, 102, 241, 0.4)',
    borderRadius: '3px',
    transition: 'background-color 0.3s ease',

    '&:hover': {
      backgroundColor: 'rgba(99, 102, 241, 0.6)',
    }
  },

  // Firefox scrollbar styling
  scrollbarWidth: 'thin',
  scrollbarColor: 'rgba(99, 102, 241, 0.4) rgba(99, 102, 241, 0.1)',

  // Smooth scrolling
  scrollBehavior: 'smooth',
}));

const SummaryText = styled(Typography)(({ theme }) => ({
  // Premium Typography System
  color: 'rgba(248, 250, 252, 0.98)',
  fontSize: '1.05rem',
  lineHeight: 1.85,
  fontWeight: 400,
  letterSpacing: '0.015em',
  wordSpacing: '0.08em',
  textAlign: 'left',
  position: 'relative',
  zIndex: 1,

  // Elite Font Stack - Modern & Readable
  fontFamily: '"SF Pro Display", "Inter", "Segoe UI Variable", "system-ui", "-apple-system", "BlinkMacSystemFont", sans-serif',
  fontFeatureSettings: '"liga" 1, "kern" 1, "calt" 1',
  textRendering: 'optimizeLegibility',
  WebkitFontSmoothing: 'antialiased',
  MozOsxFontSmoothing: 'grayscale',

  // Sophisticated Visual Effects
  textShadow: `
    0 1px 3px rgba(0, 0, 0, 0.4),
    0 2px 8px rgba(99, 102, 241, 0.08)
  `,

  // Natural text flow with consistent spacing
  margin: 0,
  padding: 0,
  width: '100%',

  // Text wrapping and overflow handling
  wordWrap: 'break-word',
  overflowWrap: 'break-word',
  hyphens: 'auto',
  WebkitHyphens: 'auto',

  // Elegant Selection & Interaction
  '&::selection': {
    backgroundColor: 'rgba(99, 102, 241, 0.25)',
    color: 'rgba(255, 255, 255, 0.98)',
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.5)',
  },

  // Subtle Animation on Appearance
  animation: 'textFadeIn 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
  '@keyframes textFadeIn': {
    '0%': {
      opacity: 0,
      transform: 'translateY(8px) scale(0.98)',
      filter: 'blur(2px)',
    },
    '100%': {
      opacity: 1,
      transform: 'translateY(0) scale(1)',
      filter: 'blur(0)',
    },
  },

  // Responsive Typography
  '@media (max-width: 768px)': {
    fontSize: '0.95rem',
    lineHeight: 1.75,
    minHeight: '2.2em',
  },

  '@media (max-width: 480px)': {
    fontSize: '0.9rem',
    lineHeight: 1.7,
    minHeight: '2em',
    letterSpacing: '0.01em',
  },

  // Premium Focus States
  '&:focus': {
    outline: '2px solid rgba(99, 102, 241, 0.4)',
    outlineOffset: '4px',
    borderRadius: '4px',
  },
}));

// Enhanced Pulse Effect Component
const PulseEffect = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '200px',
  height: '200px',
  borderRadius: '50%',
  background: `
    radial-gradient(circle,
      rgba(99, 102, 241, 0.1) 0%,
      rgba(139, 92, 246, 0.08) 30%,
      rgba(236, 72, 153, 0.06) 60%,
      transparent 80%
    )
  `,
  animation: 'megaPulse 4s ease-in-out infinite',
  zIndex: -1,

  '@keyframes megaPulse': {
    '0%, 100%': {
      transform: 'translate(-50%, -50%) scale(0.8)',
      opacity: 0.2,
      filter: 'blur(8px)',
    },
    '25%': {
      transform: 'translate(-50%, -50%) scale(1.1)',
      opacity: 0.5,
      filter: 'blur(4px)',
    },
    '50%': {
      transform: 'translate(-50%, -50%) scale(1.3)',
      opacity: 0.8,
      filter: 'blur(2px)',
    },
    '75%': {
      transform: 'translate(-50%, -50%) scale(1.1)',
      opacity: 0.4,
      filter: 'blur(6px)',
    },
  },

  '&::before': {
    content: '""',
    position: 'absolute',
    top: '20%',
    left: '20%',
    right: '20%',
    bottom: '20%',
    borderRadius: '50%',
    background: `
      radial-gradient(circle,
        rgba(168, 85, 247, 0.15) 0%,
        rgba(251, 146, 60, 0.1) 50%,
        transparent 70%
      )
    `,
    animation: 'innerPulse 3s ease-in-out infinite reverse',
    '@keyframes innerPulse': {
      '0%, 100%': {
        transform: 'scale(0.5)',
        opacity: 0.3,
      },
      '50%': {
        transform: 'scale(1.2)',
        opacity: 0.7,
      },
    }
  },
}));

const LoadingContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%', // Take full height of parent container
  width: '100%',
  gap: theme.spacing(3.5),
  color: 'rgba(248, 250, 252, 0.85)',
  padding: theme.spacing(2, 0), // Vertical padding only

  // Enhanced Spacing & Layout
  position: 'relative',

  // Typography Enhancement
  '& .MuiTypography-root': {
    fontFamily: '"SF Pro Display", "Inter", "Segoe UI Variable", sans-serif',
    textAlign: 'center',
    letterSpacing: '0.02em',
  },
}));

const ErrorContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%', // Take full height of parent container
  width: '100%',
  gap: theme.spacing(2.5),
  color: 'rgba(239, 68, 68, 0.85)',
  textAlign: 'center',
  padding: theme.spacing(2, 0), // Vertical padding only

  // Enhanced Spacing & Layout
  position: 'relative',

  // Typography Enhancement
  '& .MuiTypography-root': {
    fontFamily: '"SF Pro Display", "Inter", "Segoe UI Variable", sans-serif',
    letterSpacing: '0.01em',
  },
}));

const GradientIcon = styled(Box)(({ theme }) => ({
  background: `linear-gradient(135deg,
    #6366f1 0%,
    #8b5cf6 25%,
    #a855f7 50%,
    #ec4899 75%,
    #f59e0b 100%
  )`,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: theme.spacing(1.5),
  position: 'relative',

  // Multiple Layer Visual Effects
  '&::before': {
    content: '""',
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '180%',
    height: '180%',
    background: `
      conic-gradient(from 0deg,
        rgba(99, 102, 241, 0.3) 0deg,
        rgba(139, 92, 246, 0.4) 72deg,
        rgba(168, 85, 247, 0.35) 144deg,
        rgba(236, 72, 153, 0.4) 216deg,
        rgba(251, 146, 60, 0.35) 288deg,
        rgba(99, 102, 241, 0.3) 360deg
      )
    `,
    borderRadius: '50%',
    zIndex: -2,
    animation: 'rotateGlow 8s linear infinite',
    filter: 'blur(8px)',
    '@keyframes rotateGlow': {
      '0%': {
        transform: 'translate(-50%, -50%) rotate(0deg) scale(0.8)',
        opacity: 0.3,
      },
      '25%': {
        opacity: 0.6,
        transform: 'translate(-50%, -50%) rotate(90deg) scale(1.1)',
      },
      '50%': {
        transform: 'translate(-50%, -50%) rotate(180deg) scale(0.9)',
        opacity: 0.8,
      },
      '75%': {
        opacity: 0.5,
        transform: 'translate(-50%, -50%) rotate(270deg) scale(1.2)',
      },
      '100%': {
        transform: 'translate(-50%, -50%) rotate(360deg) scale(0.8)',
        opacity: 0.3,
      },
    },
  },

  // Enhanced Inner Glow Effect
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '140%',
    height: '140%',
    background: `radial-gradient(circle,
      rgba(99, 102, 241, 0.25) 0%,
      rgba(139, 92, 246, 0.2) 30%,
      rgba(168, 85, 247, 0.15) 50%,
      rgba(236, 72, 153, 0.2) 70%,
      transparent 90%
    )`,
    borderRadius: '50%',
    zIndex: -1,
    animation: 'iconGlow 3s ease-in-out infinite alternate',
    '@keyframes iconGlow': {
      '0%': {
        opacity: 0.4,
        transform: 'translate(-50%, -50%) scale(0.8)',
        filter: 'blur(6px)',
      },
      '50%': {
        opacity: 0.8,
        transform: 'translate(-50%, -50%) scale(1.1)',
        filter: 'blur(4px)',
      },
      '100%': {
        opacity: 0.6,
        transform: 'translate(-50%, -50%) scale(1.3)',
        filter: 'blur(8px)',
      },
    },
  },

  // Enhanced Icon Styling
  '& svg': {
    position: 'relative',
    zIndex: 2,
    filter: `
      drop-shadow(0 2px 8px rgba(99, 102, 241, 0.4))
      drop-shadow(0 4px 16px rgba(139, 92, 246, 0.3))
      drop-shadow(0 8px 32px rgba(236, 72, 153, 0.2))
    `,
    transition: 'all 0.4s cubic-bezier(0.23, 1, 0.32, 1)',
  },

  // Hover Enhancements for Interactive Feel
  '&:hover': {
    '&::before': {
      animationDuration: '4s',
      transform: 'translate(-50%, -50%) scale(1.5)',
      opacity: 0.8,
    },

    '&::after': {
      animationDuration: '2s',
      opacity: 1,
      transform: 'translate(-50%, -50%) scale(1.6)',
    },

    '& svg': {
      transform: 'scale(1.1) rotateY(10deg)',
      filter: `
        drop-shadow(0 4px 12px rgba(99, 102, 241, 0.6))
        drop-shadow(0 8px 24px rgba(139, 92, 246, 0.4))
        drop-shadow(0 16px 48px rgba(236, 72, 153, 0.3))
      `,
    },
  },
}));

// Floating Particles Background Component
const FloatingParticles = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  pointerEvents: 'none',
  overflow: 'hidden',
  borderRadius: '24px',
  zIndex: 0,

  '&::before': {
    content: '""',
    position: 'absolute',
    top: '20%',
    left: '10%',
    width: '4px',
    height: '4px',
    borderRadius: '50%',
    background: 'rgba(99, 102, 241, 0.6)',
    animation: 'particle1 12s ease-in-out infinite',
    boxShadow: '0 0 6px rgba(99, 102, 241, 0.8)',
    '@keyframes particle1': {
      '0%, 100%': {
        transform: 'translateY(0) translateX(0) scale(0.5)',
        opacity: 0.3,
      },
      '25%': {
        transform: 'translateY(-40px) translateX(30px) scale(1)',
        opacity: 0.8,
      },
      '50%': {
        transform: 'translateY(-20px) translateX(-20px) scale(0.7)',
        opacity: 1,
      },
      '75%': {
        transform: 'translateY(10px) translateX(40px) scale(1.2)',
        opacity: 0.6,
      },
    }
  },

  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: '30%',
    right: '20%',
    width: '3px',
    height: '3px',
    borderRadius: '50%',
    background: 'rgba(139, 92, 246, 0.7)',
    animation: 'particle2 15s ease-in-out infinite reverse',
    boxShadow: '0 0 8px rgba(139, 92, 246, 0.9)',
    '@keyframes particle2': {
      '0%, 100%': {
        transform: 'translateY(0) translateX(0) scale(0.3)',
        opacity: 0.2,
      },
      '33%': {
        transform: 'translateY(25px) translateX(-35px) scale(0.9)',
        opacity: 0.7,
      },
      '66%': {
        transform: 'translateY(-15px) translateX(15px) scale(1.3)',
        opacity: 1,
      },
    }
  },
}));

/**
 * VideoSummary Component
 * Displays AI-generated video summary using Gemini Flash API
 * Features beautiful typography and smooth animations
 */
const VideoSummary = ({ analysisData, videoTitle = 'Video', className }) => {
  const [summary, setSummary] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Generate summary when analysis data changes
  useEffect(() => {
    if (!analysisData) {
      setSummary('');
      setError(null);
      return;
    }

    const generateSummary = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const generatedSummary = await geminiSummaryService.generateVideoSummary(
          analysisData,
          videoTitle
        );

        setSummary(generatedSummary);
      } catch (err) {
        console.error('Failed to generate video summary:', err);
        setError('Unable to generate summary. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    generateSummary();
  }, [analysisData, videoTitle]);

  const renderContent = () => {
    if (isLoading) {
      return (
        <LoadingContainer>
          <PulseEffect />
          <motion.div
            animate={{
              rotate: 360,
              scale: [1, 1.1, 1],
            }}
            transition={{
              rotate: { duration: 3, repeat: Infinity, ease: 'linear' },
              scale: { duration: 2, repeat: Infinity, ease: 'easeInOut' }
            }}
            style={{
              position: 'relative',
              zIndex: 1,
            }}
          >
            <GradientIcon>
              <AutoAwesomeIcon sx={{
                fontSize: '2.5rem',
                filter: 'drop-shadow(0 2px 8px rgba(99, 102, 241, 0.3))',
              }} />
            </GradientIcon>
          </motion.div>

          <Typography variant="body2" sx={{
            color: 'rgba(248, 250, 252, 0.9)',
            fontWeight: 600,
            fontSize: '1.1rem',
            textAlign: 'center',
            letterSpacing: '0.02em',
            fontFamily: '"SF Pro Display", "Inter", sans-serif',
            textShadow: '0 2px 8px rgba(99, 102, 241, 0.3)',
            marginBottom: '0.5rem',
            position: 'relative',
            zIndex: 1,
          }}>
            Generating AI Summary
          </Typography>

          <Typography variant="caption" sx={{
            color: 'rgba(148, 163, 184, 0.8)',
            textAlign: 'center',
            maxWidth: '220px',
            fontSize: '0.9rem',
            lineHeight: 1.6,
            letterSpacing: '0.01em',
            fontFamily: '"Inter", sans-serif',
            fontWeight: 400,
            position: 'relative',
            zIndex: 1,
          }}>
            Analyzing content with Gemini Flash
          </Typography>
        </LoadingContainer>
      );
    }

    if (error) {
      return (
        <ErrorContainer>
          <ErrorOutlineIcon sx={{ fontSize: '2.5rem', color: 'rgba(239, 68, 68, 0.6)' }} />
          <Typography variant="body2" sx={{
            color: 'rgba(239, 68, 68, 0.9)',
            fontWeight: 600,
            fontSize: '1.05rem',
            letterSpacing: '0.01em',
            fontFamily: '"SF Pro Display", "Inter", sans-serif',
            marginBottom: '0.25rem',
          }}>
            Summary Generation Failed
          </Typography>
          <Typography variant="caption" sx={{
            color: 'rgba(148, 163, 184, 0.8)',
            maxWidth: '280px',
            fontSize: '0.85rem',
            lineHeight: 1.5,
            fontFamily: '"Inter", sans-serif',
            fontWeight: 400,
          }}>
            {error}
          </Typography>
        </ErrorContainer>
      );
    }

    if (summary) {
      return (
        <ScrollableTextContainer>
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
              duration: 0.8,
              ease: [0.25, 0.46, 0.45, 0.94],
              delay: 0.1
            }}
            style={{
              position: 'relative',
              zIndex: 1,
              width: '100%',
            }}
          >
            <SummaryText component="div">
              {summary}
            </SummaryText>
          </motion.div>
        </ScrollableTextContainer>
      );
    }

    return null;
  };

  return (
    <SummaryContainer className={className}>
      <SummaryContent elevation={0}>
        <Box className="secondary-orb" />
        <FloatingParticles />
        <AnimatePresence mode="wait">
          {renderContent()}
        </AnimatePresence>
      </SummaryContent>
    </SummaryContainer>
  );
};

export default VideoSummary;
