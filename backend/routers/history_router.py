"""
routers/history_router.py

Lịch sử hoạt động tập trung — gom analysis, rewrite, chat sessions.
Tất cả endpoints đều yêu cầu xác thực.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth import get_current_user
import models
import models_analysis
import models_rewrite
import models_chat
import models_text

router = APIRouter(prefix="/history", tags=["History"])


# ─────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────

class AnalysisHistoryEntry(BaseModel):
    history_id: int
    activity_type: str = "analysis"
    document_id: str
    document_title: Optional[str]
    mode: str
    result_summary: Optional[str]
    ai_provider: Optional[str]
    processing_ms: Optional[int]
    timestamp: datetime


class RewriteHistoryEntry(BaseModel):
    history_id: int
    activity_type: str = "rewrite"
    document_id: Optional[str]
    document_title: Optional[str]
    paragraph_id: str
    goal: str
    original_preview: str        # first 100 chars of original
    rewritten_preview: str       # first 100 chars of rewritten
    ai_provider: Optional[str]
    processing_ms: Optional[int]
    timestamp: datetime


class ChatHistoryEntry(BaseModel):
    history_id: int
    activity_type: str = "chat"
    document_id: str
    document_title: Optional[str]
    message_count: int
    last_question: Optional[str]
    timestamp: datetime


class HistoryStatsResponse(BaseModel):
    total_analyses: int
    total_rewrites: int
    total_chat_sessions: int
    analyses_by_mode: dict
    most_active_document_id: Optional[str]
    most_active_document_title: Optional[str]


class SaveAnalysisHistoryRequest(BaseModel):
    document_id: str
    mode: str
    result_summary: Optional[str] = None


class SaveAnalysisHistoryResponse(BaseModel):
    history_id: int
    document_id: str
    mode: str
    result_summary: Optional[str]
    timestamp: datetime


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _doc_title(db: Session, document_id: Optional[str]) -> Optional[str]:
    if not document_id:
        return None
    doc = db.query(models_text.Document).filter(models_text.Document.id == document_id).first()
    return doc.title if doc else None


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

# ── POST /history/analysis (lưu thủ công nếu cần) ─────────────
@router.post(
    "/analysis",
    response_model=SaveAnalysisHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lưu thủ công một mục lịch sử phân tích",
    description=(
        "Endpoint dự phòng để lưu lịch sử khi phân tích được thực hiện bên ngoài "
        "POST /analysis/analyze. Thông thường, /analysis/analyze tự động lưu."
    ),
)
def save_analysis_history(
    payload: SaveAnalysisHistoryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Verify document ownership
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

    if payload.mode not in ("reader", "writer"):
        raise HTTPException(status_code=400, detail="mode phải là 'reader' hoặc 'writer'")

    record = models_analysis.AnalysisResult(
        document_id=payload.document_id,
        user_id=current_user.id,
        mode=payload.mode,
        ai_provider="manual",
        result={},
        result_summary=payload.result_summary,
        processing_ms=None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return SaveAnalysisHistoryResponse(
        history_id=record.id,
        document_id=record.document_id,
        mode=record.mode,
        result_summary=record.result_summary,
        timestamp=record.created_at,
    )


# ── GET /history/analysis ──────────────────────────────────────
@router.get(
    "/analysis",
    response_model=List[AnalysisHistoryEntry],
    summary="Lịch sử phân tích của người dùng",
)
def get_analysis_history(
    mode: Optional[str] = Query(None, pattern="^(reader|writer)$"),
    document_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = (
        db.query(models_analysis.AnalysisResult)
        .filter(models_analysis.AnalysisResult.user_id == current_user.id)
    )
    if mode:
        q = q.filter(models_analysis.AnalysisResult.mode == mode)
    if document_id:
        q = q.filter(models_analysis.AnalysisResult.document_id == document_id)

    records = q.order_by(models_analysis.AnalysisResult.created_at.desc()).offset(offset).limit(limit).all()

    return [
        AnalysisHistoryEntry(
            history_id=r.id,
            document_id=r.document_id,
            document_title=_doc_title(db, r.document_id),
            mode=r.mode,
            result_summary=r.result_summary,
            ai_provider=r.ai_provider,
            processing_ms=r.processing_ms,
            timestamp=r.created_at,
        )
        for r in records
    ]


# ── GET /history/rewrites ──────────────────────────────────────
@router.get(
    "/rewrites",
    response_model=List[RewriteHistoryEntry],
    summary="Lịch sử viết lại đoạn văn",
)
def get_rewrite_history(
    document_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = (
        db.query(models_rewrite.RewriteRecord)
        .filter(models_rewrite.RewriteRecord.user_id == current_user.id)
    )
    if document_id:
        q = q.filter(models_rewrite.RewriteRecord.document_id == document_id)

    records = q.order_by(models_rewrite.RewriteRecord.created_at.desc()).offset(offset).limit(limit).all()

    return [
        RewriteHistoryEntry(
            history_id=r.id,
            document_id=r.document_id,
            document_title=_doc_title(db, r.document_id),
            paragraph_id=r.paragraph_id,
            goal=r.goal,
            original_preview=r.original_text[:100],
            rewritten_preview=r.rewritten_text[:100],
            ai_provider=r.ai_provider,
            processing_ms=r.processing_ms,
            timestamp=r.created_at,
        )
        for r in records
    ]


# ── GET /history/chats ─────────────────────────────────────────
@router.get(
    "/chats",
    response_model=List[ChatHistoryEntry],
    summary="Lịch sử các phiên chat",
)
def get_chat_history(
    document_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = (
        db.query(models_chat.ChatSession)
        .filter(models_chat.ChatSession.user_id == current_user.id)
    )
    if document_id:
        q = q.filter(models_chat.ChatSession.document_id == document_id)

    sessions = q.order_by(models_chat.ChatSession.created_at.desc()).offset(offset).limit(limit).all()

    entries = []
    for s in sessions:
        user_msgs = [m for m in s.messages if m.role == "user"]
        last_q = user_msgs[-1].content[:120] if user_msgs else None
        entries.append(
            ChatHistoryEntry(
                history_id=s.id,
                document_id=s.document_id,
                document_title=_doc_title(db, s.document_id),
                message_count=len(s.messages),
                last_question=last_q,
                timestamp=s.created_at,
            )
        )
    return entries


# ── GET /history/all ───────────────────────────────────────────
@router.get(
    "/all",
    summary="Tất cả hoạt động gần nhất (analysis + rewrite + chat)",
)
def get_all_history(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    uid = current_user.id

    analyses = (
        db.query(models_analysis.AnalysisResult)
        .filter(models_analysis.AnalysisResult.user_id == uid)
        .order_by(models_analysis.AnalysisResult.created_at.desc())
        .limit(limit).all()
    )
    rewrites = (
        db.query(models_rewrite.RewriteRecord)
        .filter(models_rewrite.RewriteRecord.user_id == uid)
        .order_by(models_rewrite.RewriteRecord.created_at.desc())
        .limit(limit).all()
    )
    chats = (
        db.query(models_chat.ChatSession)
        .filter(models_chat.ChatSession.user_id == uid)
        .order_by(models_chat.ChatSession.created_at.desc())
        .limit(limit).all()
    )

    items = []
    for r in analyses:
        items.append({
            "type": "analysis",
            "id": r.id,
            "document_id": r.document_id,
            "document_title": _doc_title(db, r.document_id),
            "mode": r.mode,
            "result_summary": r.result_summary,
            "timestamp": r.created_at.isoformat(),
        })
    for r in rewrites:
        items.append({
            "type": "rewrite",
            "id": r.id,
            "document_id": r.document_id,
            "document_title": _doc_title(db, r.document_id),
            "paragraph_id": r.paragraph_id,
            "goal": r.goal,
            "timestamp": r.created_at.isoformat(),
        })
    for s in chats:
        items.append({
            "type": "chat",
            "id": s.id,
            "document_id": s.document_id,
            "document_title": _doc_title(db, s.document_id),
            "message_count": len(s.messages),
            "timestamp": s.created_at.isoformat(),
        })

    # Sort by timestamp desc, take top limit
    items.sort(key=lambda x: x["timestamp"], reverse=True)
    return items[:limit]


# ── GET /history/stats ─────────────────────────────────────────
@router.get(
    "/stats",
    response_model=HistoryStatsResponse,
    summary="Thống kê hoạt động của người dùng",
)
def get_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    uid = current_user.id

    analyses = (
        db.query(models_analysis.AnalysisResult)
        .filter(models_analysis.AnalysisResult.user_id == uid)
        .all()
    )
    rewrites_count = (
        db.query(models_rewrite.RewriteRecord)
        .filter(models_rewrite.RewriteRecord.user_id == uid)
        .count()
    )
    chat_count = (
        db.query(models_chat.ChatSession)
        .filter(models_chat.ChatSession.user_id == uid)
        .count()
    )

    by_mode: dict = {}
    doc_freq: dict = {}
    for a in analyses:
        by_mode[a.mode] = by_mode.get(a.mode, 0) + 1
        doc_freq[a.document_id] = doc_freq.get(a.document_id, 0) + 1

    most_active_doc_id = max(doc_freq, key=doc_freq.get) if doc_freq else None

    return HistoryStatsResponse(
        total_analyses=len(analyses),
        total_rewrites=rewrites_count,
        total_chat_sessions=chat_count,
        analyses_by_mode=by_mode,
        most_active_document_id=most_active_doc_id,
        most_active_document_title=_doc_title(db, most_active_doc_id),
    )


# ── DELETE /history/analysis/{history_id} ─────────────────────
@router.delete(
    "/analysis/{history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa một mục lịch sử phân tích",
)
def delete_analysis_entry(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = (
        db.query(models_analysis.AnalysisResult)
        .filter(
            models_analysis.AnalysisResult.id == history_id,
            models_analysis.AnalysisResult.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy mục lịch sử")
    db.delete(record)
    db.commit()
