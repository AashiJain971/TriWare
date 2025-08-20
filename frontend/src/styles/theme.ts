/**
 * Material-UI Theme Configuration for Smart Triage Kiosk System
 * 
 * Comprehensive theming with accessibility, multi-language support,
 * and kiosk-optimized design patterns.
 */

import { createTheme, ThemeOptions } from '@mui/material/styles';
import { alpha } from '@mui/material/styles';

// Color Palette - Healthcare Optimized
const colors = {
  primary: {
    main: '#1976d2',      // Medical Blue
    light: '#42a5f5',
    dark: '#1565c0',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#2e7d32',      // Medical Green
    light: '#4caf50',
    dark: '#1b5e20',
    contrastText: '#ffffff',
  },
  error: {
    main: '#d32f2f',      // Medical Red/Critical
    light: '#ef5350',
    dark: '#c62828',
    contrastText: '#ffffff',
  },
  warning: {
    main: '#ed6c02',      // Orange/Urgent
    light: '#ff9800',
    dark: '#e65100',
    contrastText: '#ffffff',
  },
  info: {
    main: '#0288d1',      // Info Blue
    light: '#03a9f4',
    dark: '#01579b',
    contrastText: '#ffffff',
  },
  success: {
    main: '#2e7d32',      // Green/Stable
    light: '#4caf50',
    dark: '#1b5e20',
    contrastText: '#ffffff',
  },
  // Triage Colors
  triage: {
    red: '#d32f2f',       // Immediate
    orange: '#ff6f00',    // Very Urgent
    yellow: '#fbc02d',    // Urgent
    green: '#388e3c',     // Routine
    blue: '#1976d2',      // Non-urgent
  },
  // Accessibility Colors
  highContrast: {
    background: '#000000',
    text: '#ffffff',
    accent: '#ffff00',
  },
};

// Typography - Optimized for Accessibility and Multi-language
const typography = {
  fontFamily: [
    'Roboto',
    'Noto Sans Devanagari', // Hindi support
    'system-ui',
    '-apple-system',
    'BlinkMacSystemFont',
    'Arial',
    'sans-serif',
  ].join(','),
  
  // Kiosk-optimized sizes (larger for touch interface)
  h1: {
    fontSize: '2.5rem',
    fontWeight: 500,
    lineHeight: 1.2,
  },
  h2: {
    fontSize: '2.1rem',
    fontWeight: 500,
    lineHeight: 1.3,
  },
  h3: {
    fontSize: '1.8rem',
    fontWeight: 500,
    lineHeight: 1.4,
  },
  h4: {
    fontSize: '1.5rem',
    fontWeight: 500,
    lineHeight: 1.4,
  },
  h5: {
    fontSize: '1.3rem',
    fontWeight: 500,
    lineHeight: 1.5,
  },
  h6: {
    fontSize: '1.1rem',
    fontWeight: 500,
    lineHeight: 1.5,
  },
  body1: {
    fontSize: '1.1rem',
    lineHeight: 1.6,
  },
  body2: {
    fontSize: '1rem',
    lineHeight: 1.5,
  },
  button: {
    fontSize: '1.1rem',
    fontWeight: 500,
    textTransform: 'none' as const,
  },
  caption: {
    fontSize: '0.9rem',
    lineHeight: 1.4,
  },
};

// Component Customizations for Kiosk Interface
const components = {
  // Button optimizations for touch interface
  MuiButton: {
    styleOverrides: {
      root: {
        minHeight: '48px',
        padding: '12px 24px',
        borderRadius: '8px',
        fontSize: '1.1rem',
        fontWeight: 500,
        textTransform: 'none' as const,
        boxShadow: 'none',
        '&:hover': {
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        },
        '&:focus': {
          outline: '3px solid #1976d2',
          outlineOffset: '2px',
        },
      },
      sizeLarge: {
        minHeight: '56px',
        padding: '16px 32px',
        fontSize: '1.2rem',
      },
    },
  },

  // Card optimizations
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: '12px',
        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
        '&:hover': {
          boxShadow: '0 4px 20px rgba(0,0,0,0.12)',
        },
      },
    },
  },

  // Input field optimizations
  MuiTextField: {
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          minHeight: '48px',
          fontSize: '1.1rem',
          borderRadius: '8px',
          '&:focus-within': {
            outline: '2px solid #1976d2',
            outlineOffset: '2px',
          },
        },
        '& .MuiInputLabel-root': {
          fontSize: '1.1rem',
        },
      },
    },
  },

  // App Bar for kiosk header
  MuiAppBar: {
    styleOverrides: {
      root: {
        boxShadow: '0 1px 8px rgba(0,0,0,0.12)',
      },
    },
  },

  // Drawer for navigation
  MuiDrawer: {
    styleOverrides: {
      paper: {
        borderRadius: '0 12px 12px 0',
      },
    },
  },

  // Dialog for accessibility
  MuiDialog: {
    styleOverrides: {
      paper: {
        borderRadius: '12px',
        minWidth: '400px',
      },
    },
  },

  // Chip for tags and status
  MuiChip: {
    styleOverrides: {
      root: {
        height: '36px',
        fontSize: '1rem',
        fontWeight: 500,
      },
    },
  },

  // Table for data display
  MuiTableCell: {
    styleOverrides: {
      root: {
        padding: '16px',
        fontSize: '1rem',
      },
      head: {
        fontWeight: 600,
        backgroundColor: alpha('#1976d2', 0.05),
      },
    },
  },

  // Progress indicators
  MuiLinearProgress: {
    styleOverrides: {
      root: {
        borderRadius: '4px',
        height: '8px',
      },
    },
  },

  // Alert components
  MuiAlert: {
    styleOverrides: {
      root: {
        borderRadius: '8px',
        fontSize: '1rem',
        alignItems: 'center',
      },
    },
  },
};

