# 🎯 LLMagik Deploy Checklist

Follow these steps to deploy your app to GitHub Pages + Render.

---

## ✅ Pre-deployment

- [ ] **Install Node.js** (v16+)
  - Download: https://nodejs.org/
  - Verify: `node --version`
  
- [ ] **Install Git**
  - Download: https://git-scm.com/
  - Verify: `git --version`

- [ ] **Create GitHub account** (if not exists)
  - https://github.com

- [ ] **Create Render account** (if not exists)
  - https://render.com

---

## 🔧 Step 1: Configure Files

### Frontend Configuration
- [ ] Edit `frontend/.env.production`
  ```
  VITE_API_URL=https://your-backend.onrender.com
  ```

- [ ] Update `frontend/vite.config.ts`
  - Change `/LLMagik/` to `/YOUR-REPO-NAME/` if different

### Backend Configuration
- [ ] Create `backend/.env`
  ```bash
  # Copy from backend/.env.production
  # Generate SECRET_KEY: python -c "import secrets; print(secrets.token_urlsafe(32))"
  SECRET_KEY=<generated-key>
  CORS_ORIGINS=["https://USERNAME.github.io/REPO-NAME"]
  AI_PROVIDER=mock
  ```

---

## 📦 Step 2: Build Frontend

```powershell
# Windows
.\deploy.ps1

# Or manually
cd frontend
npm install
npm run build
cd ..
```

**Verify**: `frontend/dist/` folder created with files

---

## 📤 Step 3: Push to GitHub

```powershell
# Initialize repository (first time only)
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR-USERNAME/LLMagik.git
git branch -M main
git push -u origin main

# Future pushes
git add .
git commit -m "Update deployment"
git push origin main
```

---

## 🔌 Step 4: Deploy Backend (Render)

### 4.1 Create Web Service on Render
1. Go to https://render.com/dashboard
2. Click "New" → "Web Service"
3. Select your GitHub repository
4. Configure:
   ```
   Name: llmagik-backend
   Environment: Python 3.11
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

### 4.2 Set Environment Variables
In Render dashboard, add:
```
SECRET_KEY=<your-generated-key>
DATABASE_URL=postgresql://...  (or sqlite)
CORS_ORIGINS=["https://YOUR-USERNAME.github.io/LLMagik"]
AI_PROVIDER=mock
```

### 4.3 Deploy
- Click "Deploy"
- Wait for build (3-5 minutes)
- Copy deployed URL: `https://llmagik-backend.onrender.com`

---

## 📍 Step 5: Enable GitHub Pages

1. Go to repo settings
2. Select "Pages" in left sidebar
3. Configure:
   ```
   Source: Deploy from a branch
   Branch: gh-pages
   Folder: / (root)
   ```
4. Click "Save"
5. Wait 1-2 minutes for deployment

**Your site will be live at:**
```
https://YOUR-USERNAME.github.io/LLMagik/
```

---

## 🔗 Step 6: Update Frontend API URL

After backend is deployed:

1. Edit `frontend/.env.production`:
   ```
   VITE_API_URL=https://your-deployed-backend.onrender.com
   ```

2. Rebuild and push:
   ```powershell
   cd frontend
   npm run build
   git add .
   git commit -m "Update backend API URL"
   git push
   ```

3. Wait 2-3 minutes for GitHub Actions to redeploy

---

## ✅ Verification

- [ ] Frontend loads: `https://YOUR-USERNAME.github.io/LLMagik`
- [ ] Browser console: No CORS errors (F12)
- [ ] Backend API: `https://your-backend.onrender.com/docs`
- [ ] Can register new account
- [ ] Can login successfully
- [ ] Can upload document
- [ ] Can analyze document
- [ ] Chat feature works

---

## 🛠️ Troubleshooting

### "Cannot find npm"
```
Solution: Install Node.js from nodejs.org and restart PowerShell
```

### "CORS error" in browser
```
Solution: Update CORS_ORIGINS in backend/.env on Render
Settings → Environment → Edit → Update CORS_ORIGINS
```

### "404 Not Found" on GitHub Pages
```
Solution: Check repository name matches VITE_BASE_URL
Edit frontend/vite.config.ts: base: "/YOUR-REPO-NAME/"
```

### Backend returns 503 (Cold Start)
```
Solution: Render free tier sleeps after inactivity
Click deploy button again or wait 30 seconds
```

### "Cannot POST /texts/from-text"
```
Solution: 
1. Verify backend URL in frontend/.env.production
2. Rebuild frontend: npm run build
3. Push to GitHub
```

---

## 📚 Next Steps

After successful deployment:

1. **Add Real AI Provider**
   - Set `AI_PROVIDER=openai` in backend
   - Add `OPENAI_API_KEY` to environment

2. **Upgrade Database**
   - Render PostgreSQL (free tier available)
   - Update `DATABASE_URL`

3. **Test All Features**
   - Upload different file types
   - Test all analysis modes
   - Try rewriting features
   - Check history tracking

4. **Optimize Performance**
   - Add caching headers
   - Enable gzip compression
   - Optimize images

---

## 📞 Still Having Issues?

1. **Check browser console** (F12) for errors
2. **Check backend logs** on Render dashboard
3. **Check network tab** (F12 → Network)
4. **Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for detailed docs
5. **Check GitHub Actions** logs for build errors

---

**Estimated Time**: 15-20 minutes total
**Cost**: FREE (GitHub Pages + Render free tier)

🎉 You're ready to deploy!
