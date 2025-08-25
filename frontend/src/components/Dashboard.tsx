import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Alert,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import FileUpload from './FileUpload';
import { getTemplates, getJobStatus, downloadResult, TemplateInfo } from '../services/api';

interface JobItem {
  jobId: string;
  filename: string;
  status: string;
  templateId: string;
  createdAt?: string;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('ezest-updated');
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
    loadRecentJobs();
  }, []);

  const loadTemplates = async () => {
    try {
      const templatesData = await getTemplates();
      setTemplates(templatesData);
    } catch (err) {
      console.error('Failed to load templates:', err);
      setError('Failed to load templates');
    }
  };

  const loadRecentJobs = () => {
    // Load recent jobs from localStorage
    const savedJobs = localStorage.getItem('recentJobs');
    if (savedJobs) {
      setJobs(JSON.parse(savedJobs));
    }
  };

  const saveJobToHistory = (jobId: string, filename: string, templateId: string) => {
    const newJob: JobItem = {
      jobId,
      filename,
      status: 'pending',
      templateId,
      createdAt: new Date().toISOString(),
    };

    const updatedJobs = [newJob, ...jobs.slice(0, 9)]; // Keep last 10 jobs
    setJobs(updatedJobs);
    localStorage.setItem('recentJobs', JSON.stringify(updatedJobs));
  };

  const handleUploadSuccess = (jobIds: string[], filenames: string[]) => {
    jobIds.forEach((jobId, index) => {
      saveJobToHistory(jobId, filenames[index] || 'Unknown file', selectedTemplate);
    });
    
    if (jobIds.length === 1) {
      navigate(`/job/${jobIds[0]}`);
    }
  };

  const handleJobClick = (jobId: string) => {
    navigate(`/job/${jobId}`);
  };

  const handleDownload = async (jobId: string, filename: string) => {
    try {
      setLoading(true);
      const blob = await downloadResult(jobId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `formatted_${filename}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      setError('Download failed');
    } finally {
      setLoading(false);
    }
  };

  const refreshJobStatus = async (jobId: string, index: number) => {
    try {
      const status = await getJobStatus(jobId);
      const updatedJobs = [...jobs];
      updatedJobs[index].status = status.status;
      setJobs(updatedJobs);
      localStorage.setItem('recentJobs', JSON.stringify(updatedJobs));
    } catch (err) {
      console.error('Failed to refresh job status:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Resume Formatter Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload resume files and convert them to agency-specific templates automatically.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upload Resumes
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Template</InputLabel>
                <Select
                  value={selectedTemplate}
                  label="Template"
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                >
                  {templates.map((template) => (
                    <MenuItem key={template.id} value={template.id}>
                      {template.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FileUpload
                onUploadSuccess={handleUploadSuccess}
                selectedTemplate={selectedTemplate}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Stats
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Available Templates
                </Typography>
                <Typography variant="h4" color="primary">
                  {templates.length}
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Recent Jobs
                </Typography>
                <Typography variant="h4" color="primary">
                  {jobs.length}
                </Typography>
              </Box>
              <Button
                variant="outlined"
                startIcon={<FileIcon />}
                onClick={() => navigate('/templates')}
                fullWidth
              >
                View Templates
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Jobs */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Jobs
              </Typography>
              
              {jobs.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No recent jobs. Upload a resume to get started.
                </Typography>
              ) : (
                <List>
                  {jobs.map((job, index) => (
                    <ListItem key={job.jobId} divider>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <FileIcon fontSize="small" />
                            {job.filename}
                            <Chip
                              label={job.status}
                              color={getStatusColor(job.status) as any}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={`Template: ${job.templateId} • ${job.createdAt ? new Date(job.createdAt).toLocaleString() : 'Unknown time'}`}
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          onClick={() => refreshJobStatus(job.jobId, index)}
                          size="small"
                        >
                          <RefreshIcon />
                        </IconButton>
                        {job.status === 'completed' && (
                          <IconButton
                            onClick={() => handleDownload(job.jobId, job.filename)}
                            size="small"
                            color="primary"
                          >
                            <DownloadIcon />
                          </IconButton>
                        )}
                        <Button
                          size="small"
                          onClick={() => handleJobClick(job.jobId)}
                        >
                          View Details
                        </Button>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {loading && <LinearProgress sx={{ mt: 2 }} />}
    </Box>
  );
};

export default Dashboard;
