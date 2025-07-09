import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box,
  IconButton,
  Typography,
  Tooltip,
  Divider,
  Badge,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Menu as MenuIcon,
  Close as CloseIcon,
  Add as AddIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  VideoLibrary as VideoLibraryIcon,
} from '@mui/icons-material';
import { useVideo } from '../VideoContext';
import theme from '../theme';

// Enhanced Styled Components with Subtle Premium Visual Effects
const SidebarContainer = styled(motion.div)(({ isexpanded }) => ({
  position: 'fixed',
  top: 0,
  left: 0,
  height: '100vh',
  width: isexpanded === 'true' ? '340px' : '88px',
  zIndex: theme.zIndex.dropdown,
  display: 'flex',
  flexDirection: 'column',  background: `
    linear-gradient(145deg,
      #020617 0%,
      #0f172a 30%,
      #1e293b 70%,
      #334155 100%
    )
  `,
  backdropFilter: 'blur(20px) saturate(120%) brightness(0.7)',
  borderRight: `1px solid rgba(79, 70, 229, 0.1)`,
  boxShadow: `
    0 0 0 1px rgba(0, 0, 0, 0.2),
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 16px 64px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.01)
  `,
  transition: `all 0.5s cubic-bezier(0.23, 1, 0.32, 1)`,
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,    background: `
      radial-gradient(ellipse at 30% 20%, rgba(79, 70, 229, 0.01) 0%, transparent 70%),
      radial-gradient(ellipse at 70% 80%, rgba(79, 70, 229, 0.008) 0%, transparent 60%)
    `,
    pointerEvents: 'none',
    animation: 'subtleGlow 12s ease-in-out infinite alternate',
  },
  '@keyframes subtleGlow': {
    '0%': { opacity: 0.4 },
    '100%': { opacity: 0.6 },
  },
}));

const SidebarHeader = styled(Box)(({ isexpanded }) => ({
  padding: '28px 24px',
  borderBottom: '1px solid rgba(79, 70, 229, 0.06)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: isexpanded === 'true' ? 'flex-start' : 'center',
  minHeight: '88px',  background: `
    linear-gradient(135deg,
      rgba(2, 6, 23, 0.8) 0%,
      rgba(15, 23, 42, 0.7) 50%,
      rgba(30, 41, 59, 0.6) 100%
    )
  `,
  position: 'relative',
  transition: 'all 0.4s cubic-bezier(0.23, 1, 0.32, 1)',
  backdropFilter: 'blur(12px) brightness(0.6)',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,    background: `
      radial-gradient(ellipse at 50% 50%, rgba(139, 92, 246, 0.01) 0%, transparent 80%)
    `,
    pointerEvents: 'none',
    borderRadius: 'inherit',
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: 0,
    left: '24px',
    right: '24px',
    height: '1px',    background: `
      linear-gradient(90deg,
        transparent 0%,
        rgba(139, 92, 246, 0.08) 50%,
        transparent 100%
      )
    `,
    borderRadius: '0.5px',
  },
}));

const SidebarBody = styled(Box)(() => ({
  flex: 1,
  overflow: 'hidden',
  display: 'flex',
  flexDirection: 'column',
  padding: '24px',
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: '30%',
    left: '10%',
    width: '80%',
    height: '40%',    background: `
      radial-gradient(ellipse at center,
        rgba(139, 92, 246, 0.01) 0%,
        transparent 60%
      )
    `,
    pointerEvents: 'none',
    animation: 'subtleFloat 15s ease-in-out infinite alternate',
  },
  '@keyframes subtleFloat': {
    '0%': {
      transform: 'translateY(0px)',
      opacity: 0.4,
    },
    '100%': {
      transform: 'translateY(-5px)',
      opacity: 0.6,
    },
  },
}));

