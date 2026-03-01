"""
routers/auth_router.py

MongoDB-only authentication endpoints.
"""
from datetime import timedelta
from typing import Optional
import os

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from pymongo.database import Database

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    AuthUser,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from mongo import ensure_default_profile, get_mongo_db_dependency, next_sequence, utcnow

router = APIRouter(prefix="/auth", tags=["Authentication"])

SUPPORTED_ROLES = {"reader", "writer", "both"}
SUPPORTED_AGE_GROUPS = {"teen", "adult", "senior"}


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
    username: str = Field(..., min_length=3, max_length=50, examples=["john_doe"])
    email: Optional[str] = Field(None, examples=["john@example.com"])
    password: str = Field(..., min_length=6, examples=["securepass123"])
    nickname: str = Field(..., min_length=1, max_length=100, examples=["John"])
    age_group: Optional[str] = Field("adult", examples=["adult"])


class LoginRequest(BaseModel):
    username: str = Field(..., examples=["john_doe"])
    password: str = Field(..., examples=["securepass123"])


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    nickname: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserResponse] = None


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    nickname: str
    language: str
    role: str
    age_group: str
    created_at: str


class UserWithProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    nickname: str
    created_at: str
    profile: UserProfileResponse


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None)
    age_group: Optional[str] = Field(None)


def _user_to_response(user_doc: dict) -> UserResponse:
    created_at = user_doc.get("created_at")
    created_text = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
    return UserResponse(
        id=int(user_doc["user_id"]),
        username=str(user_doc["username"]),
        email=str(user_doc["email"]),
        nickname=str(user_doc["nickname"]),
        created_at=created_text,
    )


def _set_auth_cookie(response: Response, access_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "development") == "production",
        samesite="lax",
        path="/",
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Database = Depends(get_mongo_db_dependency),
):
    username = payload.username.strip()
    if db["users"].find_one({"username": username}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tên người dùng đã tồn tại")

    email = (payload.email or "").strip().lower() or f"{username}@llmagik.local"
    if db["users"].find_one({"email": email}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được sử dụng")

    now = utcnow()
    user_id = next_sequence("user_id")
    user_doc = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "nickname": payload.nickname.strip(),
        "hashed_password": hash_password(payload.password),
        "created_at": now,
        "updated_at": now,
    }
    db["users"].insert_one(user_doc)

    db["user_profiles"].insert_one(
        {
            "user_id": user_id,
            "language": "vi",
            "role": "reader",
            "age_group": _normalize_age_group(payload.age_group),
            "created_at": now,
            "updated_at": now,
        }
    )

    access_token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    _set_auth_cookie(response, access_token)

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_to_response(user_doc),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập",
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Database = Depends(get_mongo_db_dependency),
):
    user_doc = db["users"].find_one({"username": payload.username.strip()})
    if not user_doc or not verify_password(payload.password, str(user_doc.get("hashed_password", ""))):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên người dùng hoặc mật khẩu không đúng",
        )

    access_token = create_access_token(
        data={"sub": str(user_doc["username"])},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    _set_auth_cookie(response, access_token)

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_to_response(user_doc),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Gia hạn token",
)
def refresh_token(
    response: Response,
    current_user: AuthUser = Depends(get_current_user),
):
    access_token = create_access_token(
        data={"sub": current_user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    _set_auth_cookie(response, access_token)

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            nickname=current_user.nickname,
            created_at=current_user.created_at.isoformat(),
        ),
    )


@router.get(
    "/me",
    response_model=UserWithProfileResponse,
    summary="Lấy thông tin user hiện tại",
)
def get_me(
    current_user: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_mongo_db_dependency),
):
    profile = db["user_profiles"].find_one({"user_id": current_user.id})
    if not profile:
        profile = ensure_default_profile(current_user.id)

    profile_data = UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        nickname=current_user.nickname,
        language=str(profile.get("language", "vi")),
        role=str(profile.get("role", "reader")),
        age_group=str(profile.get("age_group", "adult")),
        created_at=current_user.created_at.isoformat(),
    )

    return UserWithProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        nickname=current_user.nickname,
        created_at=current_user.created_at.isoformat(),
        profile=profile_data,
    )


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="Cập nhật profile người dùng",
)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Database = Depends(get_mongo_db_dependency),
):
    if payload.nickname is not None:
        db["users"].update_one(
            {"user_id": current_user.id},
            {"$set": {"nickname": payload.nickname, "updated_at": utcnow()}},
        )
        current_user.nickname = payload.nickname

    set_doc = {"updated_at": utcnow()}
    if payload.role is not None:
        set_doc["role"] = _normalize_role(payload.role)
    if payload.age_group is not None:
        set_doc["age_group"] = _normalize_age_group(payload.age_group)

    db["user_profiles"].update_one(
        {"user_id": current_user.id},
        {
            "$set": set_doc,
            "$setOnInsert": {
                "language": "vi",
                "role": "reader",
                "age_group": "adult",
                "created_at": utcnow(),
            },
        },
        upsert=True,
    )

    profile = db["user_profiles"].find_one({"user_id": current_user.id}) or {}

    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        nickname=current_user.nickname,
        language=str(profile.get("language", "vi")),
        role=str(profile.get("role", "reader")),
        age_group=str(profile.get("age_group", "adult")),
        created_at=current_user.created_at.isoformat(),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Đăng xuất",
)
def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Đã đăng xuất thành công"}
