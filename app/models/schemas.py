from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ResumeSection(str, Enum):
    """Resume sections"""
    CONTACT_INFO = "contact_info"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    CERTIFICATIONS = "certifications"
    OTHER = "other"

class ContactInfo(BaseModel):
    """Contact information model"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None

class Experience(BaseModel):
    """Work experience model"""
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    is_current: bool = False

class Education(BaseModel):
    """Education model"""
    degree: Optional[str] = None
    institution: Optional[str] = None
    location: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None

class ExtractedData(BaseModel):
    """Extracted resume data model"""
    contact_info: ContactInfo = ContactInfo()
    summary: Optional[str] = None
    experience: List[Experience] = []
    education: List[Education] = []
    skills: List[str] = []
    certifications: List[str] = []
    raw_text: Optional[str] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

class TemplateInfo(BaseModel):
    """Template information model"""
    id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    fields: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ProcessingJob(BaseModel):
    """Processing job model"""
    job_id: str
    status: JobStatus = JobStatus.PENDING
    template_id: str
    original_filename: str
    extracted_data: Optional[ExtractedData] = None
    output_filename: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    # LLM processing options
    use_gemini: bool = False
    gemini_api_key: Optional[str] = None

class JobResponse(BaseModel):
    """Job response model"""
    job_id: str
    status: JobStatus
    message: str
    download_url: Optional[str] = None

class UploadResponse(BaseModel):
    """File upload response model"""
    filename: str
    file_size: int
    job_id: str
    message: str

class BatchUploadResponse(BaseModel):
    """Batch upload response model"""
    total_files: int
    successful_uploads: int
    failed_uploads: int
    job_ids: List[str]
    errors: List[str] = []
