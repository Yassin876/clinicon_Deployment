import uuid
from sqlalchemy import Column, Text, ForeignKey, DateTime, Date, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Visit(Base):
    __tablename__ = 'visits'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey('patients.id'), nullable=False)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey('doctors.id'), nullable=False)
    appointment_id = Column(Uuid(as_uuid=True), ForeignKey('appointments.id', ondelete='SET NULL'), unique=True)
    visit_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    chief_complaint = Column(Text)
    diagnosis = Column(Text)
    doctor_notes = Column(Text)
    follow_up_date = Column(Date)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="visits")
    doctor = relationship("Doctor", back_populates="visits")
    appointment = relationship("Appointment", back_populates="visit")
    medications = relationship("Medication", back_populates="visit")
    medical_files = relationship("MedicalFile", back_populates="visit")