// Luxury Wide Action Button with Enhanced Visual Effects
const WideActionButton = styled(motion.button)(({ isexpanded }) => ({
  width: isexpanded === 'true' ? '292px' : '56px',
  height: '56px',
  minHeight: '56px',
  maxHeight: '56px',  boxSizing: 'border-box',
  borderRadius: '16px',
  // Reset button defaults
  margin: 0,
  padding: isexpanded === 'true' ? '0 24px' : '0',
  outline: 'none',
  fontSize: 'inherit',
  fontFamily: 'inherit',
  lineHeight: 1,
  alignSelf: 'flex-start',
  flexShrink: 0,  background: `
    linear-gradient(135deg,
      #4F46E5 0%,
      #3730a3 25%,
      #2563eb 50%,
      #1d4ed8 75%,
      #1e40af 100%
    )
  `,
  color: '#ffffff',
  border: `2px solid rgba(79, 70, 229, 0.3)`,
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: isexpanded === 'true' ? 'flex-start' : 'center',
  gap: isexpanded === 'true' ? '14px' : '0',  boxShadow: `
    0 0 0 1px rgba(79, 70, 229, 0.2),
    0 8px 28px rgba(79, 70, 229, 0.25),
    0 4px 16px rgba(0, 0, 0, 0.3),
    0 16px 48px rgba(79, 70, 229, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.25),
    inset 0 -1px 0 rgba(79, 70, 229, 0.3)
  `,
  position: 'relative',
  overflow: 'hidden',
  transition: 'all 0.5s cubic-bezier(0.23, 1, 0.32, 1)',
  backdropFilter: 'blur(8px) brightness(1.1)',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: '-100%',
    width: '100%',
    height: '100%',
    background: `
      linear-gradient(90deg,
        transparent,
        rgba(255, 255, 255, 0.3) 50%,
        transparent
      )
    `,
    transition: 'left 0.6s ease',
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: '0',
    height: '0',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '50%',
    transform: 'translate(-50%, -50%)',
    transition: 'all 0.3s ease',
  },
  '&:hover': {
    transform: 'translateY(-4px) scale(1.03)',    background: `
      linear-gradient(135deg,
        #4F46E5 0%,
        #3730a3 25%,
        #2563eb 50%,
        #1d4ed8 75%,
        #1e40af 100%
      )
    `,
    boxShadow: `
      0 0 0 1px rgba(79, 70, 229, 0.4),
      0 12px 40px rgba(79, 70, 229, 0.35),
      0 6px 20px rgba(0, 0, 0, 0.4),
      0 20px 60px rgba(79, 70, 229, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.35),
      inset 0 -1px 0 rgba(79, 70, 229, 0.4)
    `,
    filter: 'brightness(1.1) saturate(1.1)',
    '&::before': {
      left: '100%',
    },
    '&::after': {
      width: '120%',
      height: '120%',
    },
  },
  '&:active': {
    transform: 'translateY(-2px) scale(1.01)',
    transition: 'transform 0.1s ease',
    filter: 'brightness(0.95)',
  },
}));

