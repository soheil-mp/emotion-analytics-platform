import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  IconButton,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Close as CloseIcon,
  YouTube as YouTubeIcon,
  CloudUpload as UploadIcon,
  Link as LinkIcon,
  VideoFile as VideoFileIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import theme from '../theme';

// Styled Components with Enhanced Premium Design
const StyledDialog = styled(Dialog)(() => ({
  '& .MuiDialog-paper': {
    background: `
      linear-gradient(135deg,
        rgba(15, 23, 42, 0.95) 0%,
        rgba(30, 41, 59, 0.9) 50%,
        rgba(15, 23, 42, 0.95) 100%
      )
    `,
    backdropFilter: 'blur(40px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '32px',
    boxShadow: `
      0 25px 80px rgba(0, 0, 0, 0.5),
      0 0 120px rgba(79, 70, 229, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.1)
    `,
    color: theme.colors.text.primary,
    minWidth: '600px',
    maxWidth: '700px',
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
        radial-gradient(1px 1px at 25px 35px, rgba(255,255,255,0.9), transparent),
        radial-gradient(1px 1px at 75px 85px, rgba(147,197,253,0.8), transparent),
        radial-gradient(2px 2px at 120px 45px, rgba(255,255,255,0.7), transparent),
        radial-gradient(1px 1px at 180px 95px, rgba(196,181,253,0.6), transparent),
        radial-gradient(1px 1px at 50px 120px, rgba(255,255,255,0.8), transparent),
        radial-gradient(2px 2px at 200px 25px, rgba(147,197,253,0.5), transparent)
      `,
      backgroundRepeat: 'repeat',
      backgroundSize: '250px 150px',
      animation: 'modalStarfield 30s linear infinite',
      opacity: 0.6,
      zIndex: 0,
      pointerEvents: 'none',
    },
    '@keyframes modalStarfield': {
      '0%': {
        transform: 'translateY(0px) translateX(0px)',
        opacity: 0.6
      },
      '50%': {
        transform: 'translateY(-75px) translateX(10px)',
        opacity: 0.8
      },
      '100%': {
        transform: 'translateY(-150px) translateX(0px)',
        opacity: 0.6
      }
    }
  },
  '& .MuiBackdrop-root': {
    background: 'rgba(2, 6, 23, 0.8)',
    backdropFilter: 'blur(12px)',
  },
}));

const StyledDialogTitle = styled(DialogTitle)(() => ({
  background: `
    linear-gradient(135deg,
      rgba(79, 70, 229, 0.15) 0%,
      rgba(30, 41, 59, 0.1) 50%,
      rgba(147, 197, 253, 0.08) 100%
    )
  `,
  borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
  color: theme.colors.text.primary,
  fontWeight: 800,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '32px',
  position: 'relative',
  zIndex: 1,
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '2px',
    background: `linear-gradient(90deg,
      ${theme.colors.primary.main},
      ${theme.colors.secondary.main},
      ${theme.colors.primary.main}
    )`,
    borderRadius: '2px',
  },
}));

const StyledTabs = styled(Tabs)(() => ({
  marginBottom: '12px',
  position: 'relative',
  zIndex: 1,
  width: '100%',
  maxWidth: '520px',
  '& .MuiTabs-indicator': {
    background: `linear-gradient(90deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
    height: 3,
    borderRadius: theme.borderRadius.full,
    boxShadow: `0 0 20px ${theme.colors.primary.main}50`,
  },
  '& .MuiTab-root': {
    color: theme.colors.text.secondary,
    fontWeight: 600,
    fontSize: '0.95rem',
    textTransform: 'none',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    borderRadius: '16px',
    margin: '0 12px',
    minHeight: '48px',
    minWidth: '200px',
    padding: '12px 24px',
    flex: 1,
    '&:hover': {
      color: theme.colors.text.primary,
      background: 'rgba(255, 255, 255, 0.05)',
      transform: 'translateY(-2px)',
    },
    '&.Mui-selected': {
      color: theme.colors.primary.main,
      fontWeight: 700,
      background: `linear-gradient(135deg,
        ${theme.colors.primary.main}10,
        ${theme.colors.secondary.main}05
      )`,
      boxShadow: `0 4px 20px ${theme.colors.primary.main}20`,
    },
  },
}));

const InputContainer = styled(Box)(() => ({
  padding: '24px',
  borderRadius: '24px',
  background: `
    linear-gradient(135deg,
      rgba(15, 23, 42, 0.8) 0%,
      rgba(30, 41, 59, 0.6) 50%,
      rgba(15, 23, 42, 0.8) 100%
    )
  `,
  backdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  marginBottom: '1px',
  position: 'relative',
  zIndex: 1,
  boxShadow: `
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1)
  `,
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  textAlign: 'center',
  width: '100%',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: `
      0 12px 40px rgba(0, 0, 0, 0.4),
      0 0 60px ${theme.colors.primary.main}15,
      inset 0 1px 0 rgba(255, 255, 255, 0.15)
    `,
    border: '1px solid rgba(255, 255, 255, 0.12)',
  },
}));

