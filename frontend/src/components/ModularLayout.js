import React from 'react';
import { motion } from 'framer-motion';
import { Box } from '@mui/material';
import { styled } from '@mui/material/styles';
import theme from '../theme';

// Styled Components
const LayoutContainer = styled(Box)(() => ({
  display: 'grid',
  gridTemplateColumns: '1fr 2fr 1fr',
  gridTemplateRows: '1fr 1fr',
  gap: theme.spacing.lg,
  height: '100vh',
  padding: theme.spacing.lg,
  paddingLeft: '80px', // Account for sidebar space
  boxSizing: 'border-box',
  minHeight: '600px',
  background: theme.colors.background.primary,
  overflow: 'hidden',
}));

const ModuleContainer = styled(motion.div)(() => ({
  borderRadius: theme.borderRadius['2xl'],
  background: theme.glassmorphism.primary.background,
  backdropFilter: theme.glassmorphism.primary.backdropFilter,
  border: theme.glassmorphism.primary.border,
  boxShadow: theme.shadows.lg,
  overflow: 'hidden',
  display: 'flex',
  flexDirection: 'column',
  position: 'relative',
  transition: `all ${theme.animation.duration.normal} ${theme.animation.easing.easeOut}`,

  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows.xl,
    border: `1px solid ${theme.colors.borderHover}`,
  },

  // Add subtle glow effect for active modules
  '&.active': {
    boxShadow: theme.shadows.glow,
    border: `1px solid ${theme.colors.borderActive}`,
  },
}));

const PlaceholderContainer = styled(Box)(() => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  color: theme.colors.text.tertiary,
  textAlign: 'center',
  padding: theme.spacing.xl,
  background: `linear-gradient(135deg, ${theme.colors.surface.glass}, rgba(255,255,255,0.05))`,
  borderRadius: theme.borderRadius.xl,
  border: `2px dashed ${theme.colors.border}`,

  '& svg': {
    fontSize: '3rem',
    marginBottom: theme.spacing.md,
    opacity: 0.5,
  },
}));

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const moduleVariants = {
  hidden: {
    opacity: 0,
    scale: 0.9,
    y: 20,
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: 'easeOut',
    },
  },
};

// Placeholder component for empty modules
const PlaceholderModule = ({ title, subtitle, icon, className = '' }) => (
  <PlaceholderContainer className={className}>
    {icon}
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <Box sx={{
        fontSize: theme.typography.fontSize.lg,
        fontWeight: theme.typography.fontWeight.semibold,
        color: theme.colors.text.secondary,
        marginBottom: theme.spacing.sm,
      }}>
        {title}
      </Box>
      <Box sx={{
        fontSize: theme.typography.fontSize.sm,
        color: theme.colors.text.tertiary,
        fontStyle: 'italic',
      }}>
        {subtitle}
      </Box>
    </motion.div>
  </PlaceholderContainer>
);

/**
 * ModularLayout Component
 * 5-box grid layout system for the dashboard
 * Layout: 2 small boxes left, 1 large center, 2 small boxes right
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.topLeft - Top left module
 * @param {React.ReactNode} props.bottomLeft - Bottom left module
 * @param {React.ReactNode} props.center - Center module (main content)
 * @param {React.ReactNode} props.topRight - Top right module
 * @param {React.ReactNode} props.bottomRight - Bottom right module
 * @param {string} props.className - Additional CSS classes
 */
const ModularLayout = ({
  topLeft,
  bottomLeft,
  center,
  topRight,
  bottomRight,
  className = '',
  ...props
}) => {
  return (
    <LayoutContainer
      className={`modular-layout ${className}`}
      component={motion.div}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      {...props}
    >
      {/* Top Left Module */}
      <ModuleContainer
        className="module module-top-left"
        style={{
          gridArea: '1 / 1',
        }}
        variants={moduleVariants}
        whileHover={{ y: -4 }}
      >
        {topLeft || (
          <PlaceholderModule
            title="Coming Soon"
            subtitle="New features will be added here"
            icon={
              <Box
                component="div"
                sx={{
                  width: 60,
                  height: 60,
                  borderRadius: '50%',
                  background: `linear-gradient(135deg, ${theme.colors.primary.main}20, ${theme.colors.secondary.main}10)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.5rem',
                }}
              >
                ✨
              </Box>
            }
          />
        )}
      </ModuleContainer>

      {/* Bottom Left Module */}
      <ModuleContainer
        className="module module-bottom-left"
        style={{
          gridArea: '2 / 1',
        }}
        variants={moduleVariants}
        whileHover={{ y: -4 }}
      >
        {bottomLeft}
      </ModuleContainer>

      {/* Center Module (spans both rows) */}
      <ModuleContainer
        className="module module-center"
        style={{
          gridColumn: '2',
          gridRow: '1 / -1',
        }}
        variants={moduleVariants}
        whileHover={{ y: -4 }}
      >
        {center}
      </ModuleContainer>

      {/* Top Right Module */}
      <ModuleContainer
        className="module module-top-right"
        style={{
          gridArea: '1 / 3',
        }}
        variants={moduleVariants}
        whileHover={{ y: -4 }}
      >
        {topRight}
      </ModuleContainer>

      {/* Bottom Right Module */}
      <ModuleContainer
        className="module module-bottom-right"
        style={{
          gridArea: '2 / 3',
        }}
        variants={moduleVariants}
        whileHover={{ y: -4 }}
      >
        {bottomRight || (
          <PlaceholderModule
            title="Future Module"
            subtitle="Additional functionality coming soon"
            icon={
              <Box
                component="div"
                sx={{
                  width: 60,
                  height: 60,
                  borderRadius: '50%',
                  background: `linear-gradient(135deg, ${theme.colors.secondary.main}20, ${theme.colors.primary.main}10)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.5rem',
                }}
              >
                🚀
              </Box>
            }
          />
        )}
      </ModuleContainer>
    </LayoutContainer>
  );
};

export { PlaceholderModule };
export default ModularLayout;