// Luxury Wide Menu Button with Premium Styling
const WideMenuButton = styled(motion.button)(({ isexpanded, isactive }) => ({  width: isexpanded === 'true' ? '292px' : '56px',
  height: '56px',
  minHeight: '56px',
  maxHeight: '56px',
  boxSizing: 'border-box',
  borderRadius: '16px',
  // Reset button defaults
  margin: 0,
  padding: isexpanded === 'true' ? '0 24px' : '0',
  outline: 'none',
  fontSize: 'inherit',
  fontFamily: 'inherit',
  lineHeight: 1,
  alignSelf: 'flex-start',
  flexShrink: 0,
  color: isactive === 'true' ? '#ffffff' : 'rgba(248, 250, 252, 0.95)',  background: isactive === 'true'
    ? `
      linear-gradient(135deg,
        rgba(139, 92, 246, 0.9) 0%,
        rgba(124, 58, 237, 0.8) 50%,
        rgba(109, 40, 217, 0.7) 100%
      )
    `
    : `
      linear-gradient(135deg,
        rgba(20, 20, 30, 0.7) 0%,
        rgba(25, 25, 35, 0.6) 50%,
        rgba(30, 30, 40, 0.5) 100%
      )
    `,
  border: `2px solid ${isactive === 'true' ? 'rgba(139, 92, 246, 0.5)' : 'rgba(255, 255, 255, 0.06)'}`,
  backdropFilter: 'blur(16px) brightness(1.1)',
  cursor: 'pointer',  display: 'flex',
  alignItems: 'center',
  justifyContent: isexpanded === 'true' ? 'flex-start' : 'center',
  gap: isexpanded === 'true' ? '14px' : '0',  boxShadow: isactive === 'true'
    ? `
      0 8px 28px rgba(139, 92, 246, 0.25),
      0 4px 16px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.15),
      inset 0 -1px 0 rgba(139, 92, 246, 0.2)
    `
    : `
      0 4px 16px rgba(0, 0, 0, 0.25),
      0 2px 8px rgba(0, 0, 0, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.03)
    `,
  transition: 'all 0.5s cubic-bezier(0.23, 1, 0.32, 1)',
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,    background: `
      radial-gradient(circle at center,
        rgba(139, 92, 246, 0.15) 0%,
        transparent 65%
      )
    `,
    opacity: 0,
    transition: 'opacity 0.4s ease',
    borderRadius: 'inherit',
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: '0',
    height: '0',
    background: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '50%',
    transform: 'translate(-50%, -50%)',
    transition: 'all 0.3s ease',
  },
  '&:hover': {    background: isactive === 'true'
      ? `
        linear-gradient(135deg,
          rgba(139, 92, 246, 1) 0%,
          rgba(124, 58, 237, 0.9) 50%,
          rgba(109, 40, 217, 0.85) 100%
        )
      `
      : `
        linear-gradient(135deg,
          rgba(30, 30, 40, 0.9) 0%,
          rgba(35, 35, 45, 0.8) 50%,
          rgba(40, 40, 50, 0.7) 100%
        )
      `,
    border: `2px solid ${isactive === 'true' ? 'rgba(139, 92, 246, 0.7)' : 'rgba(139, 92, 246, 0.3)'}`,
    transform: 'translateY(-3px) scale(1.03)',
    color: '#ffffff',    boxShadow: isactive === 'true'
      ? `
        0 12px 36px rgba(139, 92, 246, 0.35),
        0 6px 20px rgba(0, 0, 0, 0.4),
        inset 0 1px 0 rgba(255, 255, 255, 0.2),
        inset 0 -1px 0 rgba(139, 92, 246, 0.3)
      `
      : `
        0 8px 24px rgba(139, 92, 246, 0.15),
        0 4px 16px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.05)
      `,
    filter: 'brightness(1.1) saturate(1.1)',
    '&::before': {
      opacity: 1,
    },
    '&::after': {
      width: '140%',
      height: '140%',
    },
  },
  '&:active': {
    transform: 'translateY(-1px) scale(1.01)',
    transition: 'transform 0.1s ease',
    filter: 'brightness(0.95)',
  },
}));

const HistoryContainer = styled(Box)(() => ({
  flex: 1,
  overflowY: 'auto',
  marginTop: '20px',
  paddingRight: '6px',
  position: 'relative',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '20px',
    background: 'linear-gradient(180deg, rgba(15, 25, 55, 0.8) 0%, transparent 100%)',
    pointerEvents: 'none',
    zIndex: 1,
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '20px',
    background: 'linear-gradient(0deg, rgba(15, 25, 55, 0.8) 0%, transparent 100%)',
    pointerEvents: 'none',
    zIndex: 1,
  },
  '&::-webkit-scrollbar': {
    width: '8px',
  },
  '&::-webkit-scrollbar-track': {
    background: `
      linear-gradient(180deg,
        rgba(30, 41, 59, 0.4) 0%,
        rgba(45, 55, 75, 0.3) 50%,
        rgba(30, 41, 59, 0.4) 100%
      )
    `,
    borderRadius: '4px',
    margin: '6px 0',
    border: '1px solid rgba(79, 70, 229, 0.1)',
  },
  '&::-webkit-scrollbar-thumb': {
    background: `
      linear-gradient(180deg,
        rgba(79, 70, 229, 0.8) 0%,
        rgba(99, 102, 241, 0.6) 50%,
        rgba(129, 140, 248, 0.4) 100%
      )
    `,
    borderRadius: '4px',
    border: '1px solid rgba(79, 70, 229, 0.3)',
    boxShadow: `
      0 2px 8px rgba(79, 70, 229, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.1)
    `,
    '&:hover': {
      background: `
        linear-gradient(180deg,
          rgba(79, 70, 229, 1) 0%,
          rgba(99, 102, 241, 0.8) 50%,
          rgba(129, 140, 248, 0.6) 100%
        )
      `,
      boxShadow: `
        0 4px 12px rgba(79, 70, 229, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.15)
      `,
    },
  },
  '&::-webkit-scrollbar-corner': {
    background: 'transparent',
  },
}));

