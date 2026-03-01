import os
import re
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pymongo.database import Database

from auth import AuthUser, get_current_user
import schemas_text
from mongo import get_mongo_db_dependency, get_persistent_data_root, utcnow
from services.text_processor import process_input

router = APIRouter(prefix="/texts", tags=["Text Input"])

MAX_FILE_SIZE = 10 * 1024 * 1024
LEGACY_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
UPLOAD_DIR = str((get_persistent_data_root() / "llmagik" / "uploads").resolve())
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename or "uploaded_file")
    return cleaned.strip("._") or "uploaded_file"


def _original_file_path_from_doc_id(document_id: str) -> Optional[str]:
    prefix = f"{document_id}__"
    for folder in (UPLOAD_DIR, LEGACY_UPLOAD_DIR):
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            if name.startswith(prefix):
                full = os.path.join(folder, name)
                if os.path.isfile(full):
                    return full
    return None


def _doc_to_response(db: Database, doc: dict) -> schemas_text.DocumentResponse:
    para_docs = list(db["paragraphs"].find({"document_id": doc["document_id"]}).sort("index", 1))
    para_list = [
        schemas_text.ParagraphOut(id=str(p["paragraph_id"]), text=str(p["text"]))
        for p in para_docs
    ]

    if not para_list and str(doc.get("raw_text", "")).strip():
        para_list = [schemas_text.ParagraphOut(id="P1", text=str(doc["raw_text"]).strip())]

    return schemas_text.DocumentResponse(
        document_id=str(doc["document_id"]),
        title=doc.get("title"),
        source_type=str(doc.get("source_type", "text")),
        source_ref=doc.get("source_ref"),
        paragraph_count=max(int(doc.get("paragraph_count", 0)), len(para_list)),
        paragraphs=para_list,
        created_at=doc.get("created_at", utcnow()),
    )


def _save_document(
    db: Database,
    source_type: str,
    processed: dict,
    user_id: int,
    doc_id: Optional[str] = None,
) -> dict:
    doc_id = doc_id or str(uuid.uuid4())
    now = utcnow()
    doc = {
        "document_id": doc_id,
        "user_id": user_id,
        "title": processed.get("title"),
        "source_type": source_type,
        "source_ref": processed.get("source_ref"),
        "raw_text": processed.get("raw_text"),
        "paragraph_count": len(processed.get("paragraphs", [])),
        "created_at": now,
        "updated_at": now,
    }
    db["documents"].insert_one(doc)

    para_docs = []
    for i, p in enumerate(processed.get("paragraphs", [])):
        para_docs.append(
            {
                "document_id": doc_id,
                "paragraph_id": p.get("id", f"P{i + 1}"),
                "index": i,
                "text": p.get("text", ""),
            }
        )
    if para_docs:
        db["paragraphs"].insert_many(para_docs)

    return doc


@router.post(
    "/from-text",
    response_model=schemas_text.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nhập văn bản trực tiếp",
)
def ingest_text(
    payload: schemas_text.TextInputRequest,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    try:
        processed = process_input(source_type="text", text=payload.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = _save_document(db, "text", processed, current_user.id)
    return _doc_to_response(db, doc)


@router.post(
    "/from-url",
    response_model=schemas_text.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trích xuất văn bản từ URL",
)
def ingest_url(
    payload: schemas_text.UrlInputRequest,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    try:
        processed = process_input(source_type="url", url=payload.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc = _save_document(db, "url", processed, current_user.id)
    return _doc_to_response(db, doc)


@router.post(
    "/from-file",
    response_model=schemas_text.DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file PDF hoặc DOCX",
)
async def ingest_file(
    file: UploadFile = File(..., description="File PDF hoặc DOCX, tối đa 10MB"),
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "docx", "doc"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF hoặc DOCX")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File vượt quá 10MB")

    try:
        processed = process_input(source_type="file", file_bytes=file_bytes, filename=filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    doc_id = str(uuid.uuid4())
    doc = _save_document(db, "file", processed, current_user.id, doc_id=doc_id)

    safe_name = _safe_filename(filename)
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}__{safe_name}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    return _doc_to_response(db, doc)


@router.get(
    "/",
    response_model=List[schemas_text.DocumentSummaryResponse],
    summary="Lấy danh sách tài liệu của người dùng",
)
def list_documents(
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    docs = list(
        db["documents"]
        .find({"user_id": current_user.id}, {"_id": 0})
        .sort("created_at", -1)
    )
    return [
        schemas_text.DocumentSummaryResponse(
            document_id=str(d.get("document_id")),
            title=d.get("title"),
            source_type=str(d.get("source_type", "text")),
            paragraph_count=int(d.get("paragraph_count", 0)),
            created_at=d.get("created_at", utcnow()),
        )
        for d in docs
    ]


@router.get(
    "/{document_id}",
    response_model=schemas_text.DocumentResponse,
    summary="Lấy tài liệu theo ID (kèm danh sách đoạn)",
)
def get_document(
    document_id: str,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    doc = db["documents"].find_one({"document_id": document_id, "user_id": current_user.id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
    return _doc_to_response(db, doc)


@router.get(
    "/{document_id}/original",
    summary="Lấy file gốc đã upload",
)
def get_original_file(
    document_id: str,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    doc = db["documents"].find_one(
        {"document_id": document_id, "user_id": current_user.id, "source_type": "file"},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")

    file_path = _original_file_path_from_doc_id(document_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="Không tìm thấy file gốc")

    filename = os.path.basename(file_path).split("__", 1)[1] if "__" in os.path.basename(file_path) else os.path.basename(file_path)
    return FileResponse(path=file_path, filename=filename)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa tài liệu",
)
def delete_document(
    document_id: str,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    doc = db["documents"].find_one({"document_id": document_id, "user_id": current_user.id}, {"_id": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")

    original_path = _original_file_path_from_doc_id(document_id)
    db["documents"].delete_one({"document_id": document_id, "user_id": current_user.id})
    db["paragraphs"].delete_many({"document_id": document_id})
    db["analyses"].delete_many({"document_id": document_id, "user_id": current_user.id})
    db["rewrites"].delete_many({"document_id": document_id, "user_id": current_user.id})

    sessions = list(db["chat_sessions"].find({"document_id": document_id, "user_id": current_user.id}, {"session_id": 1}))
    for s in sessions:
        db["chat_messages"].delete_many({"session_id": int(s["session_id"])})
    db["chat_sessions"].delete_many({"document_id": document_id, "user_id": current_user.id})

    if original_path and os.path.exists(original_path):
        try:
            os.remove(original_path)
        except OSError:
            pass
