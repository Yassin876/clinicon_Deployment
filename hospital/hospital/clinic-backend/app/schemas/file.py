from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from uuid import UUID

class MedicalFileBase(BaseModel):
    patient_id: UUID
    visit_id: Optional[UUID] = None
    category: Optional[str] = None
    file_name: Optional[str] = None
    file_url: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None

class MedicalFileResponse(MedicalFileBase):
    id: UUID
    uploaded_by_user_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
