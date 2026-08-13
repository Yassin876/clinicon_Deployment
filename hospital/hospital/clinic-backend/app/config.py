import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل ملف .env تلقائياً
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    BASE_DIR = BASE_DIR
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/clinic_db"
    )
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")

settings = Settings()
