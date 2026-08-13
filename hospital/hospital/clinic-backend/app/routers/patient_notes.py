import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_doctor
from app.models.user import User
from app.models.doctor import Doctor
from app.services.patient_note_service import PatientNoteService
from app.schemas.patient_note import PatientNoteCreate, PatientNoteResponse

router = APIRouter(prefix="/patient-notes", tags=["Patient Notes"])


def _get_doctor_id(user: User, db: Session) -> uuid.UUID:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="ملف الطبيب غير موجود")
    return doctor.id


@router.post("/", response_model=PatientNoteResponse, status_code=status.HTTP_201_CREATED)
def create_patient_note(
    data: PatientNoteCreate,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """طبيب يضيف ملاحظة خاصة على مريض — مش المريض يشوفها"""
    service = PatientNoteService(db)
    try:
        note = service.create_note(data)
        db.commit()
        db.refresh(note)
        return note
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patient/{patient_id}", response_model=List[PatientNoteResponse])
def get_patient_notes(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """طبيب يشوف ملاحظاته على مريض (محمي ومش للمريض)"""
    return PatientNoteService(db).get_notes_by_patient(patient_id)
