/**
 * Placeholder page components
 */

import React from 'react';
import { Box, Typography, Button, Grid, Card, CardContent } from '@mui/material';
import { PersonAdd, Assessment, Devices, Dashboard as DashboardIcon, Settings as SettingsIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const menuItems = [
    { title: 'Patient Registration', icon: <PersonAdd />, path: '/register', color: 'primary' },
    { title: 'Triage Assessment', icon: <Assessment />, path: '/triage', color: 'secondary' },
    { title: 'Device Integration', icon: <Devices />, path: '/vitals', color: 'info' },
    { title: 'Queue Dashboard', icon: <DashboardIcon />, path: '/queue', color: 'success' },
  ];

  return (
    <Box sx={{ textAlign: 'center', py: 4 }}>
      <Typography variant="h3" gutterBottom>
        Smart Triage Kiosk System
      </Typography>
      <Typography variant="h6" color="text.secondary" paragraph>
        Streamlined healthcare triage with AI-powered risk assessment
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 4, maxWidth: 800, mx: 'auto' }}>
        {menuItems.map((item) => (
          <Grid item xs={12} sm={6} key={item.title}>
            <Card 
              sx={{ 
                cursor: 'pointer', 
                transition: 'transform 0.2s',
                '&:hover': { transform: 'translateY(-4px)' }
              }}
              onClick={() => navigate(item.path)}
            >
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Box sx={{ color: `${item.color}.main`, mb: 2 }}>
                  {React.cloneElement(item.icon, { fontSize: 'large' })}
                </Box>
                <Typography variant="h6">
                  {item.title}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export const Login: React.FC = () => {
  return (
    <Box sx={{ textAlign: 'center', py: 8 }}>
      <Typography variant="h4" gutterBottom>
        Staff Login
      </Typography>
      <Typography>Login functionality will be implemented here</Typography>
    </Box>
  );
};

export const TriageAssessment: React.FC = () => {
  return (
    <Box sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Triage Assessment
      </Typography>
      <Typography>AI-powered triage assessment will be implemented here</Typography>
    </Box>
  );
};

export const VitalSigns: React.FC = () => {
  return (
    <Box sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Vital Signs & Device Integration
      </Typography>
      <Typography>Device integration and vital signs monitoring will be implemented here</Typography>
    </Box>
  );
};

export const QueueManagement: React.FC = () => {
  return (
    <Box sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Queue Management
      </Typography>
      <Typography>Real-time queue management dashboard will be implemented here</Typography>
    </Box>
  );
};

export const Dashboard: React.FC = () => {
  return (
    <Box sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography>System overview dashboard will be implemented here</Typography>
    </Box>
  );
};

export const Settings: React.FC = () => {
  return (
    <Box sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        System Settings
      </Typography>
      <Typography>Application settings will be implemented here</Typography>
    </Box>
  );
};
