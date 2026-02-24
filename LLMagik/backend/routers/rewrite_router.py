import os
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
import models
import models_rewrite
import schemas_rewrite
from services.ai_service import get_provider

router = APIRouter(prefix="/rewrite", tags=["Rewrite"])


def _to_response(r: models_rewrite.RewriteRecord) -> schemas_rewrite.RewriteResponse:
    return schemas_rewrite.RewriteResponse(
        rewrite_id=r.id,
        paragraph_id=r.paragraph_id,
        goal=r.goal,
        original_text=r.original_text,
        rewritten_text=r.rewritten_text,
        explanation=r.explanation or "",
        ai_provider=r.ai_provider,
        processing_ms=r.processing_ms,
        created_at=r.created_at,
    )


# ── POST /rewrite ──────────────────────────────────────────────
@router.post(
    "/",
    response_model=schemas_rewrite.RewriteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Viết lại một đoạn văn theo mục tiêu",
)
async def rewrite_paragraph(
    payload: schemas_rewrite.RewriteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Get user's language preference
    user_profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()
    user_language = user_profile.language if user_profile else "vi"

    provider = get_provider()
    t0 = time.monotonic()
    try:
        ai_result = await provider.rewrite(
            paragraph_id=payload.paragraph_id,
            original_text=payload.original_text,
            goal=payload.goal,
            language=user_language,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service lỗi: {e}")
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    # Validate AI output has required fields
    rewritten_text = ai_result.get("rewritten_text", "")
    explanation = ai_result.get("explanation", "")

    if not rewritten_text:
        raise HTTPException(
            status_code=502,
            detail="AI không trả về nội dung viết lại hợp lệ",
        )

    record = models_rewrite.RewriteRecord(
        user_id=current_user.id,
        document_id=payload.document_id,
        paragraph_id=payload.paragraph_id,
        goal=payload.goal,
        original_text=payload.original_text,
        rewritten_text=rewritten_text,
        explanation=explanation,
        ai_provider=os.getenv("AI_PROVIDER", "mock"),
        processing_ms=elapsed_ms,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_response(record)


# ── GET /rewrite/presets ───────────────────────────────────────
@router.get(
    "/presets",
    response_model=List[str],
    summary="Danh sách mục tiêu gợi ý",
)
def get_presets():
    return schemas_rewrite.PRESET_GOALS


# ── GET /rewrite/history ───────────────────────────────────────
@router.get(
    "/history",
    response_model=List[schemas_rewrite.RewriteHistoryItem],
    summary="Lịch sử viết lại của người dùng",
)
def get_history(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    records = (
        db.query(models_rewrite.RewriteRecord)
        .filter(models_rewrite.RewriteRecord.user_id == current_user.id)
        .order_by(models_rewrite.RewriteRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        schemas_rewrite.RewriteHistoryItem(
            rewrite_id=r.id,
            paragraph_id=r.paragraph_id,
            goal=r.goal,
            ai_provider=r.ai_provider,
            processing_ms=r.processing_ms,
            created_at=r.created_at,
        )
        for r in records
    ]


# ── GET /rewrite/{rewrite_id} ──────────────────────────────────
@router.get(
    "/{rewrite_id}",
    response_model=schemas_rewrite.RewriteResponse,
    summary="Lấy kết quả viết lại theo ID",
)
def get_rewrite(
    rewrite_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = (
        db.query(models_rewrite.RewriteRecord)
        .filter(
            models_rewrite.RewriteRecord.id == rewrite_id,
            models_rewrite.RewriteRecord.user_id == current_user.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả viết lại")
    return _to_response(record)
