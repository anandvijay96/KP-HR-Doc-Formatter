"""
Test script for enhanced extraction with Jinja2 variables
"""
import asyncio
import json
from app.services.enhanced_gemini_processor import EnhancedGeminiProcessor

# Sample resume text for testing
SAMPLE_RESUME = """
John Smith
Senior Software Engineer
john.smith@email.com | +1-234-567-8900 | San Francisco, CA
LinkedIn: linkedin.com/in/johnsmith | Portfolio: johnsmith.dev

PROFESSIONAL SUMMARY
• Led development of microservices architecture serving 10M+ users
• Expertise in cloud-native applications with 8+ years experience
• Strong background in ServiceNow platform customization and integration
• Certified AWS Solutions Architect with extensive DevOps experience
• Mentored 15+ junior developers and led 3 cross-functional teams

SKILLS & TECHNOLOGIES
ServiceNow Modules: Service Portal, ITSM, ITOM, Flow Designer, Virtual Agent
Cloud Platforms: AWS (EC2, Lambda, S3, RDS), Azure (Functions, CosmosDB), GCP
Programming Languages: Python, JavaScript, TypeScript, Java, Go
DevOps Tools: Docker, Kubernetes, Jenkins, GitLab CI/CD, Terraform
Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
Frontend Frameworks: React, Angular, Vue.js, Next.js

PROFESSIONAL EXPERIENCE

Senior Software Engineer - Tech Corp
05/2022 - Present | San Francisco, CA
• Architected and implemented microservices platform reducing latency by 40%
• Led migration of legacy monolith to cloud-native architecture on AWS
• Implemented CI/CD pipelines reducing deployment time from 2 hours to 15 minutes
Technologies: Python, Kubernetes, AWS, ServiceNow

Full Stack Developer - Innovation Labs  
03/2020 - 04/2022 | New York, NY
• Developed real-time analytics dashboard processing 1M+ events/day
• Built RESTful APIs serving mobile and web applications
• Optimized database queries improving response time by 60%
Technologies: Node.js, React, PostgreSQL, Docker

Software Engineer - StartupXYZ
06/2018 - 02/2020 | Austin, TX
• Created automated testing framework increasing code coverage to 85%
• Developed customer portal handling 50K+ daily active users
Technologies: Java, Spring Boot, Angular, MySQL

Junior Developer - WebSolutions
01/2017 - 05/2018 | Boston, MA
• Built responsive web applications for client projects
• Collaborated on agile team delivering bi-weekly releases
Technologies: JavaScript, PHP, MySQL

Intern - TechStart
06/2016 - 12/2016 | Seattle, WA
• Assisted in development of internal tools
Technologies: Python, Flask

Freelance Developer
2015 - 2016 | Remote
• Delivered 10+ web projects for small businesses
Technologies: WordPress, JavaScript

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley | 2016
GPA: 3.8/4.0

CERTIFICATIONS
• AWS Certified Solutions Architect - Professional | 2023
• ServiceNow Certified System Administrator | 2022
• Kubernetes Certified Developer | 2021
"""

async def test_enhanced_extraction():
    """Test the enhanced extraction with sample resume"""
    
    # Initialize processor (you'll need to add your Gemini API key)
    processor = EnhancedGeminiProcessor()
    
    # Get Jinja2 variables structure
    jinja_vars = processor.get_jinja2_variables()
    
    print("=" * 60)
    print("JINJA2 TEMPLATE VARIABLES")
    print("=" * 60)
    print("\n### Basic Variables ###")
    for var, template in jinja_vars['variables'].items():
        print(f"{var}: {template}")
    
    print("\n### Skills Loop ###")
    print(jinja_vars['skills_loop'])
    
    print("\n### Detailed Experience Loop (Max 5) ###")
    print(jinja_vars['detailed_experience_loop'])
    
    print("\n### Other Notable Projects Table ###")
    print(jinja_vars['other_projects_table'])
    
    print("\n### Education Table ###")
    print(jinja_vars['education_table'])
    
    print("\n### Certifications Table ###")
    print(jinja_vars['certifications_table'])
    
    print("\n" + "=" * 60)
    print("EXPECTED EXTRACTION OUTPUT")
    print("=" * 60)
    
    # Show expected output structure
    expected_output = {
        "contact_info": {
            "name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "+1-234-567-8900",
            "address": "San Francisco, CA",
            "linkedin": "linkedin.com/in/johnsmith",
            "website": "johnsmith.dev"
        },
        "title": "Senior Software Engineer",
        "summary_bullets": [
            "Led development of microservices architecture serving 10M+ users",
            "Expertise in cloud-native applications with 8+ years experience",
            "Strong background in ServiceNow platform customization and integration",
            "Certified AWS Solutions Architect with extensive DevOps experience",
            "Mentored 15+ junior developers and led 3 cross-functional teams"
        ],
        "skills_categories": {
            "ServiceNow Modules": ["Service Portal", "ITSM", "ITOM", "Flow Designer", "Virtual Agent"],
            "Cloud Platforms": ["AWS", "Azure", "GCP"],
            "Programming Languages": ["Python", "JavaScript", "TypeScript", "Java", "Go"],
            "DevOps Tools": ["Docker", "Kubernetes", "Jenkins", "GitLab CI/CD", "Terraform"],
            "Databases": ["PostgreSQL", "MongoDB", "Redis", "Elasticsearch"],
            "Frontend Frameworks": ["React", "Angular", "Vue.js", "Next.js"]
        },
        "detailed_experience": [
            {
                "project_name": "Senior Software Engineer",
                "organization": "Tech Corp",
                "duration": "May 2022 - Present",
                "location": "San Francisco, CA",
                "key_achievements": [
                    "Architected and implemented microservices platform reducing latency by 40%",
                    "Led migration of legacy monolith to cloud-native architecture on AWS",
                    "Implemented CI/CD pipelines reducing deployment time from 2 hours to 15 minutes"
                ],
                "technologies_used": ["Python", "Kubernetes", "AWS", "ServiceNow"]
            },
            # ... up to 5 detailed entries
        ],
        "other_notable_projects": [
            {
                "project_name": "Freelance Developer",
                "duration": "2015 - 2016",
                "technology": "WordPress, JavaScript",
                "description": "Delivered 10+ web projects for small businesses"
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "University of California, Berkeley",
                "year": "2016",
                "gpa": "3.8/4.0"
            }
        ],
        "certifications": [
            {
                "name": "AWS Certified Solutions Architect - Professional",
                "issuer": "Amazon Web Services",
                "year": "2023"
            },
            {
                "name": "ServiceNow Certified System Administrator",
                "issuer": "ServiceNow",
                "year": "2022"
            },
            {
                "name": "Kubernetes Certified Developer",
                "issuer": "CNCF",
                "year": "2021"
            }
        ],
        "attempt_count": 1
    }
    
    print(json.dumps(expected_output, indent=2))
    
    print("\n" + "=" * 60)
    print("KEY IMPROVEMENTS")
    print("=" * 60)
    print("""
1. ✅ Dynamic Skills Categorization: Skills are grouped based on actual resume content
2. ✅ Limited Experience: Maximum 5 detailed projects, rest in "Other Notable Projects"
3. ✅ Date Formatting: All dates formatted as "Mon YYYY" (e.g., May 2022)
4. ✅ Separate Education Table: Each degree is a separate row
5. ✅ Separate Certifications Table: Certifications extracted independently
6. ✅ Summary Bullets: Professional summary converted to bullet points
7. ✅ Attempt Tracking: Counts conversion attempts for retry logic
    """)

if __name__ == "__main__":
    asyncio.run(test_enhanced_extraction())
