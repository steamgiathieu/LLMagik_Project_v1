from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mode = Column(String(20), nullable=False)           # reader | writer
    ai_provider = Column(String(20), nullable=True)     # mock | groq
    result = Column(JSON, nullable=False)               # full AI response
    result_summary = Column(Text, nullable=True)        # short human-readable summary
    processing_ms = Column(Integer, nullable=True)      # latency in ms
    created_at = Column(DateTime(timezone=True), server_default=func.now())
