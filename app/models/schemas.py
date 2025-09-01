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
    title: Optional[str] = None

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
    # Additional structured fields for template rendering
    tools_title: Optional[str] = None
    skills_grouped: Dict[str, List[str]] = {}
    additional_data: Optional[Dict[str, Any]] = None  # Store enhanced extraction data

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
    """Job processing model"""
    job_id: str
    status: JobStatus
    template_id: str
    original_filename: str
    output_filename: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Set by processor when a job reaches a terminal state
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    # Collected non-fatal issues from template rendering
    warnings: Optional[List[str]] = None
    extracted_data: Optional[ExtractedData] = None
    use_gemini: bool = False
    gemini_api_key: Optional[str] = None
    attempt_count: int = 0  # Track number of processing attempts

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
