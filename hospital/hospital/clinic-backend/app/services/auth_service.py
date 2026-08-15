from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.schemas.user import UserCreate
from app.schemas.auth import LoginRequest, TokenResponse
from app.core import security


def _resolve_pending_clinic(db: Session, details: UserCreate):
    if details.role not in {UserRole.doctor, UserRole.lab, UserRole.patient}:
        return None

    if not details.clinic_email:
        if details.role == UserRole.patient:
            raise HTTPException(
                status_code=400,
                detail="يجب إدخال البريد الإلكتروني للعيادة المسجل بها المريض"
            )
        return None

    from app.models.clinic import Clinic

    clinic = (
        db.query(Clinic)
        .join(User, Clinic.owner_user_id == User.id)
        .filter(User.email == details.clinic_email.strip())
        .first()
    )

    if not clinic:
        raise HTTPException(
            status_code=400,
            detail=f"لم يتم العثور على عيادة مسجلة بالبريد الإلكتروني '{details.clinic_email}'"
        )

    return clinic

class AuthService:
    @staticmethod
    def register_user(db: Session, details: UserCreate, force_active: bool | None = None) -> User:
        # Check email uniqueness
        existing_email_user = db.query(User).filter(User.email == details.email).first()
        if existing_email_user:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني مسجل بالفعل")

        # Check phone uniqueness (if phone number is provided)
        if details.phone_number:
            existing_phone_user = db.query(User).filter(User.phone_number == details.phone_number).first()
            if existing_phone_user:
                raise HTTPException(status_code=400, detail="رقم الهاتف مسجل بالفعل")

        # Hash password first (outside transaction) to catch bcrypt errors early
        try:
            password_hash = security.get_password_hash(details.password)
        except Exception as hash_err:
            raise HTTPException(status_code=400, detail=f"خطأ في كلمة المرور: {str(hash_err)}")

        # Atomic transaction context
        try:
            pending_clinic = _resolve_pending_clinic(db, details) if force_active is not True else None
            # Patients are active immediately but linked to the clinic via pending_clinic
            is_active_initial = True if force_active is True else (False if (pending_clinic and details.role != UserRole.patient) else True)

            # Create User
            user = User(
                full_name=details.full_name,
                email=details.email,
                password_hash=password_hash,
                phone_number=details.phone_number,
                role=details.role,
                is_active=is_active_initial,
                pending_clinic_id=pending_clinic.id if (pending_clinic and details.role != UserRole.patient) else None
            )
            db.add(user)
            db.flush()  # Extract created user ID

            # Create specific profiles
            if details.role == UserRole.patient:
                patient = Patient(
                    user_id=user.id,
                    clinic_id=pending_clinic.id if pending_clinic else None,
                    date_of_birth=details.date_of_birth,
                    gender=details.gender,
                    address=details.address,
                    blood_type=details.blood_type,
                    emergency_contact_name=details.emergency_contact_name,
                    emergency_contact_phone=details.emergency_contact_phone
                )
                db.add(patient)
            elif details.role == UserRole.doctor:
                doctor = Doctor(
                    user_id=user.id,
                    clinic_id=pending_clinic.id if pending_clinic else None,
                    specialization=details.specialization or "عام",
                    bio=details.bio,
                    location_url=details.location_url
                )
                db.add(doctor)
                db.flush()

                from app.models.doctor import DoctorAvailability
                from datetime import time

                # Provide default schedule (Sat-Thu, 09:00 - 17:00) if no availabilities passed
                avail_list = details.availabilities
                if not avail_list or len(avail_list) == 0:
                    avail_list = [
                        {'day_of_week': d, 'start_time': '09:00', 'end_time': '17:00'}
                        for d in [5, 6, 0, 1, 2, 3]
                    ]

                day_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6,
                    'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6,
                }

                for avail in avail_list:
                    dow = avail.get('day_of_week') if isinstance(avail, dict) else getattr(avail, 'day_of_week', None)
                    st = avail.get('start_time') if isinstance(avail, dict) else getattr(avail, 'start_time', None)
                    et = avail.get('end_time') if isinstance(avail, dict) else getattr(avail, 'end_time', None)

                    if isinstance(dow, str):
                        dow_lower = dow.strip().lower()
                        if dow_lower in day_map:
                            dow = day_map[dow_lower]
                        elif dow.isdigit():
                            dow = int(dow)
                        else:
                            dow = 0
                    elif not isinstance(dow, int):
                        dow = 0

                    if isinstance(st, str):
                        st_parts = [int(x) for x in st.split(':')]
                        st = time(st_parts[0], st_parts[1])
                    if isinstance(et, str):
                        et_parts = [int(x) for x in et.split(':')]
                        et = time(et_parts[0], et_parts[1])

                    avail_record = DoctorAvailability(
                        doctor_id=doctor.id,
                        day_of_week=dow,
                        start_time=st,
                        end_time=et,
                        is_active=True
                    )
                    db.add(avail_record)
            elif details.role == UserRole.lab:
                from app.models.clinic import LabEntity
                if not pending_clinic:
                    raise HTTPException(
                        status_code=400,
                        detail="يجب إدخال بريد صاحب العيادة للتسجيل كمعمل تحاليل"
                    )
                lab = LabEntity(
                    user_id=user.id,
                    clinic_id=pending_clinic.id,
                    name=details.full_name,
                    contact_info=details.phone_number
                )
                db.add(lab)
            elif details.role == UserRole.clinic_owner:
                from app.models.clinic import Clinic
                clinic = Clinic(
                    clinic_name=details.full_name,
                    address=details.address,
                    phone=details.phone_number,
                    location_url=details.location_url,
                    specializations=details.specialization,
                    owner_user_id=user.id
                )
                db.add(clinic)

            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"حدث خطأ في قاعدة البيانات أثناء التسجيل: {str(e)}")

    @staticmethod
    def login_user(db: Session, credentials: LoginRequest) -> TokenResponse:
        # Find user by email
        user = db.query(User).filter(User.email == credentials.email).first()

        # Verify email exists AND password matches
        if not user or not security.verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if not user.is_active:
            raise HTTPException(status_code=403, detail="حسابك في انتظار موافقة صاحب العيادة")

        # Get doctor_id if the user is a doctor
        doctor_id = None
        if user.role == UserRole.doctor:
            from app.models.doctor import Doctor
            doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
            if doctor:
                doctor_id = doctor.id

        # Create JWT containing user identity
        token = security.create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        })

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=user.id,
            full_name=user.full_name,
            role=user.role,
            email=user.email,
            doctor_id=doctor_id
        )
