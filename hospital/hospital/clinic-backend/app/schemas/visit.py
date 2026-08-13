from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class VisitBase(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: uuid.UUID | None = None
    visit_date: datetime | None = None
    chief_complaint: str | None = None
    diagnosis: str | None = None
    doctor_notes: str | None = None
    follow_up_date: date | None = None


class VisitCreate(VisitBase):
    pass


class VisitUpdate(BaseModel):
    chief_complaint: str | None = None
    diagnosis: str | None = None
    doctor_notes: str | None = None
    follow_up_date: date | None = None


class VisitResponse(VisitBase):
    id: uuid.UUID
    created_at: datetime
    doctor_name: str | None = None

    model_config = ConfigDict(from_attributes=True)