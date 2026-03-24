from typing import Dict, Any, Optional
from pydantic import BaseModel 
from app.models import Schema
from datetime import datetime


class FormCreateRequest(BaseModel):
    name: str
    description: str
    form_schema: Schema

class FormUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    form_schema: Optional[Schema] = None

class FormSubmissionRequest(BaseModel):
    data: Dict[str, Any]  


class FormCreateResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    version_number: int
    version_id: Optional[str] = None

class FormResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    latest_version_number: int
    latest_version_id: Optional[str] = None

class UpdateFormResponse(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: str
    version_number: Optional[int] = None
    version_id: Optional[str] = None
    changelog: Optional[Dict[str, Any]] = None

class SubmissionResponse(BaseModel):
    id: str
    form_id: str
    version_id: str
    data: Dict[str, Any]
    submitted_at: datetime


