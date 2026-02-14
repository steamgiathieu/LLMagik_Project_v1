from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ── Request ───────────────────────────────────────────────────

PRESET_GOALS = [
    "trung lập hơn",
    "rõ ràng và súc tích hơn",
    "trang trọng và chuyên nghiệp hơn",
    "thân thiện và gần gũi hơn",
    "ngắn gọn hơn",
    "chi tiết và mở rộng hơn",
]


class RewriteRequest(BaseModel):
    paragraph_id: str = Field(..., examples=["P1"])
    original_text: str = Field(..., min_length=10, examples=["Đây là đoạn văn cần viết lại."])
    goal: str = Field(
        ...,
        min_length=3,
        max_length=200,
        examples=["trung lập hơn"],
        description=f"Mục tiêu viết lại. Gợi ý: {', '.join(PRESET_GOALS)}",
    )
    document_id: Optional[str] = Field(None, description="Gắn với document nếu có")


# ── Response ──────────────────────────────────────────────────

class RewriteResponse(BaseModel):
    rewrite_id: int
    paragraph_id: str
    goal: str
    original_text: str
    rewritten_text: str
    explanation: str
    ai_provider: Optional[str]
    processing_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class RewriteHistoryItem(BaseModel):
    rewrite_id: int
    paragraph_id: str
    goal: str
    ai_provider: Optional[str]
    processing_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
