"""
تحميل المعلومات الطبية العامة فقط من ملفات .txt (بدون سجلات المرضى الشخصية).
"""
from pathlib import Path
from . import config


def _load_folder(folder: Path, tag: str) -> list[str]:
    """حمّل كل ملفات .txt من فولدر معين مع إضافة tag."""
    docs = []
    if not folder.exists():
        return docs
    for f in sorted(folder.glob("*.txt")):
        text = f.read_text(encoding="utf-8")
        docs.append(f"[{tag}]\n{text}")
    print(f"[RAG] Loaded {len(docs)} documents from {folder}")
    return docs


def load_documents() -> list[str]:
    """حمّل البيانات الطبية العامة فقط (الكتاب والمعرفة الطبية العامة)."""
    docs = []

    # المعلومات الطبية العامة فقط
    docs.extend(_load_folder(Path(config.KNOWLEDGE_PATH), "MEDICAL_KNOWLEDGE"))

    print(f"[RAG] Total documents loaded: {len(docs)}")
    return docs
