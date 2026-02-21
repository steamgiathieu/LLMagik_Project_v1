# 🚀 LLMagik - Quick Start & Debug Guide

## ⚡ 30-Second Start (Windows)

```powershell
# 1. Open PowerShell in project root
cd C:\Users\Admin\Desktop\trash\engineering\LLMagik

# 2. Run startup script
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\start.ps1

# Done! Both servers run automatically
```

**Then open in browser:**
- Frontend: http://localhost:5173
- Backend Swagger: http://localhost:8000/docs

---

## ⚡ Manual Start (If script fails)

### Terminal 1 - Backend
```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Terminal 2 - Frontend
```powershell
cd frontend
npm install
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in XXX ms
➜  Local:   http://localhost:5173/
```

---

## ✅ Both Running? Check These URLs

| URL | Purpose | Should see |
|-----|---------|-----------|
| http://localhost:5173 | Frontend | React app loads, login screen |
| http://localhost:8000/docs | Backend Swagger | Interactive API docs |
| Browser console (F12) | Errors? | Should be empty or no red errors |

---

## 🧪 Quick Test Flow

### 1. Register Account
```
1. http://localhost:5173
2. Click "Sign up" tab
3. Fill: username, email, password (6+ chars), nickname
4. Click "Register"
```

### 2. Login
```
1. Click "Login" tab
2. Use credentials you just created
3. Click "Log in"
4. Should see Home page with document grid
```

### 3. Upload Document
```
1. Click "+ Upload Document"
2. Paste some text or choose file
3. Click "Upload"
4. Should appear in document grid
```

### 4. Analyze
```
1. Click document card → Reader page
2. Select "Reader" or "Writer" mode
3. Click "Analyze" tab
4. Should show AI analysis results
```

---

## 🔴 Something Wrong? Check This

### ❌ Port 8000 already in use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill it (replace PID with number from above)
taskkill /PID 12345 /F

# Then start backend again
```

### ❌ Port 5173 already in use
```powershell
# Kill process or use different port
npm run dev -- --port 5174
```

### ❌ "Cannot find module" error (Frontend)
```powershell
cd frontend
rm -r node_modules
npm install
npm run dev
```

### ❌ "ModuleNotFoundError" (Backend)
```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### ❌ CORS error in browser
**Check frontend/.env:**
```
VITE_API_URL=http://localhost:8000
```

Must match exactly where backend is running!

### ❌ "401 Unauthorized" error
- Token expired → Logout and login again
- Check browser DevTools → Application → localStorage
- Should have `auth_token` with value starting with `ey...`

### ❌ "Cannot POST /texts/from-text"
- Backend not running? Start it first
- Backend on different port? Update VITE_API_URL

---

## 🔍 Debugging Steps (In Order)

### Step 1: Check Server Status
```powershell
# Terminal 1: Backend
Invoke-WebRequest http://localhost:8000/docs
# Should open Swagger UI in browser

# Terminal 2: Frontend  
# Should show "VITE ... ready in XXX ms"
```

### Step 2: Check Browser Console
```
F12 → Console tab
Look for red errors starting with:
- fetch failed (CORS/network issue)
- Error: (JavaScript error)
- Uncaught (React error)
```

### Step 3: Check Network Tab
```
F12 → Network tab
Click something in app
Should see:
- POST to http://localhost:8000/... (status 200/201)
- Response with JSON data
- NOT 400/401/500 errors
```

### Step 4: Check Backend Logs
```
Look at Terminal 1 (Backend)
Should show:
GET /auth/login
POST /texts/from-text
GET /analysis/analyze
etc.

If nothing appears, frontend not reaching backend
```

### Step 5: Test API Directly
```powershell
# Test if backend responds
curl http://localhost:8000/docs

# Should get HTML response, not error
```

---

## 📋 Testing Checklist

- [ ] Backend starts (no errors)
- [ ] Frontend starts (no errors)
- [ ] Browser loads http://localhost:5173
- [ ] No CORS errors in console
- [ ] Can register account
- [ ] Can login
- [ ] Can see Home page
- [ ] Can upload document
- [ ] Can see document in list
- [ ] Can click → Reader page loads
- [ ] Can analyze document
- [ ] Analysis shows results

**All checked?** ✅ Ready for development!

---

## 🛠️ Useful Commands

```powershell
# Generate SECRET_KEY for backend/.env
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Install new Python package
cd backend && venv\Scripts\activate && pip install package_name

# Install new npm package  
cd frontend && npm install package_name

# Reset backend database (WARNING: DELETES DATA)
cd backend && rm llmagik.db

# Check if ports are free
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Format Python code
pip install black && black backend/

# Format TypeScript/JavaScript
cd frontend && npm run format  # if configured, or use: npx prettier --write src/
```

---

## 📞 When Stuck

1. **Read terminal output carefully** - Error message usually says what's wrong
2. **Check browser console** (F12) - Frontend errors show here
3. **Check network tab** (F12 → Network) - See actual API calls
4. **Check .env files** - Both backend/.env and frontend/.env must exist
5. **Restart servers** - Kill processes and start fresh
6. **Check port conflicts** - Use `netstat` to find conflicts
7. **Clear cache** - `rm -rf frontend/node_modules && npm install`

---

## 🎯 Next Phase After Testing

Once everything works:

1. **Implement real AI provider**
   - Set `AI_PROVIDER=openai` in backend/.env
   - Add `OPENAI_API_KEY=sk-...` 

2. **Test all features**
   - Upload different file types
   - Test analysis modes
   - Try chat features
   - Check history tracking

3. **Prepare for production**
   - Use PostgreSQL instead of SQLite
   - Set environment variables
   - Create production build: `npm run build`
   - Deploy backend and frontend

---

## 📚 See Also

- [README.md](README.md) - Full documentation
- [DEBUGGING_GUIDE.md](DEBUGGING_GUIDE.md) - Deep dive troubleshooting
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview
- [backend/SETUP_GUIDE.md](backend/SETUP_GUIDE.md) - Backend guide
- [frontend/SETUP_GUIDE.md](frontend/SETUP_GUIDE.md) - Frontend guide

---

**You're all set! Start with `.\start.ps1` and enjoy! 🎉**
