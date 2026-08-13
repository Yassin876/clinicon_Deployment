from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.medication_reminder import MedicationReminderResponse


class MedicationBase(BaseModel):
    patient_id: uuid.UUID
    visit_id: uuid.UUID | None = None
    prescribed_by: uuid.UUID | None = None
    medicine_name: str
    dosage: str | None = None
    frequency: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True


class MedicationCreate(BaseModel):
    """Schema لإضافة دواء جديد - patient_id يُجلب تلقائياً من الـ JWT Token"""
    medicine_name: str | None = None  # الاسم الأصلي في قاعدة البيانات
    name: str | None = None           # اسم مستعار لدعم الـ UI (name=medicine_name)
    dosage: str | None = None
    frequency: str | None = None
    visit_id: uuid.UUID | None = None
    prescribed_by: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True

    def get_medicine_name(self) -> str:
        return self.medicine_name or self.name or 'دواء غير معين'


class MedicationUpdate(BaseModel):
    medicine_name: str | None = None
    dosage: str | None = None
    frequency: str | None = None
    end_date: date | None = None
    is_active: bool | None = None


class MedicationResponse(MedicationBase):
    id: uuid.UUID
    created_at: datetime
    reminders: list[MedicationReminderResponse] = []

    model_config = ConfigDict(from_attributes=True)