from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional
from uuid import UUID

class VisitBase(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    appointment_id: Optional[UUID] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    doctor_notes: Optional[str] = None
    follow_up_date: Optional[date] = None

class VisitCreate(VisitBase):
    pass

class VisitResponse(VisitBase):
    id: UUID
    visit_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
