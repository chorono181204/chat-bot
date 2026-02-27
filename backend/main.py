"""FastAPI application — entry point."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import settings
from .core.bm25_retriever import BM25Retriever
from .core.chat_engine import ChatEngine
from .core.database import init_db
from .core.embedder import EmbeddingEngine
from .core.hybrid_retriever import HybridRetriever
from .core.vector_store import VectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load AI models khi server start — 1 lần duy nhất."""
    # 1. Init database
    init_db()

    # 2. Load embedding model (chạy local)
    print("[INFO] Loading embedding model...")
    embedder = EmbeddingEngine(settings.EMBEDDING_MODEL)

    # 3. Load indexes (nếu đã build)
    vs = VectorStore(dim=768)
    bm25 = BM25Retriever()

    # Fix path: luôn resolve từ thư mục chứa file này
    base_dir = Path(__file__).parent
    processed_dir = base_dir / "data" / "processed"

    if (processed_dir / "faiss.index").exists():
        vs.load()
        bm25.load()
        print("[SUCCESS] Indexes loaded from disk")
    else:
        print("[WARN] Indexes chưa được build.")
        print("   Chạy: python -m backend.core.indexer")
        print("   Hoặc upload file qua POST /api/ingest")

    # 4. Khởi tạo các AI components
    retriever = HybridRetriever(vs, bm25, embedder)

    chat_engine = None
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        chat_engine = ChatEngine(
            retriever, 
            api_key=settings.GEMINI_API_KEY,
            provider="gemini",
            model_name="gemini-1.5-flash-latest"
        )
        if settings.GEMINI_API_KEY:
            print("[SUCCESS] ChatEngine ready (GEMINI)")
        else:
            print("[WARN] GEMINI_API_KEY missing. Please configure in .env or via UI.")
    elif provider == "ollama":
        chat_engine = ChatEngine(
            retriever,
            provider="ollama",
            model_name=settings.OLLAMA_MODEL
        )
        print(f"[SUCCESS] ChatEngine ready (OLLAMA: {settings.OLLAMA_MODEL})")

    app.state.chat_engine = chat_engine
    app.state.retriever = retriever
    app.state.embedder = embedder

    yield

    print("[INFO] Shutting down...")


app = FastAPI(
    title="Chatbot Tư Vấn Tuyển Sinh PTIT",
    description="RAG-based chatbot với Hybrid Search (FAISS + BM25). Tự build, không dùng LangChain.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["Chatbot"])


@app.get("/", tags=["Root"])
def root():
    return {
        "app": "Chatbot Tư Vấn Tuyển Sinh PTIT",
        "docs": "/docs",
        "health": "/api/health",
    }
