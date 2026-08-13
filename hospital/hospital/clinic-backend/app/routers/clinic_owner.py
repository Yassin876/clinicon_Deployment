"""
Clinic Owner Router — إدارة العيادة (دكاترة + معامل)
يتطلب role = clinic_owner
"""
import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.core.dependencies import require_clinic_owner, get_current_user
from app.models.user import User, UserRole
from app.models.clinic import Clinic, LabEntity
from app.models.doctor import Doctor
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService

router = APIRouter(prefix="/clinic", tags=["Clinic Owner"])


# ───────────── Schemas ─────────────

class ClinicRegisterRequest(BaseModel):
    clinic_name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    location_url: Optional[str] = None
    specializations: Optional[str] = None  # comma-separated


class ClinicUpdateRequest(BaseModel):
    clinic_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    location_url: Optional[str] = None
    specializations: Optional[str] = None


class InviteDoctorRequest(BaseModel):
    full_name: str
    specialization: str
    bio: Optional[str] = None


class AddClinicMemberRequest(UserCreate):
    pass


# ───────────── Endpoints ─────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_clinic(
    payload: ClinicRegisterRequest,
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """صاحب العيادة يسجّل عيادته — كل صاحب عيادة له عيادة واحدة فقط"""
    existing = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="لديك عيادة مسجّلة بالفعل. يمكنك تعديل بياناتها."
        )

    clinic = Clinic(
        clinic_name=payload.clinic_name,
        address=payload.address,
        phone=payload.phone,
        location_url=payload.location_url,
        specializations=payload.specializations,
        owner_user_id=current_user.id
    )
    db.add(clinic)
    db.commit()
    db.refresh(clinic)

    return {
        "success": True,
        "message": f"تم تسجيل عيادة '{clinic.clinic_name}' بنجاح",
        "clinic": {
            "id": str(clinic.id),
            "clinic_name": clinic.clinic_name,
            "address": clinic.address,
            "phone": clinic.phone,
            "location_url": clinic.location_url,
            "specializations": clinic.specializations,
        }
    }


