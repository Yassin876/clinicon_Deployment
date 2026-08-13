import uuid
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.medical_record import Visit
from app.schemas.visit import VisitCreate, VisitUpdate


class VisitService:
    def __init__(self, db: Session):
        self.db = db

    def create_visit(self, data: VisitCreate) -> Visit:
        visit = Visit(
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            appointment_id=data.appointment_id,
            visit_date=data.visit_date,
            chief_complaint=data.chief_complaint,
            diagnosis=data.diagnosis,
            doctor_notes=data.doctor_notes,
            follow_up_date=data.follow_up_date,
        )
        self.db.add(visit)
        self.db.flush()
        self.db.refresh(visit)
        return visit

    def get_visits_by_patient(self, patient_id: uuid.UUID) -> List[Visit]:
        return (
            self.db.query(Visit)
            .filter(Visit.patient_id == patient_id)
            .order_by(Visit.visit_date.desc())
            .all()
        )

    def update_visit(self, visit_id: uuid.UUID, data: VisitUpdate) -> Visit:
        visit = self.db.query(Visit).filter(Visit.id == visit_id).first()
        if not visit:
            raise HTTPException(status_code=404, detail="الزيارة غير موجودة")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(visit, key, value)
        self.db.flush()
        self.db.refresh(visit)
        return visit
