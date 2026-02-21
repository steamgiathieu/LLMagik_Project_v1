# 🚀 LLMagik - GitHub Pages Deployment Guide

## 📋 Prerequisite

### 1. Cài đặt Node.js
- Download từ: https://nodejs.org/ (v16+ hoặc mới hơn)
- Windows: Chạy installer và chọn "Add to PATH"
- Verify: `node --version` và `npm --version`

### 2. Cài đặt Git
- Download: https://git-scm.com/
- Verify: `git --version`

---

## 🔧 Configuration Setup

### Step 1: Cấu hình Frontend

**1a. Chỉnh sửa CORS domain:**
Mở `frontend/.env.production` và thay đổi:
```
VITE_API_URL=https://your-backend-domain.onrender.com
```

**1b. Thay đổi GitHub username:**
Mở `frontend/vite.config.ts`:
```typescript
base: process.env.VITE_BASE_URL || "/YOUR-REPO-NAME/",
```

### Step 2: Cấu hình Backend (.env)

Mở `backend/.env`:
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output vào SECRET_KEY=

# Set CORS
CORS_ORIGINS=["https://USERNAME.github.io/LLMagik"]

# Set AI Provider (mock/openai/anthropic)
AI_PROVIDER=mock
```

---

## 📦 Build Frontend

```powershell
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Output will be in: frontend/dist/
```

---

## 🚀 Deploy to GitHub Pages

### Method 1: Using GitHub Actions (Recommended)

**1. Tạo GitHub repository:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR-USERNAME/LLMagik.git
git branch -M main
git push -u origin main
```

**2. Tạo GitHub Actions workflow:**
Tạo file: `.github/workflows/deploy.yml`

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: cd frontend && npm install

      - name: Build frontend
        run: cd frontend && npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/dist
```

**3. Bật GitHub Pages:**
- Repo Settings → Pages
- Source: Deploy from a branch
- Branch: gh-pages / root
- Save

Xong! Mỗi lần push sẽ tự động build và deploy.

### Method 2: Manual Push

```powershell
# Build frontend
cd frontend
npm run build
cd ..

# Tạo gh-pages branch
git worktree add gh-pages-build gh-pages 2>$null -or git branch gh-pages

# Copy dist files
Copy-Item frontend/dist/* gh-pages-build/ -Recurse -Force

# Push to gh-pages
cd gh-pages-build
git add .
git commit -m "Deploy frontend"
git push origin gh-pages
cd ..
```

---

## 🔌 Deploy Backend (Render)

### 1. Create Render Account
- Đi đến https://render.com
- Đăng ký với GitHub

### 2. Create Web Service
1. New → Web Service
2. Connect repository
3. Configure:
   ```
   Name: llmagik-backend
   Environment: Python 3.11
   Build: pip install -r requirements.txt
   Start: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

### 3. Set Environment Variables
Environment → Add Environment Variable:
```
SECRET_KEY=<paste_generated_key>
DATABASE_URL=postgresql://user:pass@db-host/db
AI_PROVIDER=mock
CORS_ORIGINS=["https://YOUR-USERNAME.github.io/LLMagik"]
```

### 4. Deploy
- Click Deploy
- Copy deployed URL: `https://llmagik-backend.onrender.com`

### 5. Update Frontend
Edit `frontend/.env.production`:
```
VITE_API_URL=https://llmagik-backend.onrender.com
```

Rebuild and redeploy frontend.

---

## ✅ Verification Checklist

- [ ] Frontend loads: `https://YOUR-USERNAME.github.io/LLMagik`
- [ ] No CORS errors in browser console (F12)
- [ ] Backend responds: `https://your-backend.onrender.com/docs`
- [ ] Can register account
- [ ] Can login
- [ ] Can upload document
- [ ] Can analyze document

---

## 🔗 Alternative Hosting Options

| Platform | Frontend | Backend | Skill | Cost |
|----------|----------|---------|-------|------|
| GitHub Pages + Render | ✅ | ✅ | Easy | Free |
| Vercel + Render | ✅ | ✅ | Easy | Free |
| Netlify + Railway | ✅ | ✅ | Easy | Free |
| AWS | ✅ | ✅ | Hard | Pay |
| DigitalOcean | ✅ | ✅ | Medium | $5-10/mo |

---

## 🧪 Test Locally Before Deploy

```powershell
# Build locally
cd frontend
npm run build
npm run preview

# Open http://localhost:4173
# Should work same as development
```

---

## 🛠️ Troubleshooting

### "Cannot find npm"
- Install Node.js: https://nodejs.org/
- Restart PowerShell after install

### "CORS error" 
- Update CORS_ORIGINS in backend/.env
- Rebuild and redeploy

### "404 Not Found" on GitHub Pages
- Check repository name matches VITE_BASE_URL
- Run `npm run build` again

### Backend not responding
- Verify Render deployment URL
- Check environment variables on Render
- View logs: Render → Open logs

---

## 📞 Need Help?

1. Check browser console (F12)
2. View backend logs (Render dashboard)
3. Check network tab (F12 → Network)
4. Re-read this guide
5. Check GitHub Actions logs

---

**Last Updated**: February 21, 2026