@router.put("/update")
def update_clinic(
    payload: ClinicUpdateRequest,
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """تحديث بيانات العيادة"""
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        clinic = Clinic(
            clinic_name=payload.clinic_name or current_user.full_name,
            address=payload.address,
            phone=payload.phone or current_user.phone_number,
            location_url=payload.location_url,
            specializations=payload.specializations,
            owner_user_id=current_user.id
        )
        db.add(clinic)
    else:
        if payload.clinic_name is not None:
            clinic.clinic_name = payload.clinic_name
        if payload.address is not None:
            clinic.address = payload.address
        if payload.phone is not None:
            clinic.phone = payload.phone
        if payload.location_url is not None:
            clinic.location_url = payload.location_url
        if payload.specializations is not None:
            clinic.specializations = payload.specializations

    db.commit()
    db.refresh(clinic)

    return {
        "success": True,
        "message": "تم تحديث بيانات العيادة بنجاح",
        "clinic": {
            "id": str(clinic.id),
            "clinic_name": clinic.clinic_name,
            "address": clinic.address,
            "phone": clinic.phone,
            "location_url": clinic.location_url,
            "specializations": clinic.specializations,
        }
    }


@router.get("/my-clinic")
def get_my_clinic(
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """جلب بيانات عيادة الـ owner الحالي (وإنشائها تلقائياً في حال عدم وجودها)"""
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        clinic = Clinic(
            clinic_name=current_user.full_name,
            phone=current_user.phone_number,
            owner_user_id=current_user.id
        )
        db.add(clinic)
        db.commit()
        db.refresh(clinic)

    return {
        "id": str(clinic.id),
        "clinic_name": clinic.clinic_name,
        "address": clinic.address,
        "phone": clinic.phone,
        "location_url": clinic.location_url,
        "specializations": clinic.specializations,
    }


@router.post("/invite-doctor")
def invite_doctor(
    payload: InviteDoctorRequest,
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="يجب تسجيل عيادتك أولاً قبل إضافة دكاترة")

    invitation_token = secrets.token_urlsafe(32)

    return {
        "success": True,
        "message": f"تم إنشاء دعوة للطبيب {payload.full_name}",
        "invitation": {
            "doctor_name": payload.full_name,
            "specialization": payload.specialization,
            "clinic_name": clinic.clinic_name,
            "token": invitation_token,
            "instructions": "أرسل هذا الـ token للطبيب ليستخدمه عند تسجيل حسابه"
        }
    }


@router.get("/stats")
def get_clinic_owner_stats(
    date: Optional[str] = None,
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """إحصائيات مجمعة لعيادة مالك العيادة بتاريخ محدد دون المساس ببيانات المرضى"""
    from sqlalchemy import func
    from datetime import datetime
    from app.models.appointment import Appointment, AppointmentStatus

    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="لم تقم بتسجيل عيادة بعد")

    target_date_str = date if date else datetime.now().strftime("%Y-%m-%d")
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="تاريخ غير صالح، استخدم الصيغة YYYY-MM-DD")

    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic.id).all()
    doctor_map = {d.id: (d.user.full_name if d.user else "—") for d in doctors}
    doctor_ids = list(doctor_map.keys())

    stats_by_doc = {doc_id: {"doctor_name": doctor_map[doc_id], "total": 0, "completed": 0, "pending": 0} for doc_id in doctor_ids}

    if doctor_ids:
        query_results = db.query(
            Appointment.doctor_id,
            Appointment.status,
            func.count(Appointment.id)
        ).filter(
            Appointment.doctor_id.in_(doctor_ids),
            func.date(Appointment.appointment_date) == target_date
        ).group_by(
            Appointment.doctor_id,
            Appointment.status
        ).all()

        for doc_id, appt_status, count in query_results:
            if doc_id in stats_by_doc:
                stats_by_doc[doc_id]["total"] += count
                if appt_status == AppointmentStatus.completed:
                    stats_by_doc[doc_id]["completed"] += count
                elif appt_status in (AppointmentStatus.pending, AppointmentStatus.confirmed):
                    stats_by_doc[doc_id]["pending"] += count

    by_doctor_list = list(stats_by_doc.values())
    total_appointments = sum(d["total"] for d in by_doctor_list)
    total_completed = sum(d["completed"] for d in by_doctor_list)
    total_pending = sum(d["pending"] for d in by_doctor_list)

    return {
        "date": target_date_str,
        "total_appointments": total_appointments,
        "total_completed": total_completed,
        "total_pending": total_pending,
        "by_doctor": by_doctor_list
    }


@router.get("/my-doctors")
def get_my_doctors(
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """جلب الدكاترة المرتبطين بعيادة الـ owner مع الجدول الأسبوعي والإجازات الحالية"""
    from datetime import date as date_type

    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="لم تقم بتسجيل عيادة بعد")

    doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic.id).all()
    today = date_type.today()

    return {
        "clinic_name": clinic.clinic_name,
        "total": len(doctors),
        "doctors": [
            {
                "id": str(d.id),
                "name": d.user.full_name if d.user else "—",
                "specialization": d.specialization,
                "bio": d.bio,
                "is_active": d.user.is_active if d.user else False,
                "weekly_schedule": [
                    {
                        "day_of_week": str(a.day_of_week),
                        "start_time": a.start_time.strftime("%H:%M") if a.start_time else "",
                        "end_time": a.end_time.strftime("%H:%M") if a.end_time else ""
                    }
                    for a in (d.availabilities or []) if a.is_active
                ],
                "leaves": [
                    {
                        "leave_date": l.leave_date.strftime("%Y-%m-%d") if hasattr(l.leave_date, 'strftime') else str(l.leave_date),
                        "start_time": l.start_time.strftime("%H:%M") if l.start_time else "",
                        "end_time": l.end_time.strftime("%H:%M") if l.end_time else "",
                        "reason": l.reason or ""
                    }
                    for l in (d.leaves or [])
                    if (l.leave_date.date() if hasattr(l.leave_date, 'date') else l.leave_date) >= today
                ]
            }
            for d in doctors
        ]
    }


