import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
import models
import models_text
import schemas_text
from services.text_processor import process_input

router = APIRouter(prefix="/texts", tags=["Text Input"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _save_document(
    db: Session,
    source_type: str,
    processed: dict,
    user_id: Optional[int],
) -> models_text.Document:
    """Lưu Document + Paragraph vào DB, trả về Document."""
    doc_id = str(uuid.uuid4())

    doc = models_text.Document(
        id=doc_id,
        user_id=user_id,
        title=processed["title"],
        source_type=source_type,
        source_ref=processed["source_ref"],
        raw_text=processed["raw_text"],
        paragraph_count=len(processed["paragraphs"]),
    )
    db.add(doc)
    db.flush()

    for i, p in enumerate(processed["paragraphs"]):
        para = models_text.Paragraph(
            document_id=doc_id,
            paragraph_id=p["id"],
            index=i,
            text=p["text"],
        )
        db.add(para)

    db.commit()
    db.refresh(doc)
    return doc


def _doc_to_response(doc: models_text.Document) -> schemas_text.DocumentResponse:
    return schemas_text.DocumentResponse(
        document_id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        source_ref=doc.source_ref,
        paragraph_count=doc.paragraph_count,
        paragraphs=[
            schemas_text.ParagraphOut(id=p.paragraph_id, text=p.text)
            for p in doc.paragraphs
        ],
        created_at=doc.created_at,
    )


# ── POST /texts/from-text ──────────────────────────────────────
@router.post(
    "/from-text",
    response_model=schemas_text.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nhập văn bản trực tiếp",
)
def ingest_text(
    payload: schemas_text.TextInputRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        processed = process_input(source_type="text", text=payload.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = _save_document(db, "text", processed, current_user.id)
    return _doc_to_response(doc)


# ── POST /texts/from-url ───────────────────────────────────────
@router.post(
    "/from-url",
    response_model=schemas_text.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trích xuất văn bản từ URL",
)
def ingest_url(
    payload: schemas_text.UrlInputRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        processed = process_input(source_type="url", url=payload.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = _save_document(db, "url", processed, current_user.id)
    return _doc_to_response(doc)


# ── POST /texts/from-file ──────────────────────────────────────
@router.post(
    "/from-file",
    response_model=schemas_text.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file PDF hoặc DOCX",
)
async def ingest_file(
    file: UploadFile = File(..., description="File PDF hoặc DOCX, tối đa 10MB"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ("pdf", "docx", "doc"):
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ file PDF hoặc DOCX",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File vượt quá 10MB")

    try:
        processed = process_input(
            source_type="file",
            file_bytes=file_bytes,
            filename=filename,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = _save_document(db, "file", processed, current_user.id)
    return _doc_to_response(doc)


# ── GET /texts/ ────────────────────────────────────────────────
@router.get(
    "/",
    response_model=List[schemas_text.DocumentSummaryResponse],
    summary="Lấy danh sách tài liệu của người dùng",
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    docs = (
        db.query(models_text.Document)
        .filter(models_text.Document.user_id == current_user.id)
        .order_by(models_text.Document.created_at.desc())
        .all()
    )
    return [
        schemas_text.DocumentSummaryResponse(
            document_id=d.id,
            title=d.title,
            source_type=d.source_type,
            paragraph_count=d.paragraph_count,
            created_at=d.created_at,
        )
        for d in docs
    ]


# ── GET /texts/{document_id} ───────────────────────────────────
@router.get(
    "/{document_id}",
    response_model=schemas_text.DocumentResponse,
    summary="Lấy tài liệu theo ID (kèm danh sách đoạn)",
)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = (
        db.query(models_text.Document)
        .filter(
            models_text.Document.id == document_id,
            models_text.Document.user_id == current_user.id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
    return _doc_to_response(doc)


# ── DELETE /texts/{document_id} ────────────────────────────────
@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa tài liệu",
)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = (
        db.query(models_text.Document)
        .filter(
            models_text.Document.id == document_id,
            models_text.Document.user_id == current_user.id,
        )
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
    db.delete(doc)
    db.commit()
