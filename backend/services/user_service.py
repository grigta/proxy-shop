"""Service for handling user profile and history operations"""

import logging
import json
from typing import Optional, List, Tuple, Dict, Any
from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from backend.models.user import User
from backend.models.user_log import UserLog
from backend.models.proxy_history import ProxyHistory
from backend.models.pptp_history import PptpHistory
from backend.models.environment_variable import EnvironmentVariable
from backend.services.referral_service import ReferralService
from backend.services.log_service import LogService
from backend.core.security import create_access_token, create_refresh_token

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user profile and history"""

    @staticmethod
    async def get_user_profile(session: AsyncSession, user_id: int) -> Dict[str, Any]:
        """
        Get complete user profile with referral and balance information.

        Args:
            session: Database session
            user_id: User ID to get profile for

        Returns:
            Dictionary with all profile data

        Raises:
            HTTPException: If user not found
        """
        try:
            # Get user
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Determine which balance to display
            if user.balance_forward and user.balance_forward != 0:
                # Get balance from forwarded user
                balance_owner_result = await session.execute(
                    select(User).where(User.user_id == user.balance_forward)
                )
                balance_owner = balance_owner_result.scalar_one_or_none()
                display_balance = balance_owner.balance if balance_owner else user.balance
            else:
                # Use own balance
                display_balance = user.balance

            # Generate referral links
            primary_referral_id = user.myreferal_id[0] if user.myreferal_id and len(user.myreferal_id) > 0 else None
            bot_link, web_link = await ReferralService.generate_referral_links(session, primary_referral_id)

            # Calculate total earned from referrals
            # Get referral bonus percentage
            bonus_percentage_result = await session.execute(
                select(EnvironmentVariable).where(
                    EnvironmentVariable.name == "REFERRAL_BONUS_PERCENTAGE"
                )
            )
            bonus_percentage_var = bonus_percentage_result.scalar_one_or_none()
            bonus_percentage = Decimal(bonus_percentage_var.data if bonus_percentage_var else "10")

            # Get all referrals
            referrals_result = await session.execute(
                select(User.user_id).where(User.user_referal_id == user_id)
            )
            referral_user_ids = [row.user_id for row in referrals_result]

            total_earned_from_referrals = Decimal('0.00')

            if referral_user_ids:
                # Batch query for all proxy spending
                proxy_spent_result = await session.execute(
                    select(
                        func.coalesce(func.sum(ProxyHistory.price), 0).label('total')
                    ).where(
                        ProxyHistory.user_id.in_(referral_user_ids)
                    )
                )
                proxy_total = Decimal(str(proxy_spent_result.scalar() or 0))

                # Batch query for all pptp spending
                pptp_spent_result = await session.execute(
                    select(
                        func.coalesce(func.sum(PptpHistory.price), 0).label('total')
                    ).where(
                        PptpHistory.user_id.in_(referral_user_ids)
                    )
                )
                pptp_total = Decimal(str(pptp_spent_result.scalar() or 0))

                # Total spent by all referrals
                total_spent = proxy_total + pptp_total

                # Calculate bonus earned from all referrals
                total_earned_from_referrals = total_spent * (bonus_percentage / Decimal('100'))
                total_earned_from_referrals = total_earned_from_referrals.quantize(Decimal('0.01'))

            # Validate that first telegram_id is the owner
            telegram_id_owner = user.telegram_id[0] if user.telegram_id and len(user.telegram_id) > 0 else None
            linked_telegram_ids = user.telegram_id[1:] if user.telegram_id and len(user.telegram_id) > 1 else []

            # Build profile data
            profile_data = {
                "user_id": user.user_id,
                "access_code": user.access_code,
                "balance": display_balance,
                "datestamp": user.datestamp,
                "platform_registered": user.platform_registered,
                "language": user.language,
                "username": user.username,
                "telegram_id": user.telegram_id,
                "telegram_id_owner": telegram_id_owner,
                "linked_telegram_ids": linked_telegram_ids,
                "balance_forward": user.balance_forward,
                "referral_link_bot": bot_link,
                "referral_link_web": web_link,
                "myreferal_id": user.myreferal_id[0] if user.myreferal_id and len(user.myreferal_id) > 0 else None,
                "referal_quantity": user.referal_quantity,
                "total_earned_from_referrals": total_earned_from_referrals
            }

            logger.info(f"Retrieved profile for user {user_id}")
            return profile_data

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching profile for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user profile"
            )

    @staticmethod
    async def get_user_history(
        session: AsyncSession,
        user_id: int,
        action_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[UserLog], int]:
        """
        Get user's action history from logs with pagination.

        Args:
            session: Database session
            user_id: User ID
            action_type: Optional filter by action type
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of logs, total count)
        """
        try:
            # Build base query
            query = select(UserLog).where(UserLog.user_id == user_id)
            count_query = select(func.count(UserLog.id_log)).where(UserLog.user_id == user_id)

            # Apply action type filter if provided
            if action_type:
                query = query.where(UserLog.action_type == action_type)
                count_query = count_query.where(UserLog.action_type == action_type)

            # Count total
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            # Get paginated logs
            offset = (page - 1) * page_size
            result = await session.execute(
                query
                .order_by(UserLog.date_of_action.desc())
                .offset(offset)
                .limit(page_size)
            )
            logs = result.scalars().all()

            # Process logs to add formatted messages
            processed_logs = []
            for log in logs:
                # Create a copy of the log with formatted message
                log_dict = {
                    "id_log": log.id_log,
                    "user_id": log.user_id,
                    "action_type": log.action_type,
                    "action_is": log.action_is,
                    "date_of_action": log.date_of_action
                }

                # Add formatted message
                formatted_message = UserService.format_log_message(log)
                log_dict["formatted_message"] = formatted_message

                # Parse action_is for description
                try:
                    action_details = json.loads(log.action_is) if log.action_is else {}
                    log_dict["action_description"] = action_details.get("action", log.action_type)
                except:
                    log_dict["action_description"] = log.action_type

                processed_logs.append(log_dict)

            logger.info(f"Retrieved {len(processed_logs)} history items for user {user_id}")
            return processed_logs, total

        except Exception as e:
            logger.error(f"Error fetching history for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user history"
            )

    @staticmethod
    def format_log_message(log: UserLog) -> str:
        """
        Format a log entry into a readable message.

        Args:
            log: UserLog object

        Returns:
            Formatted message string
        """
        try:
            # Parse action_is JSON
            details = json.loads(log.action_is) if log.action_is else {}

            # Format date
            date_str = log.date_of_action.strftime("%Y-%m-%d %H:%M:%S")

            # Format message based on action type
            if log.action_type == "DEPOSIT":
                amount = details.get("amount_usd", details.get("amount", "0"))
                return f"DEPOSIT AMOUNT {amount} 🕞{date_str} UTC0"

            elif log.action_type == "BUY_SOCKS5":
                price = details.get("price", "0")
                return f"BUY Socks5 {price} 🕞{date_str} UTC0"

            elif log.action_type == "BUY_PPTP":
                price = details.get("price", "0")
                return f"BUY PPTP {price} 🕞{date_str} UTC0"

            elif log.action_type == "REFUND":
                amount = details.get("refunded_amount", details.get("amount", "0"))
                return f"REFUND {amount} 🕞{date_str} UTC0"

            elif log.action_type == "EXTEND_PROXY":
                proxy_type = details.get("proxy_type", "PROXY")
                hours = details.get("hours_added", details.get("hours", "0"))
                price = details.get("price", "0")
                return f"EXTEND {proxy_type} +{hours}h for {price} 🕞{date_str} UTC0"

            elif log.action_type == "COUPON_ACTIVATION":
                coupon = details.get("coupon_code", "UNKNOWN")
                discount = details.get("discount_percentage", "0")
                return f"COUPON {coupon} activated ({discount}% off) 🕞{date_str} UTC0"

            elif log.action_type == "COUPON_APPLIED":
                coupon = details.get("coupon_code", "UNKNOWN")
                amount = details.get("discount_amount", "0")
                return f"COUPON {coupon} applied (-{amount} USD) 🕞{date_str} UTC0"

            elif log.action_type == "REFERRAL_BONUS":
                amount = details.get("bonus_amount", "0")
                referral_id = details.get("referral_id", "unknown")
                return f"REFERRAL BONUS {amount} USD from user {referral_id} 🕞{date_str} UTC0"

            elif log.action_type == "LOGIN":
                platform = details.get("platform", "UNKNOWN")
                return f"LOGIN from {platform} 🕞{date_str} UTC0"

            elif log.action_type == "REGISTER":
                platform = details.get("platform", "UNKNOWN")
                return f"REGISTER on {platform} 🕞{date_str} UTC0"

            else:
                # Generic format for unknown action types
                action = details.get("action", log.action_type)
                return f"{action} 🕞{date_str} UTC0"

        except Exception as e:
            logger.error(f"Error formatting log message: {e}")
            # Return a basic format if parsing fails
            date_str = log.date_of_action.strftime("%Y-%m-%d %H:%M:%S")
            return f"{log.action_type} 🕞{date_str} UTC0"

    @staticmethod
    async def link_telegram_by_access_code(
        session: AsyncSession,
        access_code: str,
        telegram_id: int,
        username: Optional[str],
        ip: Optional[str]
    ) -> Tuple[User, str, str]:
        """
        Link Telegram account to user by access code (for users who registered on website first).

        Args:
            session: Database session
            access_code: Access code in format XXX-XXX-XXX
            telegram_id: Telegram user ID to link
            username: Optional Telegram username
            ip: Optional IP address for logging

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            HTTPException: If access code not found or telegram_id already linked
        """
        try:
            # Normalize access code to uppercase
            access_code = access_code.strip().upper()

            # Find user by access code
            result = await session.execute(
                select(User).where(User.access_code == access_code)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Access code not found"
                )

            # Check if telegram_id is already linked to another user
            existing_user_result = await session.execute(
                select(User).where(User.telegram_id.contains([telegram_id]))
            )
            existing_user = existing_user_result.scalar_one_or_none()

            if existing_user and existing_user.user_id != user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This Telegram ID is already linked to another account"
                )

            # Add telegram_id to user's telegram_id array
            if not user.telegram_id or len(user.telegram_id) == 0:
                # First telegram_id - set as owner
                user.telegram_id = [telegram_id]
            elif telegram_id not in user.telegram_id:
                # Add to existing array
                user.telegram_id = user.telegram_id + [telegram_id]

            # Update username if provided
            if username:
                user.username = username

            await session.commit()
            await session.refresh(user)

            # Log the linking action
            await LogService.log_link_telegram(
                session=session,
                user_id=user.user_id,
                telegram_id=telegram_id,
                access_code=access_code,
                ip=ip
            )
            await session.commit()

            # Create JWT tokens
            access_token = create_access_token(data={"sub": str(user.user_id)})
            refresh_token = create_refresh_token(data={"sub": str(user.user_id)})

            logger.info(f"Linked Telegram ID {telegram_id} to user {user.user_id} by access code")

            return user, access_token, refresh_token

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error linking telegram by access code: {e}")
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to link Telegram account"
            )

    @staticmethod
    async def add_linked_telegram_user(
        session: AsyncSession,
        owner_user_id: int,
        telegram_id: int
    ) -> List[int]:
        """
        Add Telegram ID to user's linked list and set balance_forward.

        Args:
            session: Database session
            owner_user_id: Owner user ID (must be first telegram_id)
            telegram_id: Telegram ID to add to linked users

        Returns:
            Updated list of linked telegram IDs (excluding owner)

        Raises:
            HTTPException: If user not found, no permissions, or telegram_id already linked
        """
        try:
            # Get owner user
            result = await session.execute(
                select(User).where(User.user_id == owner_user_id)
            )
            owner = result.scalar_one_or_none()

            if not owner:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check that caller is the owner (first telegram_id)
            if not owner.telegram_id or len(owner.telegram_id) == 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No telegram ID configured for this account"
                )

            # Check if telegram_id is already in the list
            if telegram_id in owner.telegram_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This Telegram ID is already linked to your account"
                )

            # Check if telegram_id is linked to another user
            existing_user_result = await session.execute(
                select(User).where(User.telegram_id.contains([telegram_id]))
            )
            existing_user = existing_user_result.scalar_one_or_none()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This Telegram ID is already linked to another account"
                )

            # Add telegram_id to the array
            owner.telegram_id = owner.telegram_id + [telegram_id]

            # Find user with this telegram_id as owner and set balance_forward
            target_user_result = await session.execute(
                select(User).where(
                    and_(
                        User.telegram_id.is_not(None),
                        func.array_length(User.telegram_id, 1) > 0,
                        User.telegram_id[1] == telegram_id
                    )
                )
            )
            target_user = target_user_result.scalar_one_or_none()

            if target_user:
                target_user.balance_forward = owner_user_id

            await session.commit()
            await session.refresh(owner)

            # Return linked telegram IDs (excluding owner)
            linked_telegram_ids = owner.telegram_id[1:] if len(owner.telegram_id) > 1 else []

            logger.info(f"Added telegram ID {telegram_id} to user {owner_user_id}")

            return linked_telegram_ids

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding linked telegram user: {e}")
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add linked user"
            )

    @staticmethod
    async def remove_linked_telegram_user(
        session: AsyncSession,
        owner_user_id: int,
        telegram_id: int
    ) -> List[int]:
        """
        Remove Telegram ID from user's linked list and reset balance_forward.

        Args:
            session: Database session
            owner_user_id: Owner user ID (must be first telegram_id)
            telegram_id: Telegram ID to remove from linked users

        Returns:
            Updated list of linked telegram IDs (excluding owner)

        Raises:
            HTTPException: If user not found, no permissions, or trying to remove owner
        """
        try:
            # Get owner user
            result = await session.execute(
                select(User).where(User.user_id == owner_user_id)
            )
            owner = result.scalar_one_or_none()

            if not owner:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check that telegram_id array exists
            if not owner.telegram_id or len(owner.telegram_id) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No telegram IDs configured for this account"
                )

            # Check that we're not trying to remove the owner (first element)
            if owner.telegram_id[0] == telegram_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove account owner"
                )

            # Check if telegram_id is in the list
            if telegram_id not in owner.telegram_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="This Telegram ID is not linked to your account"
                )

            # Remove telegram_id from array
            owner.telegram_id = [tid for tid in owner.telegram_id if tid != telegram_id]

            # Find user with this telegram_id as owner and reset balance_forward
            target_user_result = await session.execute(
                select(User).where(
                    and_(
                        User.telegram_id.is_not(None),
                        func.array_length(User.telegram_id, 1) > 0,
                        User.telegram_id[1] == telegram_id
                    )
                )
            )
            target_user = target_user_result.scalar_one_or_none()

            if target_user and target_user.balance_forward == owner_user_id:
                target_user.balance_forward = None

            await session.commit()
            await session.refresh(owner)

            # Return linked telegram IDs (excluding owner)
            linked_telegram_ids = owner.telegram_id[1:] if len(owner.telegram_id) > 1 else []

            logger.info(f"Removed telegram ID {telegram_id} from user {owner_user_id}")

            return linked_telegram_ids

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing linked telegram user: {e}")
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove linked user"
            )

    @staticmethod
    async def get_linked_telegram_users(
        session: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get list of linked Telegram users for account owner.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Dictionary with telegram_id_owner, linked_telegram_ids, total

        Raises:
            HTTPException: If user not found
        """
        try:
            # Get user
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Extract owner and linked telegram IDs
            telegram_id_owner = user.telegram_id[0] if user.telegram_id and len(user.telegram_id) > 0 else None
            linked_telegram_ids = user.telegram_id[1:] if user.telegram_id and len(user.telegram_id) > 1 else []

            return {
                "telegram_id_owner": telegram_id_owner,
                "linked_telegram_ids": linked_telegram_ids,
                "total": len(linked_telegram_ids)
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting linked telegram users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get linked users"
            )