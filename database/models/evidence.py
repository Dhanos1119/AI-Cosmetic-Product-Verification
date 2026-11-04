"""
SQLAlchemy ORM Model for Marketplace Platform Comparison Evidence Score
"""

import uuid
from datetime import datetime, timezone
from database.connection import Base
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class MarketplaceEvidence(Base):
    __tablename__ = "marketplace_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    listing_id = Column(String(36), ForeignKey("marketplace_listings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    total_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False, default=1)

    review_trust_score = Column(Float, nullable=False)    # 40% weight
    rating_score = Column(Float, nullable=False)          # 25% weight
    seller_trust_score = Column(Float, nullable=False)    # 20% weight
    match_confidence_score = Column(Float, nullable=False)# 15% weight

    recommendation_reason = Column(Text, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    listing = relationship("MarketplaceListing", back_populates="evidence")

    __table_args__ = (
        UniqueConstraint("listing_id", name="uq_marketplace_evidence_listing_id"),
    )

    def __repr__(self):
        return f"<MarketplaceEvidence(total={self.total_score}, rank={self.rank})>"
