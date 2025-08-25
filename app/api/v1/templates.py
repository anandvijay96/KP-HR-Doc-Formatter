from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
from pathlib import Path as PathLib

from app.core.config import settings
from app.models.schemas import TemplateInfo
from app.services.template_engine import TemplateEngine

router = APIRouter()
template_engine = TemplateEngine()

@router.get("/", response_model=List[TemplateInfo])
async def list_templates() -> List[TemplateInfo]:
    """List all available templates"""
    
    try:
        templates = template_engine.list_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing templates: {str(e)}")

@router.get("/{template_id}", response_model=TemplateInfo)
async def get_template(
    template_id: str = Path(..., description="Template ID")
) -> TemplateInfo:
    """Get template information by ID"""
    
    try:
        template_info = template_engine.get_template_info(template_id)
        if not template_info:
            raise HTTPException(status_code=404, detail="Template not found")
        return template_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving template: {str(e)}")

@router.get("/{template_id}/preview")
async def preview_template(
    template_id: str = Path(..., description="Template ID")
) -> Dict[str, Any]:
    """Get template preview/structure"""
    
    try:
        preview = template_engine.get_template_preview(template_id)
        if not preview:
            raise HTTPException(status_code=404, detail="Template not found")
        return preview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")
