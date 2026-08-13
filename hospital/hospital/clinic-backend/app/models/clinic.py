import uuid
from sqlalchemy import Column, String, Text, DateTime, Uuid, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Clinic(Base):
    __tablename__ = 'clinics'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_name = Column(String(200), nullable=False)
    address = Column(Text)
    phone = Column(String(30))
    location_url = Column(Text, nullable=True)
    specializations = Column(Text)  # comma-separated, e.g. "cardiology,orthopedics"
    owner_user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", foreign_keys=[owner_user_id])
    doctors = relationship("Doctor", back_populates="clinic")
    labs = relationship("LabEntity", back_populates="clinic", cascade="all, delete-orphan")


class LabEntity(Base):
    """معمل تحاليل مرتبط بعيادة وبحساب User"""
    __tablename__ = 'lab_entities'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=True)
    clinic_id = Column(Uuid(as_uuid=True), ForeignKey('clinics.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(200), nullable=False)
    contact_info = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    clinic = relationship("Clinic", back_populates="labs")
    user = relationship("User", foreign_keys=[user_id])
