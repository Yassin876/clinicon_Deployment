import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Uuid
from sqlalchemy import JSON
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Uuid(as_uuid=True))
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User")
