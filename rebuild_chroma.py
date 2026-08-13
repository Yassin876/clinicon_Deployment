"""
rebuild_chroma.py
مسح وبناء قاعدة بيانات ChromaDB بالكامل باستخدام موديل BGE الـ Embedding الجديد.
"""
from rag.vector_store import init_store

print("============================================================")
print(" 🔄 Rebuilding ChromaDB Vector Store with BGE Model")
print("============================================================")

init_store(force_rebuild=True)

print("\n✅ Finished rebuilding vector store with BGE embeddings!")
