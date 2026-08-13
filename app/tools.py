"""
tools.py
الأدوات متطابقة مع الـ API الحقيقي (نظام المواعيد والـ slots).
يستخدم contextvars لإدارة توكن المريض لكل طلب بشكل مستقل وآمن.
"""
import contextvars
from typing import Optional
import requests
from langchain_core.tools import tool

from . import backend_client, config

# Context variable لتخزين توكن المريض الخاص بالطلب الحالي بشكل خيطي آمن (Thread-safe)
current_patient_token: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_patient_token", default=None)


def get_token() -> Optional[str]:
    return current_patient_token.get()


# ---------- أدوات الأطباء والمواعيد ----------

@tool
def get_doctors() -> object:
    """اجلب قايمة الدكاترة المتاحين في العيادة مع أسمائهم وتخصصاتهم.
    مفيش مدخلات — بتجيب الكل.
    """
    token = get_token()
    return backend_client.get_doctors(token=token)


@tool
def get_available_slots(doctor_id: str, date: str) -> object:
    """اجلب المواعيد المتاحة لدكتور معين في يوم محدد.
    
    Args:
        doctor_id: المعرف الفريد للدكتور (UUID).
        date: التاريخ بصيغة YYYY-MM-DD (مثال: '2026-08-12').
    """
    token = get_token()
    return backend_client.get_available_slots(doctor_id=doctor_id, date_str=date, token=token)


@tool
def book_appointment(doctor_id: str, slot_datetime: str) -> object:
    """احجز موعد في وقت محدد عند دكتور.
    
    Args:
        doctor_id: المعرف الفريد للدكتور (UUID).
        slot_datetime: الوقت المختار بصيغة ISO كاملة (مثال: '2026-08-12T10:00:00').
    """
    token = get_token()
    return backend_client.book_appointment(doctor_id=doctor_id, slot_datetime=slot_datetime, token=token)


# ---------- أدوات الأدوية ----------

@tool
def get_my_medications() -> object:
    """اجلب قايمة الأدوية بتاعة المريض الحالي (اللي مسجّل دخوله).
    بترجّع اسم الدوا والجرعة والتكرار ومواعيد التذكير.
    """
    token = get_token()
    return backend_client.get_my_medications(token=token)


@tool
def add_medication(name: str, dosage: Optional[str] = None, frequency: Optional[str] = None) -> object:
    """أضف دوا جديد لقايمة أدوية المريض الحالي.

    Args:
        name: اسم الدوا، مثال 'بانادول إكسترا'.
        dosage: الجرعة، مثال 'قرص' أو 'قرصين'.
        frequency: التكرار، مثال 'مرة يومياً' أو 'مرتين يومياً'.
    """
    token = get_token()
    return backend_client.add_medication(name=name, dosage=dosage, frequency=frequency, token=token)


# ---------- أداة المعلومات الطبية (RAG) ----------

@tool
def search_medical_info(query: str) -> object:
    """ابحث في قاعدة المعرفة الطبية عن معلومات عن الأمراض والأعراض ومراحل
    العلاج ودورة حياة المرض. استخدمها لما المريض يسأل سؤال طبي عام.

    Args:
        query: السؤال أو الموضوع الطبي، مثال 'مراحل علاج السكري'.
    """
    if not config.RAG_BASE_URL:
        return {"error": "خدمة المعلومات الطبية مش متاحة حالياً. "
                         "اعتذر للمريض واقترح عليه يسأل الدكتور المختص."}
    try:
        resp = requests.post(f"{config.RAG_BASE_URL}/search",
                             json={"query": query}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("answer", "لم أجد معلومات كافية.")
    except requests.RequestException as e:
        return {"error": f"مش قادر أوصل لنظام المعلومات الطبية: {e}"}


# قايمة كل الأدوات المتاحة للشات بوت الخاص بالمريض
ALL_TOOLS = [
    get_doctors,
    get_available_slots,
    book_appointment,
    get_my_medications,
    add_medication,
    search_medical_info,
]
