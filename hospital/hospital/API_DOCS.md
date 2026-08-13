# 📋 Clinic Backend — API Documentation

**Base URL:** `http://localhost:5000/api`  
**Swagger UI:** `http://localhost:5000/docs`  
**ReDoc:** `http://localhost:5000/redoc`  
**Auth:** Bearer JWT Token في الهيدر → `Authorization: Bearer <token>`

---

## 📑 فهرس سريع — كل الـ Endpoints

| # | Method | Path | Auth | الوصف |
|---|--------|------|:----:|-------|
| 1 | GET | `/api/health` | ❌ | فحص حالة الخادم |
| 2 | POST | `/api/auth/register` | ❌ | تسجيل مستخدم جديد |
| 3 | POST | `/api/auth/login` | ❌ | تسجيل الدخول |
| 4 | GET | `/api/auth/verify-token` | ❌ | التحقق من التوكن (stub) |
| 5 | GET | `/api/doctors` | ❌ | قائمة الأطباء |
| 6 | POST | `/api/book` | ❌ | حجز موعد / طابور |
| 7 | GET | `/api/patients` | ✅ Doctor/Admin | طابور اليوم |
| 8 | GET | `/api/stats` | ✅ Doctor/Admin | إحصائيات اليوم |
| 9 | PUT | `/api/patient/{appointment_id}/done` | ✅ Doctor/Admin | إنهاء كشف مريض |
| 10 | DELETE | `/api/patients` | ✅ Admin | مسح كل الحجوزات |
| 11 | POST | `/api/medications/` | ✅ Patient | إضافة دواء |
| 12 | GET | `/api/medications/` | ✅ Patient | أدوية المريض الحالي |
| 13 | GET | `/api/medications/patient/{patient_id}` | ✅ Doctor/Admin | أدوية مريض معين |
| 14 | PUT | `/api/medications/{medication_id}` | ✅ Patient | تعديل دواء |
| 15 | DELETE | `/api/medications/{medication_id}` | ✅ Patient | حذف (تعطيل) دواء |
| 16 | POST | `/api/medications/{medication_id}/reminders` | ✅ Patient | إضافة تذكيرات |
| 17 | POST | `/api/files/upload-file` | ✅ Patient | رفع ملف طبي |
| 18 | GET | `/api/files/patient/{patient_id}` | ✅ Doctor/Admin | ملفات مريض |
| 19 | GET | `/api/files/all` | ✅ Doctor/Admin | كل الملفات |
| 20 | POST | `/api/telegram/webhook` | ❌ | Webhook تليجرام (stub) |
| 21 | POST | `/api/telegram/send-reminder` | ❌ | إرسال تذكير تليجرام |
| 22 | POST | `/api/chatbot/query` | ✅ Any logged-in | سؤال للمساعد الذكي |
| 23 | GET | `/api/admin/users` | ✅ Admin | كل المستخدمين |
| 24 | PATCH | `/api/admin/doctors/{doctor_id}/verify` | ✅ Admin | تفعيل/تعطيل طبيب |
| 25 | DELETE | `/api/admin/users/{user_id}` | ✅ Admin | حذف مستخدم |
| 26 | GET | `/api/admin/audit-logs` | ✅ Admin | سجل التدقيق |
| 27 | POST | `/api/visits/` | ✅ Doctor | تسجيل زيارة |
| 28 | GET | `/api/visits/patient/{patient_id}` | ✅ Doctor/Admin | زيارات مريض |
| 29 | PUT | `/api/visits/{visit_id}` | ✅ Doctor | تعديل زيارة |
| 30 | POST | `/api/patient-notes/` | ✅ Doctor | إضافة ملاحظة على مريض |
| 31 | GET | `/api/patient-notes/patient/{patient_id}` | ✅ Doctor/Admin | ملاحظات مريض |
| 32 | GET | `/api/records/` | ❌ | السجلات الطبية (stub) |
| 33 | GET | `/api/records/{id}` | ❌ | سجل طبي بالـ ID (stub) |

---

## ⚙️ 0. Health Check

### GET `/api/health`
**Auth Required:** ❌ No  
**Description:** التحقق من أن الخادم يعمل

