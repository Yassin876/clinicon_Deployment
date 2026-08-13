import enum
import uuid
from sqlalchemy import Column, String, Text, Date, DateTime, Boolean, BigInteger, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class GenderType(str, enum.Enum):
    male = 'male'
    female = 'female'

class Patient(Base):
    __tablename__ = 'patients'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    date_of_birth = Column(Date)
    gender = Column(Enum(GenderType, name='gender_type', native_enum=False))
    address = Column(Text)
    blood_type = Column(String(3))
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(30))
    telegram_chat_id = Column(BigInteger)
    telegram_notif_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="patient_profile")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    allergies = relationship("Allergy", back_populates="patient", cascade="all, delete-orphan")
    chronic_diseases = relationship("ChronicDisease", back_populates="patient", cascade="all, delete-orphan")
    notes = relationship("PatientNote", back_populates="patient", cascade="all, delete-orphan")
    visits = relationship("Visit", back_populates="patient")
    notifications = relationship("Notification", back_populates="patient", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="patient")
    medical_files = relationship("MedicalFile", back_populates="patient")

class Allergy(Base):
    __tablename__ = 'allergies'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    allergy_name = Column(String(150), nullable=False)
    severity = Column(String(20))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patient = relationship("Patient", back_populates="allergies")

class ChronicDisease(Base):
    __tablename__ = 'chronic_diseases'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    disease_name = Column(String(150), nullable=False)
    diagnosed_at = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patient = relationship("Patient", back_populates="chronic_diseases")

class PatientNote(Base):
    __tablename__ = 'patient_notes'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey('patients.id'), nullable=False)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey('doctors.id'), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patient = relationship("Patient", back_populates="notes")
    doctor = relationship("Doctor", back_populates="patient_notes")

class NotificationType(str, enum.Enum):
    reminder = 'Reminder'
    doctor_changed = 'Doctor Changed'
    appointment_rescheduled = 'Appointment Rescheduled'
    appointment_cancelled = 'Appointment Cancelled'

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey('patients.id'), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50))
    status = Column(String(30))

    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patient = relationship("Patient", back_populates="notifications")
