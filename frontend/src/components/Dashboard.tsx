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
import { getTemplates, getJobStatus, downloadResult, downloadBatchZip, regenerateJob, cleanupJobFiles, TemplateInfo } from '../services/api';

interface JobItem {
  jobId: string;
  filename: string;
  status: string;
  templateId: string;
  createdAt?: string;
  batchId?: string; // For grouping batch uploads
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('ezest-updated');
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloadingAll, setDownloadingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
    loadRecentJobs();
  }, []);

  // Auto-refresh job statuses every 10 seconds for pending/processing jobs
  useEffect(() => {
    const pendingJobs = jobs.filter(job => job.status === 'pending' || job.status === 'processing');
    if (pendingJobs.length === 0) return;

    const interval = setInterval(async () => {
      const updatedJobs = [...jobs];
      let hasUpdates = false;

      for (let i = 0; i < updatedJobs.length; i++) {
        const job = updatedJobs[i];
        if (job.status === 'pending' || job.status === 'processing') {
          try {
            const status = await getJobStatus(job.jobId);
            if (status.status !== job.status) {
              updatedJobs[i] = { ...job, status: status.status };
              hasUpdates = true;
            }
          } catch (error: any) {
            // If job not found (404), mark as failed to stop retrying
            if (error?.message?.includes('Job not found') || error?.message?.includes('404')) {
              updatedJobs[i] = { ...job, status: 'failed' };
              hasUpdates = true;
            }
            console.error(`Failed to refresh status for job ${job.jobId}:`, error);
          }
        }
      }

      if (hasUpdates) {
        setJobs(updatedJobs);
        localStorage.setItem('recentJobs', JSON.stringify(updatedJobs));
      }
    }, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [jobs]);

  const loadTemplates = async () => {
    try {
      const templatesData = await getTemplates();
      setTemplates(templatesData);
    } catch (err) {
      console.error('Failed to load templates:', err);
      setError('Failed to load templates');
    }
  };

  const handleRetryBatchFailed = async (batchId: string) => {
    try {
      setLoading(true);
      const items = jobs.filter(j => j.batchId === batchId);
      // Refresh statuses first
      const refreshed = await Promise.all(items.map(async (j) => {
        try { return await getJobStatus(j.jobId); } catch { return { status: j.status }; }
      }));
      const failed = items.filter((_, idx) => refreshed[idx].status === 'failed' || refreshed[idx].status === 'error');
      for (const it of failed) {
        try {
          await regenerateJob(it.jobId);
        } catch (e) {
          // ignore per-item errors
          console.warn('Regenerate failed for', it.jobId, e);
        }
      }
      // Trigger a quick refresh on UI state
      const updated = [...jobs];
      for (let i = 0; i < updated.length; i++) {
        if (updated[i].batchId === batchId && (updated[i].status === 'failed' || updated[i].status === 'error')) {
          updated[i] = { ...updated[i], status: 'processing' };
        }
      }
      setJobs(updated);
      localStorage.setItem('recentJobs', JSON.stringify(updated));
    } finally {
      setLoading(false);
    }
  };

  const handleCleanupBatch = async (batchId: string) => {
    try {
      setLoading(true);
      const items = jobs.filter(j => j.batchId === batchId);
      // Only cleanup completed
      for (const it of items) {
        if (it.status === 'completed' || it.status === 'success') {
          try { await cleanupJobFiles(it.jobId); } catch (e) { console.warn('Cleanup failed for', it.jobId, e); }
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadBatchZip = async (batchId: string) => {
    try {
      setLoading(true);
      const inBatch = jobs.filter(j => j.batchId === batchId);
      // Send all jobIds; backend will include only completed outputs
      const blob = await downloadBatchZip(inBatch.map(j => j.jobId));
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      const ts = new Date().toISOString().replace(/[:.]/g, '-');
      link.href = url;
      link.download = `formatted_batch_${ts}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Batch zip download failed:', err);
      setError(err?.message || 'Batch download failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadAll = async () => {
    try {
      setDownloadingAll(true);
      // Refresh statuses
      const updated = await Promise.all(
        jobs.map(async (j) => {
          try {
            const status = await getJobStatus(j.jobId);
            return { j, status };
          } catch (error) {
            console.error(`Failed to get status for job ${j.jobId}:`, error);
            return { j, status: { status: j.status } }; // Use cached status if API fails
          }
        })
      );
      const completed = updated.filter(u => u.status.status === 'completed' || u.status.status === 'success');
      if (completed.length === 0) return;
      // Download sequentially to avoid saturating browser
      for (const item of completed) {
        try {
          const blob = await downloadResult(item.j.jobId);
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `formatted_${item.j.filename}`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          // small delay
          await new Promise(r => setTimeout(r, 300));
        } catch (e) {
          console.error('Download failed for', item.j.jobId, e);
        }
      }
    } finally {
      setDownloadingAll(false);
    }
  };

  const loadRecentJobs = () => {
    // Load recent jobs from localStorage
    const savedJobs = localStorage.getItem('recentJobs');
    if (savedJobs) {
      setJobs(JSON.parse(savedJobs));
    }
  };

  const saveJobToHistory = (jobId: string, filename: string, templateId: string, batchId?: string) => {
    const newJob: JobItem = {
      jobId,
      filename,
      status: 'pending',
      templateId,
      createdAt: new Date().toISOString(),
      batchId,
    };

    setJobs(prev => {
      const updated = [newJob, ...prev].slice(0, 20);
      localStorage.setItem('recentJobs', JSON.stringify(updated));
      return updated;
    });
  };

  const handleUploadSuccess = (jobIds: string[], filenames: string[]) => {
    // Generate batch ID for grouping if multiple files
    const batchId = jobIds.length > 1 ? `batch_${Date.now()}` : undefined;
    
    // Save all jobs to history
    jobIds.forEach((jobId, index) => {
      saveJobToHistory(jobId, filenames[index] || 'Unknown file', selectedTemplate, batchId);
    });
    
    // Show success message for batch uploads
    if (jobIds.length > 1) {
      setError(null);
      setSuccessMessage(`Successfully uploaded ${jobIds.length} files for processing. Jobs are now visible in the list below.`);
      // Auto-hide success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
    } else if (jobIds.length === 1) {
      // For single uploads, navigate to the job details
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
    } catch (err: any) {
      console.error('Failed to refresh job status:', err);
      // If job not found, mark as failed to stop retrying
      if (err?.message?.includes('Job not found') || err?.message?.includes('404')) {
        const updatedJobs = [...jobs];
        updatedJobs[index].status = 'failed';
        setJobs(updatedJobs);
        localStorage.setItem('recentJobs', JSON.stringify(updatedJobs));
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'success':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
      case 'error':
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

      {successMessage && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
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
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownloadAll}
                  disabled={downloadingAll || jobs.length === 0}
                >
                  {downloadingAll ? 'Downloading...' : 'Download All Completed'}
                </Button>
              </Box>
              
              {jobs.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No recent jobs. Upload a resume to get started.
                </Typography>
              ) : (
                <Box>
                  {(() => {
                    // Group jobs by batchId
                    const batchMap = new Map<string, JobItem[]>();
                    const singles: JobItem[] = [];
                    for (const j of jobs) {
                      if (j.batchId) {
                        if (!batchMap.has(j.batchId)) batchMap.set(j.batchId, []);
                        batchMap.get(j.batchId)!.push(j);
                      } else {
                        singles.push(j);
                      }
                    }

                    return (
                      <Box>
                        {/* Render batch groups */}
                        {[...batchMap.entries()].map(([batchId, items]) => (
                          <Box key={batchId} sx={{ mb: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Chip label="Batch" color="primary" size="small" />
                                <Typography variant="subtitle1">{items.length} files</Typography>
                                {(() => {
                                  const completed = items.filter(j => j.status === 'completed' || j.status === 'success').length;
                                  return (
                                    <Chip label={`${completed}/${items.length} completed`} size="small" color={completed === items.length ? 'success' : 'default'} />
                                  );
                                })()}
                              </Box>
                              <Box sx={{ display: 'flex', gap: 1 }}>
                                <Button
                                  variant="outlined"
                                  size="small"
                                  startIcon={<DownloadIcon />}
                                  onClick={() => handleDownloadBatchZip(batchId)}
                                >
                                  Download Batch (zip)
                                </Button>
                                <Button
                                  variant="outlined"
                                  size="small"
                                  onClick={() => handleRetryBatchFailed(batchId)}
                                >
                                  Retry Failed
                                </Button>
                                <Button
                                  variant="text"
                                  size="small"
                                  onClick={() => handleCleanupBatch(batchId)}
                                >
                                  Cleanup
                                </Button>
                              </Box>
                            </Box>
                            <List sx={{ border: '1px dashed', borderColor: 'divider', borderRadius: 1 }}>
                              {items.map((job) => {
                                const index = jobs.findIndex(j => j.jobId === job.jobId);
                                return (
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
                                      <IconButton onClick={() => refreshJobStatus(job.jobId, index)} size="small">
                                        <RefreshIcon />
                                      </IconButton>
                                      {(job.status === 'completed' || job.status === 'success') && (
                                        <IconButton
                                          onClick={() => handleDownload(job.jobId, job.filename)}
                                          size="small"
                                          color="primary"
                                          title="Download formatted resume"
                                        >
                                          <DownloadIcon />
                                        </IconButton>
                                      )}
                                      <Button size="small" onClick={() => handleJobClick(job.jobId)}>
                                        View Details
                                      </Button>
                                    </ListItemSecondaryAction>
                                  </ListItem>
                                );
                              })}
                            </List>
                          </Box>
                        ))}

                        {/* Render single jobs */}
                        {singles.length > 0 && (
                          <List>
                            {singles.map((job) => {
                              const index = jobs.findIndex(j => j.jobId === job.jobId);
                              return (
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
                                    <IconButton onClick={() => refreshJobStatus(job.jobId, index)} size="small">
                                      <RefreshIcon />
                                    </IconButton>
                                    {(job.status === 'completed' || job.status === 'success') && (
                                      <IconButton
                                        onClick={() => handleDownload(job.jobId, job.filename)}
                                        size="small"
                                        color="primary"
                                        title="Download formatted resume"
                                      >
                                        <DownloadIcon />
                                      </IconButton>
                                    )}
                                    <Button size="small" onClick={() => handleJobClick(job.jobId)}>
                                      View Details
                                    </Button>
                                  </ListItemSecondaryAction>
                                </ListItem>
                              );
                            })}
                          </List>
                        )}
                      </Box>
                    );
                  })()}
                </Box>
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