**Response (200):**
```json
{
  "success": true,
  "message": "الخادم يعمل بشكل طبيعي",
  "status": "healthy"
}
```

---

## 🔑 1. Authentication (`/api/auth`)

### POST `/api/auth/register`
**Auth Required:** ❌ No  
**Description:** تسجيل مستخدم جديد (مريض / طبيب / أدmin)

**Request Body (JSON):**
```json
{
  "full_name": "ياسين أحمد",
  "email": "yassin@example.com",
  "password": "string123",
  "role": "patient",
  "phone_number": "01012345678",
  "date_of_birth": "1995-05-15",
  "gender": "male",
  "address": "القاهرة",
  "blood_type": "O+",
  "emergency_contact_name": "أحمد",
  "emergency_contact_phone": "01098765432",
  "specialization": "باطنة",
  "bio": "أخصائي باطنة"
}
```

**الحقول الإلزامية:** `full_name`, `email`, `password`, `role`  
**الحقول الاختيارية:** `phone_number`, `date_of_birth`, `gender`, `address`, `blood_type`, `emergency_contact_*`, `specialization`, `bio`

> `role`: `"patient"` | `"doctor"` | `"admin"`  
> `gender`: `"male"` | `"female"`  
> `password`: 8 أحرف على الأقل + حرف + رقم  
> `phone_number`: 11 رقم يبدأ بـ `01`

**Response (201):**
```json
{
  "id": "uuid",
  "full_name": "ياسين أحمد",
  "email": "yassin@example.com",
  "phone_number": "01012345678",
  "role": "patient",
  "created_at": "2026-08-01T19:00:00",
  "updated_at": "2026-08-01T19:00:00"
}
```

---

### POST `/api/auth/login`
**Auth Required:** ❌ No  
**Description:** تسجيل الدخول والحصول على JWT Token

**Request Body (JSON):**
```json
{
  "email": "yassin@example.com",
  "password": "string123"
}
```

> يدعم أيضاً Form-Data: `username` + `password` (لـ Swagger Authorize)

**Response (200):**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user_id": "uuid",
  "full_name": "ياسين أحمد",
  "role": "patient",
  "email": "yassin@example.com"
}
```

---

### GET `/api/auth/verify-token`
**Auth Required:** ❌ No  
**Description:** endpoint للتحقق من التوكن — **قيد التطوير (stub)**

**Response (200):**
```json
{ "message": "Verify token endpoint stub" }
```

---

## 🏥 2. Appointments & Queue (`/api`)

### GET `/api/doctors`
**Auth Required:** ❌ No  
**Description:** عرض قائمة الأطباء المتاحين للحجز

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "د. محمد عمر",
      "specialization": "باطنة",
      "bio": "أخصائي باطنة بخبرة 15 عاماً"
    }
  ]
}
```

---

### POST `/api/book`
**Auth Required:** ❌ No  
**Description:** حجز موعد في الطابور والحصول على رقم الدور

**Request Body (JSON):**
```json
{
  "name": "ياسين أحمد",
  "phone": "01012345678",
  "doctor_id": "uuid"
}
```

> `doctor_id` اختياري — إذا لم يُرسل يُستخدم أول طبيب متاح  
> `phone`: 11 رقم يبدأ بـ `01`

**Response (201):**
```json
{
  "success": true,
  "message": "تم الحجز بنجاح",
  "data": {
    "id": "uuid",
    "name": "ياسين أحمد",
    "phone": "01012345678",
    "queueNumber": 3,
    "estimatedTime": "10:30",
    "arrivalTime": "09:15",
    "status": "waiting",
    "bookingDate": "2026-08-01",
    "isCurrent": false,
    "waitingCount": 2
  }
}
```

**Errors:**
- `400` — اسم غير صالح / رقم هاتف غير صالح / حجز مسبق اليوم

---

### GET `/api/patients`
**Auth Required:** ✅ Doctor / Admin only  
**Description:** قائمة كل المرضى في طابور اليوم

**Response (200):**
```json
{
  "success": true,
  "count": 2,
  "data": [
    {
      "id": "uuid",
      "name": "ياسين أحمد",
      "phone": "01012345678",
      "queueNumber": 1,
      "estimatedTime": "10:00",
      "arrivalTime": "09:00",
      "status": "waiting",
      "bookingDate": "2026-08-01",
      "isCurrent": true
    }
  ]
}
```

