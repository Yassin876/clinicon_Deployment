import asyncio
import json
import os
import sys
from datetime import datetime
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi import HTTPException

from app.database import Base, SessionLocal, engine
from app.models.clinic import Clinic
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.core.dependencies import require_clinic_owner
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus
from app.routers.appointments import BookingRequest, book_appointment, get_queue_public


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_clinic_owner_dependency_accepts_string_role():
    current_user = SimpleNamespace(role="clinic_owner")
    resolved_user = require_clinic_owner(current_user=current_user)
    assert resolved_user is current_user


def test_doctor_with_clinic_email_stays_pending_until_approval(db):
    owner = AuthService.register_user(
        db,
        UserCreate(
            full_name="مالك عيادة",
            email="owner@example.com",
            phone_number="01011111111",
            role="clinic_owner",
            password="SecurePassword123",
        ),
    )

    clinic = db.query(Clinic).filter(Clinic.owner_user_id == owner.id).first()
    assert clinic is not None

    doctor = AuthService.register_user(
        db,
        UserCreate(
            full_name="د. أحمد",
            email="doctor@example.com",
            phone_number="01022222222",
            role="doctor",
            password="DoctorPassword123",
            specialization="قلب",
            clinic_email=owner.email,
        ),
    )

    assert doctor.is_active is False
    assert doctor.pending_clinic_id == clinic.id

    with pytest.raises(HTTPException) as excinfo:
        AuthService.login_user(
            db,
            LoginRequest(email="doctor@example.com", password="DoctorPassword123"),
        )

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "حسابك في انتظار موافقة صاحب العيادة"


def test_booking_response_includes_selected_doctor_id(db):
    owner = AuthService.register_user(
        db,
        UserCreate(
            full_name="مالك عيادة",
            email="owner3@example.com",
            phone_number="01088888888",
            role="clinic_owner",
            password="SecurePassword123",
        ),
    )
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == owner.id).first()
    assert clinic is not None

    doctor_user = User(
        full_name="د. منى",
        email="doctor4@example.com",
        password_hash="hash",
        phone_number="01099999999",
        role=UserRole.doctor,
        is_active=True,
    )
    db.add(doctor_user)
    db.flush()

    doctor = Doctor(user_id=doctor_user.id, specialization="قلب")
    db.add(doctor)
    db.flush()

    clinic.doctors.append(doctor)
    db.flush()

    from app.models.doctor import DoctorAvailability
    from datetime import timedelta
    tomorrow = datetime.utcnow() + timedelta(days=1)
    slot_dt = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0, 0)
    availability = DoctorAvailability(
        doctor_id=doctor.id,
        day_of_week=slot_dt.weekday(),
        start_time=datetime.min.time(),
        end_time=datetime.max.time(),
        is_active=True
    )
    db.add(availability)
    db.commit()

    patient_user = User(
        full_name="مريض جديد",
        email="patient_test@example.com",
        password_hash="hash",
        phone_number="01012345678",
        role=UserRole.patient,
        is_active=True,
    )
    db.add(patient_user)
    db.flush()

    patient = Patient(user_id=patient_user.id, clinic_id=clinic.id)
    db.add(patient)
    db.commit()

    response = asyncio.run(
        book_appointment(
            BookingRequest(patient_name="مريض جديد", patient_phone="01012345678", doctor_id=str(doctor.id), slot_datetime=slot_dt),
            db=db,
            current_user=patient_user
        )
    )

    payload = json.loads(response.body.decode())
    assert response.status_code == 201
    assert payload["data"]["doctor_id"] == str(doctor.id)


def test_clinic_owner_queue_only_shows_appointments_for_own_clinic(db):
    owner = AuthService.register_user(
        db,
        UserCreate(
            full_name="مالك عيادة",
            email="owner2@example.com",
            phone_number="01033333333",
            role="clinic_owner",
            password="SecurePassword123",
        ),
    )
    clinic = db.query(Clinic).filter(Clinic.owner_user_id == owner.id).first()
    assert clinic is not None

    doctor_user = User(
        full_name="د. سارة",
        email="doctor2@example.com",
        password_hash="hash",
        phone_number="01044444444",
        role=UserRole.doctor,
        is_active=True,
    )
    db.add(doctor_user)
    db.flush()

    doctor = Doctor(user_id=doctor_user.id, specialization="قلب")
    db.add(doctor)
    db.flush()

    clinic.doctors.append(doctor)
    db.flush()

    other_doctor_user = User(
        full_name="د. علي",
        email="doctor3@example.com",
        password_hash="hash",
        phone_number="01055555555",
        role=UserRole.doctor,
        is_active=True,
    )
    db.add(other_doctor_user)
    db.flush()

    other_doctor = Doctor(user_id=other_doctor_user.id, specialization="باطنة")
    db.add(other_doctor)
    db.flush()

    patient_user = User(
        full_name="مريض 1",
        email="patient1@example.com",
        password_hash="hash",
        phone_number="01066666666",
        role=UserRole.patient,
        is_active=True,
    )
    db.add(patient_user)
    db.flush()

    patient = Patient(user_id=patient_user.id)
    db.add(patient)
    db.flush()

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=datetime.utcnow(),
        status=AppointmentStatus.pending,
    )
    db.add(appointment)
    db.flush()

    other_patient_user = User(
        full_name="مريض 2",
        email="patient2@example.com",
        password_hash="hash",
        phone_number="01077777777",
        role=UserRole.patient,
        is_active=True,
    )
    db.add(other_patient_user)
    db.flush()

    other_patient = Patient(user_id=other_patient_user.id)
    db.add(other_patient)
    db.flush()

    other_appointment = Appointment(
        patient_id=other_patient.id,
        doctor_id=other_doctor.id,
        appointment_date=datetime.utcnow(),
        status=AppointmentStatus.pending,
    )
    db.add(other_appointment)
    db.commit()

    current_user = SimpleNamespace(id=owner.id, role="clinic_owner")
    result = asyncio.run(get_queue_public(db=db, current_user=current_user))

    assert result["success"] is True
    assert result["data"]["totalPatients"] == 1

