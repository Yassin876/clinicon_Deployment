import os
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.core.dependencies import require_doctor, require_lab, require_patient, get_current_user
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.clinic import Clinic, LabEntity
from app.models.appointment import Appointment
from app.models.medical_record import Visit
from app.models.file import MedicalFile
from app.schemas.file import MedicalFileResponse

router = APIRouter(prefix="/files", tags=["Medical Files"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "patient_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".dcm", ".txt", ".doc", ".docx"}
MAX_FILE_SIZE_MB = 15


def _validate_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"نوع الملف غير مسموح به. الأنواع المسموحة: {', '.join(ALLOWED_EXTENSIONS)}"
        )


@router.post("/upload", response_model=MedicalFileResponse, status_code=status.HTTP_201_CREATED)
@router.post("/upload-file", response_model=MedicalFileResponse, status_code=status.HTTP_201_CREATED)
async def patient_upload_file(
    file: UploadFile = File(...),
    category: Optional[str] = Form("patient_upload"),
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """رفع ملف طبي من المريض نفسه"""
    _validate_file(file)

    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="حساب المريض غير مكتمل")

    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"pat_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"حجم الملف يتجاوز الحد الأقصى ({MAX_FILE_SIZE_MB} ميجابايت)"
        )

    with open(file_path, "wb") as f:
        f.write(contents)

    db_file = MedicalFile(
        patient_id=patient.id,
        uploaded_by_user_id=current_user.id,
        file_name=file.filename,
        file_url=file_path,
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(contents),
        category=category or "patient_upload"
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return db_file


@router.get("/my", response_model=List[MedicalFileResponse])
def get_my_files(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    """جلب قائمة الملفات المرفوعة الخاصة بالمريض الحالي"""
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return []
    return db.query(MedicalFile).filter(MedicalFile.patient_id == patient.id).order_by(MedicalFile.created_at.desc()).all()


@router.post("/lab-upload", response_model=MedicalFileResponse, status_code=status.HTTP_201_CREATED)
async def lab_upload_file(
    patient_identifier: str = Form(...),
    description: Optional[str] = Form(None),
    test_name: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_lab),
    db: Session = Depends(get_db)
):
    """معمل التحاليل يرفع نتيجة تحليل/أشعة لمريض مفرز حسب عيادته"""
    _validate_file(file)

    lab_entity = db.query(LabEntity).filter(LabEntity.user_id == current_user.id).first()
    if not lab_entity:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="حساب المعمل غير مرتبط بعيادة")

    # Resolve patient by phone number or UUID
    patient = None
    try:
        pid = uuid.UUID(patient_identifier)
        patient = db.query(Patient).filter(Patient.id == pid).first()
    except (ValueError, AttributeError):
        # Search by phone number
        user_match = db.query(User).filter(User.phone_number == patient_identifier).first()
        if user_match:
            patient = db.query(Patient).filter(Patient.user_id == user_match.id).first()

    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المريض غير موجود")

    patient_id = patient.id

    # Verify patient belongs to same clinic
    clinic_doctors = db.query(Doctor.id).filter(Doctor.clinic_id == lab_entity.clinic_id).all()
    clinic_doc_ids = [d.id for d in clinic_doctors]

    has_appt = db.query(Appointment).filter(
        Appointment.patient_id == patient_id,
        Appointment.doctor_id.in_(clinic_doc_ids)
    ).first()
    has_visit = db.query(Visit).filter(
        Visit.patient_id == patient_id,
        Visit.doctor_id.in_(clinic_doc_ids)
    ).first()

    if not has_appt and not has_visit:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذا المريض غير مسجل في هذه العيادة")

    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"lab_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"حجم الملف يتجاوز الحد الأقصى ({MAX_FILE_SIZE_MB} ميجابايت)"
        )

    with open(file_path, "wb") as f:
        f.write(contents)

    db_file = MedicalFile(
        patient_id=patient_id,
        uploaded_by_user_id=current_user.id,
        file_name=file.filename,
        file_url=file_path,
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(contents),
        category="lab_result"
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return db_file


@router.get("/search-patients")
def search_patients_for_lab(
    q: Optional[str] = Query(None, min_length=2, description="البحث برقم الهاتف"),
    query: Optional[str] = Query(None, min_length=2, description="البحث برقم الهاتف (بديل)"),
    current_user: User = Depends(require_lab),
    db: Session = Depends(get_db)
):
    q = q or query
    if not q or len(q) < 2:
        return []
    """معمل التحاليل يبحث عن المريض برقم الهاتف في نفس العيادة"""
    lab_entity = db.query(LabEntity).filter(LabEntity.user_id == current_user.id).first()
    if not lab_entity:
        return []

    clinic_doctors = db.query(Doctor.id).filter(Doctor.clinic_id == lab_entity.clinic_id).all()
    clinic_doc_ids = [d.id for d in clinic_doctors]

    query = (
        db.query(Patient)
        .join(User, Patient.user_id == User.id)
        .filter(User.phone_number.ilike(f"%{q}%"))
    )

    results = query.limit(10).all()
    filtered_results = []

    for patient in results:
        has_appt = db.query(Appointment).filter(
            Appointment.patient_id == patient.id,
            Appointment.doctor_id.in_(clinic_doc_ids)
        ).first()
        has_visit = db.query(Visit).filter(
            Visit.patient_id == patient.id,
            Visit.doctor_id.in_(clinic_doc_ids)
        ).first()

        if has_appt or has_visit:
            filtered_results.append({
                "patient_id": str(patient.id),
                "full_name": patient.user.full_name,
                "phone_number": patient.user.phone_number or ""
            })

    return filtered_results


@router.get("/patient/{patient_id}", response_model=List[MedicalFileResponse])
def get_patient_files(
    patient_id: uuid.UUID,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """عرض ملفات مريض (المريض لنفسه أو الطبيب لمريضه)"""
    if current_user.role == UserRole.patient:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or patient.id != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="يمكنك عرض ملفاتك الخاصة فقط")
    elif current_user.role == UserRole.doctor:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor:
            has_appt = db.query(Appointment).filter(Appointment.patient_id == patient_id, Appointment.doctor_id == doctor.id).first()
            has_visit = db.query(Visit).filter(Visit.patient_id == patient_id, Visit.doctor_id == doctor.id).first()
            if not has_appt and not has_visit:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="يمكنك عرض ملفات المرضى التابعين لك فقط")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="حساب الطبيب غير مكتمل")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="غير متاح لهذا الحساب")

    query = db.query(MedicalFile).filter(MedicalFile.patient_id == patient_id)
    if category:
        query = query.filter(MedicalFile.category == category)

    return query.order_by(MedicalFile.created_at.desc()).all()


