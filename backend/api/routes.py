"""FastAPI routes — đầy đủ endpoints."""
import json
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import (
    create_conversation,
    get_db,
    get_history,
    save_message,
)

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────
class LLMConfig(BaseModel):
    provider: str = "gemini"
    api_key: str = ""
    model: str = "gemini-2.5-flash"


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    llm_config: Optional[LLMConfig] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    conversation_id: str


class ConversationCreate(BaseModel):
    title: str = "Cuộc hội thoại mới"


# ─── Chat Endpoints ──────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, db: Session = Depends(get_db)):
    """
    Gửi câu hỏi → nhận câu trả lời + sources.
    Tự động tạo conversation mới nếu không có conversation_id.
    """
    engine = getattr(request.app.state, "chat_engine", None)
    if engine is None:
        raise HTTPException(503, "AI engine chưa sẵn sàng. Hãy index tài liệu trước.")

    # Tạo conversation nếu cần
    conv_id = req.conversation_id
    if not conv_id:
        conv = create_conversation(db)
        conv_id = conv.id

    # Lấy history
    history = get_history(db, conv_id)

    # Generate
    result = engine.chat(req.query, history)

    # Lưu messages
    save_message(db, conv_id, "user", req.query)
    save_message(db, conv_id, "assistant", result["answer"], result["sources"])

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "conversation_id": conv_id,
    }


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request, db: Session = Depends(get_db)):
    """Streaming endpoint — Server-Sent Events."""
    engine = getattr(request.app.state, "chat_engine", None)
    if engine is None:
        raise HTTPException(503, "AI engine chưa sẵn sàng.")

    # 1. Quản lý Conversation ID và Title
    is_new = False
    if not req.conversation_id:
        # Nếu chưa có ID, tạo mới với title là đoạn đầu query
        title = req.query[:30] + "..." if len(req.query) > 30 else req.query
        conv = create_conversation(db, title=title)
        conv_id = conv.id
        is_new = True
    else:
        conv_id = req.conversation_id
    
    history = get_history(db, conv_id)

    # 2. Lưu câu hỏi của User
    save_message(db, conv_id, "user", req.query)

    # 3. Lấy config từ request nếu có
    llm_kwargs = {}
    if req.llm_config:
        llm_kwargs = {
            "api_key": req.llm_config.api_key,
            "provider": req.llm_config.provider,
            "model_name": req.llm_config.model
        }

    async def generate():
        full_answer = []
        async for data_str in engine.stream_chat(req.query, history, **llm_kwargs):
            try:
                data = json.loads(data_str)
                # Thêm conversation_id vào mọi chunk
                data["conversation_id"] = conv_id
                
                if "token" in data:
                    full_answer.append(data["token"])
                
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            except:
                # Fallback nếu không phải JSON
                yield f"data: {json.dumps({'token': data_str, 'conversation_id': conv_id}, ensure_ascii=False)}\n\n"

        # Lưu câu trả lời sau khi stream xong
        save_message(db, conv_id, "assistant", "".join(full_answer))
        yield f"data: {json.dumps({'done': True, 'conversation_id': conv_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ─── Conversation Endpoints ───────────────────────────────────
@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):
    """Lấy danh sách các cuộc hội thoại gần đây."""
    from ..core.database import get_all_conversations
    convs = get_all_conversations(db)
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in convs]


@router.post("/conversations")
def new_conversation(body: ConversationCreate, db: Session = Depends(get_db)):
    """Tạo cuộc hội thoại mới."""
    conv = create_conversation(db, title=body.title)
    return {"id": conv.id, "title": conv.title, "created_at": conv.created_at}


@router.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: str, db: Session = Depends(get_db)):
    """Lấy lịch sử tin nhắn của một cuộc hội thoại."""
    history = get_history(db, conv_id, limit=50)
    return {"conversation_id": conv_id, "messages": history}


# ─── Ingest Endpoint (Upload tài liệu) ───────────────────────
@router.post("/ingest")
async def ingest(request: Request, file: UploadFile = File(...)):
    """
    Upload file (PDF/Excel) và tự động index vào RAG pipeline.
    Dùng để thêm tài liệu tuyển sinh mà không cần restart server.
    """
    import tempfile
    from pathlib import Path
    from ..core.indexer import build_index_incremental

    allowed = {".pdf", ".xlsx", ".xls", ".txt", ".docx"}
    ext = Path(file.filename).suffix.lower()

    if ext not in allowed:
        raise HTTPException(400, f"File type không hỗ trợ: {ext}")

    # Lưu file tạm
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        engine = getattr(request.app.state, "chat_engine", None)

        # Re-index
        retriever = await build_index_incremental(tmp_path, engine)
        if engine:
            engine.retriever = retriever

        return {
            "status": "success",
            "message": f"Đã index file: {file.filename}",
            "filename": file.filename,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ─── Health ──────────────────────────────────────────────────
@router.get("/health")
def health(request: Request):
    engine = getattr(request.app.state, "chat_engine", None)
    return {
        "status": "ok",
        "engine_ready": engine is not None,
    }
