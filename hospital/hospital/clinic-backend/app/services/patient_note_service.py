import uuid
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.patient import PatientNote
from app.schemas.patient_note import PatientNoteCreate


class PatientNoteService:
    def __init__(self, db: Session):
        self.db = db

    def create_note(self, data: PatientNoteCreate) -> PatientNote:
        note = PatientNote(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            note=data.note,
        )
        self.db.add(note)
        self.db.flush()
        self.db.refresh(note)
        return note

    def get_notes_by_patient(self, patient_id: uuid.UUID) -> List[PatientNote]:
        return (
            self.db.query(PatientNote)
            .filter(PatientNote.patient_id == patient_id)
            .order_by(PatientNote.created_at.desc())
            .all()
        )
