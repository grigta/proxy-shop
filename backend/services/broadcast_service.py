import asyncio
import logging
from datetime import datetime
from typing import Optional, List

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.broadcast import Broadcast
from backend.models.user import User
from backend.core.config import settings

logger = logging.getLogger(__name__)


class BroadcastService:
    """Service for managing broadcast messages to Telegram users."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    async def create_broadcast(
        self,
        message_text: str,
        created_by: int,
        filter_language: Optional[str] = None,
        message_photo: Optional[str] = None
    ) -> Broadcast:
        """Create a new broadcast record."""
        # Count target users
        query = select(func.count()).select_from(User).where(
            User.telegram_id.isnot(None),
            User.is_blocked == False
        )
        if filter_language:
            query = query.where(User.language == filter_language)

        result = await self.db.execute(query)
        total_users = result.scalar() or 0

        broadcast = Broadcast(
            message_text=message_text,
            message_photo=message_photo,
            created_by=created_by,
            filter_language=filter_language,
            total_users=total_users,
            status='pending'
        )
        self.db.add(broadcast)
        await self.db.commit()
        await self.db.refresh(broadcast)

        return broadcast

    async def get_target_telegram_ids(
        self,
        filter_language: Optional[str] = None
    ) -> List[int]:
        """Get list of telegram IDs to send broadcast to."""
        query = select(User.telegram_id).where(
            User.telegram_id.isnot(None),
            User.is_blocked == False
        )
        if filter_language:
            query = query.where(User.language == filter_language)

        result = await self.db.execute(query)
        rows = result.scalars().all()

        # Flatten arrays of telegram_ids
        telegram_ids = []
        for tid_array in rows:
            if tid_array:
                telegram_ids.extend(tid_array)

        return list(set(telegram_ids))  # Remove duplicates

    async def send_broadcast(self, broadcast_id: int) -> dict:
        """Send broadcast to all target users."""
        # Get broadcast record
        result = await self.db.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()

        if not broadcast:
            raise ValueError(f"Broadcast {broadcast_id} not found")

        if broadcast.status != 'pending':
            raise ValueError(f"Broadcast {broadcast_id} is not in pending status")

        # Update status to running
        broadcast.status = 'running'
        broadcast.started_at = datetime.utcnow()
        await self.db.commit()

        # Get target users
        telegram_ids = await self.get_target_telegram_ids(broadcast.filter_language)
        broadcast.total_users = len(telegram_ids)
        await self.db.commit()

        sent_count = 0
        failed_count = 0

        try:
            for telegram_id in telegram_ids:
                # Check if broadcast was cancelled
                await self.db.refresh(broadcast)
                if broadcast.status == 'cancelled':
                    logger.info(f"Broadcast {broadcast_id} was cancelled")
                    break

                try:
                    if broadcast.message_photo:
                        await self.bot.send_photo(
                            chat_id=telegram_id,
                            photo=broadcast.message_photo,
                            caption=broadcast.message_text,
                            parse_mode="HTML"
                        )
                    else:
                        await self.bot.send_message(
                            chat_id=telegram_id,
                            text=broadcast.message_text,
                            parse_mode="HTML"
                        )
                    sent_count += 1

                except TelegramRetryAfter as e:
                    # Flood control - wait and retry
                    logger.warning(f"Flood control, waiting {e.retry_after} seconds")
                    await asyncio.sleep(e.retry_after)
                    try:
                        await self.bot.send_message(
                            chat_id=telegram_id,
                            text=broadcast.message_text,
                            parse_mode="HTML"
                        )
                        sent_count += 1
                    except Exception:
                        failed_count += 1

                except (TelegramForbiddenError, TelegramBadRequest) as e:
                    # User blocked bot or chat not found
                    logger.debug(f"Failed to send to {telegram_id}: {e}")
                    failed_count += 1

                except Exception as e:
                    logger.error(f"Error sending to {telegram_id}: {e}")
                    failed_count += 1

                # Update progress every 10 messages
                if (sent_count + failed_count) % 10 == 0:
                    broadcast.sent_count = sent_count
                    broadcast.failed_count = failed_count
                    await self.db.commit()

                # Rate limiting: ~25 messages per second
                await asyncio.sleep(0.04)

        finally:
            # Update final stats
            broadcast.sent_count = sent_count
            broadcast.failed_count = failed_count
            broadcast.completed_at = datetime.utcnow()
            if broadcast.status != 'cancelled':
                broadcast.status = 'completed'
            await self.db.commit()
            await self.bot.session.close()

        return {
            "broadcast_id": broadcast_id,
            "status": broadcast.status,
            "total_users": broadcast.total_users,
            "sent_count": sent_count,
            "failed_count": failed_count
        }

    async def cancel_broadcast(self, broadcast_id: int) -> bool:
        """Cancel a running broadcast."""
        result = await self.db.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()

        if not broadcast:
            return False

        if broadcast.status in ['pending', 'running']:
            broadcast.status = 'cancelled'
            broadcast.completed_at = datetime.utcnow()
            await self.db.commit()
            return True

        return False

    async def get_broadcast_status(self, broadcast_id: int) -> Optional[dict]:
        """Get current status of a broadcast."""
        result = await self.db.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()

        if not broadcast:
            return None

        return {
            "id": broadcast.id,
            "status": broadcast.status,
            "message_text": broadcast.message_text[:100] + "..." if len(broadcast.message_text) > 100 else broadcast.message_text,
            "total_users": broadcast.total_users,
            "sent_count": broadcast.sent_count,
            "failed_count": broadcast.failed_count,
            "created_at": broadcast.created_at.isoformat() if broadcast.created_at else None,
            "started_at": broadcast.started_at.isoformat() if broadcast.started_at else None,
            "completed_at": broadcast.completed_at.isoformat() if broadcast.completed_at else None,
            "progress": round((broadcast.sent_count + broadcast.failed_count) / broadcast.total_users * 100, 1) if broadcast.total_users > 0 else 0
        }

    async def get_broadcasts_list(self, limit: int = 20, offset: int = 0) -> List[dict]:
        """Get list of broadcasts with pagination."""
        result = await self.db.execute(
            select(Broadcast)
            .order_by(Broadcast.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        broadcasts = result.scalars().all()

        return [
            {
                "id": b.id,
                "status": b.status,
                "message_preview": b.message_text[:50] + "..." if len(b.message_text) > 50 else b.message_text,
                "total_users": b.total_users,
                "sent_count": b.sent_count,
                "failed_count": b.failed_count,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "completed_at": b.completed_at.isoformat() if b.completed_at else None
            }
            for b in broadcasts
        ]

    async def send_test_message(self, telegram_id: int, message_text: str, message_photo: Optional[str] = None) -> bool:
        """Send test message to a specific user."""
        try:
            if message_photo:
                await self.bot.send_photo(
                    chat_id=telegram_id,
                    photo=message_photo,
                    caption=message_text,
                    parse_mode="HTML"
                )
            else:
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=message_text,
                    parse_mode="HTML"
                )
            return True
        except Exception as e:
            logger.error(f"Test message failed: {e}")
            return False
        finally:
            await self.bot.session.close()
