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
from typing import Optional
from datetime import timedelta
import os

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


# ─────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Yêu cầu đăng ký."""
    username: str = Field(..., min_length=3, max_length=50, examples=["john_doe"])
    email: str = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=6, examples=["securepass123"])
    nickname: str = Field(..., min_length=1, max_length=100, examples=["John"])


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
    nickname: str = Field(None, min_length=1, max_length=100)
    language: str = Field(None, min_length=2, max_length=10)
    role: str = Field(None)
    age_group: str = Field(None)


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

    # Create new user
    user = models.User(
        username=payload.username,
        email=payload.email,
        nickname=payload.nickname,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    # Create user profile
    profile = models.UserProfile(
        user_id=user.id,
        language="vi",
        role="reader",
        age_group="adult",
    )
    db.add(profile)
    db.commit()
    db.refresh(user)

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
    user = db.query(models.User).filter(
        models.User.username == payload.username
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
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
        profile.language = payload.language

    if payload.role is not None:
        profile.role = payload.role

    if payload.age_group is not None:
        profile.age_group = payload.age_group

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
