#!/bin/bash

# Quick Start Script for InfoLen AI
# Chạy cả backend và frontend cùng lúc

set -e

echo "🚀 Starting InfoLen AI Development Environment..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend .env exists
if [ ! -f "backend/.env" ]; then
    echo -e "${RED}❗ backend/.env not found. Please create backend/.env before continuing!${NC}"
    echo "   Required keys: SECRET_KEY, DATABASE_URL, GROQ_API_KEY"
    echo "   Run: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    exit 1
fi

# Check if frontend .env exists
if [ ! -f "frontend/.env" ]; then
    echo -e "${RED}❗ frontend/.env not found. Please create frontend/.env before continuing!${NC}"
    echo "   Required key: VITE_API_URL"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping servers...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup INT TERM

# Start backend
echo -e "${GREEN}🔧 Starting Backend (FastAPI)...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

sleep 2

# Start frontend
echo -e "${GREEN}⚛️  Starting Frontend (React + Vite)...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}✅ Both servers started!${NC}"
echo ""
echo "📍 Backend:  http://localhost:8000"
echo "   Swagger:  http://localhost:8000/docs"
echo "📍 Frontend: http://localhost:5173"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for both processes
wait
