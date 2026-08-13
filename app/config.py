"""
إعدادات المشروع كلها في مكان واحد.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- الموديل (عن طريق Ollama أو Gemini) ---
USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() in ("true", "1", "yes")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b-gpu")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# --- الـ backend بتاع العيادة ---
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:5000/api")

# توكن الدخول — الـ backend بيتعرّف على المريض منه
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")

# --- نظام المعلومات الطبية (RAG) ---
RAG_BASE_URL = os.getenv("RAG_BASE_URL", "")

# --- إعدادات التوليد ---
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
