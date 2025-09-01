"""
Enhanced Gemini AI Integration for Resume Processing
Handles dynamic categorization and improved extraction
"""
import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import google.generativeai as genai
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class EnhancedGeminiProcessor:
    """Enhanced processor with dynamic categorization and improved extraction"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Enhanced Gemini processor with API key"""
        self.api_key = api_key
        self.model = None
        if api_key:
            self._setup_client(api_key)
    
    def _setup_client(self, api_key: str):
        """Setup Gemini API client"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Enhanced Gemini API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")
            raise
    
    def update_api_key(self, api_key: str):
        """Update API key and reinitialize client"""
        self.api_key = api_key
        self._setup_client(api_key)
    
    def create_enhanced_extraction_prompt(self, resume_text: str) -> str:
        """Create an enhanced structured prompt for resume data extraction"""
        prompt = f"""
You are an expert HR resume parser. Extract and format the following information from the resume text provided.
Format the output as a valid JSON object with the exact structure shown below.

CRITICAL REQUIREMENTS:
1. Professional Summary: Convert to 3-7 concise bullet points highlighting key achievements and skills
2. Work Experience: Limit to MAX 5 detailed projects. Any additional projects go to "other_notable_projects"
3. Dates: Format ALL dates as "Mon YYYY" (e.g., "May 2022" not "05/2022")
4. Skills: Dynamically categorize skills based on the resume content (NOT predefined categories)
5. Education: Extract as individual entries for table rows
6. Certifications: Extract separately from education

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
    "title": "Professional Title/Role",
    "summary_bullets": [
        "Achievement or skill point 1",
        "Achievement or skill point 2",
        "Achievement or skill point 3"
    ],
    "skills_categories": {{
        "Category Name 1": ["Skill 1", "Skill 2", "Skill 3"],
        "Category Name 2": ["Skill 1", "Skill 2"],
        "Category Name 3": ["Skill 1", "Skill 2", "Skill 3", "Skill 4"]
    }},
    "detailed_experience": [
        {{
            "project_name": "Project or Role Name",
            "organization": "Company Name",
            "duration": "May 2022 - Nov 2024",
            "location": "City, State",
            "key_achievements": [
                "Specific achievement or responsibility 1",
                "Specific achievement or responsibility 2",
                "Specific achievement or responsibility 3"
            ],
            "technologies_used": ["Tech 1", "Tech 2", "Tech 3"]
        }}
    ],
    "other_notable_projects": [
        {{
            "project_name": "Project Name",
            "duration": "Jan 2020 - Dec 2020",
            "technology": "Primary Technology/Framework",
            "description": "Brief one-line description"
        }}
    ],
    "education": [
        {{
            "degree": "Bachelor of Science in Computer Science",
            "institution": "University Name",
            "year": "2020",
            "gpa": "3.8/4.0"
        }}
    ],
    "certifications": [
        {{
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
            "year": "2023",
            "credential_id": "ABC123"
        }}
    ],
    "attempt_count": 1
}}

