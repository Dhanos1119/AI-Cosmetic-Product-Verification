"""
SQLAlchemy ORM Model for Review Authenticity & NLP Analysis
"""

import uuid
from datetime import datetime, timezone
from database.connection import Base
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class ReviewAnalysis(Base):
    __tablename__ = "review_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    listing_id = Column(String(36), ForeignKey("marketplace_listings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    review_authenticity_score = Column(Float, nullable=False)
    sentiment_label = Column(String(50), nullable=False)
    sentiment_score = Column(Float, nullable=True)
    average_rating = Column(Float, nullable=False, default=0.0)
    verified_buyer_percentage = Column(Float, nullable=False, default=0.0)
    authenticity_status = Column(String(100), nullable=False)
    suspicious_review_flag = Column(Boolean, nullable=False, default=False)
    summary = Column(Text, nullable=True)

    analyzed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    listing = relationship("MarketplaceListing", back_populates="review_analysis")

    __table_args__ = (
        UniqueConstraint("listing_id", name="uq_review_analyses_listing_id"),
    )

    def __repr__(self):
        return f"<ReviewAnalysis(score={self.review_authenticity_score}, label='{self.sentiment_label}')>"
