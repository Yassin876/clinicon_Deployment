from fastapi import APIRouter, Request, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import httpx
import os
import uuid
from datetime import datetime, timedelta, time
from dotenv import load_dotenv


from app.database import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor, DoctorAvailability, DoctorLeave
from app.models.patient import Patient

load_dotenv()

router = APIRouter(prefix="/telegram", tags=["Telegram"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN", "clinicon_secret_token_123").strip()

class TelegramMessage(BaseModel):
    chat_id: str
    message: str

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str = Header(None)
):
    """
    Telegram Webhook Handler for Inline Keyboard Buttons:
    1. Secret Token Security Validation
    2. Patient Identity Verification
    3. 'wait_next' (Reschedule to next slot)
    4. 'urgent' (Find alternative available doctor & rebook atomically)
    """
    # 🔒 Security Check 1: Secret Token Header
    if x_telegram_bot_api_secret_token and x_telegram_bot_api_secret_token != TELEGRAM_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized Telegram Webhook Request")

    data = await request.json()
    callback_query = data.get("callback_query")
    
    if not callback_query:
        return {"status": "ok", "message": "Ignored non-callback update"}

    callback_data = callback_query.get("data", "")
    from_user_id = callback_query.get("from", {}).get("id")
    chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", from_user_id))

    if not callback_data:
        return {"status": "ok"}

    parts = callback_data.split(":")
    action = parts[0]

    # Handle 'wait_next'
    if action == "wait_next" and len(parts) >= 2:
        appointment_id = uuid.UUID(parts[1])
        return await handle_wait_next(db, appointment_id, chat_id)

    # Handle 'urgent'
    elif action == "urgent" and len(parts) >= 2:
        appointment_id = uuid.UUID(parts[1])
        return await handle_urgent_search(db, appointment_id, chat_id)

    # Handle 'rebook' choice
    elif action == "rebook" and len(parts) >= 4:
        appointment_id = uuid.UUID(parts[1])
        alt_doctor_id = uuid.UUID(parts[2])
        slot_iso = parts[3]
        return await handle_urgent_rebook(db, appointment_id, alt_doctor_id, slot_iso, chat_id)

    return {"status": "ok"}


async def handle_wait_next(db: Session, appointment_id: uuid.UUID, chat_id: str):
    """الترحيل إلى الموعد القادم المتاح لنفس الطبيب مع القفل اللحظي لمنع السباق (Race Condition)"""
    # Atomic Lock & Security Patient Check
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).with_for_update().first()
    if not appt:
        return await send_telegram_reply(chat_id, "❌ لم يتم العثور على الموعد المطلوب.")

    # 🔒 Security Check 2: Verify Patient Identity
    patient = appt.patient
    if patient and patient.telegram_chat_id and str(patient.telegram_chat_id) != str(chat_id):
        return await send_telegram_reply(chat_id, "⛔ غير مصرح لك بتعديل هذا الموعد.")

    doctor = appt.doctor
    next_slot = find_next_available_slot(db, doctor.id, appt.appointment_date)

    if not next_slot:
        return await send_telegram_reply(chat_id, "لم نجد موعد قادم متاح قريباً للطبيب، يمكنك محاولة اختيار دكتور بديل عاجل.")

    # Update appointment status & time
    appt.appointment_date = next_slot
    appt.status = AppointmentStatus.rescheduled
    db.commit()

    reply_msg = (
        f"✅ <b>تمت إعادة الجدولة بنجاح!</b>\n\n"
        f"موعدك الجديد مع <b>د. {doctor.user.full_name if doctor.user else 'الطبيب'}</b> أصبح:\n"
        f"📅 <b>{next_slot.strftime('%Y-%m-%d')}</b> في تمام ⏰ <b>{next_slot.strftime('%H:%M')}</b>."
    )
    return await send_telegram_reply(chat_id, reply_msg)


async def handle_urgent_search(db: Session, appointment_id: uuid.UUID, chat_id: str):
    """البحث عن أطباء بدلاء متاحين من نفس التخصص وإرسال خيارات تفاعلية"""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        return await send_telegram_reply(chat_id, "❌ لم يتم العثور على الموعد.")

    doctor = appt.doctor
    specialization = doctor.specialization

    # Find alternative doctors in same specialization
    alt_doctors = db.query(Doctor).filter(
        Doctor.specialization == specialization,
        Doctor.id != doctor.id
    ).all()

    options = []
    target_date = appt.appointment_date.date()

    for d in alt_doctors:
        slot = find_next_available_slot(db, d.id, appt.appointment_date)
        if slot and slot.date() == target_date:
            options.append({
                "doctor_id": str(d.id),
                "doctor_name": d.user.full_name if d.user else "طبيب بديل",
                "slot_iso": slot.isoformat(),
                "slot_time": slot.strftime("%H:%M")
            })

    if not options:
        return await send_telegram_reply(
            chat_id,
            f"للأسف لا يوجد دكاترة بدلاء متاحين اليوم لتخصص ({specialization}). تم تسجيل موعدك في أقرب وقت قادم."
        )

    inline_buttons = []
    for opt in options[:4]:  # Show top 4 choices
        btn_text = f"👨‍⚕️ د. {opt['doctor_name']} ({opt['slot_time']})"
        btn_data = f"rebook:{appointment_id}:{opt['doctor_id']}:{opt['slot_iso']}"
        inline_buttons.append([{"text": btn_text, "callback_data": btn_data}])

    msg_text = f"🚨 <b>الدكاترة البدلاء المتاحون اليوم في تخصص ({specialization}):</b>\nيرجى اختيار الطبيب المناسب لحجز موعدك فوراً:"
    return await send_telegram_inline_keyboard(chat_id, msg_text, inline_buttons)


