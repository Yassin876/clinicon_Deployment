import uuid
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.dependencies import require_patient, require_doctor, get_current_user
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.medication import Medication
from app.services.medication_service import MedicationService
from app.schemas.medication import MedicationCreate, MedicationUpdate, MedicationResponse
from app.schemas.medication_reminder import MedicationReminderCreate, MedicationReminderResponse

router = APIRouter(prefix="/medications", tags=["Medications"])


class TelegramLinkRequest(BaseModel):
    telegram_chat_id: int
    telegram_notif_enabled: bool = True


def _get_patient_id(user: User, db: Session) -> uuid.UUID:
    """يجلب patient_id من اليوزر الحالي"""
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="ملف المريض غير موجود")
    return patient.id


@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
def create_medication(
    data: MedicationCreate,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """مريض يضيف دواء جديد"""
    patient_id = _get_patient_id(current_user, db)
    service = MedicationService(db)
    try:
        med = service.create_medication(patient_id, data)
        db.commit()
        db.refresh(med)
        return med
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{medication_id}/reminders", response_model=List[MedicationReminderResponse])
def add_reminders(
    medication_id: uuid.UUID,
    reminders: List[MedicationReminderCreate],
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """مريض يضيف تذكيرات لدواء — بيشتغل مع Telegram Scheduler"""
    patient_id = _get_patient_id(current_user, db)
    service = MedicationService(db)
    # التحقق أن الدواء ملك المريض
    med = service.get_medication_by_id(medication_id)
    if med.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="لا يمكنك إضافة تذكيرات لدواء مريض آخر")
    try:
        result = service.add_reminders(medication_id, reminders)
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def _enrich_meds(meds, db):
    """يضيف اسم الطبيب الواصف لكل دواء"""
    result = []
    for med in meds:
        d = MedicationResponse.model_validate(med).model_dump()
        if med.prescribed_by:
            doc = db.query(Doctor).filter(Doctor.id == med.prescribed_by).first()
            if doc:
                u = db.query(User).filter(User.id == doc.user_id).first()
                d['prescribed_by_name'] = u.full_name if u else None
        result.append(d)
    return result


@router.get("/")
def get_my_medications(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """مريض يشوف أدويته الحالية"""
    patient_id = _get_patient_id(current_user, db)
    meds = MedicationService(db).get_patient_medications(patient_id)
    return _enrich_meds(meds, db)


@router.get("/patient/{patient_id}", response_model=List[MedicationResponse])
def get_patient_medications_doctor(
    patient_id: uuid.UUID,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """طبيب يشوف أدوية مريض (قراءة فقط)"""
    return MedicationService(db).get_patient_medications(patient_id)


class PrescribeMedicationRequest(BaseModel):
    patient_id: uuid.UUID
    medicine_name: str
    dosage: str | None = None
    frequency: str | None = None
    visit_id: uuid.UUID | None = None


@router.post("/prescribe", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
def prescribe_medication(
    data: PrescribeMedicationRequest,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """طبيب يكتب دواء لمريض — بيظهر عند المريض في صفحة الأدوية"""
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="ملف الطبيب غير موجود")
    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="المريض غير موجود")
    try:
        med_data = MedicationCreate(
            medicine_name=data.medicine_name,
            dosage=data.dosage,
            frequency=data.frequency,
            prescribed_by=doctor.id,
            visit_id=data.visit_id,
        )
        service = MedicationService(db)
        med = service.create_medication(data.patient_id, med_data)
        db.commit()
        db.refresh(med)
        return med
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{medication_id}", response_model=MedicationResponse)
def update_medication(
    medication_id: uuid.UUID,
    data: MedicationUpdate,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """مريض يعدّل دواءه بس"""
    patient_id = _get_patient_id(current_user, db)
    service = MedicationService(db)
    try:
        med = service.update_medication(medication_id, data, patient_id)
        db.commit()
        db.refresh(med)
        return med
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    medication_id: uuid.UUID,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """مريض يوقف دواءه (soft delete)"""
    patient_id = _get_patient_id(current_user, db)
    service = MedicationService(db)
    try:
        service.delete_medication(medication_id, patient_id)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/doctor/{medication_id}", response_model=MedicationResponse)
def doctor_update_medication(
    medication_id: uuid.UUID,
    data: MedicationUpdate,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """طبيب يعدّل دواء مريض"""
    service = MedicationService(db)
    med = service.get_medication_by_id(medication_id)
    try:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(med, key, value)
        db.commit()
        db.refresh(med)
        return med
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/doctor/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
def doctor_delete_medication(
    medication_id: uuid.UUID,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    """طبيب يوقف دواء مريض (soft delete)"""
    service = MedicationService(db)
    med = service.get_medication_by_id(medication_id)
    try:
        med.is_active = False
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/telegram-link-url")
def get_telegram_link_url(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """يرجّع لينك deep link للبوت عشان المريض يضغط عليه ويتربط أوتوماتيك"""
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="ملف المريض غير موجود")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        raise HTTPException(status_code=500, detail="Telegram bot not configured")
    # هات اسم البوت
    import httpx
    try:
        resp = httpx.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=5.0)
        bot_username = resp.json().get("result", {}).get("username", "")
    except Exception:
        bot_username = "MyClinicNotifierBot"
    link = f"https://t.me/{bot_username}?start={patient.id}"
    return {"link": link, "bot_username": bot_username}


@router.post("/telegram-link")
def link_telegram(
    data: TelegramLinkRequest,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """مريض يربط حسابه بتليجرام لاستقبال التذكيرات"""
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="ملف المريض غير موجود")
    patient.telegram_chat_id = data.telegram_chat_id
    patient.telegram_notif_enabled = data.telegram_notif_enabled
    db.commit()
    return {"success": True, "message": "تم ربط تليجرام بنجاح"}


@router.get("/telegram-status")
def get_telegram_status(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """هل المريض مرتبط بتليجرام"""
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="ملف المريض غير موجود")
    return {
        "linked": bool(patient.telegram_chat_id),
        "chat_id": patient.telegram_chat_id,
        "notif_enabled": patient.telegram_notif_enabled,
    }
