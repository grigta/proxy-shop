from sqlalchemy import Index, String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime

from backend.core.database import Base


class UserLog(Base):
    __tablename__ = "user_logs"

    id_log: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date_of_action: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    action_type: Mapped[str] = mapped_column(String(50))
    action_is: Mapped[str] = mapped_column(Text)

    user: Mapped["User"] = relationship("User", back_populates="logs")

    __table_args__ = (
        Index('idx_user_logs_user_id', 'user_id'),
        Index('idx_user_logs_date', 'date_of_action'),
        Index('idx_user_logs_action_type', 'action_type'),
    )