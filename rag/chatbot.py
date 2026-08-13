"""
الـ chatbot الطبي — استرجاع المعلومات الطبية مباشرة من ChromaDB (BGE Model).
بدون تشغيل موديل توليد ثانٍ لزيادة السرعة وتقليل زمن الاستجابة.
"""
from .vector_store import search


def answer(question: str) -> dict:
    """اسأل سؤال طبي ← ابحث في المعلومات الطبية ← رجّع المستندات مباشرة."""
    documents = search(question)

    if not documents:
        return {
            "answer": "مش لاقي معلومات متعلقة بالسؤال ده في قاعدة البيانات الطبية.",
            "documents": [],
            "sources": []
        }

    context_text = "\n---\n".join(documents)

    return {
        "answer": context_text,
        "documents": documents,
        "sources": documents
    }
