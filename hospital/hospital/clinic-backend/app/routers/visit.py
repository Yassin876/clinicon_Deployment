import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_doctor, require_patient, get_current_user
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.services.visit_service import VisitService
from app.schemas.visit import VisitCreate, VisitUpdate, VisitResponse

router = APIRouter(prefix="/visits", tags=["Visits"])


def _get_doctor_id(user: User, db: Session) -> uuid.UUID:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="ملف الطبيب غير موجود")
    return doctor.id


def _enrich_visits(visits) -> list:
    """Add doctor_name, doctor_notes, and medications to each visit."""
    result = []
    for v in visits:
        data = VisitResponse.model_validate(v).model_dump()
        data["doctor_name"] = v.doctor.user.full_name if v.doctor and v.doctor.user else "—"
        data["notes"] = v.doctor_notes or ""
        data["medications"] = [
            {
                "id": str(m.id),
                "name": m.medicine_name,
                "dosage": m.dosage or "",
                "frequency": m.frequency or "",
            }
            for m in (v.medications or [])
        ]
        result.append(data)
    return result


@router.get("/my")
def get_my_visits(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """المريض يشوف زياراته الخاصة"""
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="ملف المريض غير موجود")
    visits = VisitService(db).get_visits_by_patient(patient.id)
    return _enrich_visits(visits)


@router.post("/", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
def create_visit(
    data: VisitCreate,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """طبيب يسجل زيارة جديدة بعد الكشف (تشخيص + ملاحظات)"""
    service = VisitService(db)
    try:
        visit = service.create_visit(data)
        db.commit()
        db.refresh(visit)
        return visit
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patient/{patient_id}")
def get_patient_visits(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """طبيب يشوف زيارات مريض"""
    visits = VisitService(db).get_visits_by_patient(patient_id)
    return _enrich_visits(visits)


@router.put("/{visit_id}", response_model=VisitResponse)
def update_visit(
    visit_id: uuid.UUID,
    data: VisitUpdate,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """طبيب يعدّل زيارة"""
    service = VisitService(db)
    try:
        visit = service.update_visit(visit_id, data)
        db.commit()
        db.refresh(visit)
        return visit
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
