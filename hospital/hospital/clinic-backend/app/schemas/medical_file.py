from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MedicalFileBase(BaseModel):
    patient_id: uuid.UUID
    visit_id: uuid.UUID | None = None
    uploaded_by_user_id: uuid.UUID | None = None
    category: str | None = None
    file_name: str | None = None
    file_url: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


class MedicalFileCreate(MedicalFileBase):
    pass


class MedicalFileUpdate(BaseModel):
    category: str | None = None


class MedicalFileResponse(MedicalFileBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)