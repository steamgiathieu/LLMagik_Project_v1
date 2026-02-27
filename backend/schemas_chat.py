from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ── Request ───────────────────────────────────────────────────

class ChatRequest(BaseModel):
    document_id: str = Field(..., examples=["uuid-string"])
    user_question: str = Field(..., min_length=1, max_length=1000, examples=["Ý chính của văn bản là gì?"])
    session_id: Optional[int] = Field(
        None,
        description="Tiếp tục session cũ. Bỏ trống để tạo session mới.",
    )


# ── Response ──────────────────────────────────────────────────

class ChatResponse(BaseModel):
    session_id: int
    message_id: int
    answer: str
    referenced_paragraphs: List[str]
    confidence: Optional[str]
    out_of_scope: bool
    processing_ms: Optional[int]
    created_at: datetime


class ChatMessageOut(BaseModel):
    message_id: int
    role: str
    content: str
    referenced_paragraphs: Optional[List[str]]
    confidence: Optional[str]
    out_of_scope: Optional[bool]
    processing_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionOut(BaseModel):
    session_id: int
    document_id: str
    message_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    session_id: int
    document_id: str
    messages: List[ChatMessageOut]
    created_at: datetime
