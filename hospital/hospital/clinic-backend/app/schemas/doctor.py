from pydantic import BaseModel, ConfigDict
from datetime import time, datetime
from typing import Optional
from uuid import UUID

class DoctorAvailabilityBase(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time
    is_active: bool = True

class DoctorAvailabilityResponse(DoctorAvailabilityBase):
    id: UUID
    doctor_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DoctorBase(BaseModel):
    specialization: str
    bio: Optional[str] = None
    location_url: Optional[str] = None

class DoctorCreate(DoctorBase):
    user_id: UUID

class DoctorResponse(DoctorBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
