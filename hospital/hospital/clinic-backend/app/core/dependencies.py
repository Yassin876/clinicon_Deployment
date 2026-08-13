import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core import security
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _normalize_role(role):
    if isinstance(role, UserRole):
        return role
    if isinstance(role, str):
        try:
            return UserRole(role)
        except ValueError:
            return role
    return role


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """يفك الـ JWT Token ويرجع اليوزر المرتبط به من قاعدة البيانات"""
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="التوكن غير صالح أو منتهي الصلاحية",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="توكن غير صالح")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="توكن غير صالح")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="المستخدم غير موجود")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="الحساب غير مفعّل")
    return user


def require_patient(current_user: User = Depends(get_current_user)) -> User:
    """يتأكد أن اليوزر الحالي مريض"""
    if _normalize_role(current_user.role) != UserRole.patient:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذا الإجراء مخصص للمرضى فقط")
    return current_user


def require_doctor(current_user: User = Depends(get_current_user)) -> User:
    """يتأكد أن اليوزر الحالي طبيب"""
    if _normalize_role(current_user.role) != UserRole.doctor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذا الإجراء مخصص للأطباء فقط")
    return current_user


def require_lab(current_user: User = Depends(get_current_user)) -> User:
    """يتأكد أن اليوزر معمل تحاليل"""
    if _normalize_role(current_user.role) != UserRole.lab:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذا الإجراء مخصص لمعامل التحاليل فقط")
    return current_user


def require_clinic_owner(current_user: User = Depends(get_current_user)) -> User:
    """يتأكد أن اليوزر صاحب عيادة"""
    if _normalize_role(current_user.role) != UserRole.clinic_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذا الإجراء مخصص لأصحاب العيادات فقط")
    return current_user
