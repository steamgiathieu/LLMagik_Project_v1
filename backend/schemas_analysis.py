from pydantic import BaseModel, Field
from typing import Any, Optional, List
from datetime import datetime


# ── Request ───────────────────────────────────────────────────

class ParagraphInput(BaseModel):
    id: str = Field(..., examples=["P1"])
    text: str = Field(..., min_length=1)


class AnalyzeRequest(BaseModel):
    document_id: str = Field(..., examples=["uuid-string"])
    mode: str = Field(..., pattern="^(reader|writer)$", examples=["reader"])
    paragraphs: List[ParagraphInput] = Field(..., min_length=1)


# ── Sub-schemas (reader) ──────────────────────────────────────

class ToneAnalysis(BaseModel):
    overall_tone: Optional[str] = None
    sentiment: Optional[str] = None
    confidence_score: Optional[float] = None


class ParagraphAnalysis(BaseModel):
    paragraph_id: str
    main_idea: Optional[str] = None
    notes: Optional[str] = None


class LogicIssue(BaseModel):
    paragraph_id: str
    issue: str


# ── Sub-schemas (writer) ──────────────────────────────────────

class StyleIssue(BaseModel):
    paragraph_id: str
    issue: str
    severity: Optional[str] = None


class RewriteSuggestion(BaseModel):
    paragraph_id: str
    original: Optional[str] = None
    suggestion: str


class OverallScore(BaseModel):
    clarity: Optional[int] = None
    coherence: Optional[int] = None
    style: Optional[int] = None
    note: Optional[str] = None


# ── Main response ─────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    analysis_id: int
    document_id: str
    mode: str
    ai_provider: Optional[str]
    processing_ms: Optional[int]
    created_at: datetime

    # Core (both modes)
    summary: Optional[str] = None
    tone_analysis: Optional[ToneAnalysis] = None
    paragraph_analyses: Optional[List[ParagraphAnalysis]] = None

    # Reader mode
    key_takeaways: Optional[List[str]] = None
    reading_difficulty: Optional[str] = None
    logic_issues: Optional[List[LogicIssue]] = None

    # Writer mode
    style_issues: Optional[List[StyleIssue]] = None
    rewrite_suggestions: Optional[List[RewriteSuggestion]] = None
    overall_score: Optional[OverallScore] = None

    # Raw fallback — nếu AI trả về format không khớp
    raw_result: Optional[Any] = None

    class Config:
        from_attributes = True


class AnalysisHistoryItem(BaseModel):
    analysis_id: int
    document_id: str
    mode: str
    ai_provider: Optional[str]
    result_summary: Optional[str] = None
    processing_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
