# LLMagik - Quick Start Script (PowerShell for Windows)
# Chạy cả backend và frontend cùng lúc

$ErrorActionPreference = "Stop"

Write-Host "`n🚀 Starting LLMagik Development Environment...`n" -ForegroundColor Green

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found! Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found! Please install Node.js 16+" -ForegroundColor Red
    exit 1
}

# Check backend .env
if (-not (Test-Path "backend\.env")) {
    Write-Host "⚠️  backend\.env not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "❗ Please edit backend\.env and set SECRET_KEY!" -ForegroundColor Red
    Write-Host "   Generate with: python -c `"import secrets; print(secrets.token_urlsafe(32))`""
    exit 1
}

# Check frontend .env
if (-not (Test-Path "frontend\.env")) {
    Write-Host "⚠️  frontend\.env not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item "frontend\.env.example" "frontend\.env"
}

Write-Host "`n📦 Setting up Backend...`n" -ForegroundColor Green

# Setup backend virtual environment
if (-not (Test-Path "backend\venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv backend\venv
}

# Activate venv and install dependencies
$venvActivate = "backend\venv\Scripts\Activate.ps1"
& $venvActivate

if (-not (Test-Path "backend\venv\Lib\site-packages\fastapi")) {
    Write-Host "Installing backend dependencies..."
    cd backend
    pip install -r requirements.txt
    cd ..
}

Write-Host "`n📦 Setting up Frontend...`n" -ForegroundColor Green

# Setup frontend node_modules
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies (this may take a minute)..."
    cd frontend
    npm install
    cd ..
}

# Create jobs array to track processes
$jobs = @()

Write-Host "`n🔧 Starting Backend (FastAPI)..." -ForegroundColor Green
$backendJob = Start-Process -FilePath "python" -ArgumentList "backend/main.py" `
    -WorkingDirectory "." `
    -NoNewWindow -PassThru `
    -RedirectStandardOutput "backend.log" `
    -RedirectStandardError "backend.log"

Write-Host "✓ Backend started (PID: $($backendJob.Id))" -ForegroundColor Green

Start-Sleep -Seconds 2

Write-Host "`n⚛️  Starting Frontend (React + Vite)..." -ForegroundColor Green
$frontendJob = Start-Process -FilePath "npm" -ArgumentList "run dev" `
    -WorkingDirectory "frontend" `
    -NoNewWindow -PassThru `
    -RedirectStandardOutput "frontend.log" `
    -RedirectStandardError "frontend.log"

Write-Host "✓ Frontend started (PID: $($frontendJob.Id))" -ForegroundColor Green

Write-Host "`n" -ForegroundColor Green
Write-Host "✅ Both servers started!" -ForegroundColor Green
Write-Host "`n" -ForegroundColor Green
Write-Host "📍 Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Swagger:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   ReDoc:    http://localhost:8000/redoc" -ForegroundColor Cyan
Write-Host "📍 Frontend: http://localhost:5173`n" -ForegroundColor Cyan

Write-Host "📋 Logs:" -ForegroundColor Yellow
Write-Host "   Backend:  backend.log" -ForegroundColor Yellow
Write-Host "   Frontend: frontend.log`n" -ForegroundColor Yellow

Write-Host "Press Ctrl+C to stop both servers" -ForegroundColor Yellow

# Handle cleanup on exit
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Write-Host "`n`n🛑 Stopping servers..." -ForegroundColor Yellow
    Stop-Process -Id $backendJob.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendJob.Id -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Servers stopped" -ForegroundColor Green
}

# Wait for processes
while ($true) {
    if ($backendJob.HasExited -or $frontendJob.HasExited) {
        Write-Host "`n❌ A server has crashed!" -ForegroundColor Red
        if ($backendJob.HasExited) {
            Write-Host "`nBackend log:" -ForegroundColor Yellow
            Get-Content "backend.log" -Tail 20
        }
        if ($frontendJob.HasExited) {
            Write-Host "`nFrontend log:" -ForegroundColor Yellow
            Get-Content "frontend.log" -Tail 20
        }
        exit 1
    }
    Start-Sleep -Seconds 1
}
