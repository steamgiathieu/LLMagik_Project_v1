import os
import re
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
import models
import models_rewrite
import models_text
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


def _normalize_text_for_compare(text: str) -> str:
    return " ".join((text or "").split()).strip().lower()


_VI_DIACRITIC_RE = re.compile(r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", re.IGNORECASE)
_EN_WORD_RE = re.compile(r"\b[a-zA-Z]{3,}\b")
_WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
_JA_RE = re.compile(r"[\u3040-\u30ff]")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

_EN_COMMON = {
    "the", "and", "is", "are", "of", "to", "in", "that", "for", "with", "on", "this", "it", "as", "be",
}
_VI_COMMON_NO_DIACRITICS = {
    "la", "va", "cua", "cho", "mot", "nhung", "khong", "nguoi", "noi", "nay", "do", "duoc", "voi", "trong",
}


def _detect_source_language(text: str) -> Optional[str]:
    t = (text or "").strip()
    if not t:
        return None

    if _JA_RE.search(t):
        return "ja"
    if _CJK_RE.search(t):
        return "zh"
    if _VI_DIACRITIC_RE.search(t):
        return "vi"

    words = re.findall(r"[a-zA-Z']+", t.lower())
    if words:
        en_hits = sum(1 for w in words if w in _EN_COMMON)
        vi_hits = sum(1 for w in words if w in _VI_COMMON_NO_DIACRITICS)
        if vi_hits >= max(2, en_hits + 1):
            return "vi"
        if en_hits >= max(2, vi_hits + 1):
            return "en"
        return "en"
    return None


def _is_language_mismatch(text: str, language: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False

    if language == "vi":
        has_vi_marker = bool(_VI_DIACRITIC_RE.search(t))
        en_words = len(_EN_WORD_RE.findall(t))
        all_words = len(_WORD_RE.findall(t))
        en_ratio = en_words / max(1, all_words)
        return (not has_vi_marker) and en_ratio >= 0.35

    if language == "en":
        vi_chars = len(_VI_DIACRITIC_RE.findall(t))
        latin_letters = len(re.findall(r"[A-Za-zÀ-ỹ]", t))
        return vi_chars >= 2 and (vi_chars / max(1, latin_letters)) >= 0.08
    return False


def _language_guardrail_rewrite(original_text: str, goal: str, language: str) -> str:
    return _force_minimal_rewrite(original_text, goal=goal, language=language)


def _force_minimal_rewrite(text: str, goal: str = "", language: str = "vi") -> str:
    t = (text or "").strip()
    if not t:
        return t

    if language == "en":
        s = " ".join(t.split()).lower()
        s = s.replace("show a dance", "performs a dance")
        verb_map = {
            "show": "shows",
            "perform": "performs",
            "dance": "dances",
            "write": "writes",
            "read": "reads",
            "make": "makes",
            "do": "does",
            "go": "goes",
            "have": "has",
            "play": "plays",
        }
        tokens = s.split()
        for i in range(len(tokens) - 2):
            if tokens[i] in {"the", "a", "an", "this", "that"} and tokens[i + 2] in verb_map:
                tokens[i + 2] = verb_map[tokens[i + 2]]
        for i in range(len(tokens) - 1):
            if tokens[i] in {"he", "she", "it"} and tokens[i + 1] in verb_map:
                tokens[i + 1] = verb_map[tokens[i + 1]]

        out = " ".join(tokens).strip()
        if out and not out.endswith((".", "!", "?")):
            out += "."
        if out:
            out = out[0].upper() + out[1:]
        if out and _normalize_text_for_compare(out) != _normalize_text_for_compare(t):
            return out

    parts = [s.strip() for s in t.split(". ") if s.strip()]
    if len(parts) > 1:
        out = ". ".join(parts[1:] + [parts[0]])
        return out if out.endswith((".", "!", "?")) else out + "."

    if language == "en":
        return f"In other words, {t[0].lower() + t[1:] if len(t) > 1 else t}"
    if language == "vi":
        return f"Theo cách diễn đạt khác, {t[0].lower() + t[1:] if len(t) > 1 else t}"

    if t.endswith("."):
        return t[:-1] + "!"
    if t.endswith("!"):
        return t[:-1] + "."
    return t + "."


def _same_text_explanation(language: str) -> str:
    if language == "en":
        return "AI output was too similar to the original text, so the system applied a fallback rewrite."
    if language == "vi":
        return "AI trả về nội dung quá giống bản gốc; hệ thống đã áp dụng rewrite dự phòng."
    return ""


def _same_text_explanation_append(language: str) -> str:
    if language == "en":
        return "System applied additional fallback rewrite because AI output was nearly identical to input."
    if language == "vi":
        return "Hệ thống áp dụng thêm rewrite dự phòng do kết quả AI gần như giữ nguyên bản gốc."
    return ""


def _language_guardrail_explanation(language: str) -> str:
    if language == "en":
        return "The system detected a language mismatch in AI output and automatically rewrote the result in English."
    if language == "vi":
        return "Hệ thống phát hiện AI trả về sai ngôn ngữ và đã tự động viết lại kết quả đúng tiếng Việt."
    return ""


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
    payload_original_text = (payload.original_text or "").strip()
    original_text = payload.original_text
    document_id = payload.document_id

    if payload.document_id:
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

        paragraph = (
            db.query(models_text.Paragraph)
            .filter(
                models_text.Paragraph.document_id == payload.document_id,
                models_text.Paragraph.paragraph_id == payload.paragraph_id,
            )
            .first()
        )
        if paragraph:
            original_text = paragraph.text
        elif payload_original_text:
            original_text = payload_original_text
        elif doc.raw_text and doc.raw_text.strip():
            original_text = doc.raw_text.strip()
        else:
            raise HTTPException(status_code=404, detail="Đoạn văn không tồn tại trong tài liệu")

        document_id = doc.id

    if not original_text or len(original_text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Nội dung đoạn văn quá ngắn để viết lại")

    # Get user's language preference
    user_profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()
    user_language = user_profile.language if user_profile else "vi"
    source_language = _detect_source_language(original_text)
    effective_language = source_language or user_language or "vi"

    provider = get_provider()
    t0 = time.monotonic()
    try:
        ai_result = await provider.rewrite(
            paragraph_id=payload.paragraph_id,
            original_text=original_text,
            goal=payload.goal,
            language=effective_language,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service lỗi: {e}")
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    # Validate AI output has required fields
    rewritten_text = (ai_result.get("rewritten_text", "") or "").strip()
    explanation = (ai_result.get("explanation", "") or "").strip()

    if not rewritten_text:
        raise HTTPException(
            status_code=502,
            detail="AI không trả về nội dung viết lại hợp lệ",
        )

    if _normalize_text_for_compare(rewritten_text) == _normalize_text_for_compare(original_text):
        rewritten_text = _force_minimal_rewrite(original_text, goal=payload.goal, language=effective_language)
        if not explanation:
            explanation = _same_text_explanation(effective_language)
        else:
            extra = _same_text_explanation_append(effective_language)
            if extra:
                explanation += f" | {extra}"

    if _is_language_mismatch(rewritten_text, effective_language):
        rewritten_text = _language_guardrail_rewrite(original_text, payload.goal, effective_language)
        explanation = _language_guardrail_explanation(effective_language)
    elif explanation and _is_language_mismatch(explanation, effective_language):
        explanation = _language_guardrail_explanation(effective_language)

    record = models_rewrite.RewriteRecord(
        user_id=current_user.id,
        document_id=document_id,
        paragraph_id=payload.paragraph_id,
        goal=payload.goal,
        original_text=original_text,
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
