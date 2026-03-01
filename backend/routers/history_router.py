"""
routers/history_router.py

Lịch sử hoạt động tập trung — gom analysis, rewrite, chat sessions.
Tất cả endpoints đều yêu cầu xác thực.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from pymongo.database import Database

from auth import AuthUser, get_current_user
from mongo import get_mongo_db_dependency, next_sequence, utcnow

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
    original_preview: str
    rewritten_preview: str
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

def _doc_title(db: Database, document_id: Optional[str], user_id: int) -> Optional[str]:
    if not document_id:
        return None
    doc = db["documents"].find_one(
        {"document_id": document_id, "user_id": user_id},
        {"_id": 0, "title": 1},
    )
    return str(doc.get("title") or "").strip() or None if doc else None


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

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
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    doc = db["documents"].find_one(
        {"document_id": payload.document_id, "user_id": current_user.id},
        {"_id": 0, "document_id": 1},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")

    if payload.mode not in ("reader", "writer"):
        raise HTTPException(status_code=400, detail="mode phải là 'reader' hoặc 'writer'")

    record = {
        "analysis_id": next_sequence("analysis_id"),
        "document_id": payload.document_id,
        "user_id": current_user.id,
        "mode": payload.mode,
        "ai_provider": "manual",
        "result": {},
        "result_summary": payload.result_summary,
        "processing_ms": None,
        "created_at": utcnow(),
    }
    db["analyses"].insert_one(record)

    return SaveAnalysisHistoryResponse(
        history_id=int(record["analysis_id"]),
        document_id=str(record["document_id"]),
        mode=str(record["mode"]),
        result_summary=record.get("result_summary"),
        timestamp=record.get("created_at", utcnow()),
    )


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
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    query: dict = {"user_id": current_user.id}
    if mode:
        query["mode"] = mode
    if document_id:
        query["document_id"] = document_id

    records = list(
        db["analyses"]
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )

    return [
        AnalysisHistoryEntry(
            history_id=int(r["analysis_id"]),
            document_id=str(r["document_id"]),
            document_title=_doc_title(db, r.get("document_id"), current_user.id),
            mode=str(r.get("mode", "reader")),
            result_summary=r.get("result_summary"),
            ai_provider=r.get("ai_provider"),
            processing_ms=r.get("processing_ms"),
            timestamp=r.get("created_at", utcnow()),
        )
        for r in records
    ]


@router.get(
    "/rewrites",
    response_model=List[RewriteHistoryEntry],
    summary="Lịch sử viết lại đoạn văn",
)
def get_rewrite_history(
    document_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    query: dict = {"user_id": current_user.id}
    if document_id:
        query["document_id"] = document_id

    records = list(
        db["rewrites"]
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )

    return [
        RewriteHistoryEntry(
            history_id=int(r["rewrite_id"]),
            document_id=r.get("document_id"),
            document_title=_doc_title(db, r.get("document_id"), current_user.id),
            paragraph_id=str(r.get("paragraph_id", "")),
            goal=str(r.get("goal", "")),
            original_preview=str(r.get("original_text") or "")[:100],
            rewritten_preview=str(r.get("rewritten_text") or "")[:100],
            ai_provider=r.get("ai_provider"),
            processing_ms=r.get("processing_ms"),
            timestamp=r.get("created_at", utcnow()),
        )
        for r in records
    ]


@router.get(
    "/chats",
    response_model=List[ChatHistoryEntry],
    summary="Lịch sử các phiên chat",
)
def get_chat_history(
    document_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    query: dict = {"user_id": current_user.id}
    if document_id:
        query["document_id"] = document_id

    sessions = list(
        db["chat_sessions"]
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )

    entries: list[ChatHistoryEntry] = []
    for s in sessions:
        sid = int(s["session_id"])
        message_count = db["chat_messages"].count_documents({"session_id": sid})
        last_user = db["chat_messages"].find_one(
            {"session_id": sid, "role": "user"},
            {"_id": 0, "content": 1},
            sort=[("message_id", -1)],
        )
        last_q = (last_user or {}).get("content")
        entries.append(
            ChatHistoryEntry(
                history_id=sid,
                document_id=str(s.get("document_id", "")),
                document_title=_doc_title(db, s.get("document_id"), current_user.id),
                message_count=message_count,
                last_question=(str(last_q)[:120] if last_q else None),
                timestamp=s.get("created_at", utcnow()),
            )
        )
    return entries


@router.get(
    "/all",
    summary="Tất cả hoạt động gần nhất (analysis + rewrite + chat)",
)
def get_all_history(
    limit: int = Query(30, ge=1, le=100),
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    uid = current_user.id

    analyses = list(
        db["analyses"]
        .find({"user_id": uid}, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
    )
    rewrites = list(
        db["rewrites"]
        .find({"user_id": uid}, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
    )
    chats = list(
        db["chat_sessions"]
        .find({"user_id": uid}, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit)
    )

    items: list[dict] = []
    for r in analyses:
        created_at = r.get("created_at", utcnow())
        items.append(
            {
                "type": "analysis",
                "id": int(r["analysis_id"]),
                "document_id": r.get("document_id"),
                "document_title": _doc_title(db, r.get("document_id"), uid),
                "mode": r.get("mode"),
                "result_summary": r.get("result_summary"),
                "timestamp": created_at.isoformat() if isinstance(created_at, datetime) else str(created_at),
            }
        )
    for r in rewrites:
        created_at = r.get("created_at", utcnow())
        items.append(
            {
                "type": "rewrite",
                "id": int(r["rewrite_id"]),
                "document_id": r.get("document_id"),
                "document_title": _doc_title(db, r.get("document_id"), uid),
                "paragraph_id": r.get("paragraph_id"),
                "goal": r.get("goal"),
                "timestamp": created_at.isoformat() if isinstance(created_at, datetime) else str(created_at),
            }
        )
    for s in chats:
        sid = int(s["session_id"])
        message_count = db["chat_messages"].count_documents({"session_id": sid})
        created_at = s.get("created_at", utcnow())
        items.append(
            {
                "type": "chat",
                "id": sid,
                "document_id": s.get("document_id"),
                "document_title": _doc_title(db, s.get("document_id"), uid),
                "message_count": message_count,
                "timestamp": created_at.isoformat() if isinstance(created_at, datetime) else str(created_at),
            }
        )

    items.sort(key=lambda x: x["timestamp"], reverse=True)
    return items[:limit]


@router.get(
    "/stats",
    response_model=HistoryStatsResponse,
    summary="Thống kê hoạt động của người dùng",
)
def get_stats(
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    uid = current_user.id

    analyses = list(db["analyses"].find({"user_id": uid}, {"_id": 0, "mode": 1, "document_id": 1}))
    rewrites_count = db["rewrites"].count_documents({"user_id": uid})
    chat_count = db["chat_sessions"].count_documents({"user_id": uid})

    by_mode: dict[str, int] = {}
    doc_freq: dict[str, int] = {}
    for a in analyses:
        mode = str(a.get("mode") or "reader")
        by_mode[mode] = by_mode.get(mode, 0) + 1
        did = a.get("document_id")
        if did:
            dids = str(did)
            doc_freq[dids] = doc_freq.get(dids, 0) + 1

    most_active_doc_id = max(doc_freq, key=doc_freq.get) if doc_freq else None

    return HistoryStatsResponse(
        total_analyses=len(analyses),
        total_rewrites=rewrites_count,
        total_chat_sessions=chat_count,
        analyses_by_mode=by_mode,
        most_active_document_id=most_active_doc_id,
        most_active_document_title=_doc_title(db, most_active_doc_id, uid),
    )


@router.delete(
    "/analysis/{history_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa một mục lịch sử phân tích",
)
def delete_analysis_entry(
    history_id: int,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    record = db["analyses"].find_one(
        {"analysis_id": history_id, "user_id": current_user.id},
        {"_id": 1},
    )
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy mục lịch sử")
    db["analyses"].delete_one({"analysis_id": history_id, "user_id": current_user.id})

