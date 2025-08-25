#!/usr/bin/env python3
"""
Script to regenerate the improved e-Zest template
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from app.services.improved_ezest_template import ImprovedEZestTemplateCreator

def regenerate_ezest_template():
    """Regenerate the improved e-Zest template"""
    
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    ezest_template_path = templates_dir / "ezest.docx"
    
    # Remove existing template if it exists
    if ezest_template_path.exists():
        ezest_template_path.unlink()
        print(f"Removed existing template: {ezest_template_path}")
    
    try:
        # Create improved template
        creator = ImprovedEZestTemplateCreator()
        creator.create_template(ezest_template_path)
        print(f"Successfully created improved e-Zest template at: {ezest_template_path}")
        
        # Verify file was created
        if ezest_template_path.exists():
            file_size = ezest_template_path.stat().st_size
            print(f"Template file size: {file_size} bytes")
        else:
            print("Error: Template file was not created")
            
    except Exception as e:
        print(f"Error creating template: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    regenerate_ezest_template()