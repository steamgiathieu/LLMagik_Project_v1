"""
routers/auth_router.py

Authentication endpoints:
  - POST /auth/register — Đăng ký người dùng mới
  - POST /auth/login    — Đăng nhập & nhận JWT token
  - GET /auth/me        — Lấy thông tin user hiện tại
  - PUT /auth/profile   — Cập nhật profile của user
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Any
from datetime import timedelta
import os
import logging

from pymongo import MongoClient

from database import get_db
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
import models

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────

# Supported languages
SUPPORTED_LANGUAGES = {"vi", "en", "zh", "ja", "fr"}
SUPPORTED_ROLES = {"reader", "writer", "both"}
SUPPORTED_AGE_GROUPS = {"teen", "adult", "senior"}


_mongo_client: Optional[MongoClient] = None
_mongo_users_collection = None
_mongo_profiles_collection = None
_mongo_init_attempted = False


def _mongo_db_name_from_uri(uri: str) -> str:
    tail = uri.split("://", 1)[-1]
    path = tail.split("/", 1)[-1] if "/" in tail else ""
    db_part = path.split("?", 1)[0].strip()
    return db_part or (os.getenv("MONGODB_DB_NAME", "llmagik").strip() or "llmagik")


def _init_mongo_auth_collections():
    global _mongo_client, _mongo_users_collection, _mongo_profiles_collection, _mongo_init_attempted
    if _mongo_init_attempted:
        return
    _mongo_init_attempted = True

    uri = (os.getenv("MONGODB_URI") or os.getenv("MONGODB_URL") or "").strip()
    if not uri:
        return

    try:
        db_name = (os.getenv("MONGODB_DB_NAME") or "").strip() or _mongo_db_name_from_uri(uri)
        _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=1500)
        # ping once so invalid URI/auth doesn't break later at login time
        _mongo_client.admin.command("ping")

        db = _mongo_client[db_name]
        _mongo_users_collection = db[(os.getenv("MONGODB_USERS_COLLECTION") or "users").strip() or "users"]
        _mongo_profiles_collection = db[(os.getenv("MONGODB_USER_PROFILES_COLLECTION") or "user_profiles").strip() or "user_profiles"]
    except Exception as exc:
        logger.warning("Mongo auth bridge disabled: %s", exc)
        _mongo_client = None
        _mongo_users_collection = None
        _mongo_profiles_collection = None


def _find_mongo_user(identifier: str) -> Optional[dict[str, Any]]:
    _init_mongo_auth_collections()
    if _mongo_users_collection is None:
        return None
    query = {"$or": [{"username": identifier}, {"email": identifier}]}
    return _mongo_users_collection.find_one(query)


def _mongo_password_hash(doc: dict[str, Any]) -> Optional[str]:
    for key in ("hashed_password", "password_hash", "passwordHash", "passwd_hash"):
        value = doc.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _mongo_profile(doc: dict[str, Any]) -> dict[str, str]:
    embedded = doc.get("profile") if isinstance(doc.get("profile"), dict) else {}

    profile_doc: dict[str, Any] = {}
    if embedded:
        profile_doc.update(embedded)

    # direct fields on user doc (common in simple schemas)
    for key in ("language", "role", "age_group"):
        if key in doc and doc.get(key) is not None:
            profile_doc[key] = doc.get(key)

    # optional dedicated profile collection
    _init_mongo_auth_collections()
    if _mongo_profiles_collection is not None:
        uid = doc.get("_id")
        profile_from_collection = _mongo_profiles_collection.find_one(
            {"$or": [{"user_id": uid}, {"user_id": str(uid)}]}
        )
        if isinstance(profile_from_collection, dict):
            profile_doc.update(profile_from_collection)

    return {
        "language": _normalize_language(str(profile_doc.get("language") or "vi"), "vi"),
        "role": _normalize_role(str(profile_doc.get("role") or "reader"), "reader"),
        "age_group": _normalize_age_group(str(profile_doc.get("age_group") or "adult"), "adult"),
    }


def _find_sql_user_by_identifier(db: Session, identifier: str) -> Optional[models.User]:
    return (
        db.query(models.User)
        .filter(
            (models.User.username == identifier) | (models.User.email == identifier)
        )
        .first()
    )


def _sync_sql_user_from_mongo(db: Session, mongo_user: dict[str, Any]) -> Optional[models.User]:
    hashed = _mongo_password_hash(mongo_user)
    if not hashed:
        return None

    username = str(mongo_user.get("username") or "").strip()
    email = str(mongo_user.get("email") or "").strip()
    nickname = str(mongo_user.get("nickname") or username or email or "User").strip() or "User"

    if not username and email:
        username = email.split("@", 1)[0]
    if not username:
        uid = str(mongo_user.get("_id") or "").strip() or "user"
        username = f"mongo_{uid[-8:]}"
    if not email:
        email = f"{username}@local.invalid"

    user = (
        db.query(models.User)
        .filter((models.User.username == username) | (models.User.email == email))
        .first()
    )

    if not user:
        user = models.User(
            username=username,
            email=email,
            nickname=nickname,
            hashed_password=hashed,
        )
        db.add(user)
        db.flush()
    else:
        # keep SQL mirror fresh with Mongo credentials/profile
        user.nickname = nickname
        user.hashed_password = hashed

    p = _mongo_profile(mongo_user)
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user.id).first()
    if not profile:
        profile = models.UserProfile(
            user_id=user.id,
            language=p["language"],
            role=p["role"],
            age_group=p["age_group"],
        )
        db.add(profile)
    else:
        profile.language = p["language"]
        profile.role = p["role"]
        profile.age_group = p["age_group"]

    db.commit()
    db.refresh(user)
    return user


def _upsert_mongo_user_profile(user: models.User, language: str, role: str, age_group: str) -> None:
    _init_mongo_auth_collections()
    if _mongo_users_collection is None:
        return
    try:
        _mongo_users_collection.update_one(
            {"$or": [{"username": user.username}, {"email": user.email}]},
            {
                "$set": {
                    "username": user.username,
                    "email": user.email,
                    "nickname": user.nickname,
                    "hashed_password": user.hashed_password,
                    "language": language,
                    "role": role,
                    "age_group": age_group,
                }
            },
            upsert=True,
        )
    except Exception as exc:
        logger.warning("Mongo user upsert skipped: %s", exc)

    if _mongo_profiles_collection is None:
        return
    try:
        _mongo_profiles_collection.update_one(
            {"user_id": user.id},
            {
                "$set": {
                    "user_id": user.id,
                    "language": language,
                    "role": role,
                    "age_group": age_group,
                }
            },
            upsert=True,
        )
    except Exception as exc:
        logger.warning("Mongo profile upsert skipped: %s", exc)


def _normalize_language(value: Optional[str], default: str = "vi") -> str:
    if not value:
        return default
    code = value.strip().lower()
    return code if code in SUPPORTED_LANGUAGES else default


def _normalize_role(value: Optional[str], default: str = "reader") -> str:
    if not value:
        return default
    role = value.strip().lower()
    return role if role in SUPPORTED_ROLES else default


def _normalize_age_group(value: Optional[str], default: str = "adult") -> str:
    if not value:
        return default
    age_group = value.strip().lower()
    return age_group if age_group in SUPPORTED_AGE_GROUPS else default

class RegisterRequest(BaseModel):
    """Yêu cầu đăng ký."""
    username: str = Field(..., min_length=3, max_length=50, examples=["john_doe"])
    email: str = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=6, examples=["securepass123"])
    nickname: str = Field(..., min_length=1, max_length=100, examples=["John"])
    language: Optional[str] = Field("vi", min_length=2, max_length=5, examples=["vi"])
    age_group: Optional[str] = Field("adult", examples=["adult"])


class LoginRequest(BaseModel):
    """Yêu cầu đăng nhập."""
    username: str = Field(..., examples=["john_doe"])
    password: str = Field(..., examples=["securepass123"])


class UserResponse(BaseModel):
    """Thông tin user."""
    id: int
    username: str
    email: str
    nickname: str
    created_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        data = {
            "id": obj.id,
            "username": obj.username,
            "email": obj.email,
            "nickname": obj.nickname,
            "created_at": obj.created_at.isoformat() if hasattr(obj.created_at, 'isoformat') else str(obj.created_at),
        }
        return cls(**data)


class TokenResponse(BaseModel):
    """Phản hồi token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserResponse] = None


