import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Button,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Paper,
  TextField,
  FormControlLabel,
  Switch,
  Tooltip,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  Delete as DeleteIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { uploadSingleResume, uploadBatchResumes } from '../services/api';

interface FileUploadProps {
  onUploadSuccess: (jobIds: string[], filenames: string[]) => void;
  selectedTemplate: string;
}

interface FileWithStatus {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  jobId?: string;
  error?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess, selectedTemplate }) => {
  const [files, setFiles] = useState<FileWithStatus[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useGemini, setUseGemini] = useState<boolean>(false);
  const [geminiApiKey, setGeminiApiKey] = useState<string>('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      status: 'pending' as const,
    }));
    setFiles(prev => [...prev, ...newFiles]);
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      const pendingFiles = files.filter(f => f.status === 'pending');
      
      if (pendingFiles.length === 1) {
        // Single file upload
        const fileWithStatus = pendingFiles[0];
        setFiles(prev => prev.map(f => 
          f === fileWithStatus ? { ...f, status: 'uploading' } : f
        ));

        try {
          const response = await uploadSingleResume(
            fileWithStatus.file,
            selectedTemplate,
            { useGemini, geminiApiKey: geminiApiKey || null }
          );
          setFiles(prev => prev.map(f => 
            f === fileWithStatus ? { ...f, status: 'success', jobId: response.job_id } : f
          ));
          onUploadSuccess([response.job_id], [fileWithStatus.file.name]);
        } catch (err: any) {
          console.error('Upload error (single):', err);
          setFiles(prev => prev.map(f => 
            f === fileWithStatus ? { ...f, status: 'error', error: err?.message || 'Upload failed' } : f
          ));
        }
      } else {
        // Batch upload
        setFiles(prev => prev.map(f => 
          f.status === 'pending' ? { ...f, status: 'uploading' } : f
        ));

        try {
          const response = await uploadBatchResumes(
            pendingFiles.map(f => f.file), 
            selectedTemplate,
            { useGemini, geminiApiKey: geminiApiKey || null }
          );
          
          // Update file statuses
          let jobIndex = 0;
          setFiles(prev => prev.map(f => {
            if (f.status === 'uploading') {
              if (jobIndex < response.job_ids.length) {
                const result = { ...f, status: 'success' as const, jobId: response.job_ids[jobIndex] };
                jobIndex++;
                return result;
              } else {
                return { ...f, status: 'error' as const, error: 'Upload failed' };
              }
            }
            return f;
          }));

          onUploadSuccess(response.job_ids, pendingFiles.map(f => f.file.name));
        } catch (err: any) {
          console.error('Upload error (batch):', err);
          setFiles(prev => prev.map(f => 
            f.status === 'uploading' ? { ...f, status: 'error', error: err?.message || 'Upload failed' } : f
          ));
        }
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const clearFiles = () => {
    setFiles([]);
    setError(null);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <SuccessIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      case 'uploading':
        return <LinearProgress sx={{ width: 20, height: 20 }} />;
      default:
        return <FileIcon />;
    }
  };

  const pendingFiles = files.filter(f => f.status === 'pending');
  const hasFiles = files.length > 0;

  return (
    <Box>
      {/* Dropzone */}
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          transition: 'all 0.2s ease',
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop files here' : 'Drag & drop resume files here'}
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          or click to select files
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Supported formats: PDF, DOC, DOCX (Max 10MB each)
        </Typography>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* LLM Options */}
      <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <FormControlLabel
          control={<Switch checked={useGemini} onChange={(e) => setUseGemini(e.target.checked)} />}
          label="Use Gemini LLM"
        />
        <Tooltip title="Your API key is used only to process this upload and is not stored permanently.">
          <TextField
            label="Gemini API Key"
            type="password"
            size="small"
            value={geminiApiKey}
            onChange={(e) => setGeminiApiKey(e.target.value)}
            placeholder="Enter your API key"
            sx={{ minWidth: 320 }}
            disabled={!useGemini}
          />
        </Tooltip>
      </Box>

      {/* File List */}
      {hasFiles && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Selected Files ({files.length})
          </Typography>
          
          <List>
            {files.map((fileWithStatus, index) => (
              <ListItem key={index} divider>
                <ListItemIcon>
                  {getStatusIcon(fileWithStatus.status)}
                </ListItemIcon>
                <ListItemText
                  primary={fileWithStatus.file.name}
                  secondary={
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        {(fileWithStatus.file.size / 1024 / 1024).toFixed(2)} MB
                      </Typography>
                      {fileWithStatus.error && (
                        <Typography variant="caption" color="error" display="block">
                          Error: {fileWithStatus.error}
                        </Typography>
                      )}
                      {fileWithStatus.jobId && (
                        <Typography variant="caption" color="success.main" display="block">
                          Job ID: {fileWithStatus.jobId}
                        </Typography>
                      )}
                    </Box>
                  }
                />
                {fileWithStatus.status === 'pending' && (
                  <IconButton onClick={() => removeFile(index)} size="small">
                    <DeleteIcon />
                  </IconButton>
                )}
              </ListItem>
            ))}
          </List>

          {/* Action Buttons */}
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<UploadIcon />}
              onClick={uploadFiles}
              disabled={uploading || pendingFiles.length === 0}
            >
              {uploading ? 'Uploading...' : `Upload ${pendingFiles.length} File${pendingFiles.length !== 1 ? 's' : ''}`}
            </Button>
            
            <Button
              variant="outlined"
              onClick={clearFiles}
              disabled={uploading}
            >
              Clear All
            </Button>
          </Box>

          {uploading && <LinearProgress sx={{ mt: 2 }} />}
        </Box>
      )}
    </Box>
  );
};

export default FileUpload;
