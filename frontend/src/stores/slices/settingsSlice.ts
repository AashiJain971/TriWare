/**
 * Settings Slice
 * Manages application settings and configuration
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SettingsState {
  language: 'en' | 'hi' | 'es' | 'fr';
  theme: 'light' | 'dark' | 'auto';
  fontSize: 'small' | 'medium' | 'large';
  highContrast: boolean;
  voiceEnabled: boolean;
  soundEnabled: boolean;
  kioskMode: boolean;
  autoLogout: number; // minutes
  offlineMode: boolean;
  notifications: {
    enabled: boolean;
    sound: boolean;
    vibration: boolean;
  };
  accessibility: {
    screenReader: boolean;
    reducedMotion: boolean;
    focusIndicators: boolean;
  };
}

const initialState: SettingsState = {
  language: 'en',
  theme: 'light',
  fontSize: 'medium',
  highContrast: false,
  voiceEnabled: true,
  soundEnabled: true,
  kioskMode: true,
  autoLogout: 30,
  offlineMode: false,
  notifications: {
    enabled: true,
    sound: true,
    vibration: true,
  },
  accessibility: {
    screenReader: false,
    reducedMotion: false,
    focusIndicators: true,
  },
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setLanguage: (state, action: PayloadAction<'en' | 'hi' | 'es' | 'fr'>) => {
      state.language = action.payload;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload;
    },
    setFontSize: (state, action: PayloadAction<'small' | 'medium' | 'large'>) => {
      state.fontSize = action.payload;
    },
    toggleHighContrast: (state) => {
      state.highContrast = !state.highContrast;
    },
    toggleVoice: (state) => {
      state.voiceEnabled = !state.voiceEnabled;
    },
    toggleSound: (state) => {
      state.soundEnabled = !state.soundEnabled;
    },
    setKioskMode: (state, action: PayloadAction<boolean>) => {
      state.kioskMode = action.payload;
    },
    setAutoLogout: (state, action: PayloadAction<number>) => {
      state.autoLogout = action.payload;
    },
    toggleOfflineMode: (state) => {
      state.offlineMode = !state.offlineMode;
    },
    updateNotificationSettings: (state, action: PayloadAction<Partial<SettingsState['notifications']>>) => {
      state.notifications = { ...state.notifications, ...action.payload };
    },
    updateAccessibilitySettings: (state, action: PayloadAction<Partial<SettingsState['accessibility']>>) => {
      state.accessibility = { ...state.accessibility, ...action.payload };
    },
  },
});

export const {
  setLanguage,
  setTheme,
  setFontSize,
  toggleHighContrast,
  toggleVoice,
  toggleSound,
  setKioskMode,
  setAutoLogout,
  toggleOfflineMode,
  updateNotificationSettings,
  updateAccessibilitySettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;
