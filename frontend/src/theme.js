/**
 * Sophisticated Minimalist Theme - Premium Dark Design System
 *
 * @description Implements restrained color usage with navy foundation.
 * Focus on typography, hierarchy, and subtle interactions for high-end UI.
 *
 * @version 2.0.0
 * @author AI Design System
 *
 * Key Features:
 * - Navy-based color foundation for sophistication
 * - Single primary accent (indigo) to avoid color overuse
 * - Advanced glassmorphism effects
 * - Comprehensive typography scale
 * - Professional shadow and spacing systems
 *
 * Design Philosophy:
 * - Restraint over excess
 * - Quality over quantity
 * - Consistency over variety
 * - Sophistication over flash
 */

export const theme = {
  // Sophisticated Color Palette - Minimal and Refined
  colors: {    // Navy Foundation Background System - Deep, sophisticated gradients
    background: {
      primary: 'linear-gradient(135deg, #020617 0%, #0f172a 25%, #1e293b 50%, #334155 75%, #475569 100%)',
      secondary: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
      tertiary: 'linear-gradient(135deg, #020617 0%, #0f172a 100%)',
      surface: '#0f172a',
      elevated: '#1e293b',
      subtle: 'radial-gradient(ellipse at center, #1e293b 0%, #0f172a 35%, #020617 100%)',
    },

    // Primary Accent - Sophisticated Indigo (Single accent philosophy)
    primary: {
      main: '#4F46E5', // Sophisticated indigo
      light: '#8b92ff', // Lighter indigo
      dark: '#3730a3', // Deeper indigo
      accent: '#6366f1', // Subtle highlight
      100: '#f0f4ff',
      200: '#e0edff',
      300: '#c7d6ff',
      400: '#a5b8ff',
      500: '#4F46E5',
      600: '#4338ca',
      700: '#3730a3',
      800: '#312e81',
      900: '#1e1b4b',
      glow: 'rgba(79, 70, 229, 0.4)',
    },

    // Navy Spectrum - Monochromatic foundation
    secondary: {
      main: '#475569', // Sophisticated slate
      light: '#64748b', // Lighter slate
      dark: '#334155', // Deeper slate
      accent: '#1e293b', // Surface accent
      100: '#f8fafc',
      200: '#f1f5f9',
      300: '#e2e8f0',
      400: '#cbd5e1',
      500: '#94a3b8',
      600: '#64748b',
      700: '#475569',
      800: '#334155',
      900: '#1e293b',
      glow: 'rgba(71, 85, 105, 0.3)',
    },    // Minimal Tertiary - Subtle warm accent (very sparingly used)
    tertiary: {
      main: '#d97706', // Muted amber (for warnings only)
      light: '#f59e0b',
      dark: '#92400e',
      accent: '#b45309',
      glow: 'rgba(217, 119, 6, 0.3)',
    },

    // Sophisticated Text Hierarchy - High contrast for readability
    text: {
      primary: '#f8fafc', // Crisp white for headings
      secondary: '#e2e8f0', // Soft white for body text
      tertiary: '#cbd5e1', // Light gray for metadata
      quaternary: '#94a3b8', // Muted gray for less important text
      disabled: '#64748b', // Disabled state
      accent: '#4F46E5', // Primary accent only
      inverse: '#020617', // Dark text for light backgrounds
    },

    // Minimal Status Colors - Muted and sophisticated
    status: {
      success: '#059669', // Muted emerald
      successBg: 'rgba(5, 150, 105, 0.1)',
      successGlow: 'rgba(5, 150, 105, 0.3)',
      warning: '#d97706', // Muted amber
      warningBg: 'rgba(217, 119, 6, 0.1)',
      warningGlow: 'rgba(217, 119, 6, 0.3)',
      error: '#dc2626', // Muted red
      errorBg: 'rgba(220, 38, 38, 0.1)',
      errorGlow: 'rgba(220, 38, 38, 0.3)',
      info: '#0284c7', // Muted sky blue
      infoBg: 'rgba(2, 132, 199, 0.1)',
      infoGlow: 'rgba(2, 132, 199, 0.3)',
    },

    // Refined Emotion Colors - Subtle and sophisticated
    emotion: {
      happiness: '#059669', // Muted emerald
      sadness: '#0284c7', // Muted blue
      anger: '#dc2626', // Muted red
      fear: '#7c3aed', // Muted purple
      surprise: '#d97706', // Muted amber      disgust: '#047857', // Muted forest
      neutral: '#8b93a6', // Slightly brighter balanced slate
      love: '#be185d', // Muted rose
      excitement: '#c2410c', // Muted orange
      contempt: '#64748b', // Balanced slate - Detachment
    },

    // Sophisticated Surface System - Navy-based glassmorphism
    surface: {
      glass: 'rgba(15, 23, 42, 0.8)', // Navy glassmorphism
      glassLight: 'rgba(30, 41, 59, 0.7)', // Lighter glass variant
      glassDark: 'rgba(2, 6, 23, 0.9)', // Darker glass variant
      elevated: 'rgba(30, 41, 59, 0.85)', // Elevated surfaces
      card: 'rgba(15, 23, 42, 0.6)', // Card backgrounds
      cardHover: 'rgba(30, 41, 59, 0.7)', // Card hover state
      overlay: 'rgba(2, 6, 23, 0.8)', // Modal overlays
      tooltip: 'rgba(15, 23, 42, 0.9)', // Tooltip backgrounds
      dropdown: 'rgba(30, 41, 59, 0.85)', // Dropdown backgrounds
    },

    // Minimal Border System - Subtle and refined
    border: 'rgba(203, 213, 225, 0.1)', // Very subtle borders
    borderLight: 'rgba(248, 250, 252, 0.05)', // Extremely subtle borders
    borderActive: 'rgba(79, 70, 229, 0.4)', // Primary accent borders only
    borderHover: 'rgba(203, 213, 225, 0.15)', // Hover state borders
    borderFocus: 'rgba(79, 70, 229, 0.5)', // Focus state borders (primary only)
    borderError: 'rgba(220, 38, 38, 0.3)', // Error state borders
    borderSuccess: 'rgba(5, 150, 105, 0.3)', // Success state borders

    // Refined Gradient System - Navy foundation with minimal accent
    gradients: {
      primary: 'linear-gradient(135deg, #4F46E5 0%, #3730a3 50%, #1e1b4b 100%)',
      background: 'linear-gradient(135deg, #020617 0%, #0f172a 25%, #1e293b 50%, #334155 75%, #475569 100%)',
      surface: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
      subtle: 'radial-gradient(ellipse at center, #1e293b 0%, #0f172a 35%, #020617 100%)',
      glow: 'radial-gradient(circle, rgba(79, 70, 229, 0.3) 0%, rgba(71, 85, 105, 0.1) 50%, transparent 100%)',
    },
  },
  // Premium Typography System
  typography: {
    fontFamily: {
      primary: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
      heading: '"SF Pro Display", "Inter", -apple-system, BlinkMacSystemFont, sans-serif',
      mono: '"SF Mono", "Monaco", "Inconsolata", "Roboto Mono", monospace',
      accent: '"Inter", sans-serif',
    },
    fontSize: {
      xs: '0.75rem',     // 12px - Captions, metadata
      sm: '0.875rem',    // 14px - Small text, labels
      base: '1rem',      // 16px - Body text
      md: '1.125rem',    // 18px - Large body text
      lg: '1.25rem',     // 20px - Small headings
      xl: '1.5rem',      // 24px - Medium headings
      '2xl': '1.875rem', // 30px - Large headings
      '3xl': '2.25rem',  // 36px - Extra large headings
      '4xl': '3rem',     // 48px - Display headings
      '5xl': '3.75rem',  // 60px - Hero headings
      '6xl': '4.5rem',   // 72px - Massive display
    },
    fontWeight: {
      thin: 100,
      extralight: 200,
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
      black: 900,
    },
    lineHeight: {
      none: 1,
      tight: 1.25,
      snug: 1.375,
      normal: 1.5,
      relaxed: 1.625,
      loose: 2,
    },
    letterSpacing: {
      tighter: '-0.05em',
      tight: '-0.025em',
      normal: '0em',
      wide: '0.025em',
      wider: '0.05em',
      widest: '0.1em',
    },
  },

  // Refined Spacing System
  spacing: {
    px: '1px',
    0: '0',
    0.5: '0.125rem',  // 2px
    1: '0.25rem',     // 4px
    1.5: '0.375rem',  // 6px
    2: '0.5rem',      // 8px
    2.5: '0.625rem',  // 10px
    3: '0.75rem',     // 12px
    3.5: '0.875rem',  // 14px
    4: '1rem',        // 16px
    5: '1.25rem',     // 20px
    6: '1.5rem',      // 24px
    7: '1.75rem',     // 28px
    8: '2rem',        // 32px
    9: '2.25rem',     // 36px
    10: '2.5rem',     // 40px
    11: '2.75rem',    // 44px
    12: '3rem',       // 48px
    14: '3.5rem',     // 56px
    16: '4rem',       // 64px
    20: '5rem',       // 80px
    24: '6rem',       // 96px
    28: '7rem',       // 112px
    32: '8rem',       // 128px
    36: '9rem',       // 144px
    40: '10rem',      // 160px
    44: '11rem',      // 176px
    48: '12rem',      // 192px
    52: '13rem',      // 208px
    56: '14rem',      // 224px
    60: '15rem',      // 240px
    64: '16rem',      // 256px
    72: '18rem',      // 288px
    80: '20rem',      // 320px
    96: '24rem',      // 384px
  },

  // Sophisticated Border Radius System
  borderRadius: {
    none: '0',
    xs: '0.125rem',   // 2px
    sm: '0.25rem',    // 4px
    base: '0.375rem', // 6px
    md: '0.5rem',     // 8px
    lg: '0.75rem',    // 12px
    xl: '1rem',       // 16px
    '2xl': '1.5rem',  // 24px
    '3xl': '2rem',    // 32px
    '4xl': '2.5rem',  // 40px
    full: '9999px',   // Fully rounded
  },  // Sophisticated Shadow System - Minimal and refined
  shadows: {
    none: 'none',
    xs: '0 1px 2px 0 rgba(0, 0, 0, 0.25)',
    sm: '0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
    '3xl': '0 35px 60px -15px rgba(0, 0, 0, 0.6)',

    // Minimal colored glows - Primary accent only
    glow: '0 0 20px rgba(79, 70, 229, 0.4), 0 0 40px rgba(79, 70, 229, 0.2)',
    glowSubtle: '0 0 10px rgba(79, 70, 229, 0.3)',
    glowSuccess: '0 0 15px rgba(5, 150, 105, 0.3)',
    glowError: '0 0 15px rgba(220, 38, 38, 0.3)',

    // Inner shadows for depth
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.3)',
    innerLg: 'inset 0 4px 8px 0 rgba(0, 0, 0, 0.4)',

    // Focus shadows - Primary only
    outline: '0 0 0 3px rgba(79, 70, 229, 0.4)',
  },

  // Refined Glassmorphism - Navy foundation
  glassmorphism: {
    // Premium navy glass effects
    luxury: {
      background: 'rgba(15, 23, 42, 0.9)',
      backdropFilter: 'blur(32px) saturate(150%)',
      border: '1px solid rgba(203, 213, 225, 0.15)',
      borderGradient: 'linear-gradient(135deg, rgba(79, 70, 229, 0.2), rgba(71, 85, 105, 0.1))',
    },
    primary: {
      background: 'rgba(15, 23, 42, 0.8)',
      backdropFilter: 'blur(24px) saturate(140%)',
      border: '1px solid rgba(203, 213, 225, 0.1)',
    },
    secondary: {
      background: 'rgba(30, 41, 59, 0.75)',
      backdropFilter: 'blur(20px) saturate(130%)',
      border: '1px solid rgba(203, 213, 225, 0.08)',
    },
    tertiary: {
      background: 'rgba(51, 65, 85, 0.7)',
      backdropFilter: 'blur(16px) saturate(120%)',
      border: '1px solid rgba(203, 213, 225, 0.06)',
    },
    overlay: {
      background: 'rgba(2, 6, 23, 0.85)',
      backdropFilter: 'blur(40px) saturate(140%)',
      border: '1px solid rgba(203, 213, 225, 0.05)',
    },
    modal: {
      background: 'rgba(15, 23, 42, 0.95)',
      backdropFilter: 'blur(48px) saturate(150%)',
      border: '1px solid rgba(203, 213, 225, 0.12)',
    },
  },

  // Sophisticated Animation System
  animation: {
    duration: {
      instant: '0.05s',
      fastest: '0.1s',
      faster: '0.15s',
      fast: '0.2s',
      normal: '0.3s',
      slow: '0.4s',
      slower: '0.6s',
      slowest: '0.8s',
    },
    easing: {
      linear: 'linear',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      elastic: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
      smooth: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
      sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
      premium: 'cubic-bezier(0.23, 1, 0.32, 1)',
    },
  },

  // Breakpoints for responsive design
  breakpoints: {
    xs: '0px',
    sm: '600px',
    md: '960px',
    lg: '1280px',
    xl: '1920px',
  },

  // Z-index scale
  zIndex: {
    base: 0,
    dropdown: 1000,
    overlay: 1200,
    modal: 1300,
    tooltip: 1400,
    max: 9999,
  },
};

/**
 * Export the complete theme object
 * @type {Object} Complete theme configuration
 */
export default theme;

/**
 * Named exports for individual theme sections
 * Allows for tree-shaking and modular imports
 */
export const { colors, typography, spacing, shadows, glassmorphism, animation } = theme;
