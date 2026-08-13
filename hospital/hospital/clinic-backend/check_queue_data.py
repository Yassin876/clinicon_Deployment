#!/usr/bin/env python3
"""
فحص البيانات في الـ queue لتأكد أن اسم المريض صحيح
"""
import sys
from datetime import datetime
from app.database import get_db, SessionLocal
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.user import User
from app.models.doctor import Doctor
from sqlalchemy import func

db = SessionLocal()

try:
    today = datetime.utcnow().date()
    appts = db.query(Appointment).filter(
        func.date(Appointment.appointment_date) == today
    ).order_by(Appointment.queue_number).all()
    
    print(f"\n{'='*80}")
    print(f"عدد المرضى اليوم: {len(appts)}")
    print(f"{'='*80}\n")
    
    for appt in appts:
        print(f"رقم الدور: {appt.queue_number}")
        print(f"  Appointment ID: {appt.id}")
        print(f"  Patient ID: {appt.patient_id}")
        print(f"  Doctor ID: {appt.doctor_id}")
        
        # Check patient
        if appt.patient:
            print(f"  ✓ Patient found")
            print(f"    Patient.user_id: {appt.patient.user_id}")
            if appt.patient.user:
                print(f"    ✓ User found")
                print(f"    User.full_name: {appt.patient.user.full_name}")
                print(f"    User.phone_number: {appt.patient.user.phone_number}")
            else:
                print(f"    ✗ User NOT FOUND!")
        else:
            print(f"  ✗ Patient NOT FOUND!")
        
        # Check doctor
        if appt.doctor:
            print(f"  ✓ Doctor found")
            if appt.doctor.user:
                print(f"    Doctor.user.full_name: {appt.doctor.user.full_name}")
            else:
                print(f"    ✗ Doctor User NOT FOUND!")
        else:
            print(f"  ✗ Doctor NOT FOUND!")
        
        print()
    
finally:
    db.close()