// Breakpoints for responsive design
const breakpoints = {
  values: {
    xs: 0,
    sm: 600,
    md: 960,     // Tablet portrait
    lg: 1280,    // Kiosk landscape
    xl: 1920,    // Large displays
  },
};

// Spacing system (8px base unit)
const spacing = 8;

// Base theme configuration
const baseThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: colors.primary,
    secondary: colors.secondary,
    error: colors.error,
    warning: colors.warning,
    info: colors.info,
    success: colors.success,
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    text: {
      primary: '#212121',
      secondary: '#757575',
    },
  },
  typography,
  components,
  breakpoints,
  spacing,
  shape: {
    borderRadius: 8,
  },
};

// Create base theme
export const theme = createTheme(baseThemeOptions);

// High contrast theme variant
export const highContrastTheme = createTheme({
  ...baseThemeOptions,
  palette: {
    mode: 'dark',
    primary: {
      main: '#ffff00',
      contrastText: '#000000',
    },
    secondary: {
      main: '#00ffff',
      contrastText: '#000000',
    },
    background: {
      default: '#000000',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#ffffff',
      secondary: '#cccccc',
    },
  },
});

// Large text theme variant
export const largeTextTheme = createTheme({
  ...baseThemeOptions,
  typography: {
    ...typography,
    h1: { ...typography.h1, fontSize: '3rem' },
    h2: { ...typography.h2, fontSize: '2.5rem' },
    h3: { ...typography.h3, fontSize: '2.2rem' },
    h4: { ...typography.h4, fontSize: '1.8rem' },
    h5: { ...typography.h5, fontSize: '1.6rem' },
    h6: { ...typography.h6, fontSize: '1.4rem' },
    body1: { ...typography.body1, fontSize: '1.3rem' },
    body2: { ...typography.body2, fontSize: '1.2rem' },
    button: { ...typography.button, fontSize: '1.3rem' },
  },
});

// Global styles for accessibility and kiosk optimization
export const globalStyles = {
  // High contrast support
  '.high-contrast': {
    backgroundColor: '#000000 !important',
    color: '#ffffff !important',
    '& *': {
      backgroundColor: 'transparent !important',
      color: '#ffffff !important',
      borderColor: '#ffffff !important',
    },
    '& .MuiButton-contained': {
      backgroundColor: '#ffff00 !important',
      color: '#000000 !important',
    },
  },

  // Large text support
  '.large-text': {
    fontSize: '125% !important',
    '& *': {
      fontSize: 'inherit !important',
    },
  },

  // Kiosk-specific styles
  '.kiosk-mode': {
    userSelect: 'none',
    overflow: 'hidden',
    '& input, & textarea': {
      userSelect: 'text',
    },
  },

  // Touch-friendly interactions
  '.touch-target': {
    minHeight: '44px',
    minWidth: '44px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    '&:hover': {
      backgroundColor: alpha('#1976d2', 0.04),
    },
  },

  // Offline indicator
  '.offline-indicator': {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    backgroundColor: '#f44336',
    color: '#ffffff',
    padding: '8px',
    textAlign: 'center',
    zIndex: 9999,
  },

  // Loading states
  '.loading': {
    opacity: 0.6,
    pointerEvents: 'none',
  },

  // Animation utilities
  '@keyframes pulse': {
    '0%': { opacity: 1 },
    '50%': { opacity: 0.5 },
    '100%': { opacity: 1 },
  },

  '.pulse': {
    animation: 'pulse 2s infinite',
  },

  // Print styles
  '@media print': {
    '.no-print': {
      display: 'none !important',
    },
    body: {
      backgroundColor: 'white !important',
      color: 'black !important',
    },
  },

  // Screen reader support
  '.sr-only': {
    position: 'absolute',
    width: '1px',
    height: '1px',
    padding: 0,
    margin: '-1px',
    overflow: 'hidden',
    clip: 'rect(0, 0, 0, 0)',
    whiteSpace: 'nowrap',
    border: 0,
  },

  // Focus visible polyfill
  '.js-focus-visible :focus:not(.focus-visible)': {
    outline: 'none',
  },
};

// Utility functions
export const getTriageColor = (category: string): string => {
  const colorMap: { [key: string]: string } = {
    red: colors.triage.red,
    orange: colors.triage.orange,
    yellow: colors.triage.yellow,
    green: colors.triage.green,
    blue: colors.triage.blue,
  };
  return colorMap[category.toLowerCase()] || colors.primary.main;
};

export const getTriageBackgroundColor = (category: string): string => {
  return alpha(getTriageColor(category), 0.1);
};

// Responsive utilities
export const responsive = {
  up: (breakpoint: keyof typeof breakpoints.values) => 
    `@media (min-width:${breakpoints.values[breakpoint]}px)`,
  down: (breakpoint: keyof typeof breakpoints.values) => 
    `@media (max-width:${breakpoints.values[breakpoint] - 0.05}px)`,
  between: (start: keyof typeof breakpoints.values, end: keyof typeof breakpoints.values) =>
    `@media (min-width:${breakpoints.values[start]}px) and (max-width:${breakpoints.values[end] - 0.05}px)`,
};

export default theme;