const StyledTextField = styled(TextField)(() => ({
  '& .MuiOutlinedInput-root': {
    color: theme.colors.text.primary,
    background: `
      linear-gradient(135deg,
        rgba(15, 23, 42, 0.6) 0%,
        rgba(30, 41, 59, 0.4) 100%
      )
    `,
    backdropFilter: 'blur(10px)',
    borderRadius: '16px',
    fontSize: '1rem',
    fontWeight: 500,
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    '& fieldset': {
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: '1px',
    },
    '&:hover fieldset': {
      borderColor: 'rgba(255, 255, 255, 0.2)',
      boxShadow: `0 0 20px ${theme.colors.primary.main}20`,
    },
    '&.Mui-focused fieldset': {
      borderColor: theme.colors.primary.main,
      borderWidth: '2px',
      boxShadow: `
        0 0 0 4px ${theme.colors.primary.main}20,
        0 0 30px ${theme.colors.primary.main}30
      `,
    },
  },
  '& .MuiInputLabel-root': {
    color: theme.colors.text.secondary,
    fontWeight: 500,
    '&.Mui-focused': {
      color: theme.colors.primary.main,
    },
  },
}));

const ActionButton = styled(Button)(({ variant: buttonVariant }) => ({
  borderRadius: '16px',
  fontWeight: 700,
  fontSize: '1rem',
  textTransform: 'none',
  padding: '10px 32px', // Reduced padding for better height control
  height: '44px', // Fixed height for consistency
  minHeight: '44px', // Ensure minimum height
  maxHeight: '44px', // Prevent height expansion
  lineHeight: '1.2', // Control line height
  position: 'relative',
  overflow: 'hidden',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  backdropFilter: 'blur(10px)',
  zIndex: 1,

  ...(buttonVariant === 'contained' ? {
    background: `linear-gradient(135deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
    color: theme.colors.text.primary,
    border: '1px solid rgba(255, 255, 255, 0.1)',
    boxShadow: `
      0 8px 32px ${theme.colors.primary.main}40,
      0 0 40px ${theme.colors.primary.main}20,
      inset 0 1px 0 rgba(255, 255, 255, 0.2)
    `,
    '&::before': {
      content: '""',
      position: 'absolute',
      top: 0,
      left: '-100%',
      width: '100%',
      height: '100%',
      background: `linear-gradient(90deg,
        transparent,
        rgba(255, 255, 255, 0.2),
        transparent
      )`,
      transition: 'left 0.6s ease',
      zIndex: -1,
    },
    '&:hover': {
      transform: 'translateY(-3px) scale(1.02)',
      boxShadow: `
        0 12px 40px ${theme.colors.primary.main}50,
        0 0 60px ${theme.colors.primary.main}30,
        inset 0 1px 0 rgba(255, 255, 255, 0.3)
      `,
      '&::before': {
        left: '100%',
      },
    },
    '&:active': {
      transform: 'translateY(-1px) scale(0.98)',
    },
    '&:disabled': {
      background: `
        linear-gradient(135deg,
          rgba(30, 41, 59, 0.6) 0%,
          rgba(15, 23, 42, 0.8) 100%
        )
      `,
      color: theme.colors.text.tertiary,
      boxShadow: 'none',
      transform: 'none',
      '&::before': {
        display: 'none',
      },
    },
  } : {
    background: `
      linear-gradient(135deg,
        rgba(15, 23, 42, 0.8) 0%,
        rgba(30, 41, 59, 0.6) 100%
      )
    `,
    border: '1px solid rgba(255, 255, 255, 0.15)',
    color: theme.colors.text.primary,
    backdropFilter: 'blur(20px)',
    boxShadow: `
      0 4px 20px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.1)
    `,
    '&:hover': {
      background: `
        linear-gradient(135deg,
          rgba(30, 41, 59, 0.9) 0%,
          rgba(15, 23, 42, 0.8) 100%
        )
      `,
      border: '1px solid rgba(255, 255, 255, 0.25)',
      transform: 'translateY(-2px)',
      boxShadow: `
        0 8px 32px rgba(0, 0, 0, 0.4),
        0 0 40px ${theme.colors.primary.main}15,
        inset 0 1px 0 rgba(255, 255, 255, 0.15)
      `,
    },
  }),
}));

const FileUploadArea = styled(Box)(() => ({
  border: '2px dashed rgba(255, 255, 255, 0.15)',
  borderRadius: '24px',
  padding: '32px 24px',
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  background: `
    linear-gradient(135deg,
      rgba(15, 23, 42, 0.6) 0%,
      rgba(30, 41, 59, 0.4) 50%,
      rgba(15, 23, 42, 0.6) 100%
    )
  `,
  backdropFilter: 'blur(15px)',
  position: 'relative',
  overflow: 'hidden',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  minHeight: '240px',
  width: '100%',

  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: `
      radial-gradient(circle at 30% 70%, ${theme.colors.primary.main}10, transparent),
      radial-gradient(circle at 70% 30%, ${theme.colors.secondary.main}08, transparent)
    `,
    opacity: 0,
    transition: 'opacity 0.3s ease',
    pointerEvents: 'none',
  },

  '&:hover': {
    borderColor: theme.colors.primary.main,
    transform: 'translateY(-4px)',
    boxShadow: `
      0 12px 40px rgba(0, 0, 0, 0.4),
      0 0 60px ${theme.colors.primary.main}20,
      inset 0 1px 0 rgba(255, 255, 255, 0.1)
    `,
    '&::before': {
      opacity: 1,
    },
  },

  '&:active': {
    transform: 'translateY(-2px)',
  },
}));

const StyledIconButton = styled(IconButton)(() => ({
  color: theme.colors.text.secondary,
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  borderRadius: '12px',
  padding: '12px',
  background: `
    linear-gradient(135deg,
      rgba(15, 23, 42, 0.8) 0%,
      rgba(30, 41, 59, 0.6) 100%
    )
  `,
  border: '1px solid rgba(255, 255, 255, 0.1)',
  backdropFilter: 'blur(10px)',

  '&:hover': {
    color: theme.colors.text.primary,
    background: `
      linear-gradient(135deg,
        rgba(30, 41, 59, 0.9) 0%,
        rgba(15, 23, 42, 0.8) 100%
      )
    `,
    border: '1px solid rgba(255, 255, 255, 0.2)',
    transform: 'scale(1.1) rotate(5deg)',
    boxShadow: `
      0 8px 32px rgba(0, 0, 0, 0.3),
      0 0 40px ${theme.colors.primary.main}15
    `,
  },
}));

const TabPanel = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && children}
  </div>
);

/**
 * AddVideoModal Component
 * Modal for adding new videos via YouTube URL or file upload
 * Features tabbed interface for different input methods
 */
const AddVideoModal = ({ open, onClose, onSubmit }) => {
  const [tabValue, setTabValue] = useState(0);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [uploadFile, setUploadFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setError('');
  };

  const handleClose = () => {
    setYoutubeUrl('');
    setUploadFile(null);
    setError('');
    setLoading(false);
    setTabValue(0);
    onClose();
  };
  const validateYouTubeUrl = (url) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/;
    return youtubeRegex.test(url);
  };

  const handleSubmit = async () => {
    setError('');
    setLoading(true);

    try {
      if (tabValue === 0) {
        // YouTube URL submission
        if (!youtubeUrl.trim()) {
          throw new Error('Please enter a YouTube URL');
        }
        if (!validateYouTubeUrl(youtubeUrl)) {
          throw new Error('Please enter a valid YouTube URL');
        }

        await onSubmit({ type: 'youtube', url: youtubeUrl });
      } else {
        // File upload submission
        if (!uploadFile) {
          throw new Error('Please select a video file');
        }

        await onSubmit({ type: 'file', file: uploadFile });
      }

      handleClose();
    } catch (err) {
      setError(err.message || 'An error occurred while processing your request');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      const validTypes = ['video/mp4', 'video/webm', 'video/ogg'];
      if (!validTypes.includes(file.type)) {
        setError('Please select a valid video file (MP4, WebM, or OGG)');
        return;
      }

      // Validate file size (100MB limit)
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (file.size > maxSize) {
        setError('File size must be less than 100MB');
        return;
      }

      setUploadFile(file);
      setError('');
    }
  };

  return (
    <StyledDialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
    >
      <StyledDialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{
            p: 2,
            borderRadius: '16px',
            background: `
              linear-gradient(135deg,
                ${theme.colors.primary.main}25,
                ${theme.colors.secondary.main}15
              )
            `,
            border: '1px solid rgba(255, 255, 255, 0.1)',
            backdropFilter: 'blur(10px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
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
                radial-gradient(circle at 30% 30%, ${theme.colors.primary.main}20, transparent),
                radial-gradient(circle at 70% 70%, ${theme.colors.secondary.main}15, transparent)
              `,
              animation: 'pulse 3s ease-in-out infinite',
            },
            '@keyframes pulse': {
              '0%, 100%': { opacity: 0.5 },
              '50%': { opacity: 1 },
            },
          }}>
            <YouTubeIcon sx={{
              color: theme.colors.primary.main,
              fontSize: '1.8rem',
              position: 'relative',
              zIndex: 1,
            }} />
          </Box>
          <Box>
            <Typography variant="h5" sx={{
              fontWeight: 800,
              background: `linear-gradient(135deg, ${theme.colors.text.primary}, ${theme.colors.primary.main})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 0.5,
            }}>
              Add New Video
            </Typography>
            <Typography variant="body2" sx={{
              color: theme.colors.text.secondary,
              fontWeight: 500,
            }}>
              Analyze emotions in your video content
            </Typography>
          </Box>
        </Box>

        <StyledIconButton onClick={handleClose}>
          <CloseIcon />
        </StyledIconButton>
      </StyledDialogTitle>

      <DialogContent sx={{
        p: '32px',
        pt: '24px',
        pb: '16px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
        minHeight: '60px',
        position: 'relative',
        zIndex: 1,
      }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          style={{
            width: '100%',
            maxWidth: '600px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Box sx={{
            width: '100%',
            mb: 3,
            display: 'flex',
            justifyContent: 'center',
          }}>
            <StyledTabs value={tabValue} onChange={handleTabChange} variant="fullWidth">
              <Tab
                icon={<LinkIcon fontSize="small" />}
                label="YouTube URL"
                iconPosition="start"
              />
              <Tab
                icon={<UploadIcon fontSize="small" />}
                label="Upload File"
                iconPosition="start"
              />
            </StyledTabs>
          </Box>

          <AnimatePresence mode="wait">
            <motion.div
              key={tabValue}
              initial={{ opacity: 0, x: tabValue === 0 ? -20 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: tabValue === 0 ? 20 : -20 }}
              transition={{ duration: 0.3 }}
              style={{
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
              }}
            >
              <TabPanel value={tabValue} index={0}>
                <Box sx={{
                  width: '100%',
                  display: 'flex',
                  justifyContent: 'center',
                  mb: 2,
                }}>
                  <InputContainer sx={{
                    width: '100%',
                    maxWidth: '550px',
                    textAlign: 'center',
                  }}>
                    <Box sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 1,
                      mb: 2,
                    }}>
                      <YouTubeIcon sx={{
                        color: theme.colors.primary.main,
                        fontSize: '1.5rem',
                        filter: `drop-shadow(0 0 10px ${theme.colors.primary.main}40)`,
                      }} />
                      <Typography variant="h6" sx={{
                        color: theme.colors.text.primary,
                        fontWeight: 700,
                      }}>
                        YouTube Video
                      </Typography>
                    </Box>

                    <Typography variant="body2" sx={{
                      color: theme.colors.text.secondary,
                      mb: 3,
                      fontWeight: 500,
                      lineHeight: 1.6,
                      maxWidth: '480px',
                      margin: '0 auto 24px auto',
                    }}>
                      Enter a YouTube URL to analyze the video's emotional content using our advanced AI algorithms
                    </Typography>

                    <Box sx={{ position: 'relative', width: '100%' }}>
                      <StyledTextField
                        fullWidth
                        label="YouTube URL"
                        placeholder="https://www.youtube.com/watch?v=..."
                        value={youtubeUrl}
                        onChange={(e) => setYoutubeUrl(e.target.value)}
                        disabled={loading}
                        variant="outlined"
                        InputProps={{
                          startAdornment: (
                            <Box sx={{
                              mr: 1,
                              display: 'flex',
                              alignItems: 'center',
                              p: 1,
                              borderRadius: '8px',
                              background: `linear-gradient(135deg, ${theme.colors.primary.main}15, ${theme.colors.secondary.main}10)`,
                            }}>
                              <LinkIcon sx={{
                                color: theme.colors.primary.main,
                                fontSize: '1.2rem',
                              }} />
                            </Box>
                          ),
                        }}
                        sx={{
                          position: 'relative',
                          '&::before': {
                            content: '""',
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            background: `
                              radial-gradient(circle at 20% 80%, ${theme.colors.primary.main}05, transparent),
                              radial-gradient(circle at 80% 20%, ${theme.colors.secondary.main}03, transparent)
                            `,
                            borderRadius: '16px',
                            pointerEvents: 'none',
                            zIndex: 0,
                          }
                        }}
                      />

                      {youtubeUrl && validateYouTubeUrl(youtubeUrl) && (
                        <motion.div
                          initial={{ opacity: 0, x: 10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3 }}
                          style={{
                            position: 'absolute',
                            right: 16,
                            top: '50%',
                            transform: 'translateY(-50%)',
                            zIndex: 2,
                          }}
                        >
                          <Box sx={{
                            background: `linear-gradient(135deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
                            borderRadius: '50%',
                            p: 0.5,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            boxShadow: `0 0 20px ${theme.colors.primary.main}40`,
                          }}>
                            <CheckIcon sx={{
                              color: 'white',
                              fontSize: '1rem',
                            }} />
                          </Box>
                        </motion.div>
                      )}
                    </Box>
                  </InputContainer>
                </Box>
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                <Box sx={{
                  width: '100%',
                  display: 'flex',
                  justifyContent: 'center',
                  mb: 2,
                }}>
                  <InputContainer sx={{
                    width: '100%',
                    maxWidth: '550px',
                    textAlign: 'center',
                  }}>
                    <Box sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 1,
                      mb: 2,
                    }}>
                      <VideoFileIcon sx={{
                        color: theme.colors.secondary.main,
                        fontSize: '1.5rem',
                        filter: `drop-shadow(0 0 10px ${theme.colors.secondary.main}40)`,
                      }} />
                      <Typography variant="h6" sx={{
                        color: theme.colors.text.primary,
                        fontWeight: 700,
                      }}>
                        Upload Video File
                      </Typography>
                    </Box>

                    <Typography variant="body2" sx={{
                      color: theme.colors.text.secondary,
                      mb: 3,
                      fontWeight: 500,
                      lineHeight: 1.6,
                      maxWidth: '480px',
                      margin: '0 auto 24px auto',
                    }}>
                      Upload a video file from your device for real-time emotion analysis (MP4, WebM, OGG • Max 100MB)
                    </Typography>

                    <Box sx={{
                      width: '100%',
                      mt: 1,
                      display: 'flex',
                      justifyContent: 'center',
                    }}>
                      <FileUploadArea
                        onClick={() => document.getElementById('video-upload').click()}
                        sx={{
                          width: '100%',
                          maxWidth: '480px',
                        }}
                      >
                    <input
                      type="file"
                      accept="video/*"
                      onChange={handleFileChange}
                      style={{ display: 'none' }}
                      id="video-upload"
                      disabled={loading}
                    />

                    <Box sx={{ position: 'relative', zIndex: 1 }}>
                      <motion.div
                        animate={{
                          y: [0, -10, 0],
                          rotate: [0, 5, -5, 0]
                        }}
                        transition={{
                          duration: 3,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      >
                        <UploadIcon sx={{
                          fontSize: '4rem',
                          color: theme.colors.primary.main,
                          mb: 2,
                          filter: `drop-shadow(0 0 20px ${theme.colors.primary.main}40)`,
                        }} />
                      </motion.div>

                      {uploadFile ? (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ duration: 0.3 }}
                        >
                          <Box sx={{
                            p: 3,
                            borderRadius: '16px',
                            background: `
                              linear-gradient(135deg,
                                ${theme.colors.primary.main}15,
                                ${theme.colors.secondary.main}10
                              )
                            `,
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            backdropFilter: 'blur(10px)',
                            mt: 2,
                            maxWidth: '400px',
                            margin: '16px auto 0 auto',
                          }}>
                            <Typography variant="h6" sx={{
                              color: theme.colors.text.primary,
                              fontWeight: 700,
                              mb: 1,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              gap: 1,
                              textAlign: 'center',
                            }}>
                              <VideoFileIcon sx={{ color: theme.colors.secondary.main }} />
                              {uploadFile.name}
                            </Typography>
                            <Typography variant="body2" sx={{
                              color: theme.colors.text.secondary,
                              fontWeight: 500,
                              textAlign: 'center',
                            }}>
                              Size: {(uploadFile.size / (1024 * 1024)).toFixed(2)} MB
                            </Typography>
                          </Box>
                        </motion.div>
                      ) : (
                        <Box sx={{ textAlign: 'center' }}>
                          <Typography variant="h6" sx={{
                            color: theme.colors.text.primary,
                            fontWeight: 700,
                            mb: 1,
                          }}>
                            Drop your video here
                          </Typography>
                          <Typography variant="body2" sx={{
                            color: theme.colors.text.secondary,
                            fontWeight: 500,
                            mb: 2,
                          }}>
                            Or click to browse files
                          </Typography>
                          <Typography variant="caption" sx={{
                            color: theme.colors.text.tertiary,
                            display: 'block',
                            fontStyle: 'italic',
                          }}>
                            Supports MP4, WebM, OGG • Max 100MB
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </FileUploadArea>
                    </Box>

                    {/* Unavailability Notice */}
                    <Box sx={{
                      mt: 3,
                      p: 3,
                      borderRadius: '16px',
                      background: `
                        linear-gradient(135deg,
                          rgba(251, 146, 60, 0.15),
                          rgba(245, 158, 11, 0.08)
                        )
                      `,
                      border: '1px solid rgba(251, 146, 60, 0.3)',
                      backdropFilter: 'blur(10px)',
                      textAlign: 'center',
                      maxWidth: '480px',
                      margin: '24px auto 0 auto',
                    }}>
                      <Typography variant="body2" sx={{
                        color: '#f59e0b',
                        fontWeight: 600,
                        mb: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 1,
                      }}>
                        ⚠️ Feature Currently Unavailable
                      </Typography>
                      <Typography variant="caption" sx={{
                        color: theme.colors.text.secondary,
                        fontWeight: 500,
                        lineHeight: 1.5,
                      }}>
                        Direct file upload is temporarily disabled. Please use the YouTube link option for video analysis.
                      </Typography>
                    </Box>
                  </InputContainer>
                </Box>
              </TabPanel>
            </motion.div>
          </AnimatePresence>

          {error && (
            <Box sx={{
              width: '100%',
              maxWidth: '550px',
              mt: 3,
              display: 'flex',
              justifyContent: 'center',
            }}>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
                style={{ width: '100%' }}
              >
                <Alert
                  severity="error"
                  sx={{
                    background: `
                      linear-gradient(135deg,
                        rgba(239, 68, 68, 0.15) 0%,
                        rgba(185, 28, 28, 0.1) 100%
                      )
                    `,
                    color: theme.colors.text.primary,
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '16px',
                    backdropFilter: 'blur(10px)',
                    textAlign: 'center',
                    '& .MuiAlert-icon': {
                      color: '#ef4444',
                    },
                  }}
                >
                  {error}
                </Alert>
              </motion.div>
            </Box>
          )}
        </motion.div>
      </DialogContent>

      <DialogActions sx={{
        p: '32px',
        pt: '24px',
        pb: '32px',
        gap: '16px',
        background: `
          linear-gradient(135deg,
            rgba(15, 23, 42, 0.8) 0%,
            rgba(30, 41, 59, 0.6) 100%
          )
        `,
        backdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        position: 'relative',
        zIndex: 1,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}>
        <Box sx={{
          display: 'flex',
          gap: '16px',
          alignItems: 'center',
          maxWidth: '400px',
          width: '100%',
        }}>
          <ActionButton
            onClick={handleClose}
            disabled={loading}
            sx={{
              flex: 1,
              padding: '10px 32px !important', // Force override with !important
              height: '44px !important', // Force exact height
              minHeight: '44px !important', // Ensure minimum height
              maxHeight: '44px !important', // Prevent height expansion
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              lineHeight: '1.2 !important', // Control line height
            }}
          >
            Cancel
          </ActionButton>

          <ActionButton
            variant="contained"
            onClick={handleSubmit}
            disabled={loading || (tabValue === 0 ? !youtubeUrl.trim() : true)} // Disable for file upload tab
            startIcon={loading ? <CircularProgress size={16} color="inherit" /> : null}
            sx={{
              flex: 1,
              padding: '10px 32px !important', // Force override with !important
              height: '44px !important', // Force exact height
              minHeight: '44px !important', // Ensure minimum height
              maxHeight: '44px !important', // Prevent height expansion
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              lineHeight: '1.2 !important', // Control line height
              ...(tabValue === 1 && {
                opacity: 0.5,
                cursor: 'not-allowed',
                background: `${theme.colors.surface.glass} !important`,
                '&:hover': {
                  background: `${theme.colors.surface.glass} !important`,
                  transform: 'none !important', // Prevent hover transform when disabled
                }
              })
            }}
            title={tabValue === 1 ? 'File upload functionality is currently unavailable' : ''}
          >
            {loading ? 'Processing...' : tabValue === 1 ? 'Upload Not Available' : 'Add Video'}
          </ActionButton>
        </Box>
      </DialogActions>
    </StyledDialog>
  );
};

export default AddVideoModal;
