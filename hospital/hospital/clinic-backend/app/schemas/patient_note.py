from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PatientNoteBase(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    note: str


class PatientNoteCreate(PatientNoteBase):
    pass


class PatientNoteUpdate(BaseModel):
    note: str | None = None


class PatientNoteResponse(PatientNoteBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)