import uuid
from sqlalchemy import Column, String, Text, BigInteger, ForeignKey, DateTime, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class MedicalFile(Base):
    __tablename__ = 'medical_files'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey('patients.id'), nullable=False)
    visit_id = Column(Uuid(as_uuid=True), ForeignKey('visits.id', ondelete='SET NULL'))
    uploaded_by_user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id'))
    category = Column(String(50))
    file_name = Column(String(255))
    file_url = Column(Text)
    mime_type = Column(String(100))
    file_size = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="medical_files")
    visit = relationship("Visit", back_populates="medical_files")
    uploaded_by = relationship("User")
