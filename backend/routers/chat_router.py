import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
import models
import models_text
import models_chat
import schemas_chat
from services.ai_service import get_provider

router = APIRouter(prefix="/chat", tags=["Chat"])

MAX_PARAGRAPHS_IN_CONTEXT = 30   # tránh context quá dài


def _get_or_create_session(
    db: Session,
    user_id: int,
    document_id: str,
    session_id: int | None,
) -> models_chat.ChatSession:
    """Lấy session có sẵn hoặc tạo mới."""
    if session_id is not None:
        session = (
            db.query(models_chat.ChatSession)
            .filter(
                models_chat.ChatSession.id == session_id,
                models_chat.ChatSession.user_id == user_id,
                models_chat.ChatSession.document_id == document_id,
            )
            .first()
        )
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session không tồn tại hoặc không thuộc tài liệu này",
            )
        return session

    session = models_chat.ChatSession(user_id=user_id, document_id=document_id)
    db.add(session)
    db.flush()
    return session


def _build_history(session: models_chat.ChatSession) -> list[dict]:
    """Chuyển messages trong session thành list history cho AI."""
    return [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages
    ]


def _msg_to_out(msg: models_chat.ChatMessage) -> schemas_chat.ChatMessageOut:
    return schemas_chat.ChatMessageOut(
        message_id=msg.id,
        role=msg.role,
        content=msg.content,
        referenced_paragraphs=msg.referenced_paragraphs,
        confidence=msg.confidence,
        out_of_scope=msg.out_of_scope,
        processing_ms=msg.processing_ms,
        created_at=msg.created_at,
    )


# ── POST /chat ─────────────────────────────────────────────────
@router.post(
    "/",
    response_model=schemas_chat.ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Hỏi AI về nội dung văn bản",
)
async def chat(
    payload: schemas_chat.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 1. Verify document ownership
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

    if not doc.paragraphs:
        raise HTTPException(
            status_code=422,
            detail="Tài liệu chưa có đoạn văn nào để trả lời câu hỏi",
        )

    # 2. Get or create session
    session = _get_or_create_session(
        db, current_user.id, payload.document_id, payload.session_id
    )

    # 3. Build paragraph context (capped)
    paragraphs = [
        {"id": p.paragraph_id, "text": p.text}
        for p in doc.paragraphs[:MAX_PARAGRAPHS_IN_CONTEXT]
    ]

    # 4. Build conversation history
    history = _build_history(session)

    # 5. Save user message
    user_msg = models_chat.ChatMessage(
        session_id=session.id,
        role="user",
        content=payload.user_question,
    )
    db.add(user_msg)
    db.flush()

    # 6. Get user's language preference
    user_profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()
    user_language = user_profile.language if user_profile else "vi"

    # 7. Call AI
    provider = get_provider()
    t0 = time.monotonic()
    try:
        ai_result = await provider.chat(
            question=payload.user_question,
            paragraphs=paragraphs,
            history=history,
            language=user_language,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"AI service lỗi: {e}")
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    # 7. Parse & validate AI output
    answer = ai_result.get("answer", "")
    ref_paragraphs = ai_result.get("referenced_paragraphs", [])
    confidence = ai_result.get("confidence", "medium")
    out_of_scope = bool(ai_result.get("out_of_scope", False))

    if not answer:
        db.rollback()
        raise HTTPException(status_code=502, detail="AI không trả về câu trả lời hợp lệ")

    # Sanitize: chỉ giữ P-ids hợp lệ thực sự có trong document
    valid_ids = {p.paragraph_id for p in doc.paragraphs}
    ref_paragraphs = [pid for pid in ref_paragraphs if pid in valid_ids]

    # 8. Save assistant message
    assistant_msg = models_chat.ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer,
        referenced_paragraphs=ref_paragraphs,
        confidence=confidence,
        out_of_scope=out_of_scope,
        processing_ms=elapsed_ms,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return schemas_chat.ChatResponse(
        session_id=session.id,
        message_id=assistant_msg.id,
        answer=answer,
        referenced_paragraphs=ref_paragraphs,
        confidence=confidence,
        out_of_scope=out_of_scope,
        processing_ms=elapsed_ms,
        created_at=assistant_msg.created_at,
    )


# ── GET /chat/sessions ─────────────────────────────────────────
@router.get(
    "/sessions",
    response_model=List[schemas_chat.ChatSessionOut],
    summary="Danh sách session chat của người dùng",
)
def list_sessions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    sessions = (
        db.query(models_chat.ChatSession)
        .filter(models_chat.ChatSession.user_id == current_user.id)
        .order_by(models_chat.ChatSession.created_at.desc())
        .all()
    )
    return [
        schemas_chat.ChatSessionOut(
            session_id=s.id,
            document_id=s.document_id,
            message_count=len(s.messages),
            created_at=s.created_at,
        )
        for s in sessions
    ]


# ── GET /chat/sessions/{session_id} ───────────────────────────
@router.get(
    "/sessions/{session_id}",
    response_model=schemas_chat.ChatHistoryResponse,
    summary="Lấy toàn bộ lịch sử hội thoại của một session",
)
def get_session_history(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = (
        db.query(models_chat.ChatSession)
        .filter(
            models_chat.ChatSession.id == session_id,
            models_chat.ChatSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session không tồn tại")

    return schemas_chat.ChatHistoryResponse(
        session_id=session.id,
        document_id=session.document_id,
        messages=[_msg_to_out(m) for m in session.messages],
        created_at=session.created_at,
    )


# ── DELETE /chat/sessions/{session_id} ────────────────────────
@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa session chat",
)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    session = (
        db.query(models_chat.ChatSession)
        .filter(
            models_chat.ChatSession.id == session_id,
            models_chat.ChatSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session không tồn tại")
    db.delete(session)
    db.commit()
