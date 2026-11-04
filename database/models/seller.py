"""
SQLAlchemy ORM Model for Marketplace Merchant / Seller
"""

import uuid
from datetime import datetime, timezone
from database.connection import Base
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    marketplace_id = Column(String(36), ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_name = Column(String(150), nullable=False)
    seller_url = Column(String(500), nullable=True)
    is_official_store = Column(Boolean, nullable=False, default=False)
    seller_rating = Column(Float, nullable=True)
    verified_status = Column(String(50), nullable=False, default="unverified")

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    marketplace = relationship("Marketplace", back_populates="sellers")
    listings = relationship("MarketplaceListing", back_populates="seller")

    __table_args__ = (
        UniqueConstraint("marketplace_id", "seller_name", name="uq_sellers_marketplace_name"),
        Index("idx_sellers_marketplace_id", "marketplace_id"),
    )

    def __repr__(self):
        return f"<Seller(name='{self.seller_name}', official={self.is_official_store})>"
