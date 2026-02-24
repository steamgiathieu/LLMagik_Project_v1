from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class RewriteRecord(Base):
    __tablename__ = "rewrite_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    paragraph_id = Column(String(20), nullable=False)
    goal = Column(String(200), nullable=False)
    original_text = Column(Text, nullable=False)
    rewritten_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    ai_provider = Column(String(20), nullable=True)
    processing_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
