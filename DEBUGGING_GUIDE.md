## 🐛 Debugging & Logging Guide

### 1. Check Backend Server Status

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
uvicorn main:app --reload --port 8000 --log-level debug
```

Look for:
- ✅ `Uvicorn running on http://127.0.0.1:8000`
- ⚠️ Any import errors or dependency issues
- 🔍 Logs showing received requests

**Test backend directly:**
```bash
curl http://localhost:8000/docs
# Opens Swagger UI where you can test all endpoints
```

### 2. Check Frontend Server Status

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Look for:
- ✅ `  VITE v5.x.x  ready in xxx ms`
- ✅ `➜  Local:   http://localhost:5173/`
- ⚠️ Any TypeScript errors or import issues
- 🔍 Hot reload working when files change

**Common Frontend Issues:**
- Port 5173 already in use: `npm run dev -- --port 5174`
- Module not found: `rm -rf node_modules && npm install`
- TypeScript errors: Check `terminal/Problems` panel in VS Code

### 3. Browser DevTools Debugging

**Console Errors:**
```javascript
// Press F12 → Console tab
// Look for:
- Fetch/CORS errors → Check VITE_API_URL in frontend/.env
- Authentication errors → Check JWT token in localStorage
- Component errors → Check if stores are initialized
```

**Network Tab:**
```
F12 → Network tab
- Check API calls to http://localhost:8000/auth/...
- Look for 400/401/500 responses
- Verify request headers include Authorization: Bearer <token>
```

**Application Tab:**
```
F12 → Application
- Storage → localStorage
- Look for: auth_token, document_store, etc.
- These are Zustand store data
```

### 4. Backend Database Issues

**Reset database (WARNING: Deletes all data):**
```bash
cd backend
rm llmagik.db  # or your DATABASE_URL file
# Restart backend - it will recreate the database
```

**Check database content in backend terminal:**
```bash
# After starting backend
# The file backend/llmagik.db is created
# You can inspect it with:
sqlite3 backend/llmagik.db  # if SQLite CLI installed
```

### 5. Environment Variables Check

**Backend (.env must have):**
```bash
cat backend/.env
# Should contain:
# SECRET_KEY=<random string with 32+ chars>
# ALGORITHM=HS256
# DATABASE_URL=sqlite:///./llmagik.db
# AI_PROVIDER=mock  (or: openai, anthropic)
```

**Frontend (.env must have):**
```bash
cat frontend/.env
# Should contain:
# VITE_API_URL=http://localhost:8000
```

### 6. Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `Connection refused: 8000` | Backend not running - check Terminal 1 |
| `Connection refused: 5173` | Frontend not running - check Terminal 2 |
| `CORS error` | Check `VITE_API_URL` matches backend URL |
| `401 Unauthorized` | Token expired - logout and login again |
| `Cannot find module` | Run `npm install` in frontend/ |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in backend/ |
| `Port already in use` | Kill process: `lsof -i :8000` then `kill -9 <pid>` |
| `VITE build fails` | Check TypeScript errors: `npx tsc --noEmit` |

### 7. API Testing Tools

**Option A: Postman (GUI)**
- Download https://www.postman.com/downloads/
- Import backend Swagger: http://localhost:8000/openapi.json
- Organize requests by feature

**Option B: curl (Command Line)**
```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"secret123"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Test API with token
curl -H "Authorization: Bearer $TOKEN" \ 
  http://localhost:8000/auth/me
```

**Option C: VS Code REST Client Extension**
```
1. Install: humao.rest-client
2. Create requests.rest file:
```
```http
### Register
POST http://localhost:8000/auth/register HTTP/1.1
Content-Type: application/json

{
  "username": "test",
  "email": "test@example.com",
  "password": "test123",
  "nickname": "Test User"
}

### Login
POST http://localhost:8000/auth/login HTTP/1.1
Content-Type: application/json

{
  "username": "test",
  "password": "test123"
}
```

### 8. Logging Levels

**Backend - More verbose logging:**
```bash
# In main.py, add at top:
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run:
PYTHONUNBUFFERED=1 uvicorn main:app --reload --log-level debug
```

**Frontend - React DevTools:**
```bash
# Install React DevTools Chrome extension
# 1. Go to Chrome Web Store
# 2. Search "React Developer Tools"
# 3. Inspect component tree and state changes
```

---

## 📋 Next Steps - Testing & Validation

### Phase 1: Basic Functionality Testing (30 mins)

- [ ] Backend server starts without errors
- [ ] Frontend server starts without CORS errors
- [ ] Can access http://localhost:5173 in browser
- [ ] Can access http://localhost:8000/docs (Swagger) ✅

### Phase 2: Authentication Flow (15 mins)

- [ ] **Register**: Create new account
- [ ] **Login**: Sign in with created account
- [ ] **Profile**: Update language/role/age_group
- [ ] **Logout**: Token is cleared from localStorage

**Test in Frontend:**
1. Go to http://localhost:5173
2. Click "Sign up" tab
3. Fill in: username, email, password, nickname
4. Click "Register"
5. Should redirect to login
6. Login with credentials
7. Should see Home page with document grid

### Phase 3: Document Upload (15 mins)

- [ ] **Upload Text**: Paste text → upload → appears in list
- [ ] **Upload URL**: Paste webpage URL → extract text
- [ ] **Upload File**: Choose PDF/TXT → upload → appears in list

**Test in Frontend:**
1. Click "+ Upload Document" button
2. Try each tab (Text, URL, File)
3. Should see document in Home page grid
4. Check backend logs for API calls

### Phase 4: AI Features (30 mins)

- [ ] **Analysis**: Select document → click "Read" → see analysis
- [ ] **Chat**: Ask questions about document
- [ ] **Rewrite**: Rewrite paragraphs with goals
- [ ] **History**: View all activities

**Test in Frontend Reader page:**
1. Click document → Reader page opens
2. Select mode: "Reader" or "Writer"
3. Click tab to analyze
4. Should see AI results
5. Try chat feature

### Phase 5: Backend API Testing (20 mins)

Use Swagger UI: http://localhost:8000/docs

1. **Authentication Endpoints**
   - POST /auth/register ✓
   - POST /auth/login ✓
   - GET /auth/me ✓
   - PUT /auth/profile ✓

2. **Document Endpoints**
   - POST /texts/from-text ✓
   - GET /texts/ ✓
   - GET /texts/{id} ✓
   - DELETE /texts/{id} ✓

3. **AI Endpoints**
   - POST /analysis/analyze ✓
   - POST /rewrite/ ✓
   - POST /chat/ ✓
   - GET /history/all ✓

---

## 🚀 Deployment Checklist

Once all testing passes, ready to deploy:

- [ ] Set `AI_PROVIDER` to real provider (openai/anthropic)
- [ ] Set real API keys in .env
- [ ] Switch DATABASE_URL to PostgreSQL
- [ ] Set CORS_ORIGINS to production domain
- [ ] Create production build: `npm run build`
- [ ] Deploy backend (Heroku/Docker/AWS)
- [ ] Deploy frontend (Vercel/Netlify)
- [ ] Test in production environment
- [ ] Set up monitoring/logging

---

## 📞 Need Help?

1. **Check Logs**: Backend terminal and browser console
2. **Check Status**: `http://localhost:8000/docs` should be accessible
3. **Verify .env**: Both backend/.env and frontend/.env must exist
4. **Clear Cache**: `rm -rf frontend/node_modules && npm install`
5. **Check Ports**: Make sure 8000 and 5173 are not in use

---

**Ready to go!** 🎉  
Start with Option 1 (Automated): `./start.ps1` or `./start.sh`
