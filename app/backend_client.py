"""
backend_client.py
كل نداءات الـ backend الحقيقي في مكان واحد.
متطابق مع API_DOCS.md — Base URL: http://localhost:5000/api
كل دالة تقبل token خاص بالمريض لضمان العزل التام بين المرضى.
"""
from typing import Optional
import requests
from . import config

TIMEOUT = 15


def _headers(token: Optional[str] = None) -> dict:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _request(method: str, path: str, token: Optional[str] = None, **kwargs) -> object:
    url = f"{config.BACKEND_BASE_URL}{path}"
    headers = _headers(token)
    try:
        resp = requests.request(method, url, headers=headers, timeout=TIMEOUT, **kwargs)
        resp.raise_for_status()
        if resp.status_code == 204:
            return {"success": True}
        return resp.json()
    except requests.HTTPError:
        return {"error": f"الـ backend رجّع خطأ {resp.status_code}: {resp.text}"}
    except requests.RequestException as e:
        return {"error": f"مش قادر أوصل للـ backend: {e}"}


# ===== Auth =====

def login(email, password):
    return _request("POST", "/auth/login", json={"email": email, "password": password})


def register(full_name, email, password, role="patient", **extra):
    body = {"full_name": full_name, "email": email, "password": password, "role": role}
    body.update(extra)
    return _request("POST", "/auth/register", json=body)


# ===== Doctors & Slots =====

def get_doctors(token: Optional[str] = None):
    """GET /api/doctors — بترجّع قائمة الأطباء"""
    result = _request("GET", "/doctors", token=token)
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return result


def get_available_slots(doctor_id: str, date_str: str, token: Optional[str] = None):
    """GET /api/doctors/{doctor_id}/available-slots?date=YYYY-MM-DD"""
    result = _request("GET", f"/doctors/{doctor_id}/available-slots", token=token, params={"date": date_str})
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return result


# ===== Booking (Slot-Based) =====

def book_appointment(doctor_id: str, slot_datetime: str, token: Optional[str] = None):
    """POST /api/book — حجز موعد في وقت محدد (تتطلب توكن المريض)"""
    body = {
        "doctor_id": doctor_id,
        "slot_datetime": slot_datetime
    }
    return _request("POST", "/book", token=token, json=body)


# ===== Medications =====

def get_my_medications(token: Optional[str] = None):
    """GET /api/medications/ — أدوية المريض الحالي"""
    return _request("GET", "/medications/", token=token)


def add_medication(name: str, dosage: Optional[str] = None, frequency: Optional[str] = None, token: Optional[str] = None, **extra):
    body = {"name": name}
    if dosage:
        body["dosage"] = dosage
    if frequency:
        body["frequency"] = frequency
    body.update(extra)
    return _request("POST", "/medications/", token=token, json=body)


# ===== Files & Visits =====

def upload_file(file_path: str, token: Optional[str] = None):
    """POST /api/files/upload-file — رفع ملف طبي"""
    with open(file_path, "rb") as f:
        return _request("POST", "/files/upload-file", token=token, files={"file": f})


def get_patient_visits(patient_id: str, token: Optional[str] = None):
    """GET /api/visits/patient/{id} — سجل زيارات مريض"""
    return _request("GET", f"/visits/patient/{patient_id}", token=token)
