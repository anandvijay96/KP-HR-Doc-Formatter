#!/usr/bin/env python3
"""
Render a sample resume using the template engine.
Usage:
  python scripts/render_sample.py --file <path-to-docx-in-uploads> --template ezest
If --file is omitted, picks the first .docx in uploads/.
"""

import argparse
import sys
from pathlib import Path

# Ensure app package is importable when run from repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.document_processor import DocumentProcessor
from app.services.template_engine import TemplateEngine


def main():
    parser = argparse.ArgumentParser(description="Render sample resume with a template")
    parser.add_argument("--file", type=str, help="Path to DOCX file under uploads/", default=None)
    parser.add_argument("--template", type=str, help="Template ID to use (default: ezest)", default="ezest")
    args = parser.parse_args()

    uploads_dir = REPO_ROOT / "uploads"
    if args.file:
        input_path = REPO_ROOT / args.file if not args.file.startswith(str(REPO_ROOT)) else Path(args.file)
    else:
        # Pick first .docx in uploads
        candidates = sorted(uploads_dir.glob("*.docx"))
        if not candidates:
            print(f"No .docx files found in {uploads_dir}")
            return 1
        input_path = candidates[0]

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    print(f"Using input: {input_path}")
    print(f"Using template: {args.template}")

    doc_processor = DocumentProcessor()
    template_engine = TemplateEngine()

    # Extract text and structured data
    text = doc_processor.extract_text_from_docx(input_path)
    extracted = doc_processor.advanced_data_extraction(text)

    # Apply template
    output_filename = template_engine.apply_template(extracted, args.template)
    output_path = REPO_ROOT / "output" / output_filename

    print("\n✅ Rendering completed")
    print(f"Output file: {output_path}")

    # Write verification log
    logs_dir = REPO_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    verification_path = logs_dir / "render_last.txt"
    verification_path.write_text(
        f"input={input_path}\ntemplate={args.template}\noutput={output_path}\n"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
