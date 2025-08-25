import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import { Description as DescriptionIcon } from '@mui/icons-material';
import Dashboard from './components/Dashboard';
import JobStatus from './components/JobStatus';
import Templates from './components/Templates';

function App() {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <DescriptionIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            HR Resume Formatter
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/job/:jobId" element={<JobStatus />} />
          <Route path="/templates" element={<Templates />} />
        </Routes>
      </Container>
    </Box>
  );
}

export default App;
