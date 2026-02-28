import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import engine
import models
import models_text
import models_analysis
import models_rewrite
import models_chat
from routers.auth_router import router as auth_router
from routers.texts_router import router as texts_router
from routers.analysis_router import router as analysis_router
from routers.rewrite_router import router as rewrite_router
from routers.chat_router import router as chat_router
from routers.history_router import router as history_router
from mongo import init_mongo, close_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    models_text.Base.metadata.create_all(bind=engine)
    models_analysis.Base.metadata.create_all(bind=engine)
    models_rewrite.Base.metadata.create_all(bind=engine)
    models_chat.Base.metadata.create_all(bind=engine)
    init_mongo()
    yield
    close_mongo()


app = FastAPI(
    title="InfoLens AI API",
    description="Backend cho ứng dụng đọc và phân tích văn bản AI",
    version="1.0.0",
    lifespan=lifespan,
)


def _load_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                origins = [str(x).strip() for x in parsed if str(x).strip()]
                if origins:
                    return origins
        except Exception:
            pass

    # Fallback single-origin envs often used in hosting dashboards.
    single_origin_candidates = [
        os.getenv("FRONTEND_URL", "").strip(),
        os.getenv("APP_URL", "").strip(),
        os.getenv("PUBLIC_APP_URL", "").strip(),
    ]
    single_origins = [x for x in single_origin_candidates if x]
    if single_origins:
        return single_origins

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


cors_origins = _load_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=(
        r"https?://(localhost|127\.0\.0\.1)(:\d+)?$|"
        r"https://[\w.-]+\.github\.io$|"
        r"https://[\w.-]+\.vercel\.app$|"
        r"https://[\w.-]+\.netlify\.app$|"
        r"https://[\w.-]+\.onrender\.com$"
    ),
    allow_credentials=True,  # Enable credentials (cookies)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(texts_router)
app.include_router(analysis_router)
app.include_router(rewrite_router)
app.include_router(chat_router)
app.include_router(history_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "InfoLens AI API is running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
