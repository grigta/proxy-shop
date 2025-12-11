"""Service for handling referral system operations"""

import logging
from typing import Optional, List, Tuple, Dict, Any
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status

from backend.models.user import User
from backend.models.proxy_history import ProxyHistory
from backend.models.pptp_history import PptpHistory
from backend.models.environment_variable import EnvironmentVariable
from backend.services.log_service import LogService
from backend.core.config import settings

logger = logging.getLogger(__name__)


class ReferralService:
    """Service for managing referral system operations"""

    @staticmethod
    async def generate_referral_links(
        session: AsyncSession,
        myreferal_id: str
    ) -> Tuple[str, str]:
        """
        Generate referral links for bot and web platforms.

        Args:
            session: Database session
            myreferal_id: User's referral ID (format: ref_ABCDEFGH2)

        Returns:
            Tuple of (bot_link, web_link)
        """
        # Get BOT_USERNAME from environment variables
        bot_username_result = await session.execute(
            select(EnvironmentVariable).where(
                EnvironmentVariable.name == "BOT_USERNAME"
            )
        )
        bot_username_var = bot_username_result.scalar_one_or_none()
        bot_username = bot_username_var.data if bot_username_var else settings.TELEGRAM_BOT_USERNAME

        # Get WEB_REFERRAL_BASE_URL from environment variables
        web_base_url_result = await session.execute(
            select(EnvironmentVariable).where(
                EnvironmentVariable.name == "WEB_REFERRAL_BASE_URL"
            )
        )
        web_base_url_var = web_base_url_result.scalar_one_or_none()
        web_base_url = web_base_url_var.data if web_base_url_var else settings.WEB_BASE_URL

        bot_link = f"http://t.me/{bot_username}?start={myreferal_id}"
        web_link = f"{web_base_url}/register?ref={myreferal_id}"
        return bot_link, web_link

    @staticmethod
    async def get_user_referrals(
        session: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int, Decimal]:
        """
        Get user's referrals with statistics.

        Args:
            session: Database session
            user_id: User ID whose referrals to fetch
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (referrals list with data, total count, total earned)
        """
        try:
            # Get referral bonus percentage from environment variables
            bonus_percentage_result = await session.execute(
                select(EnvironmentVariable).where(
                    EnvironmentVariable.name == "REFERRAL_BONUS_PERCENTAGE"
                )
            )
            bonus_percentage_var = bonus_percentage_result.scalar_one_or_none()
            bonus_percentage = Decimal(bonus_percentage_var.data if bonus_percentage_var else "10")

            # Get all referrals
            referrals_query = select(User).where(
                User.user_referal_id == user_id
            ).order_by(User.datestamp.desc())

            # Count total referrals
            count_result = await session.execute(
                select(func.count(User.user_id)).where(
                    User.user_referal_id == user_id
                )
            )
            total_count = count_result.scalar() or 0

            # Get paginated referrals
            offset = (page - 1) * page_size
            referrals_result = await session.execute(
                referrals_query.offset(offset).limit(page_size)
            )
            referrals = referrals_result.scalars().all()

            # Get all referral user IDs
            referral_user_ids = [r.user_id for r in referrals]

            # Batch query for proxy spending
            proxy_spending = {}
            if referral_user_ids:
                proxy_spent_result = await session.execute(
                    select(
                        ProxyHistory.user_id,
                        func.coalesce(func.sum(ProxyHistory.price), 0).label('total')
                    ).where(
                        ProxyHistory.user_id.in_(referral_user_ids)
                    ).group_by(ProxyHistory.user_id)
                )
                for row in proxy_spent_result:
                    proxy_spending[row.user_id] = Decimal(str(row.total))

            # Batch query for pptp spending
            pptp_spending = {}
            if referral_user_ids:
                pptp_spent_result = await session.execute(
                    select(
                        PptpHistory.user_id,
                        func.coalesce(func.sum(PptpHistory.price), 0).label('total')
                    ).where(
                        PptpHistory.user_id.in_(referral_user_ids)
                    ).group_by(PptpHistory.user_id)
                )
                for row in pptp_spent_result:
                    pptp_spending[row.user_id] = Decimal(str(row.total))

            # Build referral data with statistics
            referral_data = []
            total_earned = Decimal('0.00')

            for referral in referrals:
                # Get spending from pre-fetched data
                proxy_spent = proxy_spending.get(referral.user_id, Decimal('0.00'))
                pptp_spent = pptp_spending.get(referral.user_id, Decimal('0.00'))

                # Total spent by this referral
                total_spent = proxy_spent + pptp_spent

                # Calculate bonus earned from this referral
                bonus_earned = total_spent * (bonus_percentage / Decimal('100'))
                bonus_earned = bonus_earned.quantize(Decimal('0.01'))

                # Determine if referral is active (has made purchases)
                is_active = total_spent > Decimal('0')

                referral_info = {
                    "user_id": referral.user_id,
                    "username": referral.username,
                    "datestamp": referral.datestamp,
                    "total_spent": total_spent,
                    "bonus_earned": bonus_earned,
                    "is_active": is_active
                }

                referral_data.append(referral_info)
                total_earned += bonus_earned

            logger.info(f"Retrieved {len(referral_data)} referrals for user {user_id}, total earned: {total_earned}")
            return referral_data, total_count, total_earned

        except Exception as e:
            logger.error(f"Error fetching referrals for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch referrals"
            )

    @staticmethod
    async def award_referral_bonus(
        session: AsyncSession,
        referrer_id: int,
        referral_id: int,
        purchase_amount: Decimal,
        ip: Optional[str] = None
    ) -> Decimal:
        """
        Award referral bonus to referrer for referral's purchase.
        Note: This method does NOT commit the transaction - caller handles it.

        Args:
            session: Database session
            referrer_id: ID of the referrer who will receive the bonus
            referral_id: ID of the referral who made the purchase
            purchase_amount: Amount of the purchase
            ip: Client IP address (optional)

        Returns:
            Amount of bonus awarded
        """
        try:
            # Get referral bonus percentage from environment variables
            bonus_percentage_result = await session.execute(
                select(EnvironmentVariable).where(
                    EnvironmentVariable.name == "REFERRAL_BONUS_PERCENTAGE"
                )
            )
            bonus_percentage_var = bonus_percentage_result.scalar_one_or_none()
            bonus_percentage = Decimal(bonus_percentage_var.data if bonus_percentage_var else "10")

            # Calculate bonus amount
            bonus = purchase_amount * (bonus_percentage / Decimal('100'))
            bonus = bonus.quantize(Decimal('0.01'))

            # Get referrer
            referrer_result = await session.execute(
                select(User).where(User.user_id == referrer_id)
            )
            referrer = referrer_result.scalar_one_or_none()

            if not referrer:
                logger.warning(f"Referrer {referrer_id} not found for bonus award")
                return Decimal('0.00')

            # Update referrer's balance atomically
            referrer.balance += bonus

            # Flush changes (NO commit - caller handles transaction)
            await session.flush()

            # Log the bonus award
            await LogService.log_referral_bonus(
                session=session,
                referrer_id=referrer_id,
                referral_id=referral_id,
                bonus_amount=bonus,
                purchase_amount=purchase_amount,
                ip=ip
            )

            logger.info(f"Awarded {bonus} bonus to referrer {referrer_id} from referral {referral_id} purchase of {purchase_amount}")
            return bonus

        except Exception as e:
            logger.error(f"Error awarding referral bonus to {referrer_id}: {e}")
            # Don't raise exception - bonus award failure shouldn't fail the purchase
            return Decimal('0.00')

    @staticmethod
    async def is_first_purchase(session: AsyncSession, user_id: int) -> bool:
        """
        Check if this is the user's first purchase.

        Args:
            session: Database session
            user_id: User ID to check

        Returns:
            True if this is the first purchase, False otherwise
        """
        try:
            # Count purchases in proxy_history
            proxy_count_result = await session.execute(
                select(func.count()).select_from(ProxyHistory).where(
                    ProxyHistory.user_id == user_id
                )
            )
            proxy_count = proxy_count_result.scalar() or 0

            # Count purchases in pptp_history
            pptp_count_result = await session.execute(
                select(func.count()).select_from(PptpHistory).where(
                    PptpHistory.user_id == user_id
                )
            )
            pptp_count = pptp_count_result.scalar() or 0

            total_purchases = proxy_count + pptp_count

            logger.debug(f"User {user_id} has {total_purchases} total purchases")
            return total_purchases == 0

        except Exception as e:
            logger.error(f"Error checking first purchase for user {user_id}: {e}")
            # In case of error, assume it's not the first purchase to avoid double bonuses
            return False