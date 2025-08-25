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
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Paper,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Visibility as PreviewIcon,
  Description as TemplateIcon,
} from '@mui/icons-material';
import { getTemplates, getTemplatePreview, TemplateInfo } from '../services/api';

const Templates: React.FC = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewDialog, setPreviewDialog] = useState<{
    open: boolean;
    template?: TemplateInfo;
    preview?: any;
  }>({ open: false });

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const templatesData = await getTemplates();
      setTemplates(templatesData);
    } catch (err: any) {
      setError(err.message || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (template: TemplateInfo) => {
    try {
      const preview = await getTemplatePreview(template.id);
      setPreviewDialog({
        open: true,
        template,
        preview,
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load template preview');
    }
  };

  const closePreview = () => {
    setPreviewDialog({ open: false });
  };

  const renderPreviewContent = (preview: any) => {
    if (!preview || !preview.structure) {
      return <Typography>No preview available</Typography>;
    }

    return (
      <Box>
        {/* Header Section */}
        {preview.structure.header && (
          <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
            <Typography variant="h6" gutterBottom>
              Header Section
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
              Name: {preview.structure.header.name}
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
              Contact: {preview.structure.header.contact || preview.structure.header.email}
            </Typography>
          </Paper>
        )}

        {/* Sections */}
        {preview.structure.sections && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Document Sections
            </Typography>
            <List>
              {preview.structure.sections.map((section: any, index: number) => (
                <ListItem key={index} divider>
                  <ListItemText
                    primary={section.title}
                    secondary={
                      <Typography
                        variant="body2"
                        sx={{ fontFamily: 'monospace', color: 'text.secondary' }}
                      >
                        {section.content}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Legacy structure support */}
        {!preview.structure.sections && (
          <Box>
            {Object.entries(preview.structure).map(([key, value]: [string, any]) => {
              if (key === 'header') return null;
              
              return (
                <Paper key={key} sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="subtitle1" gutterBottom sx={{ textTransform: 'capitalize' }}>
                    {key.replace('_', ' ')}
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {Array.isArray(value) ? JSON.stringify(value, null, 2) : String(value)}
                  </Typography>
                </Paper>
              );
            })}
          </Box>
        )}
      </Box>
    );
  };

  if (loading) {
    return (
      <Box>
        <Typography variant="h6">Loading templates...</Typography>
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
          Available Templates
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {templates.map((template) => (
          <Grid item xs={12} md={6} lg={4} key={template.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TemplateIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" component="div">
                    {template.name}
                  </Typography>
                </Box>

                <Typography variant="body2" color="text.secondary" paragraph>
                  {template.description || 'No description available'}
                </Typography>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Version: {template.version}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Template ID: {template.id}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Supported Fields:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {template.fields.map((field) => (
                      <Chip
                        key={field}
                        label={field.replace('_', ' ')}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>

                <Typography variant="caption" color="text.secondary">
                  Created: {new Date(template.created_at).toLocaleDateString()}
                </Typography>
              </CardContent>

              <Box sx={{ p: 2, pt: 0 }}>
                <Button
                  variant="outlined"
                  startIcon={<PreviewIcon />}
                  onClick={() => handlePreview(template)}
                  fullWidth
                >
                  Preview Template
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>

      {templates.length === 0 && !loading && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <TemplateIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Templates Available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Templates will appear here once they are configured.
          </Typography>
        </Paper>
      )}

      {/* Preview Dialog */}
      <Dialog
        open={previewDialog.open}
        onClose={closePreview}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Template Preview: {previewDialog.template?.name}
        </DialogTitle>
        <DialogContent>
          {previewDialog.preview && renderPreviewContent(previewDialog.preview)}
        </DialogContent>
        <DialogActions>
          <Button onClick={closePreview}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Templates;
