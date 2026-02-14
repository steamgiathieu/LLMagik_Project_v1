# TextAnalyzer Backend

FastAPI + SQLite backend cho ứng dụng đọc và phân tích văn bản AI.

## Cấu trúc

```
backend/
├── main.py              # App entry point, CORS, router registration
├── database.py          # SQLAlchemy engine, session, Base
├── models.py            # ORM models: User, UserProfile
├── schemas.py           # Pydantic request/response schemas
├── auth.py              # JWT utils, password hashing, get_current_user
├── routers/
│   └── auth_router.py   # /auth/* endpoints
├── requirements.txt
└── .env.example
```

## Cài đặt & Chạy local

```bash
# 1. Tạo virtualenv
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Tạo file .env
cp .env.example .env
# Sửa SECRET_KEY thành chuỗi random dài >= 32 ký tự

# 4. Chạy server
uvicorn main:app --reload --port 8000
```

Server chạy tại: http://localhost:8000  
Swagger UI: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

---

## API Examples

### 1. Đăng ký

**POST** `/auth/register`

```json
// Request
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secret123",
  "nickname": "John"
}

// Response 201
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "nickname": "John",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

### 2. Đăng nhập

**POST** `/auth/login`

```json
// Request
{
  "username": "john_doe",
  "password": "secret123"
}

// Response 200
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "nickname": "John",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

### 3. Lấy thông tin bản thân

**GET** `/auth/me`  
Header: `Authorization: Bearer <token>`

```json
// Response 200
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "nickname": "John",
  "created_at": "2024-01-15T10:00:00Z",
  "profile": {
    "user_id": 1,
    "language": "vi",
    "role": "reader",
    "age_group": "adult",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

### 4. Cập nhật hồ sơ

**PUT** `/auth/profile`  
Header: `Authorization: Bearer <token>`

```json
// Request (tất cả fields đều optional)
{
  "language": "en",
  "role": "writer",
  "age_group": "teen"
}

// Response 200
{
  "user_id": 1,
  "language": "en",
  "role": "writer",
  "age_group": "teen",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### 5. Lấy hồ sơ

**GET** `/auth/profile`  
Header: `Authorization: Bearer <token>`

```json
// Response 200
{
  "user_id": 1,
  "language": "vi",
  "role": "reader",
  "age_group": "adult",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

---

## Giá trị hợp lệ

| Field | Giá trị |
|---|---|
| `role` | `reader` \| `writer` \| `both` |
| `language` | `vi`, `en`, hoặc bất kỳ mã ngôn ngữ nào |
| `age_group` | `teen`, `adult`, `senior` hoặc tự định nghĩa |

## Error Responses

```json
// 400 Bad Request
{ "detail": "Username đã tồn tại" }

// 401 Unauthorized
{ "detail": "Username hoặc password không đúng" }

// 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 6 characters",
      "type": "string_too_short"
    }
  ]
}
```
