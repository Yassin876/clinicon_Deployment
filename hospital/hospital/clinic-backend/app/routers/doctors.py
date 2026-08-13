from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional
import uuid
import os
import httpx

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.doctor import Doctor, DoctorLeave
from app.models.appointment import Appointment, AppointmentStatus

router = APIRouter(prefix="/doctors", tags=["Doctors"])

class DoctorLeaveCreate(BaseModel):
    leave_date: date
    start_time: time
    end_time: time
    reason: Optional[str] = None

class EndTodayLeaveRequest(BaseModel):
    reason: Optional[str] = None


async def _create_leave_and_notify(
    db: Session,
    doctor: Doctor,
    leave_date: date,
    start_time: time,
    end_time: time,
    reason: Optional[str] = None
):
    # 1. Save Leave Record
    leave_record = DoctorLeave(
        doctor_id=doctor.id,
        leave_date=leave_date,
        start_time=start_time,
        end_time=end_time,
        reason=reason
    )
    db.add(leave_record)
    db.commit()
    db.refresh(leave_record)

    # 2. Query Affected Appointments
    affected_appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])
    ).all()

    # Filter appointments falling on leave_date and within start_time - end_time
    leave_date_str = leave_date.isoformat()
    affected = []
    for appt in affected_appointments:
        if appt.appointment_date.date().isoformat() == leave_date_str:
            appt_time = appt.appointment_date.time()
            if start_time <= appt_time <= end_time:
                affected.append(appt)

    # 3. Send Telegram Messages with Inline Buttons
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    sent_count = 0

    if bot_token and affected:
        async with httpx.AsyncClient() as client:
            for appt in affected:
                patient = appt.patient
                chat_id = patient.telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID", "").strip()
                if not chat_id:
                    continue

                msg_text = (
                    f"⚠️ <b>تنبيه اعتذار طبيب</b>\n\n"
                    f"عزيزي المريض، نعتذر منك، اعتذر الطبيب عن موعدك يوم <b>{leave_date}</b> الساعة <b>{appt.appointment_date.strftime('%H:%M')}</b>.\n"
                    f"السبب: {reason or 'ظروف طارئة'}.\n\n"
                    f"يسعدنا مساعدتك في اختيار الخيار الأنسب لك:"
                )

                inline_keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "⏳ أستنى الموعد الجاي",
                                "callback_data": f"wait_next:{appt.id}"
                            }
                        ],
                        [
                            {
                                "text": "🚨 محتاج أدخل النهاردة",
                                "callback_data": f"urgent:{appt.id}"
                            }
                        ]
                    ]
                }

                try:
                    res = await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": msg_text,
                            "parse_mode": "HTML",
                            "reply_markup": inline_keyboard
                        },
                        timeout=5.0
                    )
                    if res.json().get("ok"):
                        sent_count += 1
                except Exception as err:
                    print(f"[Telegram Leave Notif Error]: {err}")

    return {
        "success": True,
        "message": f"تم تسجيل الإجازة وإشعار {sent_count} مريض متأثر عبر التليجرام",
        "leave_id": str(leave_record.id),
        "affected_appointments": len(affected)
    }


@router.post("/leave")
async def create_doctor_leave(
    payload: DoctorLeaveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """تسجيل إجازة/اعتذار الطبيب وإرسال خيارات إعادة الجدولة الآلية للمرضى"""
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=403, detail="هذه الصفحة خاصة بالأطباء فقط")

    return await _create_leave_and_notify(
        db=db,
        doctor=doctor,
        leave_date=payload.leave_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        reason=payload.reason
    )


@router.post("/leave/end-today")
async def end_today_leave(
    payload: Optional[EndTodayLeaveRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """إنهاء عمل الدكتور لليوم واعتذاره عن باقي مواعيد اليوم"""
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=403, detail="هذه الصفحة خاصة بالأطباء فقط")

    now = datetime.now()
    today_date = now.date()
    current_time = now.time()
    day_of_week = today_date.weekday()

    # Find doctor's availability end_time for today if configured
    from app.models.doctor import DoctorAvailability
    avail = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor.id,
        DoctorAvailability.day_of_week == day_of_week,
        DoctorAvailability.is_active == True
    ).first()

    end_t = avail.end_time if avail else time(23, 59, 59)
    reason = payload.reason if payload else None

    return await _create_leave_and_notify(
        db=db,
        doctor=doctor,
        leave_date=today_date,
        start_time=current_time,
        end_time=end_t,
        reason=reason
    )
