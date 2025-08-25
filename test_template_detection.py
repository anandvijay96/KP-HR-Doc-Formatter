#!/usr/bin/env python
"""Quick test to see if ezest-updated template is detected"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.template_engine import TemplateEngine

def main():
    try:
        engine = TemplateEngine()
        
        # Check if ezest-updated template file exists
        template_path = Path('templates/ezest-updated.docx')
        print(f"✓ Template file exists: {template_path.exists()}")
        print(f"  File size: {template_path.stat().st_size if template_path.exists() else 0} bytes")
        
        # Test get_template_info for ezest-updated
        template_info = engine.get_template_info('ezest-updated')
        if template_info:
            print(f"✓ Template detected by engine:")
            print(f"  ID: {template_info.id}")
            print(f"  Name: {template_info.name}")
            print(f"  Description: {template_info.description}")
        else:
            print("✗ Template NOT detected by engine")
        
        # List all detected templates
        templates = engine.list_templates()
        print(f"\nAll detected templates ({len(templates)}):")
        for t in templates:
            print(f"  - {t.id}: {t.name}")
            
        # Test validation on ezest-updated if it exists
        if template_path.exists():
            print(f"\nValidating {template_path.name}...")
            validation = engine.validate_template(template_path)
            print(f"  Valid: {validation.get('valid', False)}")
            print(f"  Errors: {len(validation.get('errors', []))}")
            print(f"  Warnings: {len(validation.get('warnings', []))}")
            print(f"  Found fields: {validation.get('found_fields', [])}")
            if validation.get('undeclared_variables'):
                print(f"  Undeclared variables: {validation['undeclared_variables']}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    main()