> `status`: `"waiting"` | `"done"`  
> `id` هنا = **appointment_id** (معرّف الحجز، ليس patient_id)

---

### GET `/api/stats`
**Auth Required:** ✅ Doctor / Admin only  
**Description:** إحصاءات العيادة لليوم الحالي

**Response (200):**
```json
{
  "success": true,
  "data": {
    "totalPatients": 10,
    "waitingPatients": 4,
    "completedPatients": 6,
    "currentPatient": 2,
    "currentPatientDetails": {
      "name": "ياسين أحمد",
      "queueNumber": 2,
      "phone": "01012345678"
    }
  }
}
```

---

### PUT `/api/patient/{appointment_id}/done`
**Auth Required:** ✅ Doctor / Admin only  
**Description:** إنهاء كشف مريض وتغيير حالته إلى "done"

**URL Params:** `appointment_id` (UUID) — **معرّف الحجز وليس المريض**

**Response (200):**
```json
{
  "success": true,
  "message": "تم الانتهاء من كشف المريض: ياسين أحمد"
}
```

**Errors:**
- `404` — الحجز غير موجود
- `400` — تم الانتهاء من الكشف مسبقاً

---

### DELETE `/api/patients`
**Auth Required:** ✅ Admin only  
**Description:** مسح كل حجوزات اليوم (Reset الطابور)

**Response (200):**
```json
{
  "success": true,
  "message": "تم مسح جميع بيانات الحجوزات بنجاح"
}
```

---

## 💊 3. Medications (`/api/medications`)

### POST `/api/medications/`
**Auth Required:** ✅ Patient only  
**Description:** إضافة دواء جديد لقائمة المريض المسجل

**Request Body (JSON):**
```json
{
  "name": "بانادول إكسترا",
  "medicine_name": "بانادول إكسترا",
  "dosage": "قرص",
  "frequency": "مرة يومياً",
  "visit_id": "uuid",
  "prescribed_by": "uuid",
  "start_date": "2026-08-01",
  "end_date": "2026-08-15",
  "is_active": true
}
```

> استخدم `name` أو `medicine_name` — أي منهما يكفي