async def handle_urgent_rebook(db: Session, old_appointment_id: uuid.UUID, alt_doctor_id: uuid.UUID, slot_iso: str, chat_id: str):
    """حجز الموعد الجديد للدكتور البديل وإلغاء الموعد القديم بالكامل باستخدام نفس دالة الحجز الموحدة"""
    old_appt = db.query(Appointment).filter(Appointment.id == old_appointment_id).with_for_update().first()
    if not old_appt:
        return await send_telegram_reply(chat_id, "❌ لم يتم العثور على الموعد القديم.")

    new_date = datetime.fromisoformat(slot_iso)

    # 🔒 Real-time atomic verification before insertion
    conflict = db.query(Appointment).filter(
        Appointment.doctor_id == alt_doctor_id,
        Appointment.appointment_date == new_date,
        Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed])
    ).with_for_update().first()

    if conflict:
        return await send_telegram_reply(chat_id, "⚠️ نعتذر، تم حجز هذا الموعد للتو بواسطة مريض آخر! يرجى اختيار موعد آخر.")

    # 1. Create New Appointment via standard booking model
    new_appt = Appointment(
        patient_id=old_appt.patient_id,
        doctor_id=alt_doctor_id,
        appointment_date=new_date,
        status=AppointmentStatus.confirmed,
        notes=f"حجز عاجل بديل للموعد {old_appt.id}"
    )
    db.add(new_appt)

    # 2. Update Old Appointment status
    old_appt.status = AppointmentStatus.cancelled_by_doctor
    db.commit()

    alt_doctor = db.query(Doctor).filter(Doctor.id == alt_doctor_id).first()
    doc_name = alt_doctor.user.full_name if (alt_doctor and alt_doctor.user) else "الطبيب البديل"

    confirm_text = (
        f"🎉 <b>تم تأكيد الحجز العاجل بنجاح!</b>\n\n"
        f"👨‍⚕️ <b>الطبيب الجديد:</b> د. {doc_name}\n"
        f"📅 <b>التاريخ:</b> {new_date.strftime('%Y-%m-%d')}\n"
        f"⏰ <b>الوقت:</b> {new_date.strftime('%H:%M')}\n\n"
        f"تم إغلاق وإلغاء الموعد القديم تلقائياً."
    )
    return await send_telegram_reply(chat_id, confirm_text)


def find_next_available_slot(db: Session, doctor_id: uuid.UUID, from_datetime: datetime) -> Optional[datetime]:
    """دالة حساب الموعد القادم المتاح بناءً على جدول التوفر ومطروحة منه الإجازات والحجوزات الحالية"""
    availabilities = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.is_active == True
    ).all()

    if not availabilities:
        return from_datetime + timedelta(days=1)

    leaves = db.query(DoctorLeave).filter(DoctorLeave.doctor_id == doctor_id).all()
    existing_appts = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed, AppointmentStatus.rescheduled])
    ).all()

    booked_times = {a.appointment_date for a in existing_appts}

    for day_offset in range(0, 14): # Search next 14 days
        check_date = (from_datetime + timedelta(days=day_offset)).date()
        dow = check_date.weekday() # 0 = Monday, 6 = Sunday

        for avail in availabilities:
            slot_time = avail.start_time
            dt_candidate = datetime.combine(check_date, slot_time)
            
            if dt_candidate <= from_datetime:
                continue

            # Check leave conflict
            on_leave = any(
                l.leave_date.date() == check_date and l.start_time <= slot_time <= l.end_time
                for l in leaves
            )
            if on_leave:
                continue

            # Check appointment conflict
            if dt_candidate not in booked_times:
                return dt_candidate

    return from_datetime + timedelta(days=1)


async def send_telegram_reply(chat_id: str, text: str):
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "ok", "delivered": False}

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=5.0)
    return {"status": "ok", "delivered": True}


async def send_telegram_inline_keyboard(chat_id: str, text: str, inline_keyboard: list):
    if not TELEGRAM_BOT_TOKEN:
        return {"status": "ok", "delivered": False}

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": inline_keyboard}
        }, timeout=5.0)
    return {"status": "ok", "delivered": True}
