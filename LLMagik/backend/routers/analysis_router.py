import os
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
import models
import models_text
import models_analysis
import schemas_analysis
from services.ai_service import get_provider

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def _build_response(record: models_analysis.AnalysisResult) -> schemas_analysis.AnalyzeResponse:
    """Chuyển AnalysisResult ORM → AnalyzeResponse Pydantic."""
    result: dict = record.result or {}

    def _model_or_none(cls, data):
        if not data:
            return None
        try:
            return cls(**data) if isinstance(data, dict) else None
        except Exception:
            return None

    def _list_model(cls, data):
        if not isinstance(data, list):
            return None
        out = []
        for item in data:
            try:
                out.append(cls(**item))
            except Exception:
                pass
        return out or None

    return schemas_analysis.AnalyzeResponse(
        analysis_id=record.id,
        document_id=record.document_id,
        mode=record.mode,
        ai_provider=record.ai_provider,
        processing_ms=record.processing_ms,
        created_at=record.created_at,
        # core
        summary=result.get("summary"),
        tone_analysis=_model_or_none(schemas_analysis.ToneAnalysis, result.get("tone_analysis")),
        paragraph_analyses=_list_model(schemas_analysis.ParagraphAnalysis, result.get("paragraph_analyses")),
        # reader
        key_takeaways=result.get("key_takeaways"),
        reading_difficulty=result.get("reading_difficulty"),
        logic_issues=_list_model(schemas_analysis.LogicIssue, result.get("logic_issues")),
        # writer
        style_issues=_list_model(schemas_analysis.StyleIssue, result.get("style_issues")),
        rewrite_suggestions=_list_model(schemas_analysis.RewriteSuggestion, result.get("rewrite_suggestions")),
        overall_score=_model_or_none(schemas_analysis.OverallScore, result.get("overall_score")),
        # raw fallback
        raw_result=result if "error" in result else None,
    )


# ── POST /analysis/analyze ─────────────────────────────────────
@router.post(
    "/analyze",
    response_model=schemas_analysis.AnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Phân tích văn bản bằng AI",
)
async def analyze_document(
    payload: schemas_analysis.AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Verify document belongs to user
    doc = (
        db.query(models_text.Document)
        .filter(
            models_text.Document.id == payload.document_id,
            models_text.Document.user_id == current_user.id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")

    # Convert paragraphs to plain dicts for AI service
    paragraphs = [{"id": p.id, "text": p.text} for p in payload.paragraphs]

    # Get user's language preference
    user_profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()
    user_language = user_profile.language if user_profile else "vi"

    # Call AI
    provider = get_provider()
    t0 = time.monotonic()
    try:
        ai_result = await provider.analyze(mode=payload.mode, paragraphs=paragraphs, language=user_language)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service lỗi: {e}")
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    # Build short summary for history display
    summary_text = ai_result.get("summary", "")
    if not summary_text:
        pa = ai_result.get("paragraph_analyses", [])
        summary_text = pa[0].get("main_idea", "") if pa else ""
    result_summary = summary_text[:300] if summary_text else None

    # Persist
    record = models_analysis.AnalysisResult(
        document_id=payload.document_id,
        user_id=current_user.id,
        mode=payload.mode,
        ai_provider=os.getenv("AI_PROVIDER", "mock"),
        result=ai_result,
        result_summary=result_summary,
        processing_ms=elapsed_ms,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return _build_response(record)


# ── GET /analysis/history ──────────────────────────────────────
@router.get(
    "/history",
    response_model=List[schemas_analysis.AnalysisHistoryItem],
    summary="Lịch sử phân tích của người dùng",
)
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    records = (
        db.query(models_analysis.AnalysisResult)
        .filter(models_analysis.AnalysisResult.user_id == current_user.id)
        .order_by(models_analysis.AnalysisResult.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        schemas_analysis.AnalysisHistoryItem(
            analysis_id=r.id,
            document_id=r.document_id,
            mode=r.mode,
            ai_provider=r.ai_provider,
            result_summary=r.result_summary,
            processing_ms=r.processing_ms,
            created_at=r.created_at,
        )
        for r in records
    ]


# ── GET /analysis/history/{document_id} ───────────────────────
@router.get(
    "/history/{document_id}",
    response_model=List[schemas_analysis.AnalysisHistoryItem],
    summary="Lịch sử phân tích của một tài liệu",
)
def get_document_history(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    records = (
        db.query(models_analysis.AnalysisResult)
        .filter(
            models_analysis.AnalysisResult.document_id == document_id,
            models_analysis.AnalysisResult.user_id == current_user.id,
        )
        .order_by(models_analysis.AnalysisResult.created_at.desc())
        .all()
    )
    return [
        schemas_analysis.AnalysisHistoryItem(
            analysis_id=r.id,
            document_id=r.document_id,
            mode=r.mode,
            ai_provider=r.ai_provider,
            result_summary=r.result_summary,
            processing_ms=r.processing_ms,
            created_at=r.created_at,
        )
        for r in records
    ]


# ── GET /analysis/{analysis_id} ────────────────────────────────
@router.get(
    "/{analysis_id}",
    response_model=schemas_analysis.AnalyzeResponse,
    summary="Lấy kết quả phân tích theo ID",
)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = (
        db.query(models_analysis.AnalysisResult)
        .filter(
            models_analysis.AnalysisResult.id == analysis_id,
            models_analysis.AnalysisResult.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả phân tích")
    return _build_response(record)