const HistoryItem = styled(motion.div)(({ isactive }) => ({
  marginBottom: '16px',
  borderRadius: '18px',
  overflow: 'hidden',
  background: isactive === 'true'
    ? `
      linear-gradient(135deg,
        rgba(79, 70, 229, 0.2) 0%,
        rgba(99, 102, 241, 0.15) 50%,
        rgba(129, 140, 248, 0.1) 100%
      )
    `
    : `
      linear-gradient(135deg,
        rgba(30, 41, 59, 0.6) 0%,
        rgba(45, 55, 75, 0.5) 50%,
        rgba(30, 41, 59, 0.6) 100%
      )
    `,
  border: `2px solid ${isactive === 'true' ? 'rgba(79, 70, 229, 0.4)' : 'rgba(255, 255, 255, 0.08)'}`,
  backdropFilter: 'blur(16px) brightness(1.05)',
  boxShadow: isactive === 'true'
    ? `
      0 8px 24px rgba(79, 70, 229, 0.2),
      0 4px 12px rgba(0, 0, 0, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.15),
      inset 0 -1px 0 rgba(79, 70, 229, 0.1)
    `
    : `
      0 4px 16px rgba(0, 0, 0, 0.12),
      0 2px 8px rgba(0, 0, 0, 0.08),
      inset 0 1px 0 rgba(255, 255, 255, 0.06)
    `,
  transition: 'all 0.4s cubic-bezier(0.23, 1, 0.32, 1)',
  cursor: 'pointer',
  position: 'relative',
  '&:hover': {
    background: isactive === 'true'
      ? `
        linear-gradient(135deg,
          rgba(79, 70, 229, 0.25) 0%,
          rgba(99, 102, 241, 0.2) 50%,
          rgba(129, 140, 248, 0.15) 100%
        )
      `
      : `
        linear-gradient(135deg,
          rgba(45, 55, 75, 0.8) 0%,
          rgba(60, 70, 90, 0.7) 50%,
          rgba(45, 55, 75, 0.8) 100%
        )
      `,
    border: `2px solid ${isactive === 'true' ? 'rgba(79, 70, 229, 0.6)' : 'rgba(79, 70, 229, 0.3)'}`,
    transform: 'translateY(-3px) scale(1.02)',
    boxShadow: isactive === 'true'
      ? `
        0 12px 32px rgba(79, 70, 229, 0.25),
        0 6px 16px rgba(0, 0, 0, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.2),
        inset 0 -1px 0 rgba(79, 70, 229, 0.15)
      `
      : `
        0 8px 24px rgba(79, 70, 229, 0.15),
        0 4px 12px rgba(0, 0, 0, 0.12),
        inset 0 1px 0 rgba(255, 255, 255, 0.1)
      `,
    filter: 'brightness(1.05) saturate(1.1)',
    '& .history-delete-btn': {
      opacity: 1,
      transform: 'scale(1.05)',
    },
    '&::before': {
      background: `
        linear-gradient(180deg,
          rgba(79, 70, 229, 1) 0%,
          rgba(99, 102, 241, 0.9) 50%,
          rgba(129, 140, 248, 0.8) 100%
        )
      `,
      width: '5px',
      boxShadow: '0 0 16px rgba(79, 70, 229, 0.5)',
    },
    '&::after': {
      background: 'linear-gradient(135deg, rgba(79, 70, 229, 1) 0%, rgba(99, 102, 241, 0.8) 100%)',
      width: '8px',
      height: '8px',
      boxShadow: '0 0 12px rgba(79, 70, 229, 0.8)',
    },
  },
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    width: '4px',
    height: '100%',
    background: isactive === 'true'
      ? `
        linear-gradient(180deg,
          rgba(79, 70, 229, 1) 0%,
          rgba(99, 102, 241, 0.8) 50%,
          rgba(129, 140, 248, 0.6) 100%
        )
      `
      : 'transparent',
    borderRadius: '0 2px 2px 0',
    transition: 'all 0.4s ease',
    boxShadow: isactive === 'true' ? '0 0 12px rgba(79, 70, 229, 0.4)' : 'none',
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '50%',
    right: '16px',
    width: '6px',
    height: '6px',
    background: isactive === 'true'
      ? 'linear-gradient(135deg, rgba(79, 70, 229, 0.8) 0%, rgba(99, 102, 241, 0.6) 100%)'
      : 'transparent',
    borderRadius: '50%',
    transform: 'translateY(-50%)',
    transition: 'all 0.3s ease',
    boxShadow: isactive === 'true' ? '0 0 8px rgba(79, 70, 229, 0.6)' : 'none',
  },
  '&:active': {
    transform: 'translateY(-1px) scale(1.01)',
    transition: 'transform 0.1s ease',
    filter: 'brightness(0.95)',
  },
}));