@router.get("/download/{file_id}")
def download_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """تحميل/فتح ملف"""
    db_file = db.query(MedicalFile).filter(MedicalFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الملف غير موجود")

    # Access control
    if current_user.role == UserRole.patient:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient or patient.id != db_file.patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="يمكنك تحميل ملفاتك الخاصة فقط")
    elif current_user.role == UserRole.doctor:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor:
            has_appt = db.query(Appointment).filter(Appointment.patient_id == db_file.patient_id, Appointment.doctor_id == doctor.id).first()
            has_visit = db.query(Visit).filter(Visit.patient_id == db_file.patient_id, Visit.doctor_id == doctor.id).first()
            if not has_appt and not has_visit:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="يمكنك تحميل ملفات المرضى التابعين لك فقط")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="حساب الطبيب غير مكتمل")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="غير متاح لهذا الحساب")

    if not db_file.file_url or not os.path.exists(db_file.file_url):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الملف غير موجود على القرص")

    return FileResponse(
        path=db_file.file_url,
        filename=db_file.file_name,
        media_type=db_file.mime_type
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """حذف ملف (من رفعه أو المريض صاحب الملف)"""
    db_file = db.query(MedicalFile).filter(MedicalFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="الملف غير موجود")

    # Access control
    is_uploader = db_file.uploaded_by_user_id == current_user.id
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    is_owner_patient = patient and patient.id == db_file.patient_id

    if not is_uploader and not is_owner_patient:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="لا تملك صلاحية حذف هذا الملف")

    # Remove from disk
    if db_file.file_url and os.path.exists(db_file.file_url):
        os.remove(db_file.file_url)

    db.delete(db_file)
    db.commit()
