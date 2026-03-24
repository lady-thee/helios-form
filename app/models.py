from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel
from beanie import Document, Indexed
from datetime import datetime


# ------ Nested models for form schema ------#
class VisibleWhen(BaseModel):
    field: str
    equals: Any

class SchemaField(BaseModel):
    name: str
    type: Literal["text", "number", "date", "dropdown", "checkbox", 
                    "email", "table", "computed", "file", "signature"]
    required: bool = False
    options: Optional[List[str]] = None  # For dropdowns, checkboxes
    min_length: Optional[int] = None  # For text fields
    max_length: Optional[int] = None  # For text fields
    min_value: Optional[float] = None  # For number fields
    max_value: Optional[float] = None  # For number fields
    visible_when: Optional[VisibleWhen] = None  # For conditional visibility
    expression: Optional[str] = None  # For computed fields
    

class Schema(BaseModel):
    fields: List[SchemaField]


# ---- Document models for MongoDB using Beanie ODM ----#
class Forms(Document):
    name: Indexed(str)  # pyright: ignore[reportInvalidTypeForm]
    description: Optional[str] = None
    created_at: datetime = datetime.now()
    latest_version_id: Optional[str] = None

    class Settings:
        name = "forms"


class FormVersion(Document):
    form_id: str 
    version_number: int
    form_schema: Schema
    created_at: datetime = datetime.now()

    class Settings:
        name = "form_versions"


class Submission(Document):
    form_id: str 
    version_id: str 
    data: Dict[str, Any]  # Stores field values as key-value pairs
    submitted_at: datetime = datetime.now()

    class Settings:
        name = "submissions"

