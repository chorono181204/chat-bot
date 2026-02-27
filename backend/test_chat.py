import os
import sys
from pathlib import Path

# Thêm root vào sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from backend.config import settings
from backend.core.embedder import EmbeddingEngine
from backend.core.vector_store import VectorStore
from backend.core.bm25_retriever import BM25Retriever
from backend.core.hybrid_retriever import HybridRetriever
from backend.core.chat_engine import ChatEngine

def test_chat():
    print("\n" + "="*50)
    print("RUNNING:  TESTING PTIT CHATBOT RAG PIPELINE")
    print("="*50)

    # 1. Setup components
    embedder = EmbeddingEngine(settings.EMBEDDING_MODEL)
    vs = VectorStore(dim=768)
    bm25 = BM25Retriever()

    processed_dir = Path(__file__).parent / "data" / "processed"
    if not (processed_dir / "faiss.index").exists():
        print("❌ Lỗi: Chưa build index. Hãy chạy indexer trước.")
        return

    vs.load()
    bm25.load()
    retriever = HybridRetriever(vs, bm25, embedder)

    chat_engine = ChatEngine(
        retriever,
        api_key=settings.GEMINI_API_KEY,
        provider=settings.LLM_PROVIDER,
        model_name="gemini-2.5-flash"
    )

    # 2. Test questions
    questions = [
        "Ngành CNTT mã ngành là gì và có chỉ tiêu bao nhiêu ở Hà Nội?",
        "Học phí hệ đại trà năm 2024 là bao nhiêu?",
        "Điểm chuẩn ngành An toàn thông tin năm ngoái thế nào?"
    ]

    for q in questions:
        print(f"\nUser: {q}")
        print("Bot: Thinking...", end="", flush=True)
        
        result = chat_engine.chat(q)
        
        print("\r" + " "*20 + "\r", end="") # Clear line
        print(f"Bot: {result['answer']}")
        print(f"Source: {result['sources'][0][:100]}...")

    print("\n" + "="*50)
    print("DONE:  TEST COMPLETED")
    print("="*50)

if __name__ == "__main__":
    test_chat()
