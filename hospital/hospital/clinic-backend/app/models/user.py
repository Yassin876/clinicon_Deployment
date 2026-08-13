import enum
import uuid
from sqlalchemy import Column, String, DateTime, Enum, Boolean, Uuid, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class UserRole(str, enum.Enum):
    patient = 'patient'
    doctor = 'doctor'
    lab = 'lab'
    clinic_owner = 'clinic_owner'

class User(Base):
    __tablename__ = 'users'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String(30), unique=True)
    role = Column(Enum(UserRole, name='user_role', native_enum=False), nullable=False, default=UserRole.patient)
    is_active = Column(Boolean, default=True)
    pending_clinic_id = Column(Uuid(as_uuid=True), ForeignKey('clinics.id', use_alter=True, name='fk_user_pending_clinic', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient_profile = relationship("Patient", back_populates="user", uselist=False)
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)
    pending_clinic = relationship("Clinic", foreign_keys=[pending_clinic_id])
