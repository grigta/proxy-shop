from sqlalchemy import Index, String, Integer, DateTime, Numeric, Boolean, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from backend.core.database import Base


class Catalog(Base):
    __tablename__ = "catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ig_catalog: Mapped[str] = mapped_column(String(100), unique=True)
    pre_lines_name: Mapped[str] = mapped_column(String(100))
    line_name: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    description_ru: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_eng: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pre_lines_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    take_from_user_settings: Mapped[bool] = mapped_column(Boolean, default=False)

    products: Mapped[List["Product"]] = relationship("Product", back_populates="catalog")

    __table_args__ = (
        Index('idx_catalog_pre_lines_name', 'pre_lines_name'),
        Index('idx_catalog_ig_catalog', 'ig_catalog'),
    )