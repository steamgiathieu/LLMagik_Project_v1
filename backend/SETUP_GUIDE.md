# Backend Setup & Deployment Guide

## Quick Start (Development)

### Prerequisites
- Python 3.9+
- pip or conda
- Git

### Step 1: Clone Repository
```bash
cd /path/to/LLMagik
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
# At minimum, set SECRET_KEY to a random string:
# python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Test Imports
```bash
python test_imports.py
# Should output: ✓ All imports successful! Backend is ready to start.
```

### Step 6: Start Server
```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode (no reload)
uvicorn main:app --host 0.0.0.0 --port 8000
```

Server will be available at: **http://localhost:8000**

### Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Environment Variables

### Required
```env
SECRET_KEY=<32+ character random string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
DATABASE_URL=sqlite:///./app.db
```

### Optional
```env
# AI Provider: mock (default) | openai | anthropic
AI_PROVIDER=mock

# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-haiku-20240307

# CORS Origins (development)
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

---

## Testing the Backend

### 1. Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}
```

### 2. Register User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "nickname": "Test User"
  }'
```

### 3. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
# Copy the access_token from response
```

### 4. Get Current User
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### 5. Upload Text
```bash
curl -X POST http://localhost:8000/texts/from-text \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a sample document. It contains multiple paragraphs. Each paragraph should be at least a few sentences long."
  }'
```

---

## Production Deployment

### 1. Use PostgreSQL (Recommended)
```python
# .env
DATABASE_URL=postgresql://user:password@localhost/llmagik_db
```

### 2. Set Production Environment
```bash
export ENVIRONMENT=production
export DEBUG=false
```

### 3. Use Gunicorn
```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 4. Set Proper CORS Origins
```env
CORS_ORIGINS=["https://yourdomain.com"]
```

### 5. Use HTTPS
- Configure SSL/TLS certificate
- Use reverse proxy (nginx, Apache)
- Redirect HTTP to HTTPS

### 6. Set Strong SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(42))"
```

---

## Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV AI_PROVIDER=mock
ENV DATABASE_URL=sqlite:///./app.db

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build & Run
```bash
docker build -t llmagik-backend .
docker run -p 8000:8000 --env-file .env llmagik-backend
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'X'"
**Solution**: Run `test_imports.py` to check which imports fail
```bash
python test_imports.py
```

### Issue: "CORS error in frontend"
**Solution**: Update CORS_ORIGINS in .env to include your frontend URL
```env
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000", "https://yourdomain.com"]
```

### Issue: "Database is locked"
**Solution**: You're using SQLite with multiple processes. Switch to PostgreSQL for production.

### Issue: "Secret key not set"
**Solution**: Generate and set SECRET_KEY in .env
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))" >> .env
```

### Issue: "AI provider error"
**Solution**: 
1. If using OpenAI/Anthropic, check API keys in .env
2. To use mock provider, set `AI_PROVIDER=mock`

---

## Monitoring & Logging

### Enable Request Logging
```python
# Add to main.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response
```

### Database Query Logging
```python
# In database.py
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## Performance Tips

1. **Use PostgreSQL** instead of SQLite for production
2. **Add database indexes** on frequently queried fields
3. **Enable query caching** for read-heavy operations
4. **Use connection pooling** for database
5. **Add Redis** for session caching
6. **Monitor AI service latency** and add timeouts
7. **Implement rate limiting** for API endpoints

---

## Security Checklist

- [ ] Set strong SECRET_KEY (32+ characters)
- [ ] Use HTTPS in production
- [ ] Validate all user inputs
- [ ] Use parameterized queries (SQLAlchemy ORM)
- [ ] Implement rate limiting
- [ ] Add request size limits (10MB for file uploads)
- [ ] Store sensitive data in .env (never commit)
- [ ] Use secure password requirements
- [ ] Implement audit logging
- [ ] Regular security updates for dependencies

---

## Recent Changes (Feb 2024)

### ✓ Created `auth_router.py`
- Complete authentication system
- Register, login, profile management

### ✓ Fixed Import Issues
- Corrected relative imports in `texts_router.py`
- Removed invalid `backend.` prefixes

### ✓ Updated `.env.example`
- Added AI_PROVIDER configuration
- Added API key placeholders
- Added CORS configuration

### ✓ Added Testing Tools
- `test_imports.py` - Verify all imports work

---

## Support & Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger)
- **Code Review**: See `REVIEW_SUMMARY.md`
- **Code Structure**: See `README.md`

---

Last Updated: 2025-02-21
