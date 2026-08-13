from app.schemas.user import UserBase, UserCreate, UserResponse
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.patient import (
    PatientBase, PatientCreate, PatientResponse,
    AllergyBase, AllergyResponse,
    ChronicDiseaseBase, ChronicDiseaseResponse,
    PatientNoteBase, PatientNoteResponse,
    NotificationBase, NotificationResponse
)
from app.schemas.doctor import DoctorBase, DoctorCreate, DoctorResponse, DoctorAvailabilityBase, DoctorAvailabilityResponse
from app.schemas.appointment import AppointmentBase, AppointmentCreate, AppointmentResponse
from app.schemas.medical_record import VisitBase, VisitCreate, VisitResponse
from app.schemas.file import MedicalFileBase, MedicalFileResponse
from app.schemas.medication import MedicationBase, MedicationCreate, MedicationResponse
from app.schemas.medication_reminder import MedicationReminderBase, MedicationReminderResponse

__all__ = [
    'UserBase', 'UserCreate', 'UserResponse',
    'LoginRequest', 'TokenResponse',
    'PatientBase', 'PatientCreate', 'PatientResponse',
    'AllergyBase', 'AllergyResponse',
    'ChronicDiseaseBase', 'ChronicDiseaseResponse',
    'PatientNoteBase', 'PatientNoteResponse',
    'NotificationBase', 'NotificationResponse',
    'DoctorBase', 'DoctorCreate', 'DoctorResponse', 'DoctorAvailabilityBase', 'DoctorAvailabilityResponse',
    'AppointmentBase', 'AppointmentCreate', 'AppointmentResponse',
    'VisitBase', 'VisitCreate', 'VisitResponse',
    'MedicalFileBase', 'MedicalFileResponse',
    'MedicationBase', 'MedicationCreate', 'MedicationResponse', 'MedicationReminderBase', 'MedicationReminderResponse',
]
