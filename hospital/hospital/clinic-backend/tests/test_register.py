import sys
import os
from pydantic import ValidationError
from fastapi import HTTPException

# Add parent directory to path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, SessionLocal, Base
from app.models import User, Patient, Doctor
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService

def run_tests():
    print("🔄 Starting user registration logic verification...")
    
    # 1. Recreate tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Schema built.")

    db = SessionLocal()
    try:
        # Test 1: Successful Patient registration
        print("\n🧪 Test 1: Valid Patient registration...")
        patient_data = UserCreate(
            full_name="عمر مريض تجريبي",
            email="patient.test@example.com",
            phone_number="01087654321",
            role="patient",
            password="SecurePassword123",
            date_of_birth="1995-12-10",
            gender="male",
            address="القاهرة، مصر"
        )
        user_p = AuthService.register_user(db, patient_data)
        print(f"   - User ID: {user_p.id}, Role: {user_p.role}")
        
        # Verify Patient record exists
        patient_record = db.query(Patient).filter(Patient.user_id == user_p.id).first()
        assert patient_record is not None
        assert patient_record.gender == "male"
        print("   ✅ Patient profile created and linked correctly.")

        # Test 2: Successful Doctor registration
        print("\n🧪 Test 2: Valid Doctor registration...")
        doctor_data = UserCreate(
            full_name="د. أحمد طبيب تجريبي",
            email="doctor.test@example.com",
            phone_number="01112223344",
            role="doctor",
            password="DocSecurePassword456",
            specialization="جراحة العظام",
            bio="أخصائي جراحة عظام وخبرة 10 سنوات"
        )
        user_d = AuthService.register_user(db, doctor_data)
        print(f"   - User ID: {user_d.id}, Role: {user_d.role}")
        
        # Verify Doctor record exists
        doctor_record = db.query(Doctor).filter(Doctor.user_id == user_d.id).first()
        assert doctor_record is not None
        assert doctor_record.specialization == "جراحة العظام"
        print("   ✅ Doctor profile created and linked correctly.")

        # Test 3: Uniqueness validation (email duplicate)
        print("\n🧪 Test 3: Duplicate email registration...")
        duplicate_data = UserCreate(
            full_name="مستخدم مكرر",
            email="patient.test@example.com", # Same as Test 1
            phone_number="01200000000",
            role="patient",
            password="PasswordOk999"
        )
        try:
            AuthService.register_user(db, duplicate_data)
            print("   ❌ Failed: Duplicate email was mistakenly allowed.")
            sys.exit(1)
        except HTTPException as e:
            assert e.status_code == 400
            print(f"   ✅ Succeed: Rejected correctly. Detail: {e.detail}")

        # Test 4: Uniqueness validation (phone duplicate)
        print("\n🧪 Test 4: Duplicate phone number registration...")
        duplicate_phone = UserCreate(
            full_name="مستند مكرر هاتف",
            email="phone.unique@example.com",
            phone_number="01087654321", # Same as Test 1
            role="patient",
            password="PasswordOk999"
        )
        try:
            AuthService.register_user(db, duplicate_phone)
            print("   ❌ Failed: Duplicate phone number was mistakenly allowed.")
            sys.exit(1)
        except HTTPException as e:
            assert e.status_code == 400
            print(f"   ✅ Succeed: Rejected correctly. Detail: {e.detail}")

        # Test 5: Pydantic Validation error - Wrong phone format
        print("\n🧪 Test 5: Invalid phone number format...")
        try:
            UserCreate(
                full_name="خطأ هاتف",
                email="phone.error@example.com",
                phone_number="12345", # invalid length
                role="patient",
                password="PasswordOk999"
            )
            print("   ❌ Failed: Invalid phone was mistakenly valid.")
            sys.exit(1)
        except ValidationError as e:
            print("   ✅ Succeed: Pydantic rejected incorrect phone number format.")

        # Test 6: Pydantic Validation error - Weak password
        print("\n🧪 Test 6: Weak password limits...")
        try:
            UserCreate(
                full_name="خطأ كلمة سر",
                email="password.error@example.com",
                role="patient",
                password="123" # too short, no letters
            )
            print("   ❌ Failed: Weak password was mistakenly valid.")
            sys.exit(1)
        except ValidationError as e:
            print("   ✅ Succeed: Pydantic rejected weak password.")

        print("\n🎉 All 6 core registration tests PASSED successfully!")
    finally:
        db.close()
        print("🧹 Test complete. PostgreSQL tables were reset via drop_all/create_all.")

if __name__ == "__main__":
    run_tests()
