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


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    models_text.Base.metadata.create_all(bind=engine)
    models_analysis.Base.metadata.create_all(bind=engine)
    models_rewrite.Base.metadata.create_all(bind=engine)
    models_chat.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="InfoLen AI API",
    description="Backend cho ứng dụng đọc và phân tích văn bản AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
    return {"status": "ok", "message": "InfoLen AI API is running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
