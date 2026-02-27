# 🚀 LLMagik - AI Text Analysis Application

Fullstack web application for intelligent text analysis, rewriting, and chat powered by AI.

**Backend**: FastAPI + SQLAlchemy + SQLite/PostgreSQL  
**Frontend**: React 18 + TypeScript + Zustand + Vite

## 📁 Project Structure

```
LLMagik/
├── backend/                    # FastAPI backend
│   ├── main.py                # App entry point, CORS, router registration  
│   ├── database.py            # SQLAlchemy engine, session, Base
│   ├── auth.py                # JWT utils, password hashing, get_current_user
│   ├── models.py              # User, UserProfile models
│   ├── models_text.py         # Document, Paragraph models
│   ├── models_analysis.py     # Analysis result model
│   ├── models_rewrite.py      # Rewrite result model
│   ├── models_chat.py         # ChatSession, ChatMessage models
│   ├── schemas_*.py           # Pydantic request/response schemas (4 files)
│   ├── routers/               # API routers
│   │   ├── auth_router.py     # /auth/* (register, login, profile)
│   │   ├── texts_router.py    # /texts/* (upload, list, get, delete)
│   │   ├── analysis_router.py # /analysis/* (analyze, history)
│   │   ├── rewrite_router.py  # /rewrite/* (rewrite, presets, history)
│   │   ├── chat_router.py     # /chat/* (chat, sessions, history)
│   │   └── history_router.py  # /history/* (all activities, stats)
│   ├── services/
│   │   ├── ai_service.py      # AI service (Groq)
│   │   └── text_processor.py  # Text utilities
│   ├── requirements.txt
│   ├── .env
│   └── test_imports.py
│
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── App.tsx            # Main app component
│   │   ├── main.tsx           # React entry point
│   │   ├── index.tsx          # HTML entry point
│   │   ├── pages/             # Page components
│   │   │   ├── Login.tsx
│   │   │   ├── Home.tsx
│   │   │   ├── Reader.tsx
│   │   │   ├── Profile.tsx
│   │   │   └── History.tsx
│   │   ├── components/        # Reusable components
│   │   │   ├── Navbar.tsx
│   │   │   ├── UploadModal.tsx
│   │   │   ├── AnalysisPanel.tsx
│   │   │   ├── ChatBox.tsx
│   │   │   └── RewritePanel.tsx
│   │   ├── store/             # Zustand stores
│   │   │   ├── authStore.ts
│   │   │   ├── documentStore.ts
│   │   │   ├── analysisStore.ts
│   │   │   ├── chatStore.ts
│   │   │   └── historyStore.ts
│   │   ├── hooks/             # Custom hooks
│   │   │   ├── useApi.ts
│   │   │   └── usePagination.ts
│   │   ├── api/
│   │   │   └── client.ts      # Centralized API client
│   │   ├── types/
│   │   │   └── index.ts       # TypeScript type definitions
│   │   └── *.css              # Page/component styles
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── .env
│   └── public/
│
├── start.sh                   # Bash startup script (Linux/Mac)
├── start.ps1                  # PowerShell startup script (Windows)
├── README.md                  # This file
├── PROJECT_SUMMARY.md         # Complete project overview
├── COMPLETION_CHECKLIST.md    # Feature checklist
├── backend/SETUP_GUIDE.md     # Backend setup guide
├── backend/REVIEW_SUMMARY.md  # Code review notes
└── frontend/SETUP_GUIDE.md    # Frontend setup guide
```

## 🚀 Quick Start

### Option 1: Automated (Recommended)

**Windows (PowerShell):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual Setup

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate              # Linux/Mac
# or
venv\Scripts\activate                 # Windows

# Install dependencies  
pip install -r requirements.txt

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Configure backend/.env
# Edit backend/.env and paste SECRET_KEY + GROQ_API_KEY

# Run backend
uvicorn main:app --reload --port 8000
```

**Frontend (in new terminal):**
```bash
cd frontend

# Install dependencies
npm install

# Configure frontend/.env
# VITE_API_URL should be http://localhost:8000

# Run dev server
npm run dev
```

### 📍 Access Points

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## � Deploy to Production (GitHub Pages + Render)

**Quick deployment in 3 steps:**

```powershell
# Windows
.\deploy.ps1

