from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from app.models.patient import GenderType

class AllergyBase(BaseModel):
    allergy_name: str
    severity: Optional[str] = None
    notes: Optional[str] = None

class AllergyResponse(AllergyBase):
    id: UUID
    patient_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChronicDiseaseBase(BaseModel):
    disease_name: str
    diagnosed_at: Optional[date] = None
    notes: Optional[str] = None

class ChronicDiseaseResponse(ChronicDiseaseBase):
    id: UUID
    patient_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PatientNoteBase(BaseModel):
    note: str

class PatientNoteResponse(PatientNoteBase):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationBase(BaseModel):
    title: str
    message: str
    type: Optional[str] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class NotificationResponse(NotificationBase):
    id: UUID
    patient_id: UUID
    is_read: bool
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PatientBase(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[GenderType] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    telegram_chat_id: Optional[int] = None
    telegram_notif_enabled: bool = False

class PatientCreate(PatientBase):
    user_id: UUID

class PatientResponse(PatientBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
