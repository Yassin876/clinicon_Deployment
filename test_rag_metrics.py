"""
test_rag_metrics.py
سكربت لاختبار الـ RAG والـ LLM وتوليد أوقات الـ Retrieval والـ Generation
"""
import sys
import time

print("=" * 60)
print(" 🚀 Starting RAG & LLM Metrics Test Script")
print("=" * 60)

# 1. Test RAG Retrieval
try:
    from rag.vector_store import search, init_store
    print("\n1️⃣ Testing Vector Store Retrieval...")
    init_store()
    
    query = "مراحل علاج مرض السكري والوقاية منه"
    print(f"🔍 Searching Query: '{query}'")
    
    t0 = time.time()
    docs = search(query, top_k=2)
    t1 = time.time()
    
    print(f"✅ Found {len(docs)} relevant documents in {t1 - t0:.4f} seconds total.")
    for idx, doc in enumerate(docs, 1):
        print(f"   [Doc {idx}]: {doc[:100]}...")
except Exception as e:
    print(f"❌ RAG Search error: {e}")

# 2. Test LLM Generation
try:
    from rag.llm import ask_llm
    print("\n2️⃣ Testing Qwen LLM Generation (4-bit NF4 + FP16)...")
    prompt = "ما هي نصائح الوقاية من مرض السكري بخطوات مختصرة؟"
    print(f"💬 Prompt: '{prompt}'")
    
    t0 = time.time()
    response = ask_llm(prompt)
    t1 = time.time()
    
    print(f"✅ LLM Response generated in {t1 - t0:.4f} seconds total:")
    print(f"   '{response}'")
except Exception as e:
    print(f"❌ LLM Generation error: {e}")

print("\n" + "=" * 60)
print(" 🎉 Test Completed!")
print("=" * 60)