**Response (201):**
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "medicine_name": "بانادول إكسترا",
  "dosage": "قرص",
  "frequency": "مرة يومياً",
  "visit_id": null,
  "prescribed_by": null,
  "start_date": "2026-08-01",
  "end_date": null,
  "is_active": true,
  "created_at": "2026-08-01T19:00:00",
  "reminders": []
}
```

---

### GET `/api/medications/`
**Auth Required:** ✅ Patient only  
**Description:** جلب قائمة أدوية المريض المسجل حالياً

**Response (200):**
```json
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "medicine_name": "بانادول إكسترا",
    "dosage": "قرص",
    "frequency": "مرة يومياً",
    "is_active": true,
    "created_at": "2026-08-01T19:00:00",
    "reminders": [
      { "id": "uuid", "medication_id": "uuid", "reminder_time": "08:00:00", "is_active": true }
    ]
  }
]
```

---

### GET `/api/medications/patient/{patient_id}`
**Auth Required:** ✅ Doctor / Admin only  
**Description:** جلب أدوية مريض معين (قراءة فقط)

**URL Params:** `patient_id` (UUID)

**Response (200):** نفس شكل `GET /api/medications/`

---

### PUT `/api/medications/{medication_id}`
**Auth Required:** ✅ Patient only  
**Description:** تعديل دواء يخص المريض المسجل

**URL Params:** `medication_id` (UUID)

**Request Body (JSON):**
```json
{
  "medicine_name": "بانادول",
  "dosage": "قرصين",
  "frequency": "مرتين يومياً",
  "end_date": "2026-08-20",
  "is_active": true
}
```

> كل الحقول اختيارية

**Response (200):** `MedicationResponse` (نفس شكل الإضافة)

---

### DELETE `/api/medications/{medication_id}`
**Auth Required:** ✅ Patient only  
**Description:** حذف (تعطيل) دواء — soft delete

**URL Params:** `medication_id` (UUID)

**Response (204):** No Content

---

### POST `/api/medications/{medication_id}/reminders`
**Auth Required:** ✅ Patient only  
**Description:** إضافة مواعيد تذكير لدواء معين

**URL Params:** `medication_id` (UUID)

**Request Body (JSON Array):**
```json
[
  { "reminder_time": "08:00:00", "is_active": true },
  { "reminder_time": "14:00:00", "is_active": true },
  { "reminder_time": "20:00:00", "is_active": true }
]
```

**Response (200):**
```json
[
  { "id": "uuid", "medication_id": "uuid", "reminder_time": "08:00:00", "is_active": true },
  { "id": "uuid", "medication_id": "uuid", "reminder_time": "14:00:00", "is_active": true }
]
```

---

## 📁 4. Files / Medical Records (`/api/files`)

### POST `/api/files/upload-file`
**Auth Required:** ✅ Patient only  
**Description:** رفع ملف طبي (أشعة، تحاليل، PDF)  
**Content-Type:** `multipart/form-data`

**Form Data:**
```
file: <binary file>
```

**Response (200):**
```json
{
  "success": true,
  "message": "✅ تم رفع الملف 'xray.jpg' بنجاح للمريض: yassin@example.com",
  "file": {
    "patient_email": "yassin@example.com",
    "patient_id": "uuid",
    "filename": "xray.jpg",
    "content_type": "image/jpeg",
    "size_bytes": 204800,
    "uploaded_at": "2026-08-01T19:00:00"
  }
}
```

> ⚠️ الملفات تُخزَّن مؤقتاً في الذاكرة — تُفقد عند إعادة تشغيل الخادم

---

### GET `/api/files/patient/{patient_id}`
**Auth Required:** ✅ Doctor / Admin only  
**Description:** جلب كل الملفات الطبية المرفوعة لمريض بعينه

**URL Params:** `patient_id` (UUID)

**Response (200):**
```json
{
  "patient_id": "uuid",
  "total": 2,
  "files": [
    {
      "patient_email": "yassin@example.com",
      "patient_id": "uuid",
      "filename": "xray.jpg",
      "content_type": "image/jpeg",
      "size_bytes": 204800,
      "uploaded_at": "2026-08-01T19:00:00"
    }
  ]
}
```

---

### GET `/api/files/all`
**Auth Required:** ✅ Doctor / Admin only  
**Description:** جلب كل الملفات الطبية لجميع المرضى

**Response (200):**
```json
{
  "total": 5,
  "files": [ ... ]
}
```

---

## 📲 5. Telegram Notifications (`/api/telegram`)

### POST `/api/telegram/webhook`
**Auth Required:** ❌ No  
**Description:** Webhook لتليجرام — **قيد التطوير (stub)**

**Response (200):**
```json
{ "message": "Telegram webhook stub" }
```

---

### POST `/api/telegram/send-reminder`
**Auth Required:** ❌ No (System use)  
**Description:** إرسال إشعار تذكير جرعة دواء عبر تليجرام بوت

**Request Body (JSON):**
```json
{
  "chat_id": "default",
  "message": "⏰ تذكير: حان الآن ميعاد الجرعة لدواء (بانادول)!"
}
```

> إرسال `"default"` كـ `chat_id` يستخدم `TELEGRAM_CHAT_ID` من ملف `.env` تلقائياً

**Response (200):**
```json
{ "success": true, "message": "تم إرسال التذكير بنجاح عبر تليجرام!" }
```

---

## 🤖 6. AI Chatbot (`/api/chatbot`)

### POST `/api/chatbot/query`
**Auth Required:** ✅ Any logged-in user (Patient / Doctor / Admin)  
**Description:** إرسال سؤال طبي للمساعد الذكي

**Request Body (JSON):**
```json
{ "query": "متى يجب أخذ أدوية الضغط؟" }
```

**Response (200):**
```json
{
  "message": "أهلاً ياسين، استلمنا سؤالك: '...' هذه الخاصية قيد التطوير وستعمل بالذكاء الاصطناعي قريباً."
}
```

---

## 🛡️ 7. Admin Panel (`/api/admin`)

### GET `/api/admin/users`
**Auth Required:** ✅ Admin only  
**Description:** جلب قائمة كل مستخدمي النظام

**Response (200):**
```json
[
  {
    "id": "uuid",
    "full_name": "ياسين أحمد",
    "email": "yassin@example.com",
    "role": "patient",
    "is_active": true
  }
]
```

---

### PATCH `/api/admin/doctors/{doctor_id}/verify`
**Auth Required:** ✅ Admin only  
**Description:** تفعيل أو تعطيل حساب طبيب (Toggle)

**URL Params:** `doctor_id` (UUID)

**Response (200):**
```json
{
  "message": "تم تغيير حالة الطبيب إلى: مفعّل",
  "is_active": true
}
```

---

### DELETE `/api/admin/users/{user_id}`
**Auth Required:** ✅ Admin only  
**Description:** حذف مستخدم نهائياً من النظام

**URL Params:** `user_id` (UUID)

**Response (204):** No Content

**Errors:**
- `400` — لا يمكن حذف حسابك الخاص
- `404` — المستخدم غير موجود

---

### GET `/api/admin/audit-logs`
**Auth Required:** ✅ Admin only  
**Description:** سجلات النشاط والأحداث في النظام (قراءة فقط)

**Query Params:** `limit` (اختياري، افتراضي `100`)

**Example:** `GET /api/admin/audit-logs?limit=50`

**Response (200):**
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "action": "LOGIN",
    "entity_type": "user",
    "entity_id": "uuid",
    "ip_address": "127.0.0.1",
    "created_at": "2026-08-01T19:00:00"
  }
]
```

