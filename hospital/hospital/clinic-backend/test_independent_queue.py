#!/usr/bin/env python3
"""
اختبار: كل دكتور يجب أن يكون له ترتيب أدوار مستقل
"""
import sys
from datetime import datetime
from app.database import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.clinic import Clinic
from sqlalchemy import func
from app.core import security
import uuid

db = SessionLocal()

try:
    # نظف البيانات القديمة اليوم
    today = datetime.utcnow().date()
    
    # حذف users بأرقام محددة للاختبار
    test_phones = ["01111111111", "01111111112", "01111111113", "01111111114", "01100000001", "01100000002"]
    for phone in test_phones:
        db.query(User).filter(User.phone_number == phone).delete()
    
    old_appts = db.query(Appointment).filter(
        func.date(Appointment.appointment_date) == today
    ).delete()
    db.commit()
    print(f"تم تنظيف البيانات القديمة")
    
    # الآن إنشاء 2 دكتور و 4 مرضى
    # دكتور 1: د محمد
    user_doc1 = User(
        id=uuid.uuid4(),
        full_name="د محمد علي",
        email=f"doc1_{uuid.uuid4().hex[:6]}@clinic.local",
        password_hash=security.get_password_hash("password"),
        phone_number="01100000001",
        role=UserRole.doctor,
        is_active=True
    )
    db.add(user_doc1)
    db.flush()
    
    doctor1 = Doctor(
        id=uuid.uuid4(),
        user_id=user_doc1.id,
        specialization="عيون"
    )
    db.add(doctor1)
    db.flush()
    
    # دكتور 2: د أحمد
    user_doc2 = User(
        id=uuid.uuid4(),
        full_name="د أحمد سالم",
        email=f"doc2_{uuid.uuid4().hex[:6]}@clinic.local",
        password_hash=security.get_password_hash("password"),
        phone_number="01100000002",
        role=UserRole.doctor,
        is_active=True
    )
    db.add(user_doc2)
    db.flush()
    
    doctor2 = Doctor(
        id=uuid.uuid4(),
        user_id=user_doc2.id,
        specialization="قلب"
    )
    db.add(doctor2)
    db.flush()
    
    # 4 مرضى (2 مع الدكتور الأول و 2 مع الدكتور الثاني)
    # يجب محاكاة ما يحدث في book_appointment
    patients_data = [
        ("مريض عيون 1", "01111111111", doctor1.id),
        ("مريض عيون 2", "01111111112", doctor1.id),
        ("مريض قلب 1", "01111111113", doctor2.id),
        ("مريض قلب 2", "01111111114", doctor2.id),
    ]
    
    for name, phone, doctor_id in patients_data:
        user = User(
            id=uuid.uuid4(),
            full_name=name,
            email=f"patient_{uuid.uuid4().hex[:6]}@clinic.local",
            password_hash=security.get_password_hash("password"),
            phone_number=phone,
            role=UserRole.patient,
            is_active=True
        )
        db.add(user)
        db.flush()
        
        patient = Patient(
            id=uuid.uuid4(),
            user_id=user.id
        )
        db.add(patient)
        db.flush()
        
        # حساب queue_number لهذا الدكتور (مثل الكود الفعلي)
        last_appt = db.query(Appointment).filter(
            func.date(Appointment.appointment_date) == today,
            Appointment.doctor_id == doctor_id
        ).order_by(Appointment.queue_number.desc()).first()
        q_num = (last_appt.queue_number + 1) if last_appt else 1
        
        appt = Appointment(
            id=uuid.uuid4(),
            patient_id=patient.id,
            doctor_id=doctor_id,
            appointment_date=datetime.utcnow(),
            queue_number=q_num,
            status=AppointmentStatus.pending
        )
        db.add(appt)
        db.commit()  # Commit after each to ensure queue_number is calculated correctly
    
    # الآن اعرض البيانات
    appts = db.query(Appointment).filter(
        func.date(Appointment.appointment_date) == today
    ).order_by(Appointment.doctor_id, Appointment.queue_number).all()
    
    print(f"\n{'='*80}")
    print(f"البيانات بعد الإنشاء:")
    print(f"{'='*80}\n")
    
    for appt in appts:
        doc_name = appt.doctor.user.full_name
        patient_name = appt.patient.user.full_name
        print(f"الدكتور: {doc_name:<20} | المريض: {patient_name:<20} | الرقم: {appt.queue_number}")
    
    print(f"\n✓ يجب أن تكون الأرقام مستقلة لكل دكتور!")
    print(f"  د محمد علي: 1, 2")
    print(f"  د أحمد سالم: 1, 2")
    
finally:
    db.close()
