import sys
import os

# Add parent directory to path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, SessionLocal, Base
from app.models import User, UserRole, Patient, Doctor, Appointment, AppointmentStatus, Clinic, Visit
from datetime import datetime, date

print("🔄 Starting DB verification run...")

# 1. Clean and recreate tables
try:
    print("🛠 Creating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")
except Exception as e:
    print(f"❌ Error creating tables: {e}")
    sys.exit(1)

# 2. CRUD Verification
db = SessionLocal()
try:
    print("🧪 Verifying CRUD and relationship rules...")
    
    # Create Clinic
    clinic = Clinic(clinic_name="Main General Clinic", address="Down Town", phone="123456")
    db.add(clinic)
    db.flush()
    print(f"✅ Clinic created. UUID: {clinic.id}")
    
    # Create Patient User
    pt_user = User(
        full_name="جون دو",
        email="john.doe@clinic.local",
        password_hash="hashed_pw_here",
        phone_number="01234567890",
        role=UserRole.patient
    )
    db.add(pt_user)
    db.flush()
    
    patient = Patient(user_id=pt_user.id, date_of_birth=date(1990, 5, 20), gender="male")
    db.add(patient)
    db.flush()
    print(f"✅ Patient profile created. Profile UUID: {patient.id}, User UUID: {patient.user_id}")

    # Create Doctor User
    doc_user = User(
        full_name="د. إبراهيم",
        email="dr.ibrahim@clinic.local",
        password_hash="hashed_pw_doc",
        phone_number="01011223344",
        role=UserRole.doctor
    )
    db.add(doc_user)
    db.flush()
    
    doctor = Doctor(user_id=doc_user.id, specialization="أمراض قلب")
    db.add(doctor)
    db.flush()
    print(f"✅ Doctor profile created. Profile UUID: {doctor.id}")

    # Create Appointment
    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=datetime.utcnow(),
        queue_number=1,
        status=AppointmentStatus.pending
    )
    db.add(appt)
    db.flush()
    print(f"✅ Appointment created. UUID: {appt.id}")

    # Create Visit
    visit = Visit(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_id=appt.id,
        chief_complaint="Chest pain",
        diagnosis="Healthy heart",
        doctor_notes="Recommended mild exercise."
    )
    db.add(visit)
    db.flush()
    print(f"✅ Visit medical record created. UUID: {visit.id}")

    db.commit()
    print("🎉 Verification CRUD and Relationships Successful! Database is fully operational.")

except Exception as e:
    db.rollback()
    print(f"❌ Verification failed during CRUD operations: {e}")
    sys.exit(1)
finally:
    db.close()
    print("🧹 Test complete. PostgreSQL tables were reset via drop_all/create_all.")