---

## 🩺 8. Visits — الزيارات الطبية (`/api/visits`)

### POST `/api/visits/`
**Auth Required:** ✅ Doctor only  
**Description:** الطبيب يسجل زيارة جديدة بعد الكشف (تشخيص + ملاحظات)

**Request Body (JSON):**
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "appointment_id": "uuid",
  "visit_date": "2026-08-01T14:30:00",
  "chief_complaint": "صداع مستمر",
  "diagnosis": "صداع توتري",
  "doctor_notes": "يُنصح بالراحة وتقليل التوتر",
  "follow_up_date": "2026-08-15"
}
```

**الحقول الإلزامية:** `patient_id`, `doctor_id`  
**الحقول الاختيارية:** `appointment_id`, `visit_date`, `chief_complaint`, `diagnosis`, `doctor_notes`, `follow_up_date`

**Response (201):**
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "appointment_id": "uuid",
  "visit_date": "2026-08-01T14:30:00",
  "chief_complaint": "صداع مستمر",
  "diagnosis": "صداع توتري",
  "doctor_notes": "يُنصح بالراحة وتقليل التوتر",
  "follow_up_date": "2026-08-15",
  "created_at": "2026-08-01T14:35:00"
}
```

---

### GET `/api/visits/patient/{patient_id}`
**Auth Required:** ✅ Doctor / Admin only  
**Description:** جلب سجل زيارات مريض

**URL Params:** `patient_id` (UUID)

**Response (200):**
```json
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "doctor_id": "uuid",
    "appointment_id": "uuid",
    "visit_date": "2026-08-01T14:30:00",
    "chief_complaint": "صداع مستمر",
    "diagnosis": "صداع توتري",
    "doctor_notes": "يُنصح بالراحة",
    "follow_up_date": "2026-08-15",
    "created_at": "2026-08-01T14:35:00"
  }
]
```

---

### PUT `/api/visits/{visit_id}`
**Auth Required:** ✅ Doctor only  
**Description:** تعديل زيارة طبية

**URL Params:** `visit_id` (UUID)

**Request Body (JSON):**
```json
{
  "chief_complaint": "صداع + دوخة",
  "diagnosis": "صداع توتري",
  "doctor_notes": "تم وصف مسكن",
  "follow_up_date": "2026-08-20"
}
```

> كل الحقول اختيارية

**Response (200):** `VisitResponse` (نفس شكل الإنشاء)

---

## 📝 9. Patient Notes — ملاحظات الطبيب (`/api/patient-notes`)

> ⚠️ هذه الملاحظات **خاصة بالطبيب** — المريض **لا يراها**

### POST `/api/patient-notes/`
**Auth Required:** ✅ Doctor only  
**Description:** الطبيب يضيف ملاحظة خاصة على مريض

