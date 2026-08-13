import uuid
from typing import List
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models.medication import Medication, MedicationReminder
from app.schemas.medication import MedicationCreate, MedicationUpdate
from app.schemas.medication_reminder import MedicationReminderCreate


class MedicationService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _parse_frequency_to_times(frequency: str | None) -> list:
        from datetime import time
        if not frequency:
            return [time(9, 0)]
        
        freq_lower = frequency.lower().strip()
        
        # Check for 4 times / 4 مرات
        if any(x in freq_lower for x in ["4", "four", "أربع", "اربع"]):
            return [time(8, 0), time(12, 0), time(16, 0), time(20, 0)]
        # Check for 3 times / 3 مرات / ثلاث
        elif any(x in freq_lower for x in ["3", "three", "ثلاث", "tid"]):
            return [time(8, 0), time(16, 0), time(0, 0)]
        # Check for 2 times / مرتين / مرتان / bid
        elif any(x in freq_lower for x in ["2", "twice", "two", "مرتين", "مرتان", "bid"]):
            return [time(9, 0), time(21, 0)]
        # Check for once / 1 time / مرة / daily
        else:
            return [time(9, 0)]

    def create_medication(self, patient_id: uuid.UUID, data: MedicationCreate) -> Medication:
        med = Medication(
            patient_id=patient_id,
            visit_id=data.visit_id,
            prescribed_by=data.prescribed_by,
            medicine_name=data.get_medicine_name(),
            dosage=data.dosage,
            frequency=data.frequency,
            start_date=data.start_date,
            end_date=data.end_date,
            is_active=data.is_active,
        )
        self.db.add(med)
        self.db.flush()
        self.db.refresh(med)

        # Auto-generate Medication Reminders based on frequency
        reminder_times = self._parse_frequency_to_times(data.frequency)
        for r_time in reminder_times:
            reminder = MedicationReminder(
                medication_id=med.id,
                reminder_time=r_time,
                is_active=True
            )
            self.db.add(reminder)
        self.db.flush()
        self.db.refresh(med)

        return med

    def add_reminders(self, medication_id: uuid.UUID, reminders: List[MedicationReminderCreate]) -> List[MedicationReminder]:
        created = []
        for r in reminders:
            reminder = MedicationReminder(
                medication_id=medication_id,
                reminder_time=r.reminder_time,
                is_active=r.is_active,
            )
            self.db.add(reminder)
            created.append(reminder)
        self.db.flush()
        for r in created:
            self.db.refresh(r)
        return created

    def get_patient_medications(self, patient_id: uuid.UUID) -> List[Medication]:
        return (
            self.db.query(Medication)
            .options(joinedload(Medication.reminders))
            .filter(Medication.patient_id == patient_id, Medication.is_active == True)
            .order_by(Medication.created_at.desc())
            .all()
        )

    def get_medication_by_id(self, medication_id: uuid.UUID) -> Medication:
        med = self.db.query(Medication).filter(Medication.id == medication_id).first()
        if not med:
            raise HTTPException(status_code=404, detail="الدواء غير موجود")
        return med

    def update_medication(self, medication_id: uuid.UUID, data: MedicationUpdate, patient_id: uuid.UUID) -> Medication:
        med = self.get_medication_by_id(medication_id)
        if med.patient_id != patient_id:
            raise HTTPException(status_code=403, detail="لا يمكنك تعديل دواء مريض آخر")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(med, key, value)
        self.db.flush()
        self.db.refresh(med)
        return med

    def delete_medication(self, medication_id: uuid.UUID, patient_id: uuid.UUID) -> None:
        med = self.get_medication_by_id(medication_id)
        if med.patient_id != patient_id:
            raise HTTPException(status_code=403, detail="لا يمكنك حذف دواء مريض آخر")
        med.is_active = False
        self.db.flush()