@router.post("/add-member", status_code=status.HTTP_201_CREATED)
def add_member(
    payload: AddClinicMemberRequest,
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """صاحب العيادة يضيف عضوًا مباشرةً إلى العيادة وتفعيله فورًا"""
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="يجب تسجيل عيادتك أولاً")

    if payload.role not in {UserRole.doctor, UserRole.lab}:
        raise HTTPException(status_code=400, detail="يمكن فقط إضافة أطباء أو معامل من لوحة صاحب العيادة")

    payload_data = payload.model_dump()
    payload_data["clinic_email"] = current_user.email

    user = AuthService.register_user(db=db, details=UserCreate(**payload_data), force_active=True)

    if user.role == UserRole.doctor and user.doctor_profile:
        user.doctor_profile.clinic_id = clinic.id
    elif user.role == UserRole.lab:
        existing_lab = db.query(LabEntity).filter(LabEntity.clinic_id == clinic.id, LabEntity.user_id == user.id).first()
        if not existing_lab:
            lab = LabEntity(
                clinic_id=clinic.id,
                user_id=user.id,
                name=user.full_name,
                contact_info=f"Email: {user.email} | Phone: {user.phone_number or 'N/A'}"
            )
            db.add(lab)

    db.commit()
    db.refresh(user)
    return {
        "success": True,
        "message": f"تم إضافة {user.full_name} بنجاح",
        "member": {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
        },
    }


@router.get("/my-labs")
def get_my_labs(
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """جلب المعامل المرتبطة بعيادة الـ owner"""
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="لم تقم بتسجيل عيادة بعد")

    return {
        "clinic_name": clinic.clinic_name,
        "total": len(clinic.labs),
        "labs": [
            {
                "id": str(lab.id),
                "name": lab.name,
                "contact_info": lab.contact_info,
                "added_at": lab.created_at.isoformat() if lab.created_at else None,
            }
            for lab in clinic.labs
        ]
    }


@router.get("/pending-requests")
def get_pending_requests(
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """جلب طلبات الانضمام المعلقة (دكاترة، معامل، مرضي) لعيادة الـ owner"""
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="لم تقم بتسجيل عيادة بعد")

    pending_users = db.query(User).filter(
        User.pending_clinic_id == clinic.id,
        User.is_active == False
    ).all()

    return {
        "total": len(pending_users),
        "requests": [
            {
                "id": str(u.id),
                "full_name": u.full_name,
                "email": u.email,
                "phone_number": u.phone_number,
                "role": u.role.value,
                "specialization": u.doctor_profile.specialization if u.doctor_profile else None,
                "requested_at": u.created_at.isoformat() if u.created_at else None
            }
            for u in pending_users
        ]
    }


@router.post("/approve-request/{user_id}")
def approve_request(
    user_id: str,
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """الموافقة على طلب انضمام مستخدم (تفعيل الحساب وربطه بالعيادة)"""
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="لم تقم بتسجيل عيادة بعد")

    target_user = db.query(User).filter(
        User.id == user_id,
        User.pending_clinic_id == clinic.id
    ).first()

    if not target_user:
        raise HTTPException(status_code=404, detail="الطلب غير موجود أو لا ينتمي لعيادتك")

    target_user.is_active = True
    target_user.pending_clinic_id = None

    # Link doctor to clinic if doctor
    if target_user.role == UserRole.doctor and target_user.doctor_profile:
        target_user.doctor_profile.clinic_id = clinic.id

    # Link lab to clinic if lab
    elif target_user.role == UserRole.lab:
        existing_lab = db.query(LabEntity).filter(LabEntity.clinic_id == clinic.id, LabEntity.user_id == target_user.id).first()
        if not existing_lab:
            new_lab = LabEntity(
                clinic_id=clinic.id,
                user_id=target_user.id,
                name=target_user.full_name,
                contact_info=f"Email: {target_user.email} | Phone: {target_user.phone_number or 'N/A'}"
            )
            db.add(new_lab)

    db.commit()
    return {"success": True, "message": f"تمت الموافقة وتفعيل حساب {target_user.full_name} بنجاح"}


@router.post("/reject-request/{user_id}")
def reject_request(
    user_id: str,
    current_user: User = Depends(require_clinic_owner),
    db: Session = Depends(get_db)
):
    """رفض طلب انضمام مستخدم"""
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="لم تقم بتسجيل عيادة بعد")

    target_user = db.query(User).filter(
        User.id == user_id,
        User.pending_clinic_id == clinic.id
    ).first()

    if not target_user:
        raise HTTPException(status_code=404, detail="الطلب غير موجود أو لا ينتمي لعيادتك")

    db.delete(target_user)
    db.commit()
    return {"success": True, "message": "تم رفض الطلب وحذف الحساب المعلق بنجاح"}
