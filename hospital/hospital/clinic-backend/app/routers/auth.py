from typing import Optional
from fastapi import APIRouter, Depends, status, Request, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: Session = Depends(get_db)):
    """تسجيل مستخدم جديد (مريض أو طبيب أو مسؤول)"""
    return AuthService.register_user(db=db, details=payload)

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    تسجيل الدخول والحصول على JWT Token
    يدعم إرسال JSON أو Form-Data من زر Authorize 🔓 في Swagger UI
    """
    if username and password:
        credentials = LoginRequest(email=username, password=password)
    else:
        try:
            json_data = await request.json()
            email = json_data.get("email") or json_data.get("username")
            pass_val = json_data.get("password")
            credentials = LoginRequest(email=email, password=pass_val)
        except Exception:
            raise HTTPException(status_code=422, detail="بيانات تسجيل الدخول غير صالحة")

    return AuthService.login_user(db=db, credentials=credentials)

@router.get("/verify-token")
async def verify_token():
    return {"message": "Verify token endpoint stub"}
