import React from 'react';
import { motion } from 'framer-motion';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Close as CloseIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import theme from '../theme';

// Styled Components
const StyledDialog = styled(Dialog)(() => ({
  '& .MuiDialog-paper': {
    background: theme.glassmorphism.primary.background,
    backdropFilter: theme.glassmorphism.primary.backdropFilter,
    border: theme.glassmorphism.primary.border,
    borderRadius: theme.borderRadius['2xl'],
    boxShadow: theme.shadows['2xl'],
    color: theme.colors.text.primary,
    minWidth: '600px',
    maxWidth: '700px',
  },
  '& .MuiBackdrop-root': {
    background: theme.colors.surface.overlay,
    backdropFilter: 'blur(8px)',
  },
}));

const StyledDialogTitle = styled(DialogTitle)(() => ({
  background: `linear-gradient(135deg, ${theme.colors.primary.main}15, ${theme.colors.secondary.main}08)`,
  borderBottom: `1px solid ${theme.colors.border}`,
  color: theme.colors.text.primary,
  fontWeight: theme.typography.fontWeight.bold,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing.xl,
}));

const ActionButton = styled(Button)(({ variant: buttonVariant }) => ({
  borderRadius: theme.borderRadius.lg,
  padding: `${theme.spacing.md} ${theme.spacing.xl}`,
  fontSize: theme.typography.fontSize.sm,
  fontWeight: theme.typography.fontWeight.semibold,
  textTransform: 'none',
  transition: `all ${theme.animation.duration.normal} ${theme.animation.easing.easeOut}`,

  ...(buttonVariant === 'contained' ? {
    background: `linear-gradient(135deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
    color: theme.colors.text.primary,
    boxShadow: theme.shadows.glow,
    '&:hover': {
      background: `linear-gradient(135deg, ${theme.colors.primary.light}, ${theme.colors.secondary.light})`,
      transform: 'translateY(-2px)',
      boxShadow: theme.shadows.xl,
    },
  } : {
    border: `1px solid ${theme.colors.border}`,
    color: theme.colors.text.secondary,
    background: 'transparent',
    '&:hover': {
      borderColor: theme.colors.borderHover,
      background: theme.colors.surface.glass,
      color: theme.colors.text.primary,
    },
  }),
}));

const ComingSoonContainer = styled(Box)(() => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing['4xl'],
  textAlign: 'center',
  minHeight: '400px',
  background: `linear-gradient(135deg, ${theme.colors.primary.main}08, ${theme.colors.secondary.main}04)`,
  borderRadius: theme.borderRadius['2xl'],
  border: `1px solid ${theme.colors.border}`,
  position: 'relative',
  overflow: 'hidden',
}));

const FloatingParticle = styled(Box)(({ delay = 0, size = 4 }) => ({
  position: 'absolute',
  width: `${size}px`,
  height: `${size}px`,
  borderRadius: '50%',
  background: `linear-gradient(45deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
  opacity: 0.6,
  animation: `float 6s ease-in-out infinite ${delay}s`,
  '@keyframes float': {
    '0%, 100%': {
      transform: 'translateY(0px) rotate(0deg)',
      opacity: 0.6,
    },
    '50%': {
      transform: 'translateY(-20px) rotate(180deg)',
      opacity: 1,
    },
  },
}));

/**
 * SettingsModal Component
 * Simplified modal showing "Coming Soon" message for settings
 */
const SettingsModal = ({ open, onClose }) => {
  return (
    <StyledDialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <StyledDialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{
            p: 1.5,
            borderRadius: theme.borderRadius.lg,
            background: `linear-gradient(135deg, ${theme.colors.primary.main}20, ${theme.colors.secondary.main}10)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <SettingsIcon sx={{ color: theme.colors.primary.main }} />
          </Box>
          <Typography variant="h6" sx={{ fontWeight: theme.typography.fontWeight.bold }}>
            Settings
          </Typography>
        </Box>

        <IconButton
          onClick={onClose}
          sx={{
            color: theme.colors.text.secondary,
            '&:hover': {
              background: theme.colors.surface.glass,
              color: theme.colors.text.primary,
            },
          }}
        >
          <CloseIcon />
        </IconButton>
      </StyledDialogTitle>

      <DialogContent sx={{ p: theme.spacing.xl }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <ComingSoonContainer>
            {/* Floating Particles */}
            <FloatingParticle delay={0} size={4} sx={{ top: '20%', left: '15%' }} />
            <FloatingParticle delay={1} size={6} sx={{ top: '60%', right: '20%' }} />
            <FloatingParticle delay={2} size={3} sx={{ bottom: '30%', left: '25%' }} />
            <FloatingParticle delay={0.5} size={5} sx={{ top: '40%', right: '35%' }} />
            <FloatingParticle delay={1.5} size={4} sx={{ bottom: '20%', right: '15%' }} />

            {/* Main Content */}
            <Box sx={{
              p: 3,
              borderRadius: theme.borderRadius.xl,
              background: `linear-gradient(135deg, ${theme.colors.primary.main}15, ${theme.colors.secondary.main}08)`,
              border: `1px solid ${theme.colors.primary.main}30`,
              mb: 4,
              position: 'relative',
              zIndex: 1,
            }}>
              <Box sx={{
                fontSize: '3rem',
                mb: 2,
                background: `linear-gradient(135deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                filter: 'drop-shadow(0 0 10px rgba(99, 102, 241, 0.3))',
              }}>
                🚀
              </Box>

              <Typography variant="h4" sx={{
                color: theme.colors.text.primary,
                fontWeight: theme.typography.fontWeight.bold,
                mb: 2,
                background: `linear-gradient(135deg, ${theme.colors.primary.main}, ${theme.colors.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                Coming Soon
              </Typography>

              <Typography variant="h6" sx={{
                color: theme.colors.text.secondary,
                fontWeight: theme.typography.fontWeight.medium,
                mb: 3,
              }}>
                Advanced Settings Panel
              </Typography>

              <Typography variant="body1" sx={{
                color: theme.colors.text.secondary,
                lineHeight: 1.6,
                maxWidth: '400px',
              }}>
                We're crafting an incredible settings experience with advanced customization options,
                theme controls, and powerful configuration tools. Stay tuned for the cosmic update!
              </Typography>
            </Box>

            {/* Feature Preview */}
            <Box sx={{
              display: 'flex',
              gap: 2,
              flexWrap: 'wrap',
              justifyContent: 'center',
              opacity: 0.7,
            }}>
              {['Theme Customization', 'Advanced Analytics', 'Notification Controls', 'Privacy Settings'].map((feature, index) => (
                <Box key={feature} sx={{
                  px: 2,
                  py: 1,
                  borderRadius: theme.borderRadius.lg,
                  background: theme.colors.surface.glass,
                  border: `1px solid ${theme.colors.border}`,
                  fontSize: theme.typography.fontSize.xs,
                  color: theme.colors.text.secondary,
                  fontWeight: theme.typography.fontWeight.medium,
                }}>
                  {feature}
                </Box>
              ))}
            </Box>
          </ComingSoonContainer>
        </motion.div>
      </DialogContent>

      <DialogActions sx={{
        p: theme.spacing.xl,
        pt: 0,
        gap: theme.spacing.md,
        borderTop: `1px solid ${theme.colors.border}`,
        justifyContent: 'center',
      }}>
        <ActionButton variant="contained" onClick={onClose}>
          Got it!
        </ActionButton>
      </DialogActions>
    </StyledDialog>
  );
};

export default SettingsModal;
