from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, time, timedelta
import uuid

from app.database import get_db
from app.models.user import User, UserRole
from app.models.patient import Patient, PatientNote
from app.models.doctor import Doctor, DoctorAvailability, DoctorLeave
from app.models.clinic import Clinic
from app.models.appointment import Appointment, AppointmentStatus
from app.models.medical_record import Visit
from app.core.dependencies import get_current_user, require_doctor, require_patient

router = APIRouter()

class BookingRequest(BaseModel):
    doctor_id: str
    slot_datetime: datetime
    patient_name: str = ''
    patient_phone: str = ''


@router.get('/doctors')
async def list_doctors(db: Session = Depends(get_db)):
    """قائمة الأطباء المتاحين مع أسمائهم وتخصصاتهم — بدون تسجيل دخول"""
    doctors = db.query(Doctor).join(User, Doctor.user_id == User.id).filter(User.is_active == True).all()
    return {
        'success': True,
        'data': [
            {
                'id': str(d.id),
                'name': d.user.full_name,
                'specialization': d.specialization,
                'bio': d.bio or ''
            }
            for d in doctors
        ]
    }


def get_doctor_available_slots_internal(
    doctor: Doctor,
    target_date: date,
    db: Session
) -> list[datetime]:
    # Python weekday: Monday=0, Sunday=6
    day_of_week = target_date.weekday()

    availability = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.day_of_week == day_of_week,
        DoctorAvailability.is_active == True
    ).first()

    if not availability:
        return []

    # Find leaves on target_date
    leaves = db.query(DoctorLeave).filter(
        DoctorLeave.doctor_id == doctor.id,
        func.date(DoctorLeave.leave_date) == target_date
    ).all()

    slot_duration = timedelta(minutes=doctor.slot_duration_minutes or 15)
    current_time = datetime.combine(target_date, availability.start_time)
    end_time = datetime.combine(target_date, availability.end_time)

    all_slots = []
    while current_time + slot_duration <= end_time:
        slot_start = current_time
        slot_end = current_time + slot_duration

        # Check leave collision
        is_on_leave = False
        for leave in leaves:
            leave_start = datetime.combine(target_date, leave.start_time)
            leave_end = datetime.combine(target_date, leave.end_time)
            # Overlap check
            if max(slot_start, leave_start) < min(slot_end, leave_end):
                is_on_leave = True
                break

        if not is_on_leave:
            all_slots.append(slot_start)
        current_time += slot_duration

    # Fetch existing appointments (pending or confirmed)
    existing_appts = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.id,
        func.date(Appointment.appointment_date) == target_date,
        Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])
    ).all()

    now = datetime.now()
    booked_datetimes = {
        a.appointment_date.replace(tzinfo=None) if a.appointment_date else None
        for a in existing_appts
    }

    unbooked_slots = [slot for slot in all_slots if slot not in booked_datetimes]

    # If target_date is today, filter out slots that are in the past (Egypt local time)
    if target_date == now.date():
        unbooked_slots = [slot for slot in unbooked_slots if slot >= now]

    return unbooked_slots


@router.get('/doctors/{doctor_id}/available-slots')
async def get_available_slots(
    doctor_id: str,
    date_str: str = Query(..., alias="date"),
    db: Session = Depends(get_db)
):
    try:
        doc_uuid = uuid.UUID(doctor_id)
        doctor = db.query(Doctor).filter(Doctor.id == doc_uuid).first()
        if not doctor:
            raise HTTPException(status_code=404, detail="الطبيب غير موجود")

        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        available_slots = get_doctor_available_slots_internal(doctor, target_date, db)

        available_slots_iso = [slot.isoformat() for slot in available_slots]

        return {"success": True, "data": available_slots_iso}

    except ValueError:
        raise HTTPException(status_code=400, detail="تاريخ غير صالحة، استخدم YYYY-MM-DD")
    except Exception as e:
        print(f"Exception in available-slots: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "خطأ في جلب المواعيد المتاحة"}
        )


