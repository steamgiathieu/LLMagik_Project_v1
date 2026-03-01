import time
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pymongo.database import Database

from auth import AuthUser, get_current_user
from mongo import get_mongo_db_dependency, next_sequence, utcnow
import schemas_chat
from services.ai_service import get_provider
from services.text_processor import build_paragraph_list, split_paragraphs

router = APIRouter(prefix="/chat", tags=["Chat"])

MAX_PARAGRAPHS_IN_CONTEXT = 30
SUPPORTED_UI_LANGUAGES = {"vi", "en", "zh", "ja", "fr"}


def _resolve_ui_language(x_ui_language: str | None) -> str:
    if not x_ui_language:
        return "vi"
    code = x_ui_language.strip().lower()
    return code if code in SUPPORTED_UI_LANGUAGES else "vi"


def _create_inline_document(
    db: Database,
    user_id: int,
    context_text: str,
) -> dict:
    normalized = (context_text or "").strip()
    if len(normalized) < 10:
        raise HTTPException(status_code=422, detail="Ngữ liệu tự nhập quá ngắn để chat")

    para_list = build_paragraph_list(split_paragraphs(normalized))
    if not para_list:
        para_list = [{"id": "P1", "text": normalized}]

    doc_id = str(uuid4())
    now = utcnow()
    doc = {
        "document_id": doc_id,
        "user_id": user_id,
        "title": "Inline chat context",
        "source_type": "text",
        "source_ref": "chat:inline",
        "raw_text": normalized,
        "paragraph_count": len(para_list),
        "created_at": now,
        "updated_at": now,
    }
    db["documents"].insert_one(doc)
    db["paragraphs"].insert_many(
        [
            {
                "document_id": doc_id,
                "paragraph_id": p["id"],
                "index": idx,
                "text": p["text"],
            }
            for idx, p in enumerate(para_list)
        ]
    )
    return doc


def _get_or_create_session(
    db: Database,
    user_id: int,
    document_id: str,
    session_id: int | None,
) -> dict:
    if session_id is not None:
        session = db["chat_sessions"].find_one(
            {
                "session_id": session_id,
                "user_id": user_id,
                "document_id": document_id,
            },
            {"_id": 0},
        )
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session không tồn tại hoặc không thuộc tài liệu này",
            )
        return session

    session = {
        "session_id": next_sequence("session_id"),
        "user_id": user_id,
        "document_id": document_id,
        "created_at": utcnow(),
    }
    db["chat_sessions"].insert_one(session)
    return session


def _build_history(db: Database, session_id: int) -> list[dict]:
    msgs = list(
        db["chat_messages"]
        .find({"session_id": session_id}, {"_id": 0, "role": 1, "content": 1})
        .sort("message_id", 1)
    )
    return [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in msgs]


def _msg_to_out(msg: dict) -> schemas_chat.ChatMessageOut:
    return schemas_chat.ChatMessageOut(
        message_id=int(msg["message_id"]),
        role=str(msg.get("role", "assistant")),
        content=str(msg.get("content", "")),
        referenced_paragraphs=msg.get("referenced_paragraphs"),
        confidence=msg.get("confidence"),
        out_of_scope=msg.get("out_of_scope"),
        processing_ms=msg.get("processing_ms"),
        created_at=msg.get("created_at", utcnow()),
    )


