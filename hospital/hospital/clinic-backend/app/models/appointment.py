import enum
import uuid
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime, Uuid, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class AppointmentStatus(str, enum.Enum):
    pending = 'pending'
    confirmed = 'confirmed'
    rescheduled = 'rescheduled'
    cancelled_by_doctor = 'cancelled_by_doctor'
    cancelled_by_patient = 'cancelled_by_patient'
    completed = 'completed'
    cancelled = 'cancelled'


class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey('doctors.id', ondelete='RESTRICT'), nullable=False)
    appointment_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Enum(AppointmentStatus, name='appointment_status', native_enum=False), default=AppointmentStatus.pending)
    patient_name = Column(String(200), nullable=True)   # الاسم المدخل وقت الحجز
    patient_phone = Column(String(50), nullable=True)    # الهاتف المدخل وقت الحجز
    notes = Column(Text)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('doctor_id', 'appointment_date', name='uq_doctor_slot'),
    )

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    visit = relationship("Visit", back_populates="appointment", uselist=False)
