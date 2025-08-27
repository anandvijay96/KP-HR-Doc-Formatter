import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Chip,
  Grid,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
  Autorenew as ProcessingIcon,
} from '@mui/icons-material';
import { getJobStatus, getJobResult, downloadResult, ExtractedData } from '../services/api';

const JobStatus: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [jobData, setJobData] = useState<any>(null);
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (jobId) {
      loadJobStatus();
      const interval = setInterval(() => {
        if (jobData?.status === 'pending' || jobData?.status === 'processing') {
          loadJobStatus();
        }
      }, 3000); // Poll every 3 seconds for active jobs

      return () => clearInterval(interval);
    }
  }, [jobId, jobData?.status]);

  const loadJobStatus = async () => {
    if (!jobId) return;

    try {
      setLoading(true);
      const status = await getJobStatus(jobId);
      setJobData(status);

      // If job is completed, load the result
      if (status.status === 'completed') {
        try {
          const result = await getJobResult(jobId);
          setExtractedData(result.extracted_data);
        } catch (err) {
          console.error('Failed to load job result:', err);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load job status');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!jobId) return;

    try {
      setDownloading(true);
      const blob = await downloadResult(jobId);
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = jobData.output_filename || 'formatted_resume.docx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || 'Download failed');
    } finally {
      setDownloading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <SuccessIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'processing':
        return <ProcessingIcon color="warning" />;
      default:
        return <PendingIcon color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'processing':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (loading && !jobData) {
    return (
      <Box>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading job status...
        </Typography>
      </Box>
    );
  }

  if (error && !jobData) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/')}>
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/')}
          sx={{ mr: 2 }}
        >
          Back to Dashboard
        </Button>
        <Typography variant="h5">
          Job Status
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Job Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Job Information
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Job ID
                </Typography>
                <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                  {jobId}
                </Typography>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Status
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getStatusIcon(jobData?.status)}
                  <Chip
                    label={jobData?.status || 'Unknown'}
                    color={getStatusColor(jobData?.status) as any}
                  />
                </Box>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Original File
                </Typography>
                <Typography variant="body1">
                  {jobData?.original_filename || 'Unknown'}
                </Typography>
              </Box>

              {jobData?.created_at && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Created At
                  </Typography>
                  <Typography variant="body1">
                    {new Date(jobData.created_at).toLocaleString()}
                  </Typography>
                </Box>
              )}

              {jobData?.completed_at && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Completed At
                  </Typography>
                  <Typography variant="body1">
                    {new Date(jobData.completed_at).toLocaleString()}
                  </Typography>
                </Box>
              )}

              {jobData?.processing_time && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Processing Time
                  </Typography>
                  <Typography variant="body1">
                    {jobData.processing_time.toFixed(2)} seconds
                  </Typography>
                </Box>
              )}

              {jobData?.error_message && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="error">
                    Error Message
                  </Typography>
                  <Typography variant="body1" color="error">
                    {jobData.error_message}
                  </Typography>
                </Box>
              )}

              <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                <Button
                  startIcon={<RefreshIcon />}
                  onClick={loadJobStatus}
                  disabled={loading}
                >
                  Refresh
                </Button>
                
                {jobData?.status === 'completed' && (
                  <Button
                    variant="contained"
                    startIcon={<DownloadIcon />}
                    onClick={handleDownload}
                    disabled={downloading}
                  >
                    {downloading ? 'Downloading...' : 'Download Result'}
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Extracted Data Preview */}
        {extractedData && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Extracted Data Preview
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Confidence Score
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={extractedData.confidence_score * 100}
                      sx={{ flexGrow: 1 }}
                    />
                    <Typography variant="body2">
                      {(extractedData.confidence_score * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                </Box>

                <Divider sx={{ my: 2 }} />

                {/* Contact Info */}
                {extractedData.contact_info && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Contact Information
                    </Typography>
                    <Typography variant="body2">
                      Name: {extractedData.contact_info.name || 'N/A'}
                    </Typography>
                    {extractedData.contact_info.title && (
                      <Typography variant="body2">
                        Title: {extractedData.contact_info.title}
                      </Typography>
                    )}
                    <Typography variant="body2">
                      Email: {extractedData.contact_info.email || 'N/A'}
                    </Typography>
                    <Typography variant="body2">
                      Phone: {extractedData.contact_info.phone || 'N/A'}
                    </Typography>
                  </Box>
                )}

                {/* Summary (bulletized) */}
                {extractedData.summary && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Profile Summary
                    </Typography>
                    <List dense sx={{ pl: 2 }}>
                      {extractedData.summary
                        .split('\n')
                        .map((s) => s.trim().replace(/^[-•\s]+/, ''))
                        .filter((s) => s.length > 0)
                        .slice(0, 8)
                        .map((line, idx) => (
                          <ListItem key={idx} sx={{ px: 0, display: 'list-item', listStyleType: 'disc' }}>
                            <ListItemText primaryTypographyProps={{ variant: 'body2' }} primary={line} />
                          </ListItem>
                        ))}
                    </List>
                  </Box>
                )}

                {/* Skills */}
                {extractedData.skills && extractedData.skills.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Skills ({extractedData.skills.length})
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {extractedData.skills.slice(0, 10).map((skill, index) => (
                        <Chip key={index} label={skill} size="small" />
                      ))}
                      {extractedData.skills.length > 10 && (
                        <Chip label={`+${extractedData.skills.length - 10} more`} size="small" variant="outlined" />
                      )}
                    </Box>
                  </Box>
                )}

                {/* Experience */}
                {extractedData.experience && extractedData.experience.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Experience ({extractedData.experience.length} positions)
                    </Typography>
                    <List dense>
                      {extractedData.experience.slice(0, 3).map((exp, index) => (
                        <ListItem key={index} sx={{ px: 0 }}>
                          <ListItemText
                            primary={`${exp.title || 'Position'} at ${exp.company || 'Company'}`}
                            secondary={`${exp.start_date || 'Start'} - ${exp.end_date || 'End'}`}
                          />
                        </ListItem>
                      ))}
                      {extractedData.experience.length > 3 && (
                        <ListItem sx={{ px: 0 }}>
                          <ListItemText
                            primary={`... and ${extractedData.experience.length - 3} more positions`}
                          />
                        </ListItem>
                      )}
                    </List>
                  </Box>
                )}

                {/* Education */}
                {extractedData.education && extractedData.education.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Education ({extractedData.education.length})
                    </Typography>
                    <List dense>
                      {extractedData.education.map((edu, index) => (
                        <ListItem key={index} sx={{ px: 0 }}>
                          <ListItemText
                            primary={edu.degree || 'Degree'}
                            secondary={edu.institution || 'Institution'}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Progress indicator for active jobs */}
        {(jobData?.status === 'pending' || jobData?.status === 'processing') && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="body1" gutterBottom>
                {jobData?.status === 'pending' ? 'Job is queued for processing...' : 'Processing your resume...'}
              </Typography>
              <LinearProgress />
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default JobStatus;
