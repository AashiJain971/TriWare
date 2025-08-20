/**
 * Main Layout Component
 */

import React from 'react';
import { Box, AppBar, Toolbar, Typography, Container } from '@mui/material';
import { LocalHospital } from '@mui/icons-material';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <LocalHospital sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Smart Triage Kiosk
          </Typography>
        </Toolbar>
      </AppBar>
      <Container 
        component="main" 
        maxWidth={false} 
        sx={{ 
          flexGrow: 1, 
          py: 3,
          px: { xs: 1, sm: 3 }
        }}
      >
        {children}
      </Container>
    </Box>
  );
};

export default Layout;
