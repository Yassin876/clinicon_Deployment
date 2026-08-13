from __future__ import annotations

import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict


class MedicationReminderBase(BaseModel):
    reminder_time: time
    is_active: bool = True


class MedicationReminderCreate(MedicationReminderBase):
    pass


class MedicationReminderUpdate(BaseModel):
    reminder_time: time | None = None
    is_active: bool | None = None


class MedicationReminderResponse(MedicationReminderBase):
    id: uuid.UUID
    medication_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)