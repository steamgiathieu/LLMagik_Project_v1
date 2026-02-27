# LLMagik - Deploy Script for Windows
# Chạy script này để build và prepare deploy to GitHub Pages

$ErrorActionPreference = "Stop"

Write-Host "`n🚀 LLMagik Deployment Setup`n" -ForegroundColor Green

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found!" -ForegroundColor Red
    Write-Host "❗ Download and install from: https://nodejs.org/" -ForegroundColor Yellow
    Write-Host "   Restart PowerShell after installation" -ForegroundColor Yellow
    exit 1
}

# Check Git
try {
    $gitVersion = git --version 2>&1
    Write-Host "✓ Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Git not found!" -ForegroundColor Red
    Write-Host "❗ Download and install from: https://git-scm.com/" -ForegroundColor Yellow
    exit 1
}

# Frontend setup
Write-Host "`n📦 Setting up Frontend...`n" -ForegroundColor Green

cd frontend

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies..."
    npm install
} else {
    Write-Host "npm dependencies already installed"
}

# Build
Write-Host "`n🔨 Building frontend...`n" -ForegroundColor Green
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Build successful!`n" -ForegroundColor Green
Write-Host "Output directory: frontend/dist/" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor Green

# Display next steps
Write-Host "📋 Next Steps:`n" -ForegroundColor Yellow

Write-Host "1️⃣  Update GitHub configuration:" -ForegroundColor Green
Write-Host "   - Local/dev: edit frontend/.env" -ForegroundColor Cyan
Write-Host "   - CI deploy: set VITE_API_URL in GitHub Secrets (Actions)" -ForegroundColor Cyan
Write-Host "   - Change USERNAME to your GitHub username" -ForegroundColor Cyan
Write-Host "   - Change VITE_API_URL to your backend URL" -ForegroundColor Cyan

Write-Host "`n2️⃣  Push to GitHub:" -ForegroundColor Green
Write-Host "   git add ." -ForegroundColor Cyan
Write-Host "   git commit -m 'Deploy to GitHub Pages'" -ForegroundColor Cyan
Write-Host "   git push origin main" -ForegroundColor Cyan

Write-Host "`n3️⃣  Enable GitHub Pages:" -ForegroundColor Green
Write-Host "   - Go to repo settings" -ForegroundColor Cyan
Write-Host "   - Pages → Deploy from gh-pages branch" -ForegroundColor Cyan

Write-Host "`n4️⃣  Deploy Backend (Render):" -ForegroundColor Green
Write-Host "   - Go to https://render.com" -ForegroundColor Cyan
Write-Host "   - Click 'New Web Service'" -ForegroundColor Cyan
Write-Host "   - See DEPLOYMENT_GUIDE.md for details" -ForegroundColor Cyan

Write-Host "`n📚 Read DEPLOYMENT_GUIDE.md for complete instructions`n" -ForegroundColor Yellow

cd ..
