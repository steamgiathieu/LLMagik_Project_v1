from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime


# ── Request ───────────────────────────────────────────────────

class TextInputRequest(BaseModel):
    """Nhập văn bản trực tiếp."""
    text: str = Field(..., min_length=10, examples=["Đây là đoạn văn bản cần phân tích..."])


class UrlInputRequest(BaseModel):
    """Nhập URL bài báo."""
    url: str = Field(..., examples=["https://vnexpress.net/bai-viet"])


# ── Response ──────────────────────────────────────────────────

class ParagraphOut(BaseModel):
    id: str = Field(..., examples=["P1"])
    text: str

class DocumentResponse(BaseModel):
    document_id: str
    title: Optional[str]
    source_type: str
    source_ref: Optional[str]
    paragraph_count: int
    paragraphs: List[ParagraphOut]
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentSummaryResponse(BaseModel):
    document_id: str
    title: Optional[str]
    source_type: str
    paragraph_count: int
    created_at: datetime

    class Config:
        from_attributes = True
