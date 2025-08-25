import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

from app.models.schemas import ContactInfo, Experience, Education, ExtractedData

class NLPExtractor:
    """Advanced NLP-based data extraction from resume text"""
    
    def __init__(self):
        self.nlp = None
        self._load_model()
        
    def _load_model(self):
        """Load spaCy model - disabled for Python 3.12 compatibility"""
        logging.info("Using basic NLP extraction (spaCy disabled for Python 3.12 compatibility)")
        self.nlp = None
    
    def extract_contact_info(self, text: str) -> ContactInfo:
        """Extract contact information using improved regex patterns"""
        contact_info = ContactInfo()
        lines = text.split('\n')
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text, re.IGNORECASE)
        if emails:
            contact_info.email = emails[0]
        
        # Phone extraction (multiple formats)
        phone_patterns = [
            r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'(\+?\d{1,3}[-.\s]?)?\d{10}',
            r'(\+?\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                # Clean up the phone number
                phone = re.sub(r'[^\d+]', '', phones[0])
                if len(phone) >= 10:
                    contact_info.phone = phone
                    break
        
        # LinkedIn URL extraction
        linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_matches:
            contact_info.linkedin = linkedin_matches[0]
        
        # Website extraction
        website_pattern = r'(?:https?://)?(?:www\.)?[\w.-]+\.[a-zA-Z]{2,}(?:/[\w.-]*)*'
        websites = re.findall(website_pattern, text)
        for website in websites:
            if '@' not in website and 'linkedin.com' not in website.lower():
                contact_info.website = website
                break
        
        # Improved name extraction - look for proper names in first few lines
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if not line:
                continue
                
            # Skip lines that are clearly not names
            skip_patterns = [
                r'@', r'http', r'www', r'\.com', r'phone', r'email', r'address',
                r'resume', r'cv', r'curriculum', r'vitae', r'profile', r'summary'
            ]
            
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
                continue
            
            # Look for name patterns
            words = line.split()
            if 2 <= len(words) <= 4:  # Names typically 2-4 words
                # Check if words look like names (start with capital, mostly letters)
                if all(word[0].isupper() and word.replace("'", "").replace("-", "").isalpha() 
                       for word in words if len(word) > 1):
                    # Additional check: avoid common non-name phrases
                    non_name_words = ['senior', 'junior', 'developer', 'engineer', 'manager', 
                                    'analyst', 'consultant', 'specialist', 'director', 'lead']
                    if not any(word.lower() in non_name_words for word in words):
                        contact_info.name = line
                        break
            
            # Check for title patterns (in parentheses or after name)
            title_match = re.search(r'\(([^)]+)\)', line)
            if title_match and contact_info.name and contact_info.name in line:
                # This line contains both name and title
                break
        
        # If no name found in first approach, try a more lenient search
        if not contact_info.name:
            for line in lines[:3]:
                line = line.strip()
                if line and len(line.split()) >= 2 and len(line) < 60:
                    # Very basic check - just avoid obvious non-names
                    if not any(char in line for char in ['@', '.com', 'http']):
                        words = line.split()
                        if len(words) >= 2 and all(len(word) > 1 for word in words):
                            contact_info.name = line
                            break
        
        return contact_info
    
    def extract_experience(self, text: str) -> List[Experience]:
        """Extract work experience from resume text with improved parsing"""
        experiences = []
        
        # Enhanced experience section patterns
        exp_patterns = [
            r'(?i)(?:work\s+)?experience',
            r'(?i)professional\s+experience',
            r'(?i)employment\s+history',
            r'(?i)career\s+history',
            r'(?i)work\s+history',
            r'(?i)relevant\s+work\s+experience',
            r'(?i)project\s+experience',
            r'(?i)professional\s+background'
        ]
        
        exp_section = self._extract_section(text, exp_patterns)
        if exp_section:
            # Parse individual experiences with improved logic
            experiences.extend(self._parse_experience_section(exp_section))
        
        # Also look for project-based experience patterns
        project_experiences = self._extract_project_experience(text)
        experiences.extend(project_experiences)
        
        return experiences[:5]  # Limit to 5 most recent positions
    
    def _extract_project_experience(self, text: str) -> List[Experience]:
        """Extract project-based experience entries"""
        experiences = []
        
        # Look for project patterns
        project_patterns = [
            r'(?i)project\s*[#:]?\s*\d+.*?(?=project\s*[#:]?\s*\d+|$)',
            r'(?i)(?:client|customer)\s*:.*?(?=(?:client|customer)\s*:|$)',
        ]
        
        for pattern in project_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                project_text = match.group(0).strip()
                if len(project_text) > 50:  # Minimum length for valid project
                    exp = self._parse_single_experience(project_text)
                    if exp:
                        experiences.append(exp)
        
        return experiences
    
    def _parse_single_experience(self, text: str) -> Optional[Experience]:
        """Parse a single experience entry with enhanced patterns"""
        try:
            # Enhanced company name extraction
            company_patterns = [
                r'(?i)(?:company|employer|organization)\s*:?\s*([^\n]+)',
                r'(?i)project\s*[#:]?\s*\d+.*?(?:company|client|organization)\s*:?\s*([^\n]+)',
                r'(?i)^([A-Z][A-Za-z\s&.,\-()]+?)(?:\s*[-–]|\s*\||\s*,|\s*\n)',
                r'([A-Z][A-Za-z\s&.,\-()]{2,50})(?:\s*[-–]|\s*,)',
                r'(?i)(?:at|with|for)\s+([A-Z][A-Za-z\s&.,\-()]+?)(?:\s*[-–]|\s*,|\s*\n)',
            ]
            
            company = None
            for pattern in company_patterns:
                match = re.search(pattern, text)
                if match:
                    company = match.group(1).strip()
                    # Clean up common artifacts
                    company = re.sub(r'\s*[-–].*$', '', company)
                    company = re.sub(r'\s*\|.*$', '', company)
                    if len(company) > 3 and not re.match(r'^\d+', company):
                        break
            
            # Enhanced position/title extraction
            position_patterns = [
                r'(?i)(?:position|title|role)\s*:?\s*([^\n]+)',
                r'(?i)(?:as|working as)\s+([^\n,]+)',
                r'(?i)^.*?[-–]\s*([A-Z][A-Za-z\s]+?)(?:\s*[-–]|\s*\n|$)',
                r'(?i)(senior|junior|lead|principal|associate)?\s*(developer|engineer|analyst|consultant|manager|specialist|administrator)([^\n,]*)',
                r'(?i)project\s*[#:]?\s*\d+.*?role\s*:?\s*([^\n]+)',
            ]
            
            position = None
            for pattern in position_patterns:
                match = re.search(pattern, text)
                if match:
                    if len(match.groups()) > 1:
                        # Combine multiple groups for complex patterns
                        position = ' '.join(filter(None, match.groups())).strip()
                    else:
                        position = match.group(1).strip()
                    if len(position) > 3:
                        break
            
            # Enhanced date extraction
            date_patterns = [
                r'(?i)duration\s*:?\s*([^\n]+)',
                r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|present|current)',
                r'(\w+\s+\d{4})\s*[-–]\s*(\w+\s+\d{4}|present|current)',
                r'(\d{4})\s*[-–]\s*(\d{4}|present|current)',
                r'(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{4}\s*[-–]\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s*\d{4}|present|current',
            ]
            
            start_date = None
            end_date = None
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if 'duration' in pattern.lower():
                        # Parse duration format
                        duration_text = match.group(1)
                        date_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|present|current)', duration_text, re.IGNORECASE)
                        if date_match:
                            start_date = date_match.group(1)
                            end_date = date_match.group(2)
                    else:
                        start_date = match.group(1)
                        end_date = match.group(2) if len(match.groups()) > 1 else None
                    break
            
            # Enhanced description extraction
            description_parts = []
            
            # Look for project description
            desc_patterns = [
                r'(?i)(?:project\s+)?description\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:technology|role|responsibilities)|$)',
                r'(?i)(?:summary|overview)\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:technology|role|responsibilities)|$)',
            ]
            
            for pattern in desc_patterns:
                match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                if match:
                    description_parts.append(match.group(1).strip())
                    break
            
            # Look for responsibilities
            resp_patterns = [
                r'(?i)(?:role\s*&?\s*)?responsibilities\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:technology|skills)|$)',
                r'(?i)duties\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\s*(?:technology|skills)|$)',
            ]
            
            for pattern in resp_patterns:
                match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                if match:
                    resp_text = match.group(1).strip()
                    # Clean up bullet points
                    resp_text = re.sub(r'^[•o\-*]\s*', '', resp_text, flags=re.MULTILINE)
                    description_parts.append(resp_text)
                    break
            
            description = ' '.join(description_parts) if description_parts else "Project experience"
            
            # Extract technologies
            tech_patterns = [
                r'(?i)technology\s*:?\s*([^\n]+)',
                r'(?i)technologies\s*used\s*:?\s*([^\n]+)',
                r'(?i)tech\s*stack\s*:?\s*([^\n]+)',
            ]
            
            technologies = []
            for pattern in tech_patterns:
                match = re.search(pattern, text)
                if match:
                    tech_text = match.group(1).strip()
                    technologies = [t.strip() for t in re.split(r'[,;|]', tech_text) if t.strip()]
                    break
            
            if company or position or any([start_date, end_date, description]):
                return Experience(
                    company=company or "Company",
                    title=position or "Position",
                    start_date=start_date or "Start Date",
                    end_date=end_date or "End Date",
                    description=description or "Job description",
                    location="",
                    is_current=bool(end_date and ('present' in end_date.lower() or 'current' in end_date.lower()) if end_date else False),
                )
                
        except Exception as e:
            print(f"Error parsing experience: {e}")
            
        return None
    
    def extract_education(self, text: str) -> List[Education]:
        """Extract education information"""
        education_list = []
        
        # Find education section
        education_patterns = [
            r'(?i)education',
            r'(?i)academic\s+background',
            r'(?i)qualifications'
        ]
        
        education_section = self._extract_section(text, education_patterns)
        if not education_section:
            return education_list
        
        # Common degree patterns
        degree_patterns = [
            r'(?i)(bachelor|master|phd|doctorate|associate|diploma|certificate).*?(?:of|in|degree)?\s+([^\n,]+)',
            r'(?i)(b\.?[as]\.?|m\.?[as]\.?|ph\.?d\.?|m\.?b\.?a\.?)\s+([^\n,]+)',
        ]
        
        lines = education_section.split('\n')
        current_education = Education()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to match degree patterns
            for pattern in degree_patterns:
                match = re.search(pattern, line)
                if match:
                    current_education.degree = match.group(0).strip()
                    break
            
            # Look for institution names (usually capitalized words)
            if not current_education.institution:
                # Simple heuristic: look for capitalized words that might be institutions
                words = line.split()
                if len(words) >= 2:
                    capitalized_words = [w for w in words if w[0].isupper() and len(w) > 2]
                    if len(capitalized_words) >= 2:
                        current_education.institution = ' '.join(capitalized_words)
            
            # Look for dates
            date_pattern = r'(\d{4})'
            dates = re.findall(date_pattern, line)
            if dates and not current_education.graduation_date:
                current_education.graduation_date = dates[-1]  # Take the latest year
        
        if current_education.degree or current_education.institution:
            education_list.append(current_education)
        
        return education_list
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        skills = []
        
        # Find skills section
        skills_patterns = [
            r'(?i)(?:technical\s+)?skills',
            r'(?i)core\s+competencies',
            r'(?i)technologies',
            r'(?i)expertise',
            r'(?i)tools\s+and\s+technologies'
        ]
        
        skills_section = self._extract_section(text, skills_patterns)
        if skills_section:
            # Extract skills from dedicated section
            skills.extend(self._parse_skills_section(skills_section))
        
        # Enhanced skill detection for ServiceNow and other technologies
        common_skills = [
            # ServiceNow specific
            'servicenow', 'itsm', 'itom', 'hrsd', 'service portal', 'flow designer',
            'business rules', 'client scripts', 'ui policies', 'glide script',
            'rest apis', 'soap apis', 'orchestration', 'discovery', 'event management',
            'incident management', 'problem management', 'change management',
            'service mapping', 'hr case management', 'csa', 'cad', 'cis-hrsd', 'cis-itom',
            
            # Programming & Technologies
            'javascript', 'python', 'java', 'html', 'css', 'xml', 'json',
            'angular', 'react', 'vue', 'node.js', 'typescript',
            
            # Databases & Tools
            'sql', 'mysql', 'postgresql', 'mongodb', 'oracle',
            'workday', 'oracle cloud', 'okta', 'docusign', 'adobe sign', 'peoplesoft',
            
            # Methodologies
            'agile', 'scrum', 'sdlc', 'waterfall', 'itil',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'ci/cd', 'git',
            
            # Other
            'integration hub', 'performance analytics', 'project management', 'leadership'
        ]
        
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                # Avoid duplicates
                skill_title = skill.title() if skill.islower() else skill
                if skill_title not in skills and skill_title.lower() not in [s.lower() for s in skills]:
                    skills.append(skill_title)
        
        # Also extract skills from profile/summary section for better coverage
        summary_patterns = [r'(?i)profile\s+summary', r'(?i)professional\s+summary', r'(?i)summary']
        summary_section = self._extract_section(text, summary_patterns)
        if summary_section:
            for skill in common_skills:
                if skill.lower() in summary_section.lower():
                    skill_title = skill.title() if skill.islower() else skill
                    if skill_title not in skills and skill_title.lower() not in [s.lower() for s in skills]:
                        skills.append(skill_title)
        
        return skills[:20]  # Increased limit for better coverage
    
    def _extract_section(self, text: str, patterns: List[str]) -> str:
        """Extract a specific section from resume text"""
        lines = text.split('\n')
        section_start = -1
        
        # Find section start
        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line):
                    section_start = i
                    break
            if section_start != -1:
                break
        
        if section_start == -1:
            return ""
        
        # Find section end (next major section or end of document)
        section_end = len(lines)
        end_patterns = [
            r'(?i)experience', r'(?i)education', r'(?i)skills', r'(?i)projects',
            r'(?i)certifications', r'(?i)awards', r'(?i)references'
        ]
        
        for i in range(section_start + 1, len(lines)):
            line = lines[i].strip()
            if line and any(re.match(pattern, line) for pattern in end_patterns):
                # Make sure it's actually a section header (not just mentioning the word)
                if len(line.split()) <= 3 and line[0].isupper():
                    section_end = i
                    break
        
        return '\n'.join(lines[section_start:section_end])
    
    def _parse_experience_section(self, section_text: str) -> List[Experience]:
        """Parse experience section into individual Experience objects with improved logic"""
        experiences = []
        
        # Enhanced splitting patterns for different resume formats
        split_patterns = [
            r'\n\s*\n',  # Double newlines
            r'(?=\d{4}\s*[-–])',  # Year patterns
            r'(?i)(?=(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4})',  # Month year
            r'(?i)(?=project\s*[#:]?\s*\d+)',  # Project patterns
            r'(?i)(?=company\s*:)',  # Company patterns
            r'(?i)(?=position\s*:)',  # Position patterns
        ]
        
        entries = [section_text]  # Start with full text
        for pattern in split_patterns:
            new_entries = []
            for entry in entries:
                new_entries.extend(re.split(pattern, entry))
            entries = new_entries
        
        for entry in entries:
            entry = entry.strip()
            if len(entry) < 20:  # Skip very short entries
                continue
                
            exp = self._parse_single_experience(entry)
            if exp:
                experiences.append(exp)
        
        return experiences
    
    def _split_job_entries(self, experience_text: str) -> List[str]:
        """Split experience section into individual job entries"""
        lines = experience_text.split('\n')
        entries = []
        current_entry = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Heuristic: new job entry likely starts with job title or company
            # Look for patterns that suggest a new job entry
            if (len(current_entry) > 0 and 
                (self._looks_like_job_title(line) or self._looks_like_company(line))):
                entries.append('\n'.join(current_entry))
                current_entry = [line]
            else:
                current_entry.append(line)
        
        if current_entry:
            entries.append('\n'.join(current_entry))
        
        return entries
    
    def _looks_like_job_title(self, line: str) -> bool:
        """Heuristic to identify job titles"""
        job_title_keywords = [
            'engineer', 'developer', 'manager', 'analyst', 'specialist',
            'coordinator', 'director', 'lead', 'senior', 'junior', 'associate'
        ]
        return any(keyword in line.lower() for keyword in job_title_keywords)
    
    def _looks_like_company(self, line: str) -> bool:
        """Heuristic to identify company names"""
        # Companies often have certain suffixes
        company_suffixes = ['inc', 'llc', 'corp', 'ltd', 'company', 'technologies', 'solutions']
        return any(suffix in line.lower() for suffix in company_suffixes)
    
    def _parse_job_entry(self, entry: str) -> Optional[Experience]:
        """Parse individual job entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None
        
        experience = Experience()
        
        # First line is likely job title or company
        if self._looks_like_job_title(lines[0]):
            experience.title = lines[0]
            if len(lines) > 1:
                experience.company = lines[1]
        else:
            experience.company = lines[0]
            if len(lines) > 1 and self._looks_like_job_title(lines[1]):
                experience.title = lines[1]
        
        # Look for dates
        date_pattern = r'(\d{1,2}/\d{4}|\d{4}|\w+\s+\d{4})'
        for line in lines:
            dates = re.findall(date_pattern, line)
            if len(dates) >= 2:
                experience.start_date = dates[0]
                experience.end_date = dates[1]
                break
            elif len(dates) == 1:
                if 'present' in line.lower() or 'current' in line.lower():
                    experience.start_date = dates[0]
                    experience.end_date = "Present"
                    experience.is_current = True
        
        # Combine remaining lines as description
        description_lines = []
        for line in lines[2:]:  # Skip title and company
            if not re.search(date_pattern, line):  # Skip date lines
                description_lines.append(line)
        
        if description_lines:
            experience.description = '\n'.join(description_lines)
        
        return experience if experience.title or experience.company else None
    
    def _parse_skills_section(self, skills_text: str) -> List[str]:
        """Parse skills from skills section"""
        skills = []
        
        # Common delimiters for skills
        delimiters = [',', ';', '|', '•', '·', '\n']
        
        # Replace delimiters with commas for easier splitting
        text = skills_text
        for delimiter in delimiters[1:]:  # Skip comma
            text = text.replace(delimiter, ',')
        
        # Split and clean
        skill_candidates = [skill.strip() for skill in text.split(',')]
        
        for skill in skill_candidates:
            # Basic validation
            if (skill and 
                len(skill) > 1 and 
                len(skill) < 50 and 
                not skill.lower() in ['skills', 'technologies', 'expertise']):
                skills.append(skill)
        
        return skills
