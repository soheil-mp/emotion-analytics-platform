import React from 'react';
import { motion } from 'framer-motion';
import { Box, Typography } from '@mui/material';
import { PsychologyAlt as PsychologyIcon } from '@mui/icons-material';
import EmotionCurrent from './EmotionCurrent';
import theme from '../theme';

/**
 * EmotionPulse Module
 * Displays current emotion analysis in the top-right position
 * Real-time emotion detection with premium styling
 */
const EmotionPulse = ({
  emotion,
  subEmotion,
  intensity,
  relatedEmotions = [],
  isActive = false
}) => {
  return (
    <Box sx={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <Box sx={{
        p: 3,
        borderBottom: `1px solid ${theme.colors.border}`,
        background: `linear-gradient(135deg, ${theme.colors.primary.main}10, ${theme.colors.secondary.main}05)`,
      }}>
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box sx={{
              p: 1.5,
              borderRadius: theme.borderRadius.lg,
              background: `linear-gradient(135deg, ${theme.colors.primary.main}20, ${theme.colors.secondary.main}10)`,
              border: `1px solid ${theme.colors.primary.main}40`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <PsychologyIcon sx={{
                color: theme.colors.primary.main,
                fontSize: '1.25rem'
              }} />
            </Box>

            <Box>
              <Typography variant="h6" sx={{
                color: theme.colors.text.primary,
                fontSize: theme.typography.fontSize.lg,
                fontWeight: theme.typography.fontWeight.semibold,
                mb: 0.5,
                textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              }}>
                Emotion Pulse
              </Typography>
              <Typography variant="body2" sx={{
                color: theme.colors.text.tertiary,
                fontSize: theme.typography.fontSize.sm,
              }}>
                Real-time analysis
              </Typography>
            </Box>
          </Box>

          {isActive && (
            <Box sx={{
              mt: 1,
              px: 2,
              py: 0.5,
              background: theme.colors.status.successBg,
              border: `1px solid ${theme.colors.status.success}40`,
              borderRadius: theme.borderRadius.full,
              display: 'inline-flex',
              alignItems: 'center',
              fontSize: theme.typography.fontSize.xs,
              color: theme.colors.status.success,
              fontWeight: theme.typography.fontWeight.medium,
            }}>
              <motion.div
                animate={{
                  scale: [1, 1.2, 1],
                  opacity: [0.7, 1, 0.7],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: theme.colors.status.success,
                  marginRight: 6,
                }}
              />
              LIVE
            </Box>
          )}
        </motion.div>
      </Box>

      {/* Main Content Area */}
      <Box sx={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        p: 3,
        position: 'relative',
      }}>
        {/* Background decorative elements */}
        <motion.div
          animate={{
            rotate: [0, 360],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: 'linear',
          }}
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: 100,
            height: 100,
            background: `radial-gradient(circle, ${theme.colors.primary.main}20 0%, transparent 70%)`,
            borderRadius: '50%',
            zIndex: 0,
          }}
        />

        {/* Emotion Display */}
        <Box sx={{
          position: 'relative',
          zIndex: 1,
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <EmotionCurrent
            emotion={emotion}
            subEmotion={subEmotion}
            intensity={intensity}
            relatedEmotions={relatedEmotions}
            compact={true}
          />
        </Box>
      </Box>

      {/* Footer with additional info */}
      {(emotion || intensity) && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Box sx={{
            p: 2,
            borderTop: `1px solid ${theme.colors.border}`,
            background: theme.colors.surface.glass,
          }}>
            <Box sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 1,
            }}>
              <Typography variant="body2" sx={{
                color: theme.colors.text.secondary,
                fontSize: theme.typography.fontSize.sm,
                fontWeight: theme.typography.fontWeight.medium,
              }}>
                Current State
              </Typography>
              <Box sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}>
                <Box sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: emotion ? theme.colors.emotion[emotion] || theme.colors.primary.main : theme.colors.text.tertiary,
                }} />
                <Typography variant="caption" sx={{
                  color: theme.colors.text.primary,
                  fontSize: theme.typography.fontSize.xs,
                  fontWeight: theme.typography.fontWeight.semibold,
                  textTransform: 'capitalize',
                }}>
                  {emotion || 'Analyzing...'}
                </Typography>
              </Box>
            </Box>

            {intensity && (
              <Box sx={{ mt: 1 }}>
                <Box sx={{
                  height: 4,
                  background: theme.colors.surface.card,
                  borderRadius: theme.borderRadius.full,
                  overflow: 'hidden',
                }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${intensity * 100}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    style={{
                      height: '100%',
                      background: `linear-gradient(90deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
                      borderRadius: theme.borderRadius.full,
                    }}
                  />
                </Box>
                <Typography variant="caption" sx={{
                  color: theme.colors.text.tertiary,
                  fontSize: theme.typography.fontSize.xs,
                  mt: 0.5,
                  display: 'block',
                }}>
                  Intensity: {Math.round((intensity || 0) * 100)}%
                </Typography>
              </Box>
            )}
          </Box>
        </motion.div>
      )}
    </Box>
  );
};

export default EmotionPulse;