// Delete Button for History Items
const HistoryDeleteButton = styled(IconButton)(({ theme }) => ({
  position: 'absolute',
  top: '8px',
  right: '8px',
  width: '28px',
  height: '28px',
  padding: '6px',
  borderRadius: '8px',
  background: 'rgba(239, 68, 68, 0.15)',
  border: '1px solid rgba(239, 68, 68, 0.3)',
  color: '#EF4444',
  opacity: 0.8,
  transition: 'all 0.2s cubic-bezier(0.23, 1, 0.32, 1)',
  zIndex: 10,
  backdropFilter: 'blur(8px)',
  '&:hover': {
    opacity: 1,
    background: 'rgba(239, 68, 68, 0.25)',
    borderColor: 'rgba(239, 68, 68, 0.5)',
    transform: 'scale(1.1)',
    boxShadow: '0 4px 12px rgba(239, 68, 68, 0.4)',
  },
  '&:active': {
    transform: 'scale(0.95)',
  },
  '& .MuiSvgIcon-root': {
    fontSize: '1rem',
    fontWeight: 'bold',
  },
}));

/**
 * Enhanced Sidebar Component
 * Implements premium dark theme with glassmorphism effects
 * Provides navigation, history management, and quick actions
 */
const Sidebar = ({
  videoHistory = [],
  onAddVideo,
  onSettings,
  onVideoSelect,
  currentVideoId = null
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { removeFromHistory } = useVideo();

  const toggleSidebar = () => {
    setIsExpanded(!isExpanded);
  };

  const handleAddVideo = () => {
    if (onAddVideo) onAddVideo();
  };

  const handleSettings = () => {
    if (onSettings) onSettings();
  };

  const handleDeleteVideo = (e, videoId) => {
    e.stopPropagation();
    e.preventDefault();

    // Add visual feedback
    const button = e.currentTarget;
    button.style.transform = 'scale(0.8)';

    setTimeout(() => {
      removeFromHistory(videoId);
    }, 150);
  };

  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <>
      <SidebarContainer
        isexpanded={isExpanded.toString()}
        initial={{ x: -60 }}
        animate={{ x: 0 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >        {/* Header */}
        <SidebarHeader isexpanded={isExpanded.toString()}>
          <Tooltip title={isExpanded ? '' : 'Toggle Menu'} placement="right">            <IconButton
              onClick={toggleSidebar}
              sx={{
                color: 'rgba(248, 250, 252, 0.95)',
                width: '52px',
                height: '52px',
                borderRadius: '16px',
                background: `
                  linear-gradient(135deg,
                    rgba(30, 41, 59, 0.7) 0%,
                    rgba(45, 55, 75, 0.6) 50%,
                    rgba(30, 41, 59, 0.7) 100%
                  )
                `,
                border: '2px solid rgba(255, 255, 255, 0.12)',
                backdropFilter: 'blur(16px) brightness(1.1)',
                boxShadow: `
                  0 4px 16px rgba(0, 0, 0, 0.15),
                  0 2px 8px rgba(0, 0, 0, 0.1),
                  inset 0 1px 0 rgba(255, 255, 255, 0.1),
                  inset 0 -1px 0 rgba(79, 70, 229, 0.1)
                `,
                transition: 'all 0.4s cubic-bezier(0.23, 1, 0.32, 1)',
                position: 'relative',
                overflow: 'hidden',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: `
                    radial-gradient(circle at center,
                      rgba(79, 70, 229, 0.1) 0%,
                      transparent 70%
                    )
                  `,
                  opacity: 0,
                  transition: 'opacity 0.3s ease',
                  borderRadius: 'inherit',
                },
                '&:hover': {
                  background: `
                    linear-gradient(135deg,
                      rgba(79, 70, 229, 0.6) 0%,
                      rgba(99, 102, 241, 0.5) 50%,
                      rgba(129, 140, 248, 0.4) 100%
                    )
                  `,
                  border: '2px solid rgba(79, 70, 229, 0.5)',
                  transform: 'scale(1.08) translateY(-2px)',
                  color: '#ffffff',
                  boxShadow: `
                    0 8px 24px rgba(79, 70, 229, 0.3),
                    0 4px 12px rgba(0, 0, 0, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.15),
                    inset 0 -1px 0 rgba(79, 70, 229, 0.2)
                  `,
                  filter: 'brightness(1.1) saturate(1.2)',
                  '&::before': {
                    opacity: 1,
                  },
                },
                '&:active': {
                  transform: 'scale(1.03)',
                  transition: 'transform 0.1s ease',
                  filter: 'brightness(0.95)',
                }
              }}
            >
              {isExpanded ? <CloseIcon /> : <MenuIcon />}
            </IconButton>
          </Tooltip>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                style={{ flex: 1, marginLeft: 16 }}
              >                <Typography variant="h6" sx={{
                  fontWeight: 900,
                  fontSize: '1.35rem',
                  background: `
                    linear-gradient(145deg,
                      #ffffff 0%,
                      rgba(248, 250, 252, 0.95) 15%,
                      rgba(79, 70, 229, 0.95) 35%,
                      rgba(99, 102, 241, 0.9) 55%,
                      rgba(129, 140, 248, 0.85) 75%,
                      rgba(248, 250, 252, 0.95) 85%,
                      #ffffff 100%
                    )
                  `,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  letterSpacing: '0.03em',
                  textShadow: `
                    0 2px 8px rgba(79, 70, 229, 0.3),
                    0 4px 16px rgba(99, 102, 241, 0.2),
                    0 1px 3px rgba(0, 0, 0, 0.3)
                  `,
                  filter: 'drop-shadow(0 0 8px rgba(79, 70, 229, 0.2))',
                  position: 'relative',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: '-2px',
                    left: '-2px',
                    right: '-2px',
                    bottom: '-2px',
                    background: `
                      linear-gradient(145deg,
                        transparent 0%,
                        rgba(79, 70, 229, 0.1) 35%,
                        rgba(99, 102, 241, 0.08) 55%,
                        rgba(129, 140, 248, 0.06) 75%,
                        transparent 100%
                      )
                    `,
                    borderRadius: '8px',
                    zIndex: -1,
                    filter: 'blur(4px)',
                  },
                }}>
                  Emotion Universe
                </Typography>
              </motion.div>
            )}
          </AnimatePresence>
        </SidebarHeader>

        {/* Body */}
        <SidebarBody>          {/* Add Video Button */}
          <Box sx={{
            mb: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'justify-content 0.3s ease',
          }}>
            <Tooltip title={isExpanded ? '' : 'Add Video'} placement="right">
              <WideActionButton
                isexpanded={isExpanded.toString()}
                onClick={handleAddVideo}
                whileHover={{ scale: isExpanded ? 1.02 : 1.05 }}
                whileTap={{ scale: isExpanded ? 1 : 1.02 }}
                transition={{ duration: 0.2, ease: 'easeOut' }}
              >
                <AddIcon sx={{
                  fontSize: '1.35rem',
                  filter: `
                    drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3))
                    drop-shadow(0 0 8px rgba(255, 255, 255, 0.2))
                  `,
                }} />
                <AnimatePresence>
                  {isExpanded && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.3, ease: 'easeOut' }}
                      style={{
                        fontSize: '0.95rem',
                        fontWeight: 700,
                        letterSpacing: '0.025em',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                      }}
                    >
                      Add New Video
                    </motion.span>
                  )}
                </AnimatePresence>
              </WideActionButton>
            </Tooltip>
          </Box>          <Divider sx={{
            borderColor: 'rgba(79, 70, 229, 0.2)',
            mb: 3,
            '&::before, &::after': {
              borderColor: 'rgba(79, 70, 229, 0.2)',
            }
          }} />

          {/* Video History Section */}
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
              >                {/* Enhanced History Header */}
                <Box sx={{
                  mb: 3,
                  display: 'flex',
                  alignItems: 'center',
                  padding: '18px 24px',
                  background: `                    linear-gradient(135deg,
                      rgba(25, 35, 65, 0.6) 0%,
                      rgba(35, 45, 75, 0.5) 50%,
                      rgba(45, 55, 85, 0.4) 100%
                    )
                  `,
                  borderRadius: '14px',
                  border: '1px solid rgba(79, 70, 229, 0.08)',
                  backdropFilter: 'blur(12px) brightness(0.9)',
                  boxShadow: `
                    0 4px 16px rgba(0, 0, 0, 0.15),
                    0 2px 8px rgba(0, 0, 0, 0.1),
                    inset 0 1px 0 rgba(255, 255, 255, 0.06)
                  `,
                  position: 'relative',
                  overflow: 'hidden',
                  transition: 'all 0.3s cubic-bezier(0.23, 1, 0.32, 1)',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: `
                      radial-gradient(ellipse at 30% 50%, rgba(79, 70, 229, 0.03) 0%, transparent 70%),
                      radial-gradient(ellipse at 70% 50%, rgba(99, 102, 241, 0.02) 0%, transparent 70%)
                    `,
                    pointerEvents: 'none',
                    borderRadius: 'inherit',
                  },
                  '&:hover': {
                    background: `                      linear-gradient(135deg,
                        rgba(35, 45, 75, 0.8) 0%,
                        rgba(45, 55, 85, 0.7) 50%,
                        rgba(55, 65, 95, 0.6) 100%
                      )
                    `,
                    border: '1px solid rgba(79, 70, 229, 0.12)',
                    boxShadow: `
                      0 6px 20px rgba(0, 0, 0, 0.2),
                      0 3px 12px rgba(0, 0, 0, 0.15),
                      inset 0 1px 0 rgba(255, 255, 255, 0.08)
                    `,
                  },
                }}>
                  <HistoryIcon sx={{
                    fontSize: '1.1rem',
                    color: 'rgba(79, 70, 229, 0.9)',
                    mr: 2,
                    filter: `
                      drop-shadow(0 1px 2px rgba(79, 70, 229, 0.2))
                      drop-shadow(0 0 4px rgba(79, 70, 229, 0.1))
                    `,
                    background: `
                      linear-gradient(135deg,
                        rgba(79, 70, 229, 0.05) 0%,
                        rgba(99, 102, 241, 0.03) 100%
                      )
                    `,
                    borderRadius: '6px',
                    padding: '4px',
                    border: '1px solid rgba(79, 70, 229, 0.1)',
                  }} />                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle1" sx={{
                      color: 'rgba(248, 250, 252, 0.95)',
                      fontWeight: 700,
                      fontSize: '1rem',
                      letterSpacing: '0.02em',
                      lineHeight: 1.2,
                      textShadow: `
                        0 1px 2px rgba(0, 0, 0, 0.2)
                      `,
                    }}>
                      Recent Videos
                    </Typography>
                    <Typography variant="caption" sx={{
                      color: 'rgba(248, 250, 252, 0.6)',
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      textShadow: '0 1px 1px rgba(0, 0, 0, 0.1)',
                      letterSpacing: '0.01em',
                    }}>
                      {videoHistory.length} {videoHistory.length === 1 ? 'video' : 'videos'}
                    </Typography>
                  </Box>
                  <Badge
                    badgeContent={videoHistory.length}
                    color="primary"
                    sx={{
                      '& .MuiBadge-badge': {
                        background: `
                          linear-gradient(135deg,
                            rgba(79, 70, 229, 0.9) 0%,
                            rgba(99, 102, 241, 0.8) 50%,
                            rgba(129, 140, 248, 0.7) 100%
                          )
                        `,
                        color: '#ffffff',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        boxShadow: `
                          0 2px 6px rgba(79, 70, 229, 0.3),
                          0 1px 3px rgba(0, 0, 0, 0.15)
                        `,
                        minWidth: '18px',
                        height: '18px',
                        border: '1px solid rgba(79, 70, 229, 0.2)',
                        textShadow: '0 1px 1px rgba(0, 0, 0, 0.2)',
                      }
                    }}
                  >
                    <VideoLibraryIcon sx={{
                      fontSize: '1.1rem',
                      color: 'rgba(79, 70, 229, 0.7)',
                      filter: `
                        drop-shadow(0 1px 2px rgba(79, 70, 229, 0.15))
                        drop-shadow(0 0 3px rgba(99, 102, 241, 0.1))
                      `,
                    }} />
                  </Badge>
                </Box>

                <HistoryContainer>
                  {videoHistory.length > 0 ? (
                    videoHistory.map((video, index) => (
                      <HistoryItem
                        key={video.id || index}
                        isactive={(currentVideoId === video.id).toString()}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        onClick={() => onVideoSelect(video)}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        {/* Delete Button */}
                        <HistoryDeleteButton
                          className="history-delete-btn"
                          onClick={(e) => handleDeleteVideo(e, video.id)}
                          aria-label={`Remove ${video.title || 'video'} from history`}
                          title="Remove from history"
                          size="small"
                        >
                          <CloseIcon fontSize="inherit" />
                        </HistoryDeleteButton>

                        <Box sx={{ p: 3, cursor: 'pointer' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                            <VideoLibraryIcon sx={{
                              fontSize: '1.1rem',
                              color: 'rgba(79, 70, 229, 0.8)',
                              mr: 1.5,
                              filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.1))',
                            }} />
                            <Typography variant="body2" sx={{
                              color: 'rgba(248, 250, 252, 0.95)',
                              fontWeight: 600,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              flex: 1,
                              fontSize: '0.875rem',
                              letterSpacing: '0.01em',
                            }}>
                              {video.title || 'Untitled Video'}
                            </Typography>
                          </Box>

                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="caption" sx={{
                              color: 'rgba(248, 250, 252, 0.5)',
                              fontSize: '0.7rem',
                              fontWeight: 500,
                            }}>
                              {video.date ? formatDate(video.date) : 'No date'}
                            </Typography>

                            {video.duration && (
                              <Typography variant="caption" sx={{
                                color: 'rgba(248, 250, 252, 0.8)',
                                fontSize: '0.7rem',
                                fontWeight: 600,
                                background: 'rgba(79, 70, 229, 0.2)',
                                border: '1px solid rgba(79, 70, 229, 0.3)',
                                backdropFilter: 'blur(5px)',
                                px: 1.5,
                                py: 0.5,
                                borderRadius: '8px',
                                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                              }}>
                                {formatDuration(video.duration)}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      </HistoryItem>
                    ))
                  ) : (                    <Box sx={{
                      textAlign: 'center',
                      py: 4,
                      color: 'rgba(248, 250, 252, 0.4)',
                    }}>
                      <VideoLibraryIcon sx={{
                        fontSize: '2.5rem',
                        mb: 1.5,
                        opacity: 0.4,
                        filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1))',
                      }} />
                      <Typography variant="body2" sx={{
                        color: 'rgba(248, 250, 252, 0.6)',
                        fontWeight: 600,
                        mb: 0.5,
                      }}>
                        No videos yet
                      </Typography>
                      <Typography variant="caption" sx={{
                        color: 'rgba(248, 250, 252, 0.4)',
                        fontWeight: 500,
                      }}>
                        Add a video to get started
                      </Typography>
                    </Box>
                  )}
                </HistoryContainer>
              </motion.div>
            )}
          </AnimatePresence>          {/* Settings Button */}
          <Box sx={{
            mt: 'auto',
            pt: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'justify-content 0.3s ease',
          }}>
            <Tooltip title={isExpanded ? '' : 'Settings'} placement="right">
              <WideMenuButton
                isexpanded={isExpanded.toString()}
                isactive="false"
                onClick={handleSettings}
                whileHover={{ scale: isExpanded ? 1.02 : 1.05 }}
                whileTap={{ scale: isExpanded ? 1 : 1.02 }}
                transition={{ duration: 0.2, ease: 'easeOut' }}
              >                <SettingsIcon sx={{
                  fontSize: '1.35rem',
                  color: 'rgba(79, 70, 229, 1)',
                  filter: `
                    drop-shadow(0 2px 4px rgba(79, 70, 229, 0.4))
                    drop-shadow(0 0 8px rgba(99, 102, 241, 0.3))
                  `,
                }} />
                <AnimatePresence>
                  {isExpanded && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.3, ease: 'easeOut' }}
                      style={{
                        fontSize: '0.95rem',
                        fontWeight: 700,
                        letterSpacing: '0.025em',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                      }}
                    >
                      Settings
                    </motion.span>
                  )}
                </AnimatePresence>
              </WideMenuButton>
            </Tooltip>
          </Box>
        </SidebarBody>
      </SidebarContainer>

      {/* Backdrop for mobile */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={toggleSidebar}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.5)',
              zIndex: theme.zIndex.dropdown - 1,
              display: 'none',
              '@media (max-width: 768px)': {
                display: 'block',
              },
            }}
          />
        )}
      </AnimatePresence>
    </>
  );
};

export default Sidebar;
