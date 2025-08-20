/**
 * Smart Triage Kiosk System - Main Application Component
 * 
 * This is the root component that sets up the application structure,
 * routing, theme, internationalization, and global providers.
 */

import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline, GlobalStyles } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Store and Theme
import { store } from './stores';
import { theme, globalStyles } from './styles/theme';

// Context Providers
import ErrorBoundary from './providers/ErrorBoundary';
import { 
  PWAProvider, 
  AccessibilityProvider, 
  SettingsProvider,
  NotificationProvider,
  DeviceProvider,
  AuthProvider,
  LoadingScreen,
  OfflineIndicator
} from './providers';

// Layout Components
import Layout from './components/layout/Layout';

// Feature Pages (Lazy Loaded)
const HomePage = React.lazy(() => import('./pages').then(m => ({ default: m.HomePage })));
const PatientRegistration = React.lazy(() => import('./components/PatientRegistration'));
const TriageAssessment = React.lazy(() => import('./pages').then(m => ({ default: m.TriageAssessment })));
const QueueManagement = React.lazy(() => import('./pages').then(m => ({ default: m.QueueManagement })));
const VitalSigns = React.lazy(() => import('./pages').then(m => ({ default: m.VitalSigns })));
const Dashboard = React.lazy(() => import('./pages').then(m => ({ default: m.Dashboard })));
const Settings = React.lazy(() => import('./pages').then(m => ({ default: m.Settings })));
const Login = React.lazy(() => import('./pages').then(m => ({ default: m.Login })));

// Service Worker Registration
import { registerSW } from './utils/serviceWorker';

// React Query Configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: 1000,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (replaces cacheTime)
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
      retryDelay: 1000,
    },
  },
});

const App: React.FC = () => {
  useEffect(() => {
    // Register Service Worker for PWA functionality
    registerSW();
    
    // Initialize application telemetry
    console.log('Smart Triage Kiosk System v1.0.0 - Starting...');
    
    // Set up global error handling
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);
    });
    
    // Set up visibility change handling for power management
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        console.log('App went to background');
      } else {
        console.log('App came to foreground');
      }
    });
    
    // Initialize accessibility features
    const handleKeyDown = (event: KeyboardEvent) => {
      // Global keyboard shortcuts for accessibility
      if (event.altKey) {
        switch (event.key) {
          case '1':
            window.location.href = '/';
            break;
          case '2':
            window.location.href = '/register';
            break;
          case '3':
            window.location.href = '/triage';
            break;
          case 'h':
            // Toggle high contrast
            document.body.classList.toggle('high-contrast');
            break;
          case '+':
            // Increase font size
            document.body.classList.add('large-text');
            break;
          case '-':
            // Decrease font size
            document.body.classList.remove('large-text');
            break;
        }
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider theme={theme}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <CssBaseline />
              <GlobalStyles styles={globalStyles} />
              
              <PWAProvider>
                <AccessibilityProvider>
                  <SettingsProvider>
                    <NotificationProvider>
                      <DeviceProvider>
                        <AuthProvider>
                          <Router>
                            <Layout>
                              <Suspense fallback={<LoadingScreen />}>
                                <Routes>
                                  {/* Public Routes */}
                                  <Route path="/login" element={<Login />} />
                                  
                                  {/* Main Application Routes */}
                                  <Route path="/" element={<HomePage />} />
                                  <Route path="/register" element={<PatientRegistration />} />
                                  <Route path="/triage" element={<TriageAssessment />} />
                                  <Route path="/triage/:patientId" element={<TriageAssessment />} />
                                  <Route path="/vitals" element={<VitalSigns />} />
                                  <Route path="/vitals/:patientId" element={<VitalSigns />} />
                                  <Route path="/queue" element={<QueueManagement />} />
                                  <Route path="/dashboard" element={<Dashboard />} />
                                  <Route path="/settings" element={<Settings />} />
                                  
                                  {/* Redirect unknown routes to home */}
                                  <Route path="*" element={<Navigate to="/" replace />} />
                                </Routes>
                              </Suspense>
                              
                              {/* Global Components */}
                              <OfflineIndicator />
                            </Layout>
                          </Router>
                        </AuthProvider>
                      </DeviceProvider>
                    </NotificationProvider>
                  </SettingsProvider>
                </AccessibilityProvider>
              </PWAProvider>
              
            </LocalizationProvider>
          </ThemeProvider>
          
          {/* Development Tools */}
          {process.env.NODE_ENV === 'development' && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </QueryClientProvider>
      </Provider>
    </ErrorBoundary>
  );
};

export default App;
