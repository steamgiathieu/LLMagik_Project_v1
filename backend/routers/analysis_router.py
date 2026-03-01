import os
import time
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pymongo.database import Database

from auth import AuthUser, get_current_user
from mongo import get_mongo_db_dependency, next_sequence, utcnow
import schemas_analysis
from services.ai_service import get_provider

router = APIRouter(prefix="/analysis", tags=["Analysis"])
SUPPORTED_UI_LANGUAGES = {"vi", "en", "zh", "ja", "fr"}


def _resolve_ui_language(x_ui_language: str | None) -> str:
    if not x_ui_language:
        return "vi"
    code = x_ui_language.strip().lower()
    return code if code in SUPPORTED_UI_LANGUAGES else "vi"


def _build_response(record: dict) -> schemas_analysis.AnalyzeResponse:
    result: dict = record.get("result") or {}

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
        analysis_id=int(record["analysis_id"]),
        document_id=str(record["document_id"]),
        mode=str(record["mode"]),
        ai_provider=record.get("ai_provider"),
        processing_ms=record.get("processing_ms"),
        created_at=record.get("created_at", utcnow()),
        summary=result.get("summary"),
        tone_analysis=_model_or_none(schemas_analysis.ToneAnalysis, result.get("tone_analysis")),
        paragraph_analyses=_list_model(schemas_analysis.ParagraphAnalysis, result.get("paragraph_analyses")),
        key_takeaways=result.get("key_takeaways"),
        reading_difficulty=result.get("reading_difficulty"),
        readability_metrics=_model_or_none(schemas_analysis.ReadabilityMetrics, result.get("readability_metrics")),
        claim_checks=_list_model(schemas_analysis.ClaimCheckItem, result.get("claim_checks")),
        critical_reading_guard=_model_or_none(schemas_analysis.CriticalReadingGuard, result.get("critical_reading_guard")),
        logic_issues=_list_model(schemas_analysis.LogicIssue, result.get("logic_issues")),
        reader_summary_breakdown=_model_or_none(schemas_analysis.ReaderSummaryBreakdown, result.get("reader_summary_breakdown")),
        deep_style_analysis=_model_or_none(schemas_analysis.DeepStyleAnalysis, result.get("deep_style_analysis")),
        logic_diagnostics=_list_model(schemas_analysis.LogicDiagnostic, result.get("logic_diagnostics")),
        style_issues=_list_model(schemas_analysis.StyleIssue, result.get("style_issues")),
        rewrite_suggestions=_list_model(schemas_analysis.RewriteSuggestion, result.get("rewrite_suggestions")),
        overall_score=_model_or_none(schemas_analysis.OverallScore, result.get("overall_score")),
        raw_result=result if "error" in result else None,
    )


@router.post(
    "/analyze",
    response_model=schemas_analysis.AnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Phân tích văn bản bằng AI",
)
async def analyze_document(
    payload: schemas_analysis.AnalyzeRequest,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
    x_ui_language: str | None = Header(default=None, alias="X-UI-Language"),
):
    doc = db["documents"].find_one(
        {"document_id": payload.document_id, "user_id": current_user.id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")

    paragraphs = [{"id": p.id, "text": p.text} for p in payload.paragraphs]
    request_language = _resolve_ui_language(x_ui_language)

    provider = get_provider()
    t0 = time.monotonic()
    try:
        ai_result = await provider.analyze(mode=payload.mode, paragraphs=paragraphs, language=request_language)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service lỗi: {e}")
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    summary_text = ai_result.get("summary", "")
    if not summary_text:
        pa = ai_result.get("paragraph_analyses", [])
        summary_text = pa[0].get("main_idea", "") if pa else ""
    result_summary = summary_text[:300] if summary_text else None

    record = {
        "analysis_id": next_sequence("analysis_id"),
        "document_id": payload.document_id,
        "user_id": current_user.id,
        "mode": payload.mode,
        "ai_provider": os.getenv("AI_PROVIDER", "mock"),
        "result": ai_result,
        "result_summary": result_summary,
        "processing_ms": elapsed_ms,
        "created_at": utcnow(),
    }
    db["analyses"].insert_one(record)
    return _build_response(record)


@router.get(
    "/history",
    response_model=List[schemas_analysis.AnalysisHistoryItem],
    summary="Lịch sử phân tích của người dùng",
)
def get_history(
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    cursor = (
        db["analyses"]
        .find({"user_id": current_user.id}, {"_id": 0})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    records = list(cursor)
    return [
        schemas_analysis.AnalysisHistoryItem(
            analysis_id=int(r["analysis_id"]),
            document_id=str(r["document_id"]),
            mode=str(r["mode"]),
            ai_provider=r.get("ai_provider"),
            result_summary=r.get("result_summary"),
            processing_ms=r.get("processing_ms"),
            created_at=r.get("created_at", utcnow()),
        )
        for r in records
    ]


@router.get(
    "/history/{document_id}",
    response_model=List[schemas_analysis.AnalysisHistoryItem],
    summary="Lịch sử phân tích của một tài liệu",
)
def get_document_history(
    document_id: str,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    records = list(
        db["analyses"]
        .find({"document_id": document_id, "user_id": current_user.id}, {"_id": 0})
        .sort("created_at", -1)
    )
    return [
        schemas_analysis.AnalysisHistoryItem(
            analysis_id=int(r["analysis_id"]),
            document_id=str(r["document_id"]),
            mode=str(r["mode"]),
            ai_provider=r.get("ai_provider"),
            result_summary=r.get("result_summary"),
            processing_ms=r.get("processing_ms"),
            created_at=r.get("created_at", utcnow()),
        )
        for r in records
    ]


@router.get(
    "/{analysis_id}",
    response_model=schemas_analysis.AnalyzeResponse,
    summary="Lấy kết quả phân tích theo ID",
)
def get_analysis(
    analysis_id: int,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    record = db["analyses"].find_one({"analysis_id": analysis_id, "user_id": current_user.id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả phân tích")
    return _build_response(record)
