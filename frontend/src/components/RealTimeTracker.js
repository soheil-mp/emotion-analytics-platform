import React from 'react';
import { motion } from 'framer-motion';
import { Box, Typography } from '@mui/material';
import { Timeline as TimelineIcon } from '@mui/icons-material';
import EmotionTimeline from './EmotionTimeline';
import theme from '../theme';

/**
 * RealTimeTracker Module
 * Displays emotion timeline analysis in the bottom-left position
 * Shows emotion changes over time with timeline visualization
 */
const RealTimeTracker = ({
  data = [],
  currentTime = 0,
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
        background: `linear-gradient(135deg, ${theme.colors.secondary.main}10, ${theme.colors.primary.main}05)`,
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
              background: `linear-gradient(135deg, ${theme.colors.secondary.main}20, ${theme.colors.primary.main}10)`,
              border: `1px solid ${theme.colors.secondary.main}40`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <TimelineIcon sx={{
                color: theme.colors.secondary.main,
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
                Real-Time Tracker
              </Typography>
              <Typography variant="body2" sx={{
                color: theme.colors.text.tertiary,
                fontSize: theme.typography.fontSize.sm,
              }}>
                Emotion timeline
              </Typography>
            </Box>
          </Box>

          {isActive && (
            <Box sx={{
              mt: 1,
              px: 2,
              py: 0.5,
              background: theme.colors.status.infoBg,
              border: `1px solid ${theme.colors.status.info}40`,
              borderRadius: theme.borderRadius.full,
              display: 'inline-flex',
              alignItems: 'center',
              fontSize: theme.typography.fontSize.xs,
              color: theme.colors.status.info,
              fontWeight: theme.typography.fontWeight.medium,
            }}>
              <motion.div
                animate={{
                  x: [-2, 2, -2],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: theme.colors.status.info,
                  marginRight: 6,
                }}
              />
              TRACKING
            </Box>
          )}
        </motion.div>
      </Box>

      {/* Main Content Area */}
      <Box sx={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        p: 2,
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Background decorative elements */}
        <motion.div
          animate={{
            rotate: [0, -360],
            scale: [1, 1.05, 1],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: 'linear',
          }}
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            width: 80,
            height: 80,
            background: `radial-gradient(circle, ${theme.colors.secondary.main}15 0%, transparent 70%)`,
            borderRadius: '50%',
            zIndex: 0,
          }}
        />

        {/* Timeline Display */}
        <Box sx={{
          position: 'relative',
          zIndex: 1,
          height: '100%',
          minHeight: 250,
        }}>
          {data && data.length > 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              style={{ height: '100%' }}
            >
              <EmotionTimeline
                data={data}
                currentTime={currentTime}
              />
            </motion.div>
          ) : (
            <Box sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: theme.colors.text.tertiary,
              textAlign: 'center',
            }}>
              <motion.div
                animate={{
                  y: [-5, 5, -5],
                  opacity: [0.5, 0.8, 0.5],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
              >
                <TimelineIcon sx={{ fontSize: '3rem', mb: 2, opacity: 0.3 }} />
              </motion.div>

              <Typography variant="body2" sx={{
                color: theme.colors.text.secondary,
                fontWeight: theme.typography.fontWeight.medium,
                mb: 1,
              }}>
                No timeline data
              </Typography>

              <Typography variant="caption" sx={{
                color: theme.colors.text.tertiary,
                fontSize: theme.typography.fontSize.xs,
              }}>
                Process a video to see emotion changes over time
              </Typography>
            </Box>
          )}
        </Box>
      </Box>

      {/* Footer with stats */}
      {data && data.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Box sx={{
            p: 2,
            borderTop: `1px solid ${theme.colors.border}`,
            background: theme.colors.surface.glass,
          }}>
            <Box sx={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 2,
            }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" sx={{
                  color: theme.colors.text.primary,
                  fontSize: theme.typography.fontSize.lg,
                  fontWeight: theme.typography.fontWeight.semibold,
                }}>
                  {data.length}
                </Typography>
                <Typography variant="caption" sx={{
                  color: theme.colors.text.tertiary,
                  fontSize: theme.typography.fontSize.xs,
                }}>
                  Data Points
                </Typography>
              </Box>

              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" sx={{
                  color: theme.colors.text.primary,
                  fontSize: theme.typography.fontSize.lg,
                  fontWeight: theme.typography.fontWeight.semibold,
                }}>
                  {Math.round(currentTime)}s
                </Typography>
                <Typography variant="caption" sx={{
                  color: theme.colors.text.tertiary,
                  fontSize: theme.typography.fontSize.xs,
                }}>
                  Current Time
                </Typography>
              </Box>
            </Box>
          </Box>
        </motion.div>
      )}
    </Box>
  );
};

export default RealTimeTracker;
