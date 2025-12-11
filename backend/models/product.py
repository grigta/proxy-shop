from sqlalchemy import Index, String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from datetime import datetime

from backend.core.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    catalog_id: Mapped[int] = mapped_column(Integer, ForeignKey('catalog.id', ondelete='CASCADE'), nullable=False)
    pre_lines_name: Mapped[str] = mapped_column(String(100))
    line_name: Mapped[str] = mapped_column(String(100))
    product: Mapped[str] = mapped_column(JSONB)

    catalog: Mapped["Catalog"] = relationship("Catalog", back_populates="products")
    proxy_history: Mapped[List["ProxyHistory"]] = relationship("ProxyHistory", back_populates="product")
    pptp_history: Mapped[List["PptpHistory"]] = relationship("PptpHistory", back_populates="product")

    __table_args__ = (
        Index('idx_products_catalog_id', 'catalog_id'),
        Index('idx_products_pre_lines_name', 'pre_lines_name'),
        Index('idx_products_datestamp', 'datestamp'),
        # GIN index for JSONB filtering - critical for performance when filtering by country, state, city, zip
        Index('idx_products_product_gin', 'product', postgresql_using='gin'),
    )