@router.post('/book')
async def book_appointment(
    payload: BookingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_patient)
):
    try:
        # Get patient profile
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'success': False, 'message': 'حساب المريض غير مكتمل'}
            )

        try:
            doc_uuid = uuid.UUID(payload.doctor_id)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'success': False, 'message': 'معرف الطبيب غير صالح'}
            )

        doctor = db.query(Doctor).filter(Doctor.id == doc_uuid).first()
        if not doctor:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'success': False, 'message': 'الطبيب غير موجود'}
            )

        slot_dt = payload.slot_datetime
        if slot_dt.tzinfo is not None:
            slot_dt = slot_dt.replace(tzinfo=None)

        # Validate that slot_dt is in the list of available slots
        available_slots = get_doctor_available_slots_internal(doctor, slot_dt.date(), db)
        if slot_dt not in available_slots:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'success': False, 'message': 'هذا الموعد غير متاح للحجز'}
            )

        # Check existing appointment for doctor at exact slot_datetime
        existing_appt = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date == slot_dt,
            Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])
        ).first()

        if existing_appt:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'success': False, 'message': 'هذا الموعد حُجز بالفعل، اختر موعداً آخر'}
            )

        new_appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=slot_dt,
            status=AppointmentStatus.pending,
            patient_name=payload.patient_name or current_user.full_name,
            patient_phone=payload.patient_phone or current_user.phone_number or '',
        )
        db.add(new_appt)
        db.commit()
        db.refresh(new_appt)

        doctor_name = doctor.user.full_name if doctor.user else '—'

        patient_data = {
            'id': str(new_appt.id),
            'patient_id': str(patient.id),
            'doctor_id': str(doctor.id),
            'doctor': doctor_name,
            'name': current_user.full_name,
            'phone': current_user.phone_number,
            'status': 'waiting',
            'bookingDate': slot_dt.strftime('%Y-%m-%d'),
            'appointmentTime': slot_dt.strftime('%H:%M'),
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                'success': True,
                'data': patient_data,
                'message': 'تم الحجز بنجاح'
            }
        )
    except Exception as e:
        db.rollback()
        print(f"Exception in booking: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'success': False, 'message': 'خطأ داخلي في الخادم'}
        )


@router.get('/queue')
async def get_queue_public(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """مواعيدي القادمة للمريض المسجل دخول، أو قائمة المواعيد للطبيب/إحصائيات لمالك العيادة"""
    try:
        if current_user.role == UserRole.patient:
            patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
            if not patient:
                return {'success': True, 'data': [], 'count': 0}

            appts = db.query(Appointment).filter(
                Appointment.patient_id == patient.id,
                Appointment.appointment_date >= datetime.utcnow(),
                Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])
            ).order_by(Appointment.appointment_date.asc()).all()

            patients_data = []
            for appt in appts:
                user = appt.patient.user
                doctor_name = appt.doctor.user.full_name if appt.doctor else '—'
                patients_data.append({
                    'id': str(appt.id),
                    'patient_id': str(appt.patient_id),
                    'doctor_id': str(appt.doctor_id),
                    'name': user.full_name if user else '',
                    'phone': user.phone_number if user else '',
                    'appointmentTime': appt.appointment_date.strftime('%H:%M') if appt.appointment_date else '',
                    'status': 'waiting' if appt.status == AppointmentStatus.pending else appt.status.value,
                    'bookingDate': appt.appointment_date.strftime('%Y-%m-%d') if appt.appointment_date else '',
                    'doctor': doctor_name,
                })

            return {
                'success': True,
                'data': patients_data,
                'count': len(patients_data),
            }

        elif current_user.role == UserRole.doctor:
            doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
            if not doctor:
                return {'success': True, 'data': [], 'count': 0}

            today = datetime.utcnow().date()
            appts = db.query(Appointment).filter(
                Appointment.doctor_id == doctor.id,
                func.date(Appointment.appointment_date) == today,
                Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])
            ).order_by(Appointment.appointment_date.asc()).all()

            patients_data = []
            for appt in appts:
                doctor_name = appt.doctor.user.full_name if appt.doctor else '—'
                patients_data.append({
                    'id': str(appt.id),
                    'patient_id': str(appt.patient_id),
                    'doctor_id': str(appt.doctor_id),
                    'name': appt.patient_name or (appt.patient.user.full_name if appt.patient and appt.patient.user else ''),
                    'phone': appt.patient_phone or (appt.patient.user.phone_number if appt.patient and appt.patient.user else ''),
                    'appointmentTime': appt.appointment_date.strftime('%H:%M') if appt.appointment_date else '',
                    'status': 'waiting' if appt.status == AppointmentStatus.pending else appt.status.value,
                    'bookingDate': appt.appointment_date.strftime('%Y-%m-%d') if appt.appointment_date else '',
                    'doctor': doctor_name,
                })

            return {
                'success': True,
                'data': patients_data,
                'count': len(patients_data),
            }

        elif current_user.role == UserRole.clinic_owner:
            clinic = db.query(Clinic).filter(Clinic.owner_user_id == current_user.id).first()
            if not clinic:
                return {
                    'success': True,
                    'data': {'totalPatients': 0, 'waitingPatients': 0, 'completedPatients': 0, 'doctorStats': []}
                }

            today = datetime.utcnow().date()
            doctors = db.query(Doctor).filter(Doctor.clinic_id == clinic.id).all()
            if not doctors:
                return {
                    'success': True,
                    'data': {'totalPatients': 0, 'waitingPatients': 0, 'completedPatients': 0, 'doctorStats': []}
                }

            doctor_ids = [d.id for d in doctors]
            base_q = db.query(Appointment).filter(
                Appointment.doctor_id.in_(doctor_ids),
                func.date(Appointment.appointment_date) == today
            )

            total = base_q.count()
            waiting = base_q.filter(Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])).count()
            completed = base_q.filter(Appointment.status == AppointmentStatus.completed).count()

            # Per doctor stats + schedule info
            # Today's day of week (0: Monday, 6: Sunday -> stored in availability)
            day_name = today.strftime('%A')
            doctor_stats = []
            for doc in doctors:
                doc_name = doc.user.full_name if doc.user else 'طبيب'
                doc_appts = db.query(Appointment).filter(
                    Appointment.doctor_id == doc.id,
                    func.date(Appointment.appointment_date) == today
                ).all()
                doc_total = len(doc_appts)
                doc_completed = sum(1 for a in doc_appts if a.status == AppointmentStatus.completed)
                doc_pending = sum(1 for a in doc_appts if a.status in (AppointmentStatus.pending, AppointmentStatus.confirmed))

                # Doctor schedule today
                todays_avail = [a for a in (doc.availabilities or []) if str(a.day_of_week).strip().lower() == day_name.lower() or str(a.day_of_week) == str(today.weekday())]
                if todays_avail and todays_avail[0].start_time and todays_avail[0].end_time:
                    work_hours = f"{todays_avail[0].start_time.strftime('%I:%M %p')} - {todays_avail[0].end_time.strftime('%I:%M %p')}"
                else:
                    work_hours = "غير محدد اليوم"

                doctor_stats.append({
                    'doctor_id': str(doc.id),
                    'doctor_name': doc_name,
                    'specialization': doc.specialization or '',
                    'work_hours': work_hours,
                    'total': doc_total,
                    'completed': doc_completed,
                    'pending': doc_pending,
                })

            return {
                'success': True,
                'data': {
                    'totalPatients': total,
                    'waitingPatients': waiting,
                    'completedPatients': completed,
                    'doctorStats': doctor_stats,
                }
            }
        else:
            return {'success': True, 'data': [], 'count': 0}

    except Exception as e:
        print(f"Exception in get_queue: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'success': False, 'message': 'خطأ في جلب البيانات', 'data': []}
        )