@router.post(
    "/",
    response_model=schemas_chat.ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Hỏi AI về nội dung văn bản",
)
async def chat(
    payload: schemas_chat.ChatRequest,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
    x_ui_language: str | None = Header(default=None, alias="X-UI-Language"),
):
    inline_text = (payload.context_text or "").strip()

    if payload.document_id:
        doc = db["documents"].find_one(
            {"document_id": payload.document_id, "user_id": current_user.id},
            {"_id": 0},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại")
    elif inline_text:
        doc = _create_inline_document(db, current_user.id, inline_text)
    else:
        raise HTTPException(status_code=422, detail="Cần cung cấp document_id hoặc context_text để chat")

    paragraph_docs = list(
        db["paragraphs"]
        .find({"document_id": doc["document_id"]}, {"_id": 0})
        .sort("index", 1)
    )
    if not paragraph_docs:
        raise HTTPException(status_code=422, detail="Tài liệu chưa có đoạn văn nào để trả lời câu hỏi")

    session = _get_or_create_session(db, current_user.id, doc["document_id"], payload.session_id)

    paragraphs = [
        {"id": p["paragraph_id"], "text": p["text"]}
        for p in paragraph_docs[:MAX_PARAGRAPHS_IN_CONTEXT]
    ]
    history = _build_history(db, int(session["session_id"]))

    user_message_id = next_sequence("chat_message_id")
    db["chat_messages"].insert_one(
        {
            "message_id": user_message_id,
            "session_id": int(session["session_id"]),
            "role": "user",
            "content": payload.user_question,
            "created_at": utcnow(),
        }
    )

    request_language = _resolve_ui_language(x_ui_language)
    provider = get_provider()
    t0 = time.monotonic()
    try:
        ai_result = await provider.chat(
            question=payload.user_question,
            paragraphs=paragraphs,
            history=history,
            language=request_language,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service lỗi: {e}")
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    answer = ai_result.get("answer", "")
    ref_paragraphs = ai_result.get("referenced_paragraphs", [])
    confidence = ai_result.get("confidence", "medium")
    out_of_scope = bool(ai_result.get("out_of_scope", False))

    if not answer:
        raise HTTPException(status_code=502, detail="AI không trả về câu trả lời hợp lệ")

    valid_ids = {str(p["paragraph_id"]) for p in paragraph_docs}
    ref_paragraphs = [pid for pid in ref_paragraphs if pid in valid_ids]

    assistant_message_id = next_sequence("chat_message_id")
    assistant_doc = {
        "message_id": assistant_message_id,
        "session_id": int(session["session_id"]),
        "role": "assistant",
        "content": answer,
        "referenced_paragraphs": ref_paragraphs,
        "confidence": confidence,
        "out_of_scope": out_of_scope,
        "processing_ms": elapsed_ms,
        "created_at": utcnow(),
    }
    db["chat_messages"].insert_one(assistant_doc)

    return schemas_chat.ChatResponse(
        session_id=int(session["session_id"]),
        document_id=str(doc["document_id"]),
        message_id=assistant_message_id,
        answer=answer,
        referenced_paragraphs=ref_paragraphs,
        confidence=confidence,
        out_of_scope=out_of_scope,
        processing_ms=elapsed_ms,
        created_at=assistant_doc["created_at"],
    )


@router.get(
    "/sessions",
    response_model=List[schemas_chat.ChatSessionOut],
    summary="Danh sách session chat của người dùng",
)
def list_sessions(
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    sessions = list(
        db["chat_sessions"]
        .find({"user_id": current_user.id}, {"_id": 0})
        .sort("created_at", -1)
    )
    out: list[schemas_chat.ChatSessionOut] = []
    for s in sessions:
        message_count = db["chat_messages"].count_documents({"session_id": int(s["session_id"])})
        out.append(
            schemas_chat.ChatSessionOut(
                session_id=int(s["session_id"]),
                document_id=str(s["document_id"]),
                message_count=message_count,
                created_at=s.get("created_at", utcnow()),
            )
        )
    return out


@router.get(
    "/sessions/{session_id}",
    response_model=schemas_chat.ChatHistoryResponse,
    summary="Lấy toàn bộ lịch sử hội thoại của một session",
)
def get_session_history(
    session_id: int,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    session = db["chat_sessions"].find_one(
        {"session_id": session_id, "user_id": current_user.id},
        {"_id": 0},
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session không tồn tại")

    msgs = list(
        db["chat_messages"]
        .find({"session_id": session_id}, {"_id": 0})
        .sort("message_id", 1)
    )
    return schemas_chat.ChatHistoryResponse(
        session_id=session_id,
        document_id=str(session["document_id"]),
        messages=[_msg_to_out(m) for m in msgs],
        created_at=session.get("created_at", utcnow()),
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa session chat",
)
def delete_session(
    session_id: int,
    db: Database = Depends(get_mongo_db_dependency),
    current_user: AuthUser = Depends(get_current_user),
):
    session = db["chat_sessions"].find_one(
        {"session_id": session_id, "user_id": current_user.id},
        {"_id": 1},
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session không tồn tại")

    db["chat_messages"].delete_many({"session_id": session_id})
    db["chat_sessions"].delete_one({"session_id": session_id, "user_id": current_user.id})
