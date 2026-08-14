"""
إعدادات نظام الـ RAG — كلها من .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

# مسار ملفات السجلات الطبية
DATA_PATH = os.getenv("RAG_DATA_PATH", "rag/data/medical_record")

# مسار المعلومات الطبية العامة
KNOWLEDGE_PATH = os.getenv("RAG_KNOWLEDGE_PATH", "rag/data/medical_knowledge")

# ChromaDB
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "rag/database")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "medical_records")

# عدد النتائج من البحث
TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# موديل الـ embedding (خفيف جداً لسيرفرات الـ 512MB RAM)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

