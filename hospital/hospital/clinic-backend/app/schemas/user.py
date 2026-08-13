from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from datetime import date, datetime
from typing import Optional
from uuid import UUID
import re

from app.models.user import UserRole
from app.models.patient import GenderType

class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    role: UserRole

class UserCreate(UserBase):
    password: str
    clinic_email: Optional[EmailStr] = None
    
    # Optional patient profiling details
    date_of_birth: Optional[date] = None
    gender: Optional[GenderType] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    # Optional doctor profiling details
    specialization: Optional[str] = None
    bio: Optional[str] = None
    location_url: Optional[str] = None
    availabilities: Optional[list] = None


    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('كلمة المرور لازم تكون 8 حروف على الأقل')
        if not any(c.isalpha() for c in v):
            raise ValueError('كلمة المرور لازم فيها حرف واحد على الأقل (عربي أو إنجليزي)')
        if not re.search(r'\d', v):
            raise ValueError('كلمة المرور لازم فيها رقم واحد على الأقل')
        # Truncate to 72 bytes for bcrypt safety
        encoded = v.encode('utf-8')
        if len(encoded) > 72:
            v = encoded[:72].decode('utf-8', 'ignore')
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_egypt_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        phone_clean = re.sub(r'[^\d]', '', v)
        if not re.match(r'^01[0-25-9]\d{8}$', phone_clean):
            raise ValueError('رقم الهاتف غير صالح، يجب أن يكون 11 رقماً ويبدأ بـ 01 (مثل 01012345678)')
        return phone_clean

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
