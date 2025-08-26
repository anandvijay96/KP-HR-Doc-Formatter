"""
Gemini AI Integration for Resume Processing
Handles LLM-based extraction and formatting of resume data
"""
import json
import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from pydantic import BaseModel

from app.models.schemas import ExtractedData, ContactInfo, Experience, Education

logger = logging.getLogger(__name__)

class GeminiProcessor:
    """Process resumes using Google's Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini processor with API key"""
        self.api_key = api_key
        self.model = None
        if api_key:
            self._setup_client(api_key)
    
    def _setup_client(self, api_key: str):
        """Setup Gemini API client"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")
            raise
    
    def update_api_key(self, api_key: str):
        """Update API key and reinitialize client"""
        self.api_key = api_key
        self._setup_client(api_key)
    
    def create_extraction_prompt(self, resume_text: str) -> str:
        """Create a structured prompt for resume data extraction"""
        prompt = f"""
You are an expert HR resume parser. Extract and format the following information from the resume text provided.
Format the output as a valid JSON object with the exact structure shown below.

IMPORTANT FORMATTING REQUIREMENTS:
1. Professional Summary: Convert to 3-7 concise bullet points highlighting key achievements and skills
2. Work Experience: Reorganize as "Project-wise Experience" with focus on projects/achievements rather than job titles
3. Education: Format as "Degree - Institution (Year)" or similar clean format
4. Skills: Extract both technical and soft skills, organize them clearly

RESUME TEXT:
{resume_text}

OUTPUT JSON STRUCTURE (use exactly this format):
{{
    "contact_info": {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "+1234567890",
        "address": "City, State",
        "linkedin": "linkedin.com/in/profile",
        "website": "portfolio.com"
    }},
    "title": "Professional Title/Role (e.g., Senior Software Engineer, Data Analyst)",
    "summary_bullets": [
        "Achievement or skill point 1",
        "Achievement or skill point 2",
        "Achievement or skill point 3"
    ],
    "project_experience": [
        {{
            "project_name": "Project or Role Name",
            "organization": "Company Name",
            "duration": "MM/YYYY - MM/YYYY or Present",
            "location": "City, State",
            "key_achievements": [
                "Specific achievement or responsibility 1",
                "Specific achievement or responsibility 2"
            ],
            "technologies": ["Tech1", "Tech2"]
        }}
    ],
    "education": [
        {{
            "qualification": "Degree Name - Major/Specialization",
            "institution": "University/College Name",
            "year": "YYYY or YYYY-YYYY",
            "gpa": "GPA if mentioned",
            "achievements": "Honors, awards, or notable achievements"
        }}
    ],
    "skills": {{
        "technical": ["Skill1", "Skill2", "Skill3"],
        "soft": ["Communication", "Leadership", etc.],
        "tools": ["Tool1", "Tool2"],
        "languages": ["Language1", "Language2"]
    }},
    "certifications": ["Certification 1", "Certification 2"]
}}

RULES:
- Extract actual data from the resume, don't make up information
- If information is not found, use null or empty array/string
- Format dates consistently
- Professional summary should be impactful and concise
- Group similar skills together
- For work experience, focus on achievements and impact rather than just responsibilities
- Return ONLY the JSON object, no additional text
"""
        return prompt
    
    async def extract_resume_data(self, resume_text: str) -> Dict[str, Any]:
        """Extract structured data from resume text using Gemini"""
        if not self.model:
            raise ValueError("Gemini API not initialized. Please provide API key.")
        
        try:
            # Create extraction prompt
            prompt = self.create_extraction_prompt(resume_text)
            
            # Generate response from Gemini
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            extracted_data = json.loads(response_text.strip())
            
            logger.info("Successfully extracted resume data using Gemini")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
            logger.debug(f"Response text: {response_text[:500]}")
            raise ValueError("Failed to parse LLM response. Please try again.")
        except Exception as e:
            logger.error(f"Gemini extraction failed: {str(e)}")
            raise
    
    def convert_to_extracted_data(self, gemini_data: Dict[str, Any]) -> ExtractedData:
        """Convert Gemini response to ExtractedData model"""
        try:
            # Extract contact info
            contact_data = gemini_data.get('contact_info', {})
            contact_info = ContactInfo(
                name=contact_data.get('name'),
                email=contact_data.get('email'),
                phone=contact_data.get('phone'),
                address=contact_data.get('address'),
                linkedin=contact_data.get('linkedin'),
                website=contact_data.get('website')
            )
            
            # Format professional summary from bullets
            summary_bullets = gemini_data.get('summary_bullets', [])
            summary = '\n'.join([f"• {bullet}" for bullet in summary_bullets if bullet])
            
            # Convert project experience to Experience objects
            experiences = []
            for project in gemini_data.get('project_experience', []):
                # Combine achievements into description
                achievements = project.get('key_achievements', [])
                description = '\n'.join([f"• {ach}" for ach in achievements])
                if project.get('technologies'):
                    description += f"\n\nTechnologies: {', '.join(project['technologies'])}"
                
                exp = Experience(
                    title=project.get('project_name', 'Project'),
                    company=project.get('organization'),
                    location=project.get('location'),
                    start_date=project.get('duration', '').split(' - ')[0] if project.get('duration') else None,
                    end_date=project.get('duration', '').split(' - ')[1] if ' - ' in project.get('duration', '') else None,
                    description=description,
                    is_current='Present' in project.get('duration', '')
                )
                experiences.append(exp)
            
            # Convert education
            education_list = []
            for edu in gemini_data.get('education', []):
                education = Education(
                    degree=edu.get('qualification'),
                    institution=edu.get('institution'),
                    graduation_date=edu.get('year'),
                    gpa=edu.get('gpa'),
                    honors=edu.get('achievements')
                )
                education_list.append(education)
            
            # Extract and flatten skills
            skills_data = gemini_data.get('skills', {})
            all_skills = []
            if isinstance(skills_data, dict):
                for category, skill_list in skills_data.items():
                    if isinstance(skill_list, list):
                        all_skills.extend(skill_list)
            elif isinstance(skills_data, list):
                all_skills = skills_data
            
            # Get certifications
            certifications = gemini_data.get('certifications', [])
            
            # Add professional title to summary if available
            title = gemini_data.get('title', '')
            if title and summary:
                summary = f"**{title}**\n\n{summary}"
            elif title:
                summary = title
            
            return ExtractedData(
                contact_info=contact_info,
                summary=summary,
                experience=experiences,
                education=education_list,
                skills=all_skills[:20],  # Limit skills to top 20
                certifications=certifications,
                confidence_score=0.95  # High confidence for LLM extraction
            )
            
        except Exception as e:
            logger.error(f"Failed to convert Gemini data to ExtractedData: {str(e)}")
            raise

    async def process_resume(self, resume_text: str) -> ExtractedData:
        """Main method to process resume text and return structured data"""
        gemini_data = await self.extract_resume_data(resume_text)
        return self.convert_to_extracted_data(gemini_data)
