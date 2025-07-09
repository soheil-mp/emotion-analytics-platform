import React, { useEffect } from 'react';
import { Box, Typography } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { styled } from '@mui/material/styles';
import { getEmotionColor, getIntensityValue } from '../utils';

// Enhanced Cosmic Emotion Pulse Container with starfield animation
const EmotionPulse = styled(Box)(({ theme, compact }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  flex: 1,
  position: 'relative',
  overflow: 'hidden',
  padding: compact ? theme.spacing(1, 0) : theme.spacing(4, 0),
  borderRadius: theme.shape.borderRadius * 2,
  background: `
    linear-gradient(135deg,
      rgba(6, 11, 40, 0.95) 0%,
      rgba(20, 25, 60, 0.9) 25%,
      rgba(15, 23, 42, 0.95) 50%,
      rgba(8, 15, 35, 0.98) 75%,
      rgba(2, 6, 23, 1) 100%
    )
  `,
  backdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  boxShadow: `
    0 20px 60px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    inset 0 -1px 0 rgba(255, 255, 255, 0.05)
  `,
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
      radial-gradient(2px 2px at 200px 25px, rgba(147,197,253,0.5), transparent),
      radial-gradient(1px 1px at 30px 200px, rgba(255,255,255,0.6), transparent),
      radial-gradient(1px 1px at 160px 160px, rgba(196,181,253,0.7), transparent)
    `,
    backgroundRepeat: 'repeat',
    backgroundSize: '250px 150px',
    animation: 'cosmicDrift 25s linear infinite',
    opacity: 0.8
  },
  '@keyframes cosmicDrift': {
    '0%': {
      transform: 'translateY(0px) translateX(0px)',
      opacity: 0.8
    },
    '50%': {
      transform: 'translateY(-75px) translateX(10px)',
      opacity: 1
    },
    '100%': {
      transform: 'translateY(-150px) translateX(0px)',
      opacity: 0.8
    }
  }
}));

// Enhanced Emotion Orb with sophisticated visual effects
const EmotionOrb = styled(motion.div)(({ color, size = 120, intensity = 0.5, compact }) => ({
  width: compact ? size * 0.8 : size,
  height: compact ? size * 0.8 : size,
  borderRadius: '50%',
  background: `
    radial-gradient(circle at 30% 30%, ${color}FF 0%, ${color}DD 25%, ${color}BB 50%, ${color}88 75%, ${color}33 100%),
    radial-gradient(circle at 70% 70%, ${color}77 0%, ${color}44 50%, ${color}11 100%)
  `,
  boxShadow: `
    0 0 ${30 * intensity}px ${20 * intensity}px ${color}44,
    0 0 ${60 * intensity}px ${40 * intensity}px ${color}22,
    0 0 ${90 * intensity}px ${60 * intensity}px ${color}11,
    inset 0 0 ${40 * intensity}px ${color}55,
    inset 0 ${5 * intensity}px ${20 * intensity}px rgba(255, 255, 255, 0.3)
  `,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  position: 'relative',
  zIndex: 2,
  isolation: 'isolate',
  cursor: 'pointer',
  transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: -size * (compact ? 0.12 : 0.18),
    left: -size * (compact ? 0.12 : 0.18),
    right: -size * (compact ? 0.12 : 0.18),
    bottom: -size * (compact ? 0.12 : 0.18),
    borderRadius: '50%',
    border: `3px solid ${color}33`,
    opacity: 0.8,
    animation: 'pulse 4s infinite ease-in-out',
    zIndex: -1,
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: -size * (compact ? 0.06 : 0.08),
    left: -size * (compact ? 0.06 : 0.08),
    right: -size * (compact ? 0.06 : 0.08),
    bottom: -size * (compact ? 0.06 : 0.08),
    borderRadius: '50%',
    border: `2px solid ${color}55`,
    opacity: 0.6,
    animation: 'pulse 3s 0.5s infinite ease-in-out',
    zIndex: -1,
  },
  '&:hover': {
    transform: 'scale(1.05)',
    boxShadow: `
      0 0 ${40 * intensity}px ${30 * intensity}px ${color}55,
      0 0 ${80 * intensity}px ${60 * intensity}px ${color}33,
      0 0 ${120 * intensity}px ${80 * intensity}px ${color}11,
      inset 0 0 ${50 * intensity}px ${color}66
    `,
  }
}));

const InnerGlow = styled(motion.div)(({ color, size = 60 }) => ({
  position: 'absolute',
  width: size,
  height: size,
  borderRadius: '50%',
  background: `radial-gradient(circle, ${color}99 0%, ${color}00 70%)`,
  opacity: 0.7,
}));

// Enhanced emotion label with modern gradient text
const EmotionLabel = styled(Typography)(({ color, compact }) => ({
  fontWeight: 800,
  fontSize: compact ? '2.2rem' : '2.8rem',
  background: `linear-gradient(135deg, ${color}, ${color}CC, ${color}99)`,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
  textTransform: 'capitalize',
  letterSpacing: '-0.03em',
  marginBottom: '0.5rem',
  fontFamily: '"Inter", sans-serif',
  fontVariant: 'small-caps',
  position: 'relative',
  textAlign: 'center',
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: '-8px',
    left: '50%',
    transform: 'translateX(-50%)',
    width: '60%',
    height: '3px',
    background: `linear-gradient(90deg, transparent, ${color}77, transparent)`,
    borderRadius: '2px',
  }
}));

// Modern intensity indicator with enhanced visual feedback
const IntensityIndicator = styled(motion.div)(({ color, intensity, compact }) => ({
  width: compact ? '140px' : '180px',
  height: compact ? '8px' : '12px',
  backgroundColor: 'rgba(0, 0, 0, 0.08)',
  borderRadius: '6px',
  overflow: 'hidden',
  marginTop: compact ? '8px' : '12px',
  position: 'relative',
  boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.1)',
  border: '1px solid rgba(255, 255, 255, 0.3)',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    height: '100%',
    width: `${Math.max(intensity * 100, 5)}%`,
    background: `linear-gradient(90deg, ${color}FF 0%, ${color}DD 50%, ${color}BB 100%)`,
    borderRadius: '6px',
    boxShadow: `0 0 12px ${color}88, inset 0 1px 0 rgba(255, 255, 255, 0.3)`,
    transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    height: '100%',
    width: `${Math.max(intensity * 100, 5)}%`,
    background: `linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)`,
    borderRadius: '6px',
    animation: 'shimmer 2s infinite ease-in-out',
  },
  '@keyframes shimmer': {
    '0%': { transform: 'translateX(-100%)' },
    '50%': { transform: 'translateX(0%)' },
    '100%': { transform: 'translateX(100%)' }
  },
  '@keyframes pulse': {
    '0%, 100%': {
      transform: 'scale(1)',
      opacity: 0.8
    },
    '50%': {
      transform: 'scale(1.02)',
      opacity: 1
    }
  }
}));

// Enhanced intensity percentage display
const IntensityPercentage = styled(Typography)(({ color, compact }) => ({
  fontSize: compact ? '0.9rem' : '1.1rem',
  fontWeight: 700,
  color: color,
  marginTop: '8px',
  textAlign: 'center',
  fontFamily: '"Inter", sans-serif',
  letterSpacing: '0.5px',
  marginLeft: '8px',
}));

// New styled component for sub-emotion display under the main emotion
const SubEmotionDisplay = styled(Typography)(({ color, compact }) => ({
  fontWeight: 500,
  fontSize: compact ? '0.8rem' : '0.95rem',
  color: color,
  textTransform: 'capitalize',
  opacity: 0.85,
  marginTop: '-0.2rem',
  marginBottom: compact ? '0.5rem' : '0.7rem',
  fontFamily: '"Inter", sans-serif',
}));

// Orbital Ring Component for cosmic effect
const OrbitalRing = styled(motion.div)(({ color, size, thickness = 2 }) => ({
  position: 'absolute',
  width: size,
  height: size,
  borderRadius: '50%',
  border: `${thickness}px solid ${color}30`,
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  pointerEvents: 'none'
}));

// Energy Wave Component
const EnergyWave = styled(motion.div)(({ color, size }) => ({
  position: 'absolute',
  width: size,
  height: size,
  borderRadius: '50%',
  border: `1px solid ${color}40`,
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  pointerEvents: 'none'
}));

// Cosmic Aura Component
const CosmicAura = styled(motion.div)(({ color, size }) => ({
  position: 'absolute',
  width: size,
  height: size,
  borderRadius: '50%',
  background: `radial-gradient(circle, ${color}15 0%, transparent 70%)`,
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  pointerEvents: 'none'
}));

// Ethereal Particle Component with enhanced movement
const EtherealParticle = styled(motion.div)(({ color, size = 3 }) => ({
  position: 'absolute',
  width: `${size}px`,
  height: `${size}px`,
  borderRadius: '50%',
  background: `radial-gradient(circle, ${color}, ${color}80)`,
  boxShadow: `0 0 ${size * 4}px ${color}`,
  filter: 'blur(0.5px)',
  opacity: 0.8,
}));

const EmotionCurrent = ({ emotion, subEmotion, intensity = 0.5, relatedEmotions = [], compact = false }) => {
  useEffect(() => {
    // Reset any effects when emotion changes
  }, [emotion]);

  if (!emotion) {
    const noEmotionColor = '#9CA3AF';
    const size = compact ? 90 : 120;

    // Enhanced ethereal particles for no emotion state - more spacey and abstract
    const noEmotionParticles = Array.from({ length: 8 }, (_, i) => ({
      id: i,
      angle: (i / 8) * Math.PI * 2,
      radius: 50 + Math.random() * 40,
      scale: 0.3 + Math.random() * 0.4,
      duration: 10 + Math.random() * 8,
      delay: i * 0.6,
      size: 2 + Math.random() * 3,
      spiralOffset: Math.random() * Math.PI * 2,
      type: i % 3 // 0: dot, 1: ring, 2: line
    }));

    return (
      <Box sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        justifyContent: 'center',
      }}>
        <EmotionPulse compact={compact}>
          <AnimatePresence mode="wait">
            <motion.div
              key="no-emotion"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.5 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                width: '100%',
                height: '100%',
                padding: '10px',
                position: 'relative',
              }}
            >
              <Box
                sx={{
                  position: 'relative',
                  width: compact ? (size + 120) : (size + 160),
                  height: compact ? (size + 120) : (size + 160),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginY: compact ? 0 : 0.5,
                }}
              >
                {/* Enhanced Cosmic Aura Background for No Emotion - Subtle and Minimalist */}
                <CosmicAura
                  color={noEmotionColor}
                  size={compact ? 180 : 250}
                  animate={{
                    opacity: [0.05, 0.15, 0.25, 0.15, 0.05],
                    scale: [0.8, 1.0, 1.1, 1.0, 0.8],
                    rotate: [0, 20, 40, 60, 80]
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 12,
                    ease: "easeInOut"
                  }}
                />

                {/* Secondary aura for subtle depth */}
                <CosmicAura
                  color={noEmotionColor}
                  size={compact ? 130 : 180}
                  animate={{
                    opacity: [0.08, 0.2, 0.3, 0.2, 0.08],
                    scale: [0.9, 1.1, 1.3, 1.0, 0.9],
                    rotate: [0, -30, -60, -90, -120]
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 8,
                    ease: "easeInOut",
                    delay: 0.5
                  }}
                />

                {/* Enhanced Orbital Rings for No Emotion - Slower and more contemplative */}
                <OrbitalRing
                  color={noEmotionColor}
                  size={size * 2.2}
                  thickness={1}
                  animate={{
                    rotate: [0, 360],
                    scale: [1, 1.02, 1],
                    opacity: [0.15, 0.3, 0.15]
                  }}
                  transition={{
                    rotate: { duration: 60, repeat: Infinity, ease: "linear" },
                    scale: { duration: 6, repeat: Infinity, ease: "easeInOut" },
                    opacity: { duration: 5, repeat: Infinity, ease: "easeInOut" }
                  }}
                />

                <OrbitalRing
                  color={noEmotionColor}
                  size={size * 1.6}
                  thickness={1.5}
                  animate={{
                    rotate: [0, -360],
                    scale: [1, 1.04, 1],
                    opacity: [0.2, 0.4, 0.2]
                  }}
                  transition={{
                    rotate: { duration: 45, repeat: Infinity, ease: "linear" },
                    scale: { duration: 4.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 },
                    opacity: { duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }
                  }}
                />

                {/* Ethereal Particles for No Emotion - Abstract Geometric Elements */}
                {noEmotionParticles.map((particle) => {
                  const baseElement = particle.type === 0 ? (
                    // Floating dots
                    <Box
                      sx={{
                        width: particle.size,
                        height: particle.size,
                        borderRadius: '50%',
                        background: `radial-gradient(circle, ${noEmotionColor}CC 0%, ${noEmotionColor}60 70%, transparent 100%)`,
                        boxShadow: `0 0 12px ${noEmotionColor}40`,
                      }}
                    />
                  ) : particle.type === 1 ? (
                    // Floating rings
                    <Box
                      sx={{
                        width: particle.size * 2,
                        height: particle.size * 2,
                        borderRadius: '50%',
                        border: `1px solid ${noEmotionColor}60`,
                        background: 'transparent',
                        boxShadow: `inset 0 0 8px ${noEmotionColor}30, 0 0 8px ${noEmotionColor}30`,
                      }}
                    />
                  ) : (
                    // Floating lines/dashes
                    <Box
                      sx={{
                        width: particle.size * 1.5,
                        height: '1px',
                        background: `linear-gradient(90deg, transparent, ${noEmotionColor}80, transparent)`,
                        boxShadow: `0 0 6px ${noEmotionColor}40`,
                      }}
                    />
                  );

                  return (
                    <motion.div
                      key={particle.id}
                      style={{
                        position: 'absolute',
                        left: '50%',
                        top: '50%',
                        marginLeft: `-${particle.size}px`,
                        marginTop: `-${particle.size}px`,
                      }}
                      animate={{
                        x: [
                          Math.cos(particle.angle) * particle.radius * 0.6,
                          Math.cos(particle.angle + particle.spiralOffset) * particle.radius * 1.1,
                          Math.cos(particle.angle + particle.spiralOffset * 2) * particle.radius * 0.8,
                          Math.cos(particle.angle + particle.spiralOffset * 3) * particle.radius * 1.2,
                          Math.cos(particle.angle + particle.spiralOffset * 4) * particle.radius * 0.6,
                        ],
                        y: [
                          Math.sin(particle.angle) * particle.radius * 0.6,
                          Math.sin(particle.angle + particle.spiralOffset) * particle.radius * 1.1,
                          Math.sin(particle.angle + particle.spiralOffset * 2) * particle.radius * 0.8,
                          Math.sin(particle.angle + particle.spiralOffset * 3) * particle.radius * 1.2,
                          Math.sin(particle.angle + particle.spiralOffset * 4) * particle.radius * 0.6,
                        ],
                        scale: [particle.scale * 0.4, particle.scale * 1.2, particle.scale * 0.8, particle.scale * 1.1, particle.scale * 0.4],
                        opacity: [0.2, 0.7, 1, 0.5, 0.2],
                        rotate: particle.type === 2 ? [0, 90, 180, 270, 360] : [0, 60, 120, 180, 240, 300, 360]
                      }}
                      transition={{
                        duration: particle.duration,
                        delay: particle.delay,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                    >
                      {baseElement}
                    </motion.div>
                  );
                })}

                {/* Enhanced No Emotion Orb - Abstract Geometric Design */}
                <EmotionOrb
                  color={noEmotionColor}
                  size={size}
                  intensity={0.3}
                  compact={compact}
                  animate={{
                    scale: [1, 1.02, 1],
                    opacity: [0.7, 1, 0.7],
                  }}
                  transition={{
                    scale: { duration: 4, repeat: Infinity, ease: "easeInOut" },
                    opacity: { duration: 3, repeat: Infinity, ease: "easeInOut" },
                  }}
                  style={{
                    cursor: 'default',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                  }}
                >
                  {/* Central Void - Abstract representation of "no emotion" */}
                  <motion.div
                    animate={{
                      rotate: [0, 360],
                      scale: [1, 1.05, 1],
                    }}
                    transition={{
                      rotate: { duration: 15, repeat: Infinity, ease: "linear" },
                      scale: { duration: 3, repeat: Infinity, ease: "easeInOut" }
                    }}
                    style={{
                      position: 'relative',
                      width: compact ? '40px' : '50px',
                      height: compact ? '40px' : '50px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    {/* Outer Ring */}
                    <Box
                      sx={{
                        position: 'absolute',
                        width: '100%',
                        height: '100%',
                        borderRadius: '50%',
                        border: `2px solid ${noEmotionColor}60`,
                        boxShadow: `0 0 15px ${noEmotionColor}30`,
                      }}
                    />

                    {/* Middle Ring */}
                    <motion.div
                      animate={{
                        rotate: [0, -360],
                        scale: [0.7, 0.8, 0.7],
                      }}
                      transition={{
                        rotate: { duration: 10, repeat: Infinity, ease: "linear" },
                        scale: { duration: 2.5, repeat: Infinity, ease: "easeInOut" }
                      }}
                      style={{
                        position: 'absolute',
                        width: '70%',
                        height: '70%',
                        borderRadius: '50%',
                        border: `1px solid ${noEmotionColor}40`,
                        boxShadow: `inset 0 0 10px ${noEmotionColor}20`,
                      }}
                    />

                    {/* Inner Core - Subtle glow */}
                    <motion.div
                      animate={{
                        scale: [0.3, 0.5, 0.3],
                        opacity: [0.4, 0.8, 0.4],
                      }}
                      transition={{
                        duration: 4,
                        repeat: Infinity,
                        ease: "easeInOut"
                      }}
                      style={{
                        width: '40%',
                        height: '40%',
                        borderRadius: '50%',
                        background: `radial-gradient(circle, ${noEmotionColor}80 0%, ${noEmotionColor}40 50%, transparent 100%)`,
                        boxShadow: `0 0 20px ${noEmotionColor}50`,
                      }}
                    />

                    {/* Floating Dots - Representing neutral energy */}
                    {[0, 1, 2, 3].map((i) => (
                      <motion.div
                        key={i}
                        animate={{
                          x: [
                            Math.cos((i * Math.PI) / 2) * (compact ? 25 : 30),
                            Math.cos((i * Math.PI) / 2 + Math.PI / 4) * (compact ? 30 : 35),
                            Math.cos((i * Math.PI) / 2 + Math.PI / 2) * (compact ? 25 : 30),
                            Math.cos((i * Math.PI) / 2 + (3 * Math.PI) / 4) * (compact ? 20 : 25),
                            Math.cos((i * Math.PI) / 2) * (compact ? 25 : 30),
                          ],
                          y: [
                            Math.sin((i * Math.PI) / 2) * (compact ? 25 : 30),
                            Math.sin((i * Math.PI) / 2 + Math.PI / 4) * (compact ? 30 : 35),
                            Math.sin((i * Math.PI) / 2 + Math.PI / 2) * (compact ? 25 : 30),
                            Math.sin((i * Math.PI) / 2 + (3 * Math.PI) / 4) * (compact ? 20 : 25),
                            Math.sin((i * Math.PI) / 2) * (compact ? 25 : 30),
                          ],
                          scale: [0.5, 1, 0.8, 1.2, 0.5],
                          opacity: [0.3, 0.8, 1, 0.6, 0.3],
                        }}
                        transition={{
                          duration: 6 + i * 0.5,
                          repeat: Infinity,
                          ease: "easeInOut",
                          delay: i * 0.8,
                        }}
                        style={{
                          position: 'absolute',
                          width: compact ? '4px' : '6px',
                          height: compact ? '4px' : '6px',
                          borderRadius: '50%',
                          background: `radial-gradient(circle, ${noEmotionColor}FF 0%, ${noEmotionColor}80 70%, transparent 100%)`,
                          boxShadow: `0 0 8px ${noEmotionColor}60`,
                        }}
                      />
                    ))}

                    {/* Subtle Energy Waves */}
                    {[0, 1].map((i) => (
                      <motion.div
                        key={`wave-${i}`}
                        animate={{
                          scale: [0, 1.5, 0],
                          opacity: [0, 0.3, 0],
                        }}
                        transition={{
                          duration: 3,
                          repeat: Infinity,
                          ease: "easeOut",
                          delay: i * 1.5,
                        }}
                        style={{
                          position: 'absolute',
                          width: '150%',
                          height: '150%',
                          borderRadius: '50%',
                          border: `1px solid ${noEmotionColor}30`,
                          pointerEvents: 'none',
                        }}
                      />
                    ))}
                  </motion.div>
                </EmotionOrb>
              </Box>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.5 }}
              >
                <Box sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  mt: 1,
                }}>
                  <EmotionLabel color={noEmotionColor} compact={compact}>
                    No Emotion
                  </EmotionLabel>
                  <SubEmotionDisplay color={noEmotionColor} compact={compact}>
                    None
                  </SubEmotionDisplay>
                  <Box sx={{
                    display: 'flex',
                    alignItems: 'center',
                    mt: 0.5
                  }}>
                    <IntensityIndicator
                      color={noEmotionColor}
                      intensity={0}
                      compact={compact}
                      initial={{ width: 0 }}
                      animate={{ width: compact ? '120px' : '160px' }}
                      transition={{ duration: 0.8, delay: 0.5, ease: 'easeOut' }}
                    />
                    <IntensityPercentage color={noEmotionColor} compact={compact}>
                      0%
                    </IntensityPercentage>
                  </Box>
                </Box>
              </motion.div>
            </motion.div>
          </AnimatePresence>
        </EmotionPulse>
      </Box>
    );
  }

  const mainColor = getEmotionColor(emotion);
  const intensityValue = getIntensityValue(intensity);
  const size = compact ?
    (90 + (intensityValue * 30)) :
    (120 + (intensityValue * 40));
  // Enhanced ethereal particles for organic cosmic effect
  const etherealParticles = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    angle: (i / 20) * Math.PI * 2,
    radius: 60 + Math.random() * 80,
    scale: 0.3 + Math.random() * 0.8,
    duration: 6 + Math.random() * 8,
    delay: i * 0.2,
    size: 1.5 + Math.random() * 4,
    spiralOffset: Math.random() * Math.PI * 2
  }));

  return (
    <Box sx={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      justifyContent: 'center',
    }}>
      <EmotionPulse compact={compact}>
        <AnimatePresence mode="wait">
          <motion.div
            key={emotion + subEmotion}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.5 }}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              width: '100%',
              height: '100%',
              padding: '10px',
              position: 'relative',
            }}
          >
            <Box
              sx={{
                position: 'relative',
                width: compact ? (size + 120) : (size + 160),
                height: compact ? (size + 120) : (size + 160),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginY: compact ? 0 : 0.5,
              }}
            >              {/* Enhanced Cosmic Aura Background with breathing effect */}
              <CosmicAura
                color={mainColor}
                size={compact ? 250 : 350}
                animate={{
                  opacity: [0.2, 0.5, 0.8, 0.5, 0.2],
                  scale: [0.6, 1.0, 1.3, 1.1, 0.6],
                  rotate: [0, 45, 90, 135, 180]
                }}
                transition={{
                  repeat: Infinity,
                  duration: 6,
                  ease: "easeInOut"
                }}
              />

              {/* Secondary aura for depth */}
              <CosmicAura
                color={mainColor}
                size={compact ? 180 : 280}
                animate={{
                  opacity: [0.3, 0.7, 0.9, 0.6, 0.3],
                  scale: [0.8, 1.2, 1.5, 1.0, 0.8],
                  rotate: [0, -60, -120, -180, -240]
                }}
                transition={{
                  repeat: Infinity,
                  duration: 4.5,
                  ease: "easeInOut",
                  delay: 0.5
                }}
              />{/* Enhanced Orbital Rings with organic movement */}
              <OrbitalRing
                color={mainColor}
                size={size * 3}
                thickness={1}
                animate={{
                  rotate: [0, 360],
                  scale: [1, 1.05, 1],
                  opacity: [0.3, 0.7, 0.3]
                }}
                transition={{
                  rotate: { duration: 40, repeat: Infinity, ease: "linear" },
                  scale: { duration: 4, repeat: Infinity, ease: "easeInOut" },
                  opacity: { duration: 3, repeat: Infinity, ease: "easeInOut" }
                }}
              />

              <OrbitalRing
                color={mainColor}
                size={size * 2.2}
                thickness={2}
                animate={{
                  rotate: [0, -360],
                  scale: [1, 1.08, 1],
                  opacity: [0.4, 0.8, 0.4]
                }}
                transition={{
                  rotate: { duration: 25, repeat: Infinity, ease: "linear" },
                  scale: { duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 },
                  opacity: { duration: 2.5, repeat: Infinity, ease: "easeInOut", delay: 0.5 }
                }}
              />

              <OrbitalRing
                color={mainColor}
                size={size * 1.7}
                thickness={1}
                animate={{
                  rotate: [0, 360],
                  scale: [1, 1.12, 1],
                  opacity: [0.5, 0.9, 0.5]
                }}
                transition={{
                  rotate: { duration: 18, repeat: Infinity, ease: "linear" },
                  scale: { duration: 3, repeat: Infinity, ease: "easeInOut", delay: 1 },
                  opacity: { duration: 2, repeat: Infinity, ease: "easeInOut", delay: 1 }
                }}
              />

              {/* Enhanced Energy Waves with organic pulsing */}
              {[1, 2, 3, 4].map((wave, i) => (
                <EnergyWave
                  key={wave}
                  color={mainColor}
                  size={size * (1.2 + i * 0.4)}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{
                    scale: [0, 1.8, 2.5, 0],
                    opacity: [0, 0.3, 0.8, 0]
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 4,
                    delay: i * 0.8,
                    ease: "easeOut"
                  }}
                />
              ))}              {/* Enhanced Ethereal Particles with organic spiral movement */}
              {etherealParticles.map(particle => {
                // Create spiral movement pattern
                const spiralRadius = particle.radius;
                const spiralX = Math.cos(particle.angle + particle.spiralOffset) * spiralRadius;
                const spiralY = Math.sin(particle.angle + particle.spiralOffset) * spiralRadius;

                return (
                  <EtherealParticle
                    key={particle.id}
                    color={mainColor}
                    size={particle.size}
                    initial={{
                      x: 0,
                      y: 0,
                      scale: 0,
                      opacity: 0
                    }}
                    animate={{
                      x: [
                        0,
                        spiralX * 0.3,
                        spiralX * 0.7,
                        spiralX,
                        spiralX * 1.2,
                        spiralX * 0.8,
                        spiralX * 0.4,
                        0
                      ],
                      y: [
                        0,
                        spiralY * 0.3,
                        spiralY * 0.7,
                        spiralY,
                        spiralY * 1.2,
                        spiralY * 0.8,
                        spiralY * 0.4,
                        0
                      ],
                      scale: [
                        0,
                        particle.scale * 0.5,
                        particle.scale,
                        particle.scale * 1.3,
                        particle.scale * 1.1,
                        particle.scale * 0.8,
                        particle.scale * 0.3,
                        0
                      ],
                      opacity: [0, 0.4, 0.8, 1, 0.8, 0.5, 0.2, 0],
                      rotate: [0, 180, 360, 540, 720, 900, 1080, 1260]
                    }}
                    transition={{
                      repeat: Infinity,
                      duration: particle.duration,
                      delay: particle.delay,
                      ease: "easeInOut"
                    }}
                  />
                );
              })}{/* Main Emotion Orb with enhanced effects - NO EMOJIS, pure abstract */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{
                  scale: 1,
                  transition: {
                    type: 'spring',
                    damping: 15,
                    stiffness: 200,
                  }
                }}
                style={{ position: 'relative', zIndex: 10 }}
              >
                <EmotionOrb
                  color={mainColor}
                  size={size}
                  intensity={intensityValue}
                  compact={compact}
                  animate={{
                    scale: [1, 1.08, 1],
                    boxShadow: [
                      `0 0 ${35 * intensityValue}px ${20 * intensityValue}px ${mainColor}33`,
                      `0 0 ${60 * intensityValue}px ${45 * intensityValue}px ${mainColor}55`,
                      `0 0 ${35 * intensityValue}px ${20 * intensityValue}px ${mainColor}33`
                    ]
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 2.5,
                    ease: "easeInOut"
                  }}
                >
                  {/* Inner pulsing core - pure color energy */}
                  <InnerGlow
                    color={mainColor}
                    size={size * 0.6}
                    animate={{
                      opacity: [0.3, 0.9, 0.3],
                      scale: [0.7, 1.4, 0.7],
                    }}
                    transition={{
                      repeat: Infinity,
                      duration: 2,
                      ease: "easeInOut"
                    }}
                  />

                  {/* Secondary inner glow for depth */}
                  <InnerGlow
                    color={mainColor}
                    size={size * 0.4}
                    animate={{
                      opacity: [0.5, 1, 0.5],
                      scale: [0.8, 1.6, 0.8],
                    }}
                    transition={{
                      repeat: Infinity,
                      duration: 1.5,
                      ease: "easeInOut",
                      delay: 0.3
                    }}
                  />

                  {/* Core energy center */}
                  <Box
                    sx={{
                      position: 'absolute',
                      width: size * 0.25,
                      height: size * 0.25,
                      borderRadius: '50%',
                      background: `radial-gradient(circle, ${mainColor}FF 0%, ${mainColor}AA 50%, ${mainColor}00 100%)`,
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      animation: 'coreGlow 1.8s ease-in-out infinite',
                      '@keyframes coreGlow': {
                        '0%, 100%': {
                          boxShadow: `0 0 ${size * 0.1}px ${mainColor}FF`,
                          filter: 'brightness(1)'
                        },
                        '50%': {
                          boxShadow: `0 0 ${size * 0.2}px ${mainColor}FF`,
                          filter: 'brightness(1.5)'
                        }
                      }
                    }}
                  />
                </EmotionOrb>
              </motion.div>
            </Box>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              style={{ position: 'relative', zIndex: 20 }}
            >
              <Box sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                mt: 1,
              }}>
                <EmotionLabel color={mainColor} compact={compact}>
                  {emotion}
                </EmotionLabel>

                {subEmotion && (
                  <SubEmotionDisplay color={getEmotionColor(subEmotion)} compact={compact}>
                    {subEmotion}
                  </SubEmotionDisplay>
                )}

                <Box sx={{
                  display: 'flex',
                  alignItems: 'center',
                  mt: 0.5
                }}>
                  <IntensityIndicator
                    color={mainColor}
                    intensity={intensityValue}
                    compact={compact}
                    initial={{ width: 0 }}
                    animate={{ width: compact ? '140px' : '180px' }}
                    transition={{ duration: 0.8, delay: 0.5, ease: 'easeOut' }}
                  />
                  <IntensityPercentage color={mainColor} compact={compact}>
                    {(intensityValue * 100).toFixed(0)}%
                  </IntensityPercentage>
                </Box>
              </Box>
            </motion.div>
          </motion.div>
        </AnimatePresence>
      </EmotionPulse>
    </Box>
  );
};

export default EmotionCurrent;
