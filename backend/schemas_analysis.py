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

class ReaderSummaryBreakdown(BaseModel):
    main_points: Optional[List[str]] = None
    figures: Optional[List[str]] = None
    argument_flow: Optional[List[str]] = None


class DeepStyleAnalysis(BaseModel):
    emotional_tone: Optional[str] = None
    inflammatory_word_frequency: Optional[str] = None
    group_bias_level: Optional[str] = None
    notes: Optional[str] = None


class LogicDiagnostic(BaseModel):
    paragraph_id: str
    issue_type: str
    description: str
    evidence: Optional[str] = None
    severity: Optional[str] = None


class ReadabilityMetrics(BaseModel):
    accessibility_score: Optional[int] = None
    accessibility_label: Optional[str] = None
    avg_sentence_length_words: Optional[float] = None
    long_sentence_ratio: Optional[float] = None
    lexical_diversity: Optional[float] = None
    recommended_reader_profile: Optional[str] = None
    note: Optional[str] = None


class ClaimCheckItem(BaseModel):
    paragraph_id: str
    claim: str
    evidence_in_text: Optional[str] = None
    support_level: Optional[str] = None
    risk_if_believed: Optional[str] = None
    verification_prompt: Optional[str] = None


class CriticalReadingGuard(BaseModel):
    persuasion_risk: Optional[str] = None
    manipulation_signals: Optional[List[str]] = None
    missing_context_flags: Optional[List[str]] = None
    fact_check_actions: Optional[List[str]] = None
    alternative_views: Optional[List[str]] = None
    do_not_conclude_yet: Optional[List[str]] = None


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
    readability_metrics: Optional[ReadabilityMetrics] = None
    claim_checks: Optional[List[ClaimCheckItem]] = None
    critical_reading_guard: Optional[CriticalReadingGuard] = None
    logic_issues: Optional[List[LogicIssue]] = None
    reader_summary_breakdown: Optional[ReaderSummaryBreakdown] = None
    deep_style_analysis: Optional[DeepStyleAnalysis] = None
    logic_diagnostics: Optional[List[LogicDiagnostic]] = None

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
