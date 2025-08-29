from fastapi import APIRouter, HTTPException, Path, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
from pathlib import Path as PathLib

from app.core.config import settings
from app.models.schemas import TemplateInfo
import app.services.template_engine as template_engine_module

router = APIRouter()

def get_template_engine() -> template_engine_module.TemplateEngine:
    return template_engine_module.TemplateEngine()

@router.get("/", response_model=List[TemplateInfo])
async def list_templates(
    template_engine: template_engine_module.TemplateEngine = Depends(get_template_engine),
) -> List[TemplateInfo]:
    """List all available templates"""
    
    try:
        templates = template_engine.list_templates()
        return templates
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing templates: {str(e)}")

@router.get("/{template_id}", response_model=TemplateInfo)
async def get_template(
    template_id: str = Path(..., description="Template ID"),
    template_engine: template_engine_module.TemplateEngine = Depends(get_template_engine),
) -> TemplateInfo:
    """Get template information by ID"""
    
    try:
        template_info = template_engine.get_template_info(template_id)
        if not template_info:
            raise HTTPException(status_code=404, detail="Template not found")
        return template_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving template: {str(e)}")

@router.get("/{template_id}/preview")
async def preview_template(
    template_id: str = Path(..., description="Template ID"),
    template_engine: template_engine_module.TemplateEngine = Depends(get_template_engine),
) -> Dict[str, Any]:
    """Get template preview/structure"""
    
    try:
        preview = template_engine.get_template_preview(template_id)
        if not preview:
            raise HTTPException(status_code=404, detail="Template not found")
        return preview
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")