# Linux/Mac
chmod +x deploy.sh
./deploy.sh
```

**Then follow [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for:**
- ✅ Frontend → GitHub Pages (free)
- ✅ Backend → Render (free tier available)
- ✅ Custom domain setup (optional)

**Result:**
- Frontend: `https://YOUR-USERNAME.github.io/LLMagik`
- Backend: `https://your-backend.onrender.com`

---

## �📡 API Endpoints Overview

### Authentication (6 endpoints)
- `POST /auth/register` - Register new account
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info
- `PUT /auth/profile` - Update profile settings

### Document Management (6 endpoints)
- `POST /texts/from-text` - Upload plain text
- `POST /texts/from-url` - Extract text from URL
- `POST /texts/from-file` - Upload file (PDF, DOCX, TXT)
- `GET /texts/` - List all documents
- `GET /texts/{id}` - Get document details
- `DELETE /texts/{id}` - Delete document

### Analysis (2 endpoints)
- `POST /analysis/analyze` - Analyze document (reader/writer mode)
- `GET /analysis/history` - Get analysis history

### Rewriting (3 endpoints)
- `POST /rewrite/` - Rewrite paragraph with goal
- `GET /rewrite/presets` - Get available rewrite goals
- `GET /rewrite/history` - Get rewrite history

### Chat (4 endpoints)
- `POST /chat/` - Ask question about document
- `GET /chat/sessions` - List chat sessions
- `GET /chat/sessions/{id}` - Get chat conversation
- `DELETE /chat/sessions/{id}` - Delete session

### History (5 endpoints)
- `GET /history/all` - Get all activities
- `GET /history/analyses` - Analysis history
- `GET /history/rewrites` - Rewrite history
- `GET /history/chats` - Chat history
- `GET /history/stats` - User statistics

**Total: 26+ API endpoints**

---

## 🤖 AI Provider Setup (Rewrite thực tế)

Hệ thống dùng **Groq** cho AI features (analyze/rewrite/chat):

1. Tạo API key tại: `https://console.groq.com/keys`
2. Sửa `backend/.env`:

```env
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.1-8b-instant
```

Khi đã cấu hình key, endpoint `POST /rewrite/` sẽ trả kết quả viết lại thực tế bằng Groq.

---

## 🔗 API Usage Examples

### Example 1: Register & Login

**Register:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "password": "secret123",
    "nickname": "John Doe"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "secret123"}'
```

Response (save `access_token` for next requests):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {"id": 1, "username": "john", "email": "john@example.com"}
}
```

### Example 2: Upload Document & Analyze

**Upload text:**
```bash
TOKEN="your_access_token"
curl -X POST http://localhost:8000/texts/from-text \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Article",
    "content": "Your text here..."
  }'
```

**Analyze document (Reader mode):**
```bash
curl -X POST http://localhost:8000/analysis/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 1,
    "mode": "reader",
    "paragraphs": [0, 1, 2]
  }'
```

### Example 3: Ask Question to Document

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": 1,
    "question": "What is the main topic?"
  }'
