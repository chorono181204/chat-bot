"""Database module — lưu conversation history bằng SQLite."""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import settings


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    title = Column(String, default="Cuộc hội thoại mới")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, nullable=False)
    role = Column(String, nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    sources = Column(Text, default="")      # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── DB Setup ────────────────────────────────────────────────
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)
    print("  [INFO] Database initialized.")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── CRUD ────────────────────────────────────────────────────
def create_conversation(db: Session, title: str = "Cuộc hội thoại mới") -> Conversation:
    conv = Conversation(id=str(uuid.uuid4()), title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def save_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    sources: List[str] = None,
) -> Message:
    import json
    msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=json.dumps(sources or [], ensure_ascii=False),
    )
    db.add(msg)
    db.commit()
    return msg


def get_history(db: Session, conversation_id: str, limit: int = 50) -> List[dict]:
    """Lấy lịch sử hội thoại, trả về format cho ChatEngine."""
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
        .all()
    )
    import json
    return [
        {
            "role": m.role, 
            "content": m.content, 
            "sources": json.loads(m.sources) if m.sources else []
        } for m in msgs
    ]


def get_all_conversations(db: Session, limit: int = 20) -> List[Conversation]:
    return (
        db.query(Conversation)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
        .all()
    )


def update_conversation_title(db: Session, conversation_id: str, title: str):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv:
        conv.title = title
        db.commit()
        db.refresh(conv)
    return conv
