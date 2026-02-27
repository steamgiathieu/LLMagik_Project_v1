#!/bin/bash

# LLMagik - Deploy Script for Linux/Mac
# Run this script to build and prepare deploy to GitHub Pages

set -e

echo -e "\n🚀 LLMagik Deployment Setup\n"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "✗ Node.js not found!"
    echo "❗ Download and install from: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✓ Node.js found: $NODE_VERSION"

# Check Git
if ! command -v git &> /dev/null; then
    echo "✗ Git not found!"
    echo "❗ Install with: brew install git (Mac) or apt install git (Linux)"
    exit 1
fi

GIT_VERSION=$(git --version)
echo "✓ Git found: $GIT_VERSION"

# Frontend setup
echo -e "\n📦 Setting up Frontend...\n"

cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
else
    echo "npm dependencies already installed"
fi

# Build
echo -e "\n🔨 Building frontend...\n"
npm run build

if [ $? -ne 0 ]; then
    echo "✗ Build failed!"
    exit 1
fi

echo -e "\n✅ Build successful!\n"
echo "Output directory: frontend/dist/"
echo ""

# Display next steps
echo -e "📋 Next Steps:\n"

echo "1️⃣  Update GitHub configuration:"
echo "   - Edit frontend/.env"
echo "   - Set VITE_API_URL to your backend URL"
echo "   - Set VITE_BASE_URL to your deploy base path (e.g. /LLMagik/)"

echo -e "\n2️⃣  Push to GitHub:"
echo "   git add ."
echo "   git commit -m 'Deploy to GitHub Pages'"
echo "   git push origin main"

echo -e "\n3️⃣  Enable GitHub Pages:"
echo "   - Go to repo settings"
echo "   - Pages → Deploy from gh-pages branch"

echo -e "\n4️⃣  Deploy Backend (Render):"
echo "   - Go to https://render.com"
echo "   - Click 'New Web Service'"
echo "   - See DEPLOYMENT_GUIDE.md for details"

echo -e "\n📚 Read DEPLOYMENT_GUIDE.md for complete instructions\n"

cd ..