class UserProfileResponse(BaseModel):
    """Thông tin profile user."""
    id: int
    username: str
    email: str
    nickname: str
    language: str
    role: str
    age_group: str
    created_at: str

    class Config:
        from_attributes = True


class UserWithProfileResponse(BaseModel):
    """User đầy đủ thông tin với profile."""
    id: int
    username: str
    email: str
    nickname: str
    created_at: str
    profile: UserProfileResponse  # Nested profile
    
    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Cập nhật profile."""
    nickname: Optional[str] = Field(None, min_length=1, max_length=100)
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    role: Optional[str] = Field(None)
    age_group: Optional[str] = Field(None)


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Đăng ký người dùng mới.
    
    Kiểm tra xem username và email có tồn tại chưa.
    Nếu không, tạo user mới và trả về JWT token trong cookie.
    """
    # Check if username/email already exists
    existing_username = db.query(models.User).filter(
        models.User.username == payload.username
    ).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên người dùng đã tồn tại",
        )

    existing_email = db.query(models.User).filter(
        models.User.email == payload.email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng",
        )

    # Optional Mongo duplicate checks (if Mongo auth bridge is enabled)
    existing_mongo_by_username = _find_mongo_user(payload.username)
    if existing_mongo_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên người dùng đã tồn tại",
        )

    existing_mongo_by_email = _find_mongo_user(payload.email)
    if existing_mongo_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được sử dụng",
        )

    # Create new user
    user = models.User(
        username=payload.username,
        email=payload.email,
        nickname=payload.nickname,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    lang = _normalize_language(payload.language)
    age_group = _normalize_age_group(payload.age_group)

    # Create user profile
    profile = models.UserProfile(
        user_id=user.id,
        language=lang,
        role="reader",
        age_group=age_group,
    )
    db.add(profile)
    db.commit()
    db.refresh(user)

    # Best-effort mirror to Mongo (for deployments storing auth users in Mongo)
    _upsert_mongo_user_profile(user, language=lang, role="reader", age_group=age_group)

    # Create access token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Set HTTP-only secure cookie
    if response:
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
            httponly=True,
            secure=os.getenv("ENVIRONMENT", "development") == "production",  # Only HTTPS in production
            samesite="lax",
            path="/",
        )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập",
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Đăng nhập với username và password.
    
    Trả về JWT access_token trong cookie nếu thành công.
    """
    user = _find_sql_user_by_identifier(db, payload.username)
    authenticated = bool(user and verify_password(payload.password, user.hashed_password))

    # Mongo fallback: if SQL doesn't have this account, try Mongo and sync into SQL.
    if not authenticated:
        mongo_user = _find_mongo_user(payload.username)
        mongo_hash = _mongo_password_hash(mongo_user) if mongo_user else None
        if mongo_user and mongo_hash and verify_password(payload.password, mongo_hash):
            user = _sync_sql_user_from_mongo(db, mongo_user)
            authenticated = user is not None

    if not authenticated or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên người dùng hoặc mật khẩu không đúng",
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Set HTTP-only secure cookie
    if response:
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
            httponly=True,
            secure=os.getenv("ENVIRONMENT", "development") == "production",  # Only HTTPS in production
            samesite="lax",
            path="/",
        )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Gia hạn token",
)
def refresh_token(
    response: Response,
    current_user: models.User = Depends(get_current_user),
):
    """
    Gia hạn JWT token bằng cách tạo token mới.
    
    Yêu cầu xác thực (JWT token hiện tại).
    """
    access_token = create_access_token(
        data={"sub": current_user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Update HTTP-only secure cookie
    if response:
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
            httponly=True,
            secure=os.getenv("ENVIRONMENT", "development") == "production",
            samesite="lax",
            path="/",
        )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_orm(current_user),
    )


@router.get(
    "/me",
    response_model=UserWithProfileResponse,
    summary="Lấy thông tin user hiện tại",
)
def get_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lấy thông tin profile của user hiện tại.
    
    Yêu cầu xác thực (JWT token).
    """
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        # Create default profile if not exists
        profile = models.UserProfile(
            user_id=current_user.id,
            language="vi",
            role="reader",
            age_group="adult",
        )
        db.add(profile)
        db.commit()

    # Build nested response with profile field
    profile_data = UserProfileResponse(
        id=profile.user_id,
        username=current_user.username,
        email=current_user.email,
        nickname=current_user.nickname,
        language=profile.language,
        role=profile.role,
        age_group=profile.age_group,
        created_at=current_user.created_at.isoformat() if hasattr(current_user.created_at, 'isoformat') else str(current_user.created_at),
    )
    
    return UserWithProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        nickname=current_user.nickname,
        created_at=current_user.created_at.isoformat() if hasattr(current_user.created_at, 'isoformat') else str(current_user.created_at),
        profile=profile_data,
    )


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="Cập nhật profile người dùng",
)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cập nhật profile của user.
    
    Các trường có thể cập nhật: nickname, language, role, age_group.
    """
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        profile = models.UserProfile(user_id=current_user.id)
        db.add(profile)

    # Update profile fields if provided
    if payload.nickname is not None:
        current_user.nickname = payload.nickname

    if payload.language is not None:
        profile.language = _normalize_language(payload.language, profile.language or "vi")

    if payload.role is not None:
        profile.role = _normalize_role(payload.role, profile.role or "reader")

    if payload.age_group is not None:
        profile.age_group = _normalize_age_group(payload.age_group, profile.age_group or "adult")

    db.commit()
    db.refresh(current_user)
    db.refresh(profile)

    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        nickname=current_user.nickname,
        language=profile.language,
        role=profile.role,
        age_group=profile.age_group,
        created_at=current_user.created_at.isoformat(),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Đăng xuất",
)
def logout(response: Response):
    """
    Đăng xuất người dùng bằng cách xóa cookie.
    """
    if response:
        response.delete_cookie(
            key="access_token",
            path="/",
        )
    
    return {"message": "Đã đăng xuất thành công"}
