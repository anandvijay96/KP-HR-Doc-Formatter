#!/usr/bin/env python3
"""
Test script to verify improved resume extraction functionality
"""

import sys
import os
from pathlib import Path

# Ensure repository root is on sys.path so 'app' package imports work
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.document_processor import DocumentProcessor
from app.services.nlp_extractor import NLPExtractor
import json

def test_extraction():
    """Test the improved extraction with a sample document"""
    
    # Initialize processors
    doc_processor = DocumentProcessor()
    nlp_extractor = NLPExtractor()
    
    # Test with one of the uploaded documents
    sample_file = Path("uploads/0d81958a-35d0-4335-9e9b-1094dd589dee_CV_Rahul_Shrivastav_Senior_ServiceNow_Developer_e-Zest (1) 1.docx")
    
    if not sample_file.exists():
        print(f"Sample file not found: {sample_file}")
        return
    
    print(f"Testing extraction with: {sample_file.name}")
    print("=" * 60)
    
    try:
        # Extract text using improved method
        print("1. Extracting text from DOCX...")
        text = doc_processor.extract_text_from_docx(sample_file)
        print(f"Extracted text length: {len(text)} characters")
        print("\nFirst 500 characters:")
        print("-" * 40)
        print(text[:500])
        print("-" * 40)
        
        # Test contact info extraction
        print("\n2. Extracting contact information...")
        contact_info = nlp_extractor.extract_contact_info(text)
        print(f"Name: {contact_info.name}")
        print(f"Email: {contact_info.email}")
        print(f"Phone: {contact_info.phone}")
        print(f"Address: {contact_info.address}")
        
        # Test experience extraction
        print("\n3. Extracting work experience...")
        experiences = nlp_extractor.extract_experience(text)
        print(f"Found {len(experiences)} experience entries:")
        for i, exp in enumerate(experiences[:3], 1):  # Show first 3
            print(f"\nExperience {i}:")
            print(f"  Company: {exp.company}")
            # schemas.Experience uses 'title' for role/title
            print(f"  Title: {exp.title}")
            print(f"  Duration: {exp.start_date} - {exp.end_date}")
            print(f"  Description: {exp.description[:100]}...")
            if hasattr(exp, 'technologies') and exp.technologies:
                print(f"  Technologies: {', '.join(exp.technologies[:5])}")
        
        # Test skills extraction
        print("\n4. Extracting skills...")
        skills = nlp_extractor.extract_skills(text)
        print(f"Found {len(skills)} skills:")
        print(f"Skills: {', '.join(skills[:10])}")  # Show first 10
        
        # Test education extraction
        print("\n5. Extracting education...")
        education = nlp_extractor.extract_education(text)
        print(f"Found {len(education)} education entries:")
        for i, edu in enumerate(education, 1):
            print(f"\nEducation {i}:")
            print(f"  Degree: {edu.degree}")
            print(f"  Institution: {edu.institution}")
            print(f"  Graduation: {edu.graduation_date}")
        
        print("\n" + "=" * 60)
        print("Extraction test completed successfully!")
        
    except Exception as e:
        print(f"Error during extraction test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extraction()
