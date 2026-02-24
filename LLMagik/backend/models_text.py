from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, index=True)   # UUID string
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(500), nullable=True)
    source_type = Column(String(20), nullable=False)         # text | url | file
    source_ref = Column(String(1000), nullable=True)         # original URL or filename
    raw_text = Column(Text, nullable=True)
    paragraph_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    paragraphs = relationship("Paragraph", back_populates="document", cascade="all, delete-orphan", order_by="Paragraph.index")


class Paragraph(Base):
    __tablename__ = "paragraphs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    paragraph_id = Column(String(10), nullable=False)        # P1, P2, ...
    index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    document = relationship("Document", back_populates="paragraphs")