```

---

## 🐛 Debugging & Logging

### Backend Debugging

**Start with detailed logging:**
```bash
cd backend
source venv/bin/activate
PYTHONUNBUFFERED=1 uvicorn main:app --reload --log-level debug
```

**Test backend directly:**
```bash
# Open browser: http://localhost:8000/docs
# This opens Swagger UI to test all endpoints
```

**Check database:**
```bash
# List all tables (if using SQLite)
sqlite3 backend/llmagik.db ".tables"
```

### Frontend Debugging

**Browser DevTools (F12):**
- **Console**: Fetch errors, TypeScript issues
- **Network**: Check API requests/responses  
- **Application**: localStorage for auth token and state
- **React DevTools**: Inspect component state

**Common Frontend Issues:**
- CORS error → Check `VITE_API_URL` in `frontend/.env`
- 401 error → Token expired, logout and login again
- Cannot find module → `rm -rf node_modules && npm install`
- Port in use → `npm run dev -- --port 5174`

### Full Debugging Guide

See **[DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)** for:
- Detailed troubleshooting steps
- API testing tools (Postman, curl, REST Client)
- Common issues & solutions
- Testing checklists

---

## ✅ Testing Checklist

### Phase 1: Server Status (5 mins)
- [ ] Backend: http://localhost:8000/docs accessible
- [ ] Frontend: http://localhost:5173 loads
- [ ] No CORS errors in browser console

### Phase 2: Authentication (10 mins)
- [ ] Register new account
- [ ] Login with credentials
- [ ] View profile information
- [ ] Update user preferences

### Phase 3: Documents (10 mins)
- [ ] Upload text document
- [ ] Upload from URL
- [ ] Upload file (PDF/TXT)
- [ ] View document list
- [ ] Delete document

### Phase 4: AI Features (15 mins)
- [ ] Analyze document (Reader mode)
- [ ] Analyze document (Writer mode)
- [ ] Chat with document AI
- [ ] Rewrite paragraph
- [ ] View activity history

### Phase 5: API Endpoints (10 mins)
Test all endpoints in Swagger UI: http://localhost:8000/docs

---

## 📚 Documentation Files

- **README.md** - This file
- **[DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)** - Troubleshooting & testing
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview
- **[COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md)** - Features & status
- **[backend/SETUP_GUIDE.md](backend/SETUP_GUIDE.md)** - Backend deployment
- **[backend/REVIEW_SUMMARY.md](backend/REVIEW_SUMMARY.md)** - Code review notes
- **[frontend/SETUP_GUIDE.md](frontend/SETUP_GUIDE.md)** - Frontend deployment

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       React Frontend                         │
│  (Pages, Components, Zustand Stores, TypeScript)            │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/JSON
                       ↕ Bearer Token Auth
┌──────────────────────┴──────────────────────────────────────┐
│                     FastAPI Backend                          │
│  (Routers, Models, Services, Database)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQL Queries
                       ↕ 
┌──────────────────────┴──────────────────────────────────────┐
│                    SQLite Database                           │
│  (Users, Documents, Analysis, Chat, History)               │
└──────────────────────────────────────────────────────────────┘
```

**Frontend → Backend Communication:**
1. User action in React component
2. Call Zustand store action
3. Store calls API client
4. API client sends HTTP request + JWT token
5. Backend validates token
6. Backend processes request
7. Backend returns JSON response
8. Store updates state
9. React re-renders component

---

## 🔐 Security Features

✅ Password hashing with bcrypt  
✅ JWT token authentication  
✅ CORS protection (origin validation)  
✅ Input validation with Pydantic  
✅ SQL injection prevention (SQLAlchemy ORM)  
✅ Automatic token expiration  
✅ User-scoped data access (can't access other users' data)  

---

## 📊 Technology Stack

**Frontend:**
- React 18.3 + TypeScript 5.4
- Vite 5.1 (next-gen build tool)
- Zustand 4.5 (lightweight state management)
- React Router v6 (client routing)
- CSS Modules (component styling)

**Backend:**
- FastAPI 0.100+ (async web framework)
- Python 3.9+
- SQLAlchemy 2.0+ (ORM)
- SQLite (dev) / PostgreSQL (production)
- python-jose (JWT tokens)
- bcrypt (password hashing)
- Pydantic (data validation)

**Deployment:**
- Frontend: Netlify, Vercel, or AWS S3 + CloudFront
- Backend: Heroku, AWS EC2, DigitalOcean, or Docker
- Database: PostgreSQL (managed by Neon, Render, etc.)

---

## 🎯 Next Steps

1. **[Setup & Run](README.md#-quick-start)** - Start both servers
2. **[Test Application](DEBUGGING_GUIDE.md#-next-steps---testing--validation)** - Validate all features  
3. **Configure AI in [`backend/.env`](backend/.env)** - Set `GROQ_API_KEY`
4. **[Deploy to Production](backend/SETUP_GUIDE.md#deployment)** - Go live

---

## 📄 License & Credits

This is an educational/portfolio project demonstrating:
- Full-stack web development (Frontend + Backend)
- TypeScript + Python best practices
- AI integration patterns
- Database design
- API design
- State management
- Authentication & Security

---

**Status**: ✅ Ready for Development & Testing  
**Last Updated**: February 21, 2025

For detailed guidance, see [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md)
