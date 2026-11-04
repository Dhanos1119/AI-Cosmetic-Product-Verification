"""
SQLAlchemy ORM Model for Marketplace Platform Registry
"""

import uuid
from datetime import datetime, timezone
from database.connection import Base
from sqlalchemy import Column, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Marketplace(Base):
    __tablename__ = "marketplaces"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    platform_code = Column(String(50), unique=True, nullable=False, index=True)
    platform_name = Column(String(100), nullable=False)
    base_url = Column(String(255), nullable=False)
    api_type = Column(String(50), nullable=False, default="http_scraper")
    currency_code = Column(String(10), nullable=False, default="USD")
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    sellers = relationship("Seller", back_populates="marketplace", cascade="all, delete-orphan")
    listings = relationship("MarketplaceListing", back_populates="marketplace", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("platform_code", name="uq_marketplaces_platform_code"),
    )

    def __repr__(self):
        return f"<Marketplace(code='{self.platform_code}', name='{self.platform_name}')>"
