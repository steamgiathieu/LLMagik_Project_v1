#!/usr/bin/env python3
"""
test_imports.py - Test if all Python imports work correctly

Run this to verify the backend setup before starting the server.
"""
import sys
from pathlib import Path

def test_imports():
    """Test all project imports."""
    print("Testing LLMagik Backend Imports...\n")
    
    errors = []
    successes = []
    
    tests = [
        ("FastAPI", "from fastapi import FastAPI"),
        ("SQLAlchemy", "from sqlalchemy import create_engine"),
        ("Pydantic", "from pydantic import BaseModel"),
        ("Python-dotenv", "from dotenv import load_dotenv"),
        ("Passlib", "from passlib.context import CryptContext"),
        ("PyJWT", "from jose import jwt"),
        
        # Project modules
        ("database", "import database"),
        ("auth", "import auth"),
        ("models", "import models"),
        ("models_text", "import models_text"),
        ("models_analysis", "import models_analysis"),
        ("models_rewrite", "import models_rewrite"),
        ("models_chat", "import models_chat"),
        
        # Services
        ("text_processor", "from services.text_processor import process_input"),
        ("ai_service", "from services.ai_service import get_provider"),
        
        # Routers
        ("auth_router", "from routers.auth_router import router as auth_router"),
        ("texts_router", "from routers.texts_router import router as texts_router"),
        ("analysis_router", "from routers.analysis_router import router as analysis_router"),
        ("rewrite_router", "from routers.rewrite_router import router as rewrite_router"),
        ("chat_router", "from routers.chat_router import router as chat_router"),
        ("history_router", "from routers.history_router import router as history_router"),
    ]
    
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            successes.append(name)
            print(f"✓ {name:<30} OK")
        except Exception as e:
            errors.append((name, str(e)))
            print(f"✗ {name:<30} FAILED: {str(e)[:50]}")
    
    # Print summary
    print("\n" + "="*60)
    print(f"SUMMARY: {len(successes)} OK, {len(errors)} FAILED")
    
    if errors:
        print("\nFailed imports:")
        for name, error in errors:
            print(f"  - {name}: {error}")
        return False
    else:
        print("\n✓ All imports successful! Backend is ready to start.")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