@router.get('/patients')
async def get_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """بيانات المرضى التفصيلية — الطبيب يشوف مرضاه بس"""
    try:
        today = datetime.utcnow().date()
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            return {'success': True, 'data': [], 'count': 0}

        appts = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id,
            func.date(Appointment.appointment_date) == today
        ).order_by(Appointment.appointment_date.asc()).all()

        patients_data = []
        for appt in appts:
            user = appt.patient.user
            doctor_name = appt.doctor.user.full_name if appt.doctor else '—'
            patients_data.append({
                'id': str(appt.id),
                'name': user.full_name if user else '',
                'phone': user.phone_number if user else '',
                'appointmentTime': appt.appointment_date.strftime('%H:%M') if appt.appointment_date else '',
                'status': 'waiting' if appt.status == AppointmentStatus.pending else appt.status.value,
                'bookingDate': appt.appointment_date.strftime('%Y-%m-%d') if appt.appointment_date else '',
                'doctor': doctor_name,
            })

        return {
            'success': True,
            'data': patients_data,
            'count': len(patients_data),
        }
    except Exception as e:
        print(f"Exception in get_patients: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'success': False, 'message': 'خطأ في جلب البيانات', 'data': []}
        )


@router.get('/stats')
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    try:
        today = datetime.utcnow().date()
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            return {
                'success': True,
                'data': {
                    'totalPatients': 0, 'waitingPatients': 0, 'completedPatients': 0
                }
            }

        base_q = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id,
            func.date(Appointment.appointment_date) == today
        )

        total = base_q.count()
        waiting = base_q.filter(Appointment.status == AppointmentStatus.pending).count()
        completed = base_q.filter(Appointment.status == AppointmentStatus.completed).count()

        return {
            'success': True,
            'data': {
                'totalPatients': total,
                'waitingPatients': waiting,
                'completedPatients': completed,
            }
        }
    except Exception as e:
        print(f"Exception in stats: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'success': False,
                'message': 'خطأ في جلب الإحصائيات',
                'data': {
                    'totalPatients': 0, 'waitingPatients': 0, 'completedPatients': 0
                }
            }
        )


@router.put('/patient/{appointment_id}/done')
async def mark_patient_done(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    try:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="هذا الموعد ليس ضمن مرضاك"
            )

        appt_uuid = uuid.UUID(appointment_id)
        appt = db.query(Appointment).filter(Appointment.id == appt_uuid).first()
        if not appt:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'success': False, 'message': 'الحجز غير موجود'}
            )

        if appt.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="هذا الموعد ليس ضمن مرضاك"
            )

        if appt.status == AppointmentStatus.completed:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={'success': False, 'message': 'تم الانتهاء من كشف هذا المريض مسبقاً'}
            )

        appt.status = AppointmentStatus.completed
        appt.completed_at = datetime.utcnow()

        # Fetch existing visit or build new one with doctor's recorded notes
        existing_visit = db.query(Visit).filter(Visit.appointment_id == appt.id).first()
        if not existing_visit:
            # Check if doctor wrote any PatientNote during the consultation
            latest_note = (
                db.query(PatientNote)
                .filter(PatientNote.patient_id == appt.patient_id, PatientNote.doctor_id == doctor.id)
                .order_by(PatientNote.created_at.desc())
                .first()
            )
            recorded_notes = latest_note.note if latest_note else "تم إنهاء الكشف بنجاح"

            new_visit = Visit(
                patient_id=appt.patient_id,
                doctor_id=appt.doctor_id,
                appointment_id=appt.id,
                visit_date=datetime.utcnow(),
                chief_complaint="تم إتمام الكشف في العيادة",
                diagnosis="كشف عيادة",
                doctor_notes=recorded_notes,
            )
            db.add(new_visit)

        db.commit()

        user = appt.patient.user
        return {
            'success': True,
            'message': f'تم الانتهاء من كشف المريض: {user.full_name if user else ""}'
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Exception patch done: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'success': False, 'message': 'خطأ في تحديث البيانات'}
        )


