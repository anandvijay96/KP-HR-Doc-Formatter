#!/usr/bin/env python
"""
Helper: Add a DOCX as a template and validate placeholders.

Usage examples:
  python scripts/add_template.py --file docs/Sample\ files/CV_Name_Title_e-Zest 1 (1).docx --template-id ezest_v2 --preview

Behavior:
- Copies the given DOCX into templates/<template-id>.docx
- Runs robust validation via TemplateEngine.validate_template()
- Prints a JSON report and exit code 0 on success, non-zero on validation failure
- If --preview is set, renders a preview with a sample context to outputs/preview_<template-id>.docx (does not require extraction)
"""

import argparse
import json
import sys
from pathlib import Path

from app.services.template_engine import TemplateEngine
from docxtpl import DocxTemplate


def build_sample_context():
    return {
        'contact_info': {
            'name': 'Sample Candidate',
            'email': 'candidate@example.com',
            'phone': '+1-555-0100',
            'address': '123 Sample Street',
            'linkedin': 'linkedin.com/in/sample',
            'website': 'sample.dev',
        },
        'summary': 'Experienced professional skilled in Python, FastAPI, and document automation.',
        'experience': [
            {
                'title': 'Senior Engineer',
                'company': 'ACME Inc.',
                'location': 'Remote',
                'start_date': 'Jan 2022',
                'end_date': 'Present',
                'description': 'Lead development of resume formatter platform.',
                'is_current': True,
            },
            {
                'title': 'Engineer',
                'company': 'Beta Corp',
                'location': 'Pune, IN',
                'start_date': 'Aug 2019',
                'end_date': 'Dec 2021',
                'description': 'Built OCR/NLP pipelines for document processing.',
                'is_current': False,
            }
        ],
        'education': [
            {
                'degree': 'B.Tech, Computer Science',
                'institution': 'Tech University',
                'location': 'City',
                'graduation_date': '2019',
                'gpa': '8.9/10',
                'honors': 'First Class with Distinction',
            }
        ],
        'skills': ['Python', 'FastAPI', 'Celery', 'React', 'DocxTpl']
    }


def main():
    parser = argparse.ArgumentParser(description='Add and validate a DOCX template')
    parser.add_argument('--file', required=True, help='Path to source DOCX file')
    parser.add_argument('--template-id', required=False, help='Template ID (filename stem) to save as')
    parser.add_argument('--preview', action='store_true', help='Render a preview with sample context')
    args = parser.parse_args()

    src_path = Path(args.file).expanduser().resolve()
    if not src_path.exists() or src_path.suffix.lower() != '.docx':
        print(json.dumps({'ok': False, 'error': 'Source file must be an existing .docx'}))
        sys.exit(2)

    engine = TemplateEngine()
    templates_dir = engine.templates_dir
    outputs_dir = engine.output_dir

    template_id = args.template_id or src_path.stem
    dst_path = templates_dir / f"{template_id}.docx"

    # Copy preserving content using python-docx save to avoid locked/temporary artifacts
    try:
        # Load and re-save to strip odd metadata/locks
        doc = DocxTemplate(str(src_path))
        doc.save(str(dst_path))
    except Exception:
        # Fallback: raw copy if docxtpl cannot parse (still allow validation to report issues)
        import shutil
        shutil.copyfile(src_path, dst_path)

    # Validate
    report = engine.validate_template(dst_path)
    ok = report.get('valid', False) and not report.get('errors')

    # Optionally render preview using sample context directly
    preview_file = None
    if args.preview:
        try:
            sample_ctx = build_sample_context()
            tpl = DocxTemplate(str(dst_path))
            tpl.render(sample_ctx)
            preview_file = outputs_dir / f"preview_{template_id}.docx"
            tpl.save(str(preview_file))
            report['preview'] = str(preview_file)
        except Exception as e:
            report.setdefault('warnings', []).append(f'Preview render failed: {e}')

    print(json.dumps({'ok': ok, 'template_id': template_id, 'path': str(dst_path), **report}, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
