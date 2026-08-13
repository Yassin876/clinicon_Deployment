"""
Reminder Scheduler
1. تذكيرات الأدوية — قبل كل جرعة بـ 5 دقايق
2. تذكيرات المواعيد — قبل الموعد بـ 15 دقيقة
"""
import threading
import time as _time
from datetime import datetime, timedelta
import httpx
import os

from sqlalchemy import func

from app.database import SessionLocal
from app.models.medication import Medication, MedicationReminder
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.user import User
import uuid as _uuid

_sent_today = set()          # (reminder_id, date_str) — تذكيرات الأدوية
_sent_appt_today = set()     # (appointment_id, date_str) — تذكيرات المواعيد
_last_update_id = 0          # آخر update من تليجرام تم معالجته


def _send_telegram(chat_id: int, message: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or not chat_id:
        print(f"[Reminder] Skipped — no token or chat_id")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
            })
        result = res.json()
        if result.get("ok"):
            print(f"[Reminder] ✓ Sent to {chat_id}")
            return True
        else:
            print(f"[Reminder] ✗ Telegram error: {result.get('description')}")
            return False
    except Exception as e:
        print(f"[Reminder] ✗ Connection error: {e}")
        return False


def _check_reminders():
    """يشيك على كل التذكيرات ويبعت اللي جاي موعدها."""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time = now.time()

    # الوقت اللي قبل التذكير بـ 5 دقايق
    window_start = (now - timedelta(minutes=1)).time()
    window_end = (now + timedelta(minutes=6)).time()

    db = SessionLocal()
    try:
        reminders = db.query(MedicationReminder).filter(
            MedicationReminder.is_active == True
        ).all()

        for r in reminders:
            key = (str(r.id), today_str)
            if key in _sent_today:
                continue

            # هل وقت التذكير ناقص 5 دقايق جوا الـ window بتاعتنا؟
            reminder_dt = datetime.combine(now.date(), r.reminder_time)
            send_at = reminder_dt - timedelta(minutes=5)
            send_time = send_at.time()

            # هل إحنا في نطاق الدقيقة دي؟
            if not (window_start <= send_time <= window_end):
                continue

            # هات بيانات الدواء والمريض
            med = db.query(Medication).filter(Medication.id == r.medication_id).first()
            if not med or not med.is_active:
                continue

            patient = db.query(Patient).filter(Patient.id == med.patient_id).first()
            if not patient or not patient.telegram_chat_id or not patient.telegram_notif_enabled:
                continue

            # ابني الرسالة
            time_str = r.reminder_time.strftime("%H:%M")
            msg = (
                f"💊 <b>تذكير دواء</b>\n\n"
                f"الدواء: <b>{med.medicine_name}</b>\n"
                f"الجرعة: {med.dosage or '—'}\n"
                f"الموعد: {time_str}\n\n"
                f"⏰ موعد جرعتك بعد 5 دقايق!"
            )

            if _send_telegram(patient.telegram_chat_id, msg):
                _sent_today.add(key)

    except Exception as e:
        print(f"[Reminder] Error checking reminders: {e}")
    finally:
        db.close()

    # نظّف الـ sent_today من الأيام القديمة
    old_keys = [k for k in _sent_today if k[1] != today_str]
    for k in old_keys:
        _sent_today.discard(k)


def _check_telegram_starts():
    """يشيك على رسائل /start الجديدة في البوت ويربط الـ chat_id بالمريض أوتوماتيك."""
    global _last_update_id
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": _last_update_id + 1, "timeout": 0}

    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(url, params=params)
        data = res.json()
        if not data.get("ok"):
            return

        updates = data.get("result", [])
        if not updates:
            return

        db = SessionLocal()
        try:
            for update in updates:
                _last_update_id = max(_last_update_id, update["update_id"])
                msg = update.get("message", {})
                text = msg.get("text", "")
                chat_id = msg.get("chat", {}).get("id")

                if not text.startswith("/start ") or not chat_id:
                    continue

                # /start patient_uuid
                patient_id_str = text.replace("/start ", "").strip()
                try:
                    patient_id = _uuid.UUID(patient_id_str)
                except ValueError:
                    continue

                patient = db.query(Patient).filter(Patient.id == patient_id).first()
                if not patient:
                    continue

                patient.telegram_chat_id = chat_id
                patient.telegram_notif_enabled = True
                db.commit()

                # ابعت رسالة تأكيد للمريض
                user = db.query(User).filter(User.id == patient.user_id).first()
                name = user.full_name if user else "المريض"
                _send_telegram(chat_id, (
                    f"✅ أهلاً <b>{name}</b>!\n\n"
                    f"تم ربط حسابك بنجاح.\n"
                    f"هتوصلك تذكيرات الأدوية والمواعيد هنا. 💊📅"
                ))
                print(f"[Telegram] Auto-linked patient {patient_id} → chat {chat_id}")

        except Exception as e:
            print(f"[Telegram] Error processing starts: {e}")
            db.rollback()
        finally:
            db.close()

    except Exception as e:
        print(f"[Telegram] Error fetching updates: {e}")


def _check_appointment_reminders():
    """يشيك على المواعيد الجاية ويبعت تذكير قبلها بـ 3 ساعات."""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # المواعيد اللي في خلال 3 ساعات من دلوقتي (تذكير قبل الموعد بـ 3 ساعات)
    window_start = now + timedelta(hours=3, minutes=-1)
    window_end = now + timedelta(hours=3, minutes=1)

    db = SessionLocal()
    try:
        appointments = db.query(Appointment).filter(
            Appointment.status.in_([AppointmentStatus.pending, AppointmentStatus.confirmed]),
            Appointment.appointment_date >= window_start,
            Appointment.appointment_date <= window_end,
        ).all()

        for appt in appointments:
            key = (str(appt.id), today_str)
            if key in _sent_appt_today:
                continue

            patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
            if not patient or not patient.telegram_chat_id or not patient.telegram_notif_enabled:
                continue

            # هات اسم الدكتور
            doctor = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
            doctor_name = "الطبيب"
            if doctor:
                user = db.query(User).filter(User.id == doctor.user_id).first()
                if user:
                    doctor_name = user.full_name

            appt_time = appt.appointment_date.strftime("%H:%M")

            msg = (
                f"📅 <b>تذكير موعد</b>\n\n"
                f"لديك موعد مع الدكتور <b>{doctor_name}</b>\n"
                f"الساعة: <b>{appt_time}</b>\n\n"
                f"موعدك بعد 3 ساعات، يرجى الاستعداد. ⏰"
            )

            if _send_telegram(patient.telegram_chat_id, msg):
                _sent_appt_today.add(key)

    except Exception as e:
        print(f"[Reminder] Error checking appointment reminders: {e}")
    finally:
        db.close()

    # نظّف القديم
    old_keys = [k for k in _sent_appt_today if k[1] != today_str]
    for k in old_keys:
        _sent_appt_today.discard(k)


def _scheduler_loop():
    """بيشتغل كل 60 ثانية."""
    print("[Reminder] Scheduler started — checking every 60 seconds")
    while True:
        try:
            _check_telegram_starts()
            _check_reminders()
            _check_appointment_reminders()
        except Exception as e:
            print(f"[Reminder] Loop error: {e}")
        _time.sleep(60)


def start_scheduler():
    """يشغّل الـ scheduler في background thread."""
    t = threading.Thread(target=_scheduler_loop, daemon=True)
    t.start()
    print("[Reminder] Background scheduler thread started")
