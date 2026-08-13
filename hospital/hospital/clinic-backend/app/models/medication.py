import uuid
from sqlalchemy import Column, String, Date, Boolean, ForeignKey, Time, CheckConstraint, DateTime, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Medication(Base):
    __tablename__ = 'medications'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey('patients.id'), nullable=False)
    visit_id = Column(Uuid(as_uuid=True), ForeignKey('visits.id', ondelete='SET NULL'))
    prescribed_by = Column(Uuid(as_uuid=True), ForeignKey('doctors.id'))
    medicine_name = Column(String(200), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    start_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('end_date IS NULL OR start_date IS NULL OR end_date >= start_date', name='check_medication_dates'),
    )

    # Relationships
    patient = relationship("Patient", back_populates="medications")
    visit = relationship("Visit", back_populates="medications")
    prescribed_by_doctor = relationship("Doctor", back_populates="prescribed_medications")
    reminders = relationship("MedicationReminder", back_populates="medication", cascade="all, delete-orphan")

class MedicationReminder(Base):
    __tablename__ = 'medication_reminders'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medication_id = Column(Uuid(as_uuid=True), ForeignKey('medications.id', ondelete='CASCADE'), nullable=False)
    reminder_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    medication = relationship("Medication", back_populates="reminders")
