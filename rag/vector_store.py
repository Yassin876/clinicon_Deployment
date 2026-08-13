"""
ChromaDB vector store — تخزين واسترجاع السجلات الطبية.
BGE embedding model: FP16 + CUDA (single load, eval mode).
"""
import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import time
import torch
import chromadb
from sentence_transformers import SentenceTransformer
from . import config
from .loader import load_documents

_model: SentenceTransformer | None = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[RAG] Loading embedding model: {config.EMBEDDING_MODEL}")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = SentenceTransformer(config.EMBEDDING_MODEL, device=device)

        # FP16 on CUDA for memory efficiency
        if device == "cuda":
            _model = _model.half()  # cast to FP16

        _model.eval()
        print(f"[RAG] Embedding model loaded on {device.upper()} | dtype=FP16")
    return _model


def init_store(force_rebuild: bool = False):
    """حمّل أو ابني الـ vector store."""
    global _collection
    client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)

    # لو الـ collection موجودة ومش عايزين نعيد بنائها
    try:
        _collection = client.get_collection(config.COLLECTION_NAME)
        if not force_rebuild and _collection.count() > 0:
            print(f"[RAG] Collection '{config.COLLECTION_NAME}' exists ({_collection.count()} docs)")
            return
    except Exception:
        pass

    # ابنيها من الصفر
    print("[RAG] Building vector store...")
    try:
        client.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass

    _collection = client.create_collection(config.COLLECTION_NAME)
    documents = load_documents()
    if not documents:
        print("[RAG] Warning: no documents found!")
        return

    model = _get_model()
    with torch.inference_mode():
        embeddings = model.encode(documents, convert_to_numpy=True).tolist()

    for i, (doc, emb) in enumerate(zip(documents, embeddings)):
        _collection.add(
            ids=[f"patient_{i}"],
            documents=[doc],
            embeddings=[emb],
        )
    print(f"[RAG] Stored {len(documents)} documents in ChromaDB")


def search(query: str, top_k: int | None = None) -> list[str]:
    """ابحث عن أقرب سجلات طبية للسؤال مع حساب طباعة الوقت المستهلك في الاسترجاع (Retrieval Time)."""
    global _collection
    start_time = time.time()
    
    if _collection is None:
        init_store()
    if _collection is None or _collection.count() == 0:
        return []

    model = _get_model()
    with torch.inference_mode():
        query_emb = model.encode(query, convert_to_numpy=True).tolist()

    results = _collection.query(
        query_embeddings=[query_emb],
        n_results=top_k or config.TOP_K,
        include=["documents", "distances"],
    )

    elapsed_retrieval = time.time() - start_time
    print(f"⏱️ [Metric] Retrieval Time (BGE Embedding Search): {elapsed_retrieval:.4f} seconds")

    if not results["documents"] or not results["documents"][0]:
        return []

    # فلتر النتائج — لو المسافة كبيرة (مش relevant)، ما ترجّعهاش
    RELEVANCE_THRESHOLD = 1.3
    filtered = []
    for doc, dist in zip(results["documents"][0], results["distances"][0]):
        if dist <= RELEVANCE_THRESHOLD:
            filtered.append(doc)

    return filtered
