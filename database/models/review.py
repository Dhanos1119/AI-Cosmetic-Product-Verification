"""
SQLAlchemy ORM Model for Customer Review
"""

import uuid
from datetime import datetime, timezone
from database.connection import Base
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class CustomerReview(Base):
    __tablename__ = "customer_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    listing_id = Column(String(36), ForeignKey("marketplace_listings.id", ondelete="CASCADE"), nullable=False, index=True)

    author = Column(String(150), nullable=True, default="Anonymous")
    rating = Column(Float, nullable=True, default=0.0)
    comment_text = Column(Text, nullable=True)
    review_date = Column(String(50), nullable=True)
    is_verified_purchase = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    listing = relationship("MarketplaceListing", back_populates="reviews")

    __table_args__ = (
        Index("idx_reviews_listing_id", "listing_id"),
    )

    def __repr__(self):
        return f"<CustomerReview(author='{self.author}', rating={self.rating}, verified={self.is_verified_purchase})>"
