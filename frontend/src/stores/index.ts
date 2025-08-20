/**
 * Redux Store Configuration
 * Main application state management
 */

import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';

// Slice imports
import authSlice from './slices/authSlice';
import patientSlice from './slices/patientSlice';
import deviceSlice from './slices/deviceSlice';
import settingsSlice from './slices/settingsSlice';
import triageSlice from './slices/triageSlice';
import queueSlice from './slices/queueSlice';

// Combine reducers
const rootReducer = combineReducers({
  auth: authSlice,
  patients: patientSlice,
  devices: deviceSlice,
  settings: settingsSlice,
  triage: triageSlice,
  queue: queueSlice,
});

// Persist configuration
const persistConfig = {
  key: 'triware-root',
  storage,
  whitelist: ['auth', 'settings', 'devices'], // Only persist these slices
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default store;
