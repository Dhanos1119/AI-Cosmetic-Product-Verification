"""
SQLAlchemy ORM Model for Catalog Cosmetic Product
"""

import uuid
from datetime import datetime, timezone
from database.connection import Base
from sqlalchemy import Column, String, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(50), unique=True, nullable=False, index=True)
    brand = Column(String(100), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    product_type = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    shade_or_variant = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    listings = relationship("MarketplaceListing", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("brand", "product_name", "shade_or_variant", name="uq_products_brand_name_variant"),
        Index("idx_products_product_id", "product_id"),
        Index("idx_products_brand", "brand"),
    )

    def __repr__(self):
        return f"<Product(product_id='{self.product_id}', brand='{self.brand}', name='{self.product_name}')>"
