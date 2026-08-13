import sys
import os
from datetime import date, time, datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import create_app
from app.database import engine, Base, SessionLocal
from app.models import User, Patient, Doctor, UserRole
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate

app = create_app()
client = TestClient(app)

def run_full_scenario():
    print("=" * 60)
    print("🧪 بدء سيناريو الاختبار الشامل للنظام (Full E2E Test Scenario)")
    print("=" * 60)

    # 1. إعادات تهيئة قاعدة البيانات
    print("\n1️⃣ إعادة بناء جداول قاعدة البيانات...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ تم بناء الجداول بنجاح.")

    db = SessionLocal()

    # 2. إنشاء حسابات الأدوار الثلاثة (أدمن، طبيب، مريض)
    print("\n2️⃣ إنشاء حسابات النظام (أدمن، طبيب، مريض)...")

    # أدمن
    admin_user = AuthService.register_user(db, UserCreate(
        full_name="د. أحمد الأدمن",
        email="admin@clinic.com",
        phone_number="01000000000",
        role="admin",
        password="AdminPassword123"
    ))
    admin_user.is_active = True

    # طبيب
    doctor_user = AuthService.register_user(db, UserCreate(
        full_name="د. إبراهيم علي (أخصائي العظام)",
        email="doctor@clinic.com",
        phone_number="01111111111",
        role="doctor",
        password="DoctorPassword123",
        specialization="عظام"
    ))
    doctor_user.is_active = True

    # مريض
    patient_user = AuthService.register_user(db, UserCreate(
        full_name="عمر أحمد المريض",
        email="patient@clinic.com",
        phone_number="01222222222",
        role="patient",
        password="PatientPassword123",
        date_of_birth="1995-05-15",
        gender="male",
        address="القاهرة"
    ))
    patient_user.is_active = True

    db.commit()

    doctor_obj = db.query(Doctor).filter(Doctor.user_id == doctor_user.id).first()
    patient_obj = db.query(Patient).filter(Patient.user_id == patient_user.id).first()

    print(f"   ✅ تم إنشاء الأدمن ID: {admin_user.id}")
    print(f"   ✅ تم إنشاء الطبيب ID: {doctor_obj.id} ({doctor_user.full_name})")
    print(f"   ✅ تم إنشاء المريض ID: {patient_obj.id} ({patient_user.full_name})")

    # 3. تسجيل دخول المريض وتصفح الأطباء والحجز
    print("\n3️⃣ رحلة المريض: تسجيل الدخول، تصفح الأطباء، وحجز موعد...")

    # تسجيل دخول المريض
    login_res = client.post("/api/auth/login", json={
        "email": "patient@clinic.com",
        "password": "PatientPassword123"
    })
    assert login_res.status_code == 200, f"فشل دخول المريض: {login_res.text}"
    patient_token = login_res.json()["access_token"]
    patient_headers = {"Authorization": f"Bearer {patient_token}"}
    print("   ✅ تم تسجيل دخول المريض بنجاح والحصول على JWT Token.")

    # تصفح قائمة الأطباء
    docs_res = client.get("/api/doctors")
    assert docs_res.status_code == 200
    doctors_list = docs_res.json()["data"]
    print(f"   ✅ المريض يتصفح الأطباء: تم العثور على {len(doctors_list)} طبيب (التخصص: {doctors_list[0]['specialization']}).")

    # حجز موعد مع الطبيب
    book_res = client.post("/api/book", json={
        "name": patient_user.full_name,
        "phone": patient_user.phone_number,
        "doctor_id": str(doctor_obj.id)
    })
    assert book_res.status_code in (200, 201), f"فشل الحجز: {book_res.text}"
    booking_data = book_res.json()["data"]
    print(f"   ✅ تم الحجز بنجاح! رقم الدور: {booking_data['queueNumber']} | الوقت المتوقع: {booking_data['estimatedTime']}")

    # 4. المريض يضيف دواء وتذكير
    print("\n4️⃣ المريض يضيف دواء وتذكير بالجرعة...")
    med_res = client.post("/api/medications/", json={
        "patient_id": str(patient_obj.id),
        "medicine_name": "بانادول إكسترا",
        "dosage": "قرصين بعد الأكل",
        "frequency": "مرتين يومياً",
        "is_active": True
    }, headers=patient_headers)
    assert med_res.status_code == 201, f"فشل إضافة الدواء: {med_res.text}"
    med_data = med_res.json()
    print(f"   ✅ تم إضافة الدواء بنجاح: {med_data['medicine_name']} (ID: {med_data['id']})")

    # إضافة تذكير
    rem_res = client.post(f"/api/medications/{med_data['id']}/reminders", json=[
        {"reminder_time": "20:00:00", "is_active": True}
    ], headers=patient_headers)
    assert rem_res.status_code == 200
    print("   ✅ تم إضافة تذكير التليجرام الساعة 20:00 بنجاح.")

    # 5. رحلة الطبيب: تسجيل الدخول ومتابعة الدور وتسجيل الزيارة والملاحظات
    print("\n5️⃣ رحلة الطبيب: تسجيل الدخول والإشراف على الكشف...")
    doc_login = client.post("/api/auth/login", json={
        "email": "doctor@clinic.com",
        "password": "DoctorPassword123"
    })
    assert doc_login.status_code == 200
    doctor_token = doc_login.json()["access_token"]
    doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
    print("   ✅ تم تسجيل دخول الطبيب وحصوله على JWT Token.")

    # الطبيب يشوف قائمة المرضى
    patients_res = client.get("/api/patients", headers=doctor_headers)
    assert patients_res.status_code == 200
    print(f"   ✅ الطبيب يتصفح مرضى اليوم: وجد {len(patients_res.json()['data'])} مريض في الانتظار.")

    # الطبيب يعلم الكشف كـ "مكتمل"
    appointment_id = booking_data["id"]
    done_res = client.put(f"/api/patient/{appointment_id}/done", headers=doctor_headers)
    assert done_res.status_code == 200
    print("   ✅ الطبيب قام بإنهاء الكشف وتغيير الحالة إلى 'تم الكشف'.")

    # الطبيب يسجل بيانات الزيارة الطبية
    visit_res = client.post("/api/visits/", json={
        "patient_id": str(patient_obj.id),
        "doctor_id": str(doctor_obj.id),
        "appointment_id": str(appointment_id),
        "chief_complaint": "ألم حاد في المفصل عند الصعود",
        "diagnosis": "التهاب بالمفاصل مع خشونة خفيفة",
        "doctor_notes": "راحة أسبوع مع كمادات دافئة"
    }, headers=doctor_headers)
    assert visit_res.status_code == 201, f"فشل تسجيل الزيارة: {visit_res.text}"
    print("   ✅ تم تسجيل الزيارة والتشخيص الطبي بنجاح.")

    # الطبيب يضيف ملاحظة سرية خاصة على المريض
    note_res = client.post("/api/patient-notes/", json={
        "patient_id": str(patient_obj.id),
        "doctor_id": str(doctor_obj.id),
        "note": "ملاحظة سرية: المريض لديه حساسية خفيفة من مشتقات السلفا"
    }, headers=doctor_headers)
    assert note_res.status_code == 201
    print("   ✅ تم إضافة الملاحظة الطبية السرية بنجاح.")

    # 6. اختبار حماية الصلاحيات (RBAC Verification)
    print("\n6️⃣ اختبار حماية الصلاحيات (RBAC Verification)...")
    
    # المريض يحاول قراءة قائمة مرضى اليوم والانتظار -> يجب أن يُمنع (403 Forbidden)
    patients_forbidden = client.get("/api/patients", headers=patient_headers)
    assert patients_forbidden.status_code == 403, f"المريض يجب أن يمنع من مشاهدة مرضى اليوم: {patients_forbidden.text}"
    print("   🔒 [نجاح حماية RBAC]: المريض مُنع بنجاح من رؤية قائمة مرضى العيادة والانتظار (403 Forbidden).")

    # المريض يحاول الوصول لملاحظات الطبيب السرية -> يجب أن يُمنع (403 Forbidden)
    forbidden_res = client.get(f"/api/patient-notes/patient/{patient_obj.id}", headers=patient_headers)
    assert forbidden_res.status_code == 403
    print("   🔒 [نجاح حماية RBAC]: المريض مُنع بنجاح من رؤية ملاحظات الطبيب السرية (403 Forbidden).")

    # المريض يقرأ أدويته -> مسموح
    meds_check = client.get("/api/medications/", headers=patient_headers)
    assert meds_check.status_code == 200
    print(f"   ✅ المريض يقرأ قائمة أدويته الحالية بنجاح (عدد الأدويـة: {len(meds_check.json())}).")

    # 7. رحلة الأدمن: لوحة التحكم وسجلات التدقيق
    print("\n7️⃣ رحلة الأدمن: لوحة التحكم والاطلاع على سجلات التدقيق (Audit Logs)...")
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@clinic.com",
        "password": "AdminPassword123"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    users_res = client.get("/api/admin/users", headers=admin_headers)
    assert users_res.status_code == 200
    print(f"   ✅ الأدمن يشوف قائمة جميع المستخدمين: {len(users_res.json())} مستخدمين.")

    logs_res = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert logs_res.status_code == 200
    print(f"   ✅ الأدمن يتصفح الـ Audit Logs (سجلات التدقيق الأمني).")

    print("\n" + "=" * 60)
    print("🎉 تم اجتياز جميع اختبارات السيناريو الشامل بنجاح 100%!")
    print("=" * 60)

if __name__ == "__main__":
    run_full_scenario()