IMPORTANT NOTES:
- For skills_categories: Create categories dynamically based on the resume (e.g., "ServiceNow Modules", "Cloud Platforms", "Programming Languages", "DevOps Tools", etc.)
- Limit detailed_experience to MAXIMUM 5 entries
- Any work experience beyond 5 entries goes to other_notable_projects in condensed format
- Format ALL dates as "Mon YYYY" (e.g., "Jan 2020", "May 2022", "Present")
- Separate certifications from education
- Each education entry should be a separate object for table rendering
"""
        return prompt
    
    def format_date(self, date_str: str) -> str:
        """Convert various date formats to 'Mon YYYY' format"""
        if not date_str or date_str.lower() == 'present':
            return 'Present'
        
        # Month abbreviations
        months = {
            '01': 'Jan', '1': 'Jan', 'january': 'Jan',
            '02': 'Feb', '2': 'Feb', 'february': 'Feb',
            '03': 'Mar', '3': 'Mar', 'march': 'Mar',
            '04': 'Apr', '4': 'Apr', 'april': 'Apr',
            '05': 'May', '5': 'May', 'may': 'May',
            '06': 'Jun', '6': 'Jun', 'june': 'Jun',
            '07': 'Jul', '7': 'Jul', 'july': 'Jul',
            '08': 'Aug', '8': 'Aug', 'august': 'Aug',
            '09': 'Sep', '9': 'Sep', 'september': 'Sep',
            '10': 'Oct', '10': 'Oct', 'october': 'Oct',
            '11': 'Nov', '11': 'Nov', 'november': 'Nov',
            '12': 'Dec', '12': 'Dec', 'december': 'Dec'
        }
        
        # Try to parse MM/YYYY or MM-YYYY format
        patterns = [
            r'(\d{1,2})[/-](\d{4})',  # MM/YYYY or MM-YYYY
            r'(\d{4})[/-](\d{1,2})',  # YYYY/MM or YYYY-MM
            r'([a-zA-Z]+)\s+(\d{4})',  # Month YYYY
            r'(\d{4})\s+([a-zA-Z]+)',  # YYYY Month
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                g1, g2 = match.groups()
                # Determine which is month and which is year
                if g1.isdigit() and int(g1) > 12:  # g1 is year
                    year = g1
                    month = months.get(g2.lower(), months.get(g2, g2))
                elif g2.isdigit() and int(g2) > 12:  # g2 is year
                    year = g2
                    month = months.get(g1.lower(), months.get(g1, g1))
                else:
                    # Assume first is month if both could be valid
                    month = months.get(g1.lower(), months.get(g1, g1))
                    year = g2
                
                return f"{month} {year}"
        
        return date_str  # Return as-is if no pattern matches
    
    async def extract_enhanced_data(self, resume_text: str) -> Dict[str, Any]:
        """Extract data using enhanced Gemini API with dynamic categorization"""
        if not self.model:
            raise ValueError("Gemini API client not initialized")
        
        try:
            prompt = self.create_enhanced_extraction_prompt(resume_text)
            response = self.model.generate_content(prompt)
            
            # Parse the response
            response_text = response.text
            
            # Clean up the response - remove markdown code blocks if present
            response_text = re.sub(r'^```json\s*', '', response_text, flags=re.MULTILINE)
            response_text = re.sub(r'^```\s*', '', response_text, flags=re.MULTILINE)
            response_text = re.sub(r'\s*```$', '', response_text, flags=re.MULTILINE)
            
            # Parse JSON
            extracted_data = json.loads(response_text)
            
            # Post-process dates to ensure Mon YYYY format
            if 'detailed_experience' in extracted_data:
                for exp in extracted_data['detailed_experience']:
                    if 'duration' in exp:
                        # Split duration (e.g., "05/2022 - 11/2024")
                        parts = exp['duration'].split('-')
                        if len(parts) == 2:
                            start = self.format_date(parts[0].strip())
                            end = self.format_date(parts[1].strip())
                            exp['duration'] = f"{start} - {end}"
            
            if 'other_notable_projects' in extracted_data:
                for proj in extracted_data['other_notable_projects']:
                    if 'duration' in proj:
                        parts = proj['duration'].split('-')
                        if len(parts) == 2:
                            start = self.format_date(parts[0].strip())
                            end = self.format_date(parts[1].strip())
                            proj['duration'] = f"{start} - {end}"
            
            # Initialize attempt_count if not present
            if 'attempt_count' not in extracted_data:
                extracted_data['attempt_count'] = 1
            
            logger.info("Successfully extracted enhanced data using Gemini API")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON response from Gemini API: {str(e)}")
        except Exception as e:
            logger.error(f"Gemini extraction failed: {str(e)}")
            raise
    
    def get_jinja2_variables(self) -> Dict[str, str]:
        """Return the Jinja2 variable structure for template rendering"""
        return {
            "variables": {
                "name": "{{ contact_info.name }}",
                "email": "{{ contact_info.email }}",
                "phone": "{{ contact_info.phone }}",
                "address": "{{ contact_info.address }}",
                "linkedin": "{{ contact_info.linkedin }}",
                "website": "{{ contact_info.website }}",
                "title": "{{ title }}",
                "summary_bullets": "{% for bullet in summary_bullets %}\n• {{ bullet }}\n{% endfor %}",
                "attempt_count": "{{ attempt_count }}"
            },
            "skills_loop": """
{% for category, skills in skills_categories.items() %}
    <b>{{ category }}:</b> {{ skills|join(', ') }}
{% endfor %}
""",
            "detailed_experience_loop": """
{% for exp in detailed_experience[:5] %}
    Project: {{ exp.project_name }}
    Organization: {{ exp.organization }}
    Duration: {{ exp.duration }}
    Location: {{ exp.location }}
    {% for achievement in exp.key_achievements %}
        • {{ achievement }}
    {% endfor %}
    Technologies: {{ exp.technologies_used|join(', ') }}
{% endfor %}
""",
            "other_projects_table": """
<table>
    <tr>
        <th>Project Name</th>
        <th>Duration</th>
        <th>Technology</th>
        <th>Description</th>
    </tr>
    {% for proj in other_notable_projects %}
    <tr>
        <td>{{ proj.project_name }}</td>
        <td>{{ proj.duration }}</td>
        <td>{{ proj.technology }}</td>
        <td>{{ proj.description }}</td>
    </tr>
    {% endfor %}
</table>
""",
            "education_table": """
<table>
    <tr>
        <th>Degree</th>
        <th>Institution</th>
        <th>Year</th>
    </tr>
    {% for edu in education %}
    <tr>
        <td>{{ edu.degree }}</td>
        <td>{{ edu.institution }}</td>
        <td>{{ edu.year }}</td>
    </tr>
    {% endfor %}
</table>
""",
            "certifications_table": """
<table>
    <tr>
        <th>Certification</th>
        <th>Issuer</th>
        <th>Year</th>
    </tr>
    {% for cert in certifications %}
    <tr>
        <td>{{ cert.name }}</td>
        <td>{{ cert.issuer }}</td>
        <td>{{ cert.year }}</td>
    </tr>
    {% endfor %}
</table>
"""
        }
