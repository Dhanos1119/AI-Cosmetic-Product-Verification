"""
SQLAlchemy ORM Model for Marketplace Product Listing
"""

import uuid
from datetime import datetime, timezone
from database.connection import Base
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    marketplace_id = Column(String(36), ForeignKey("marketplaces.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(String(36), ForeignKey("sellers.id", ondelete="SET NULL"), nullable=True, index=True)

    raw_title = Column(String(500), nullable=False)
    price = Column(Float, nullable=True, default=0.0)
    currency = Column(String(10), nullable=True, default="USD")
    rating = Column(Float, nullable=True, default=0.0)
    review_count = Column(Integer, nullable=True, default=0)
    product_url = Column(String(1000), nullable=True, index=True)
    product_image_url = Column(String(1000), nullable=True)

    source_status = Column(String(50), nullable=False, default="available")
    match_status = Column(String(50), nullable=False, default="Not a Match")
    match_confidence = Column(Float, nullable=False, default=0.0)
    status_explanation = Column(Text, nullable=True)

    search_query = Column(String(500), nullable=True)
    listing_status = Column(String(50), nullable=False, default="UNAVAILABLE")
    passed_match_threshold = Column(Boolean, nullable=False, default=False)

    last_scraped_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    product = relationship("Product", back_populates="listings")
    marketplace = relationship("Marketplace", back_populates="listings")
    seller = relationship("Seller", back_populates="listings")
    reviews = relationship("CustomerReview", back_populates="listing", cascade="all, delete-orphan")
    review_analysis = relationship("ReviewAnalysis", back_populates="listing", uselist=False, cascade="all, delete-orphan")
    evidence = relationship("MarketplaceEvidence", back_populates="listing", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("marketplace_id", "product_url", name="uq_listings_marketplace_url"),
        Index("idx_listings_product_marketplace", "product_id", "marketplace_id"),
        Index("idx_listings_match_confidence", "match_confidence"),
    )

    def __repr__(self):
        return f"<MarketplaceListing(title='{self.raw_title[:30]}', price={self.price}, match={self.match_status})>"
