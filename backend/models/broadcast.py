from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
import enum

from backend.core.database import Base


class BroadcastStatus(enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    cancelled = "cancelled"


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    message_photo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)

    total_users: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Filter options (stored as JSON-like string or separate fields)
    filter_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # ru, en, or null for all

    # Relationship
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_broadcasts_status', 'status'),
        Index('idx_broadcasts_created_at', 'created_at'),
    )
