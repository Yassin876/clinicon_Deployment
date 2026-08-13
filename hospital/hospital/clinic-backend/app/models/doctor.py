import uuid
from sqlalchemy import Column, String, Text, SmallInteger, Time, Boolean, ForeignKey, CheckConstraint, DateTime, Uuid, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Doctor(Base):
    __tablename__ = 'doctors'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    clinic_id = Column(Uuid(as_uuid=True), ForeignKey('clinics.id', ondelete='SET NULL'), nullable=True)
    specialization = Column(String(150), nullable=False)
    slot_duration_minutes = Column(Integer, default=15, nullable=False)
    bio = Column(Text)
    location_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="doctor_profile")
    clinic = relationship("Clinic", back_populates="doctors", foreign_keys=[clinic_id])
    availabilities = relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")
    leaves = relationship("DoctorLeave", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")
    visits = relationship("Visit", back_populates="doctor")
    patient_notes = relationship("PatientNote", back_populates="doctor")
    prescribed_medications = relationship("Medication", back_populates="prescribed_by_doctor")

class DoctorAvailability(Base):
    __tablename__ = 'doctor_availability'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    day_of_week = Column(SmallInteger)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('start_time < end_time', name='check_start_time_before_end_time'),
    )

    doctor = relationship("Doctor", back_populates="availabilities")

class DoctorLeave(Base):
    __tablename__ = 'doctor_leave'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    leave_date = Column(DateTime(timezone=True), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="leaves")

