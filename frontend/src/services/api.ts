import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

function extractError(err: any): Error {
  const msg = err?.response?.data?.detail || err?.message || 'Request failed';
  return new Error(msg);
}

export interface ContactInfo {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  linkedin?: string;
  website?: string;
  title?: string;
}

export interface Experience {
  title?: string;
  company?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  description?: string;
  is_current: boolean;
}

export interface Education {
  degree?: string;
  institution?: string;
  location?: string;
  graduation_date?: string;
  gpa?: string;
  honors?: string;
}

export interface ExtractedData {
  contact_info: ContactInfo;
  summary?: string;
  experience: Experience[];
  education: Education[];
  skills: string[];
  certifications?: string[];
  raw_text?: string;
  confidence_score: number;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  original_filename: string;
  output_filename?: string;
  error_message?: string;
  created_at?: string;
  completed_at?: string;
  processing_time?: number;
}

export interface TemplateInfo {
  id: string;
  name: string;
  description?: string;
  version: string;
  fields: string[];
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  filename: string;
  file_size: number;
  job_id: string;
  message: string;
}

export interface BatchUploadResponse {
  total_files: number;
  successful_uploads: number;
  failed_uploads: number;
  job_ids: string[];
  errors: string[];
}

// Upload API
export const uploadSingleResume = async (
  file: File,
  templateId: string = 'ezest-updated',
  options?: { useGemini?: boolean; geminiApiKey?: string | null }
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('template_id', templateId);
  if (options?.useGemini) formData.append('use_gemini', String(!!options.useGemini));
  if (options?.geminiApiKey) formData.append('gemini_api_key', options.geminiApiKey);

  try {
    const response = await api.post('/upload/single', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // Extend timeout for uploads (default instance is 30s)
      timeout: 180000,
    });
    return response.data;
  } catch (err: any) {
    throw extractError(err);
  }
};

export const uploadBatchResumes = async (
  files: File[],
  templateId: string = 'ezest-updated',
  options?: { useGemini?: boolean; geminiApiKey?: string | null }
): Promise<BatchUploadResponse> => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  formData.append('template_id', templateId);
  if (options?.useGemini) formData.append('use_gemini', String(!!options.useGemini));
  if (options?.geminiApiKey) formData.append('gemini_api_key', options.geminiApiKey);

  try {
    const response = await api.post('/upload/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // Batch can be slower due to multiple files; allow more time
      timeout: 180000,
    });
    return response.data;
  } catch (err: any) {
    throw extractError(err);
  }
};

// Job API
export const getJobStatus = async (jobId: string): Promise<JobStatus> => {
  const response = await api.get(`/jobs/${jobId}/status`);
  return response.data;
};

export const getJobResult = async (jobId: string): Promise<any> => {
  const response = await api.get(`/jobs/${jobId}/result`);
  return response.data;
};

// Regenerate rendered DOCX for a job using current extracted data and template
export const regenerateJob = async (jobId: string): Promise<{ output_filename?: string; message?: string }> => {
  const response = await api.post(`/jobs/${jobId}/render`);
  return response.data;
};

export const cancelJob = async (jobId: string): Promise<{ message: string; job_id: string }> => {
  const response = await api.delete(`/jobs/${jobId}`);
  return response.data;
};

// Template API
export const getTemplates = async (): Promise<TemplateInfo[]> => {
  const response = await api.get('/templates/');
  return response.data;
};

export const getTemplate = async (templateId: string): Promise<TemplateInfo> => {
  const response = await api.get(`/templates/${templateId}`);
  return response.data;
};

export const getTemplatePreview = async (templateId: string): Promise<any> => {
  const response = await api.get(`/templates/${templateId}/preview`);
  return response.data;
};

// Download API
export const downloadResult = async (jobId: string): Promise<Blob> => {
  const response = await api.get(`/download/${jobId}`, {
    responseType: 'blob',
  });
  return response.data;
};

export const downloadBatchZip = async (jobIds: string[]): Promise<Blob> => {
  const response = await api.post(
    `/download/batch`,
    jobIds,
    {
      responseType: 'blob',
    }
  );
  return response.data;
};

export const cleanupJobFiles = async (jobId: string): Promise<{ message: string; job_id: string }> => {
  const response = await api.delete(`/download/${jobId}`);
  return response.data;
};

export default api;