**Request Body (JSON):**
```json
{
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "note": "المريض يحتاج متابعة ضغط الدم"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "doctor_id": "uuid",
  "note": "المريض يحتاج متابعة ضغط الدم",
  "created_at": "2026-08-01T19:00:00"
}
```

---

### GET `/api/patient-notes/patient/{patient_id}`
**Auth Required:** ✅ Doctor / Admin only  
**Description:** جلب ملاحظات الطبيب على مريض

**URL Params:** `patient_id` (UUID)

**Response (200):**
```json
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "doctor_id": "uuid",
    "note": "المريض يحتاج متابعة ضغط الدم",
    "created_at": "2026-08-01T19:00:00"
  }
]
```

---

## 📋 10. Medical Records — Stubs (`/api/records`)

> ⚠️ هذه الـ endpoints **قيد التطوير** — لا تستخدمها في الإنتاج حالياً

### GET `/api/records/`
**Auth Required:** ❌ No  
**Response (200):**
```json
{ "message": "Get records endpoint stub" }
```

### GET `/api/records/{id}`
**Auth Required:** ❌ No  
**URL Params:** `id`  
**Response (200):**
```json
{ "message": "Get record {id} endpoint stub" }
```

---

## 📌 ملاحظات مهمة للـ Frontend

### 🔐 طريقة إرسال الـ Token

```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${accessToken}`
};
```

### 👥 RBAC — صلاحيات الأدوار

| الصلاحية | مريض | طبيب | أدمن | زائر |
|---|:---:|:---:|:---:|:---:|
| تسجيل / دخول | ✅ | ✅ | ✅ | ✅ |
| حجز موعد | ✅ | ✅ | ✅ | ✅ |
| رؤية الأطباء | ✅ | ✅ | ✅ | ✅ |
| إضافة / تعديل / حذف أدوية | ✅ | ❌ | ❌ | ❌ |
| رفع ملفات طبية | ✅ | ❌ | ❌ | ❌ |
| شات بوت طبي | ✅ | ✅ | ✅ | ❌ |
| رؤية طابور المرضى | ❌ | ✅ | ✅ | ❌ |
| إحصاءات العيادة | ❌ | ✅ | ✅ | ❌ |
| عرض ملفات / أدوية مريض | ❌ | ✅ | ✅ | ❌ |
| إنهاء كشف مريض | ❌ | ✅ | ✅ | ❌ |
| تسجيل / تعديل زيارات | ❌ | ✅ | ❌ | ❌ |
| ملاحظات الطبيب على المريض | ❌ | ✅ | ✅ (قراءة) | ❌ |
| مسح كل الحجوزات | ❌ | ❌ | ✅ | ❌ |
| لوحة الأدmin | ❌ | ❌ | ✅ | ❌ |

### ⚠️ نقاط مهمة

1. **`appointment_id` ≠ `patient_id`** — في الطابور، حقل `id` في `/api/patients` هو معرّف الحجز، ويُستخدم في `PUT /api/patient/{appointment_id}/done`
2. **`DELETE` يرجع `204 No Content`** — بدون body (medications, admin/users)
3. **الملفات in-memory** — تُفقد عند restart الخادم
4. **Stubs** — `/api/auth/verify-token`, `/api/records/*`, `/api/telegram/webhook` غير مكتملة

### ❌ أخطاء شائعة

| HTTP Code | المعنى |
|---|---|
| `400 Bad Request` | بيانات غير صالحة (هاتف، اسم، حجز مكرر...) |
| `401 Unauthorized` | لم يُرسل Token أو منتهي الصلاحية |
| `403 Forbidden` | Token صحيح لكن الدور غير مسموح |
| `404 Not Found` | المورد غير موجود |
| `422 Unprocessable Entity` | Validation error (Pydantic) |
| `500 Internal Server Error` | خطأ في الخادم |

### 📦 Response Format العام

معظم endpoints ترجع:
```json
{ "success": true/false, "message": "...", "data": { ... } }
```

Endpoints الـ CRUD (medications, visits, admin/users) ترجع الـ object مباشرة أو array.

---

**آخر تحديث:** 2026-08-01 — **33 endpoint** نشط في `clinic-backend`
