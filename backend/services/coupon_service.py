"""Service for handling coupon operations and discounts"""

import logging
from typing import Optional, Tuple, List
from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from backend.models.coupon import Coupon
from backend.models.user_coupon_activation import UserCouponActivation
from backend.models.user import User
from backend.services.log_service import LogService

logger = logging.getLogger(__name__)


class CouponService:
    """Service for managing coupons and discount operations"""

    @staticmethod
    async def validate_and_get_coupon(session: AsyncSession, coupon_code: str) -> Coupon:
        """
        Validate and retrieve a coupon by its code.

        Args:
            session: Database session
            coupon_code: The coupon code to validate

        Returns:
            Coupon: Valid coupon object

        Raises:
            HTTPException: If coupon is invalid, inactive, expired, or usage limit reached
        """
        try:
            # Find coupon by code
            result = await session.execute(
                select(Coupon).where(Coupon.coupon == coupon_code)
            )
            coupon = result.scalar_one_or_none()

            if not coupon:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Coupon not found"
                )

            # Check if coupon is active
            if not coupon.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coupon is inactive"
                )

            # Check expiration
            if coupon.expires_at and coupon.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coupon has expired"
                )

            # Check usage limit
            if coupon.max_usage is not None and coupon.usage_quantity >= coupon.max_usage:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Coupon usage limit reached"
                )

            return coupon

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating coupon {coupon_code}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate coupon"
            )

    @staticmethod
    async def activate_coupon(
        session: AsyncSession,
        user_id: int,
        coupon_code: str,
        ip: Optional[str] = None
    ) -> Coupon:
        """
        Activate a coupon for a user (validate and log only).

        Args:
            session: Database session
            user_id: User ID activating the coupon
            coupon_code: Coupon code to activate
            ip: Client IP address (optional)

        Returns:
            Coupon: Valid coupon object

        Raises:
            HTTPException: If coupon is invalid or user has already used it
        """
        try:
            # Validate coupon
            coupon = await CouponService.validate_and_get_coupon(session, coupon_code)

            # Check if user has already used this coupon
            existing_activation = await session.execute(
                select(UserCouponActivation).where(
                    and_(
                        UserCouponActivation.user_id == user_id,
                        UserCouponActivation.coupon_id == coupon.id_cupon
                    )
                )
            )

            if existing_activation.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already used this coupon"
                )

            # Log activation
            await LogService.log_coupon_activation(
                session=session,
                user_id=user_id,
                coupon_code=coupon_code,
                discount_percentage=coupon.discount_percentage,
                ip=ip
            )

            # Commit transaction
            await session.commit()

            logger.info(f"User {user_id} activated coupon {coupon_code}")
            return coupon

        except HTTPException:
            await session.rollback()
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.warning(f"Duplicate activation attempt for user {user_id} and coupon {coupon_code}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already used this coupon"
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Error activating coupon for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to activate coupon"
            )

    @staticmethod
    async def apply_coupon_to_purchase(
        session: AsyncSession,
        user_id: int,
        coupon_code: str,
        original_price: Decimal
    ) -> Tuple[Decimal, Decimal, int]:
        """
        Apply a coupon to a purchase and calculate the discount.
        Note: This method does NOT commit the transaction - caller handles it.

        Args:
            session: Database session
            user_id: User ID making the purchase
            coupon_code: Coupon code to apply
            original_price: Original price before discount

        Returns:
            Tuple of (final_price, discount_amount, coupon_id)

        Raises:
            HTTPException: If coupon is invalid or user has already used it
        """
        try:
            # Validate coupon
            coupon = await CouponService.validate_and_get_coupon(session, coupon_code)

            # Check if user has already used this coupon
            existing_activation = await session.execute(
                select(UserCouponActivation).where(
                    and_(
                        UserCouponActivation.user_id == user_id,
                        UserCouponActivation.coupon_id == coupon.id_cupon
                    )
                )
            )

            activation_record = existing_activation.scalar_one_or_none()

            # If activation exists with discount_applied > 0, coupon was already used for purchase
            if activation_record and activation_record.discount_applied > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already used this coupon"
                )

            # Calculate discount
            discount_amount = original_price * (coupon.discount_percentage / Decimal('100'))
            discount_amount = discount_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places

            # Calculate final price
            final_price = original_price - discount_amount

            # Ensure final price is not negative
            if final_price < Decimal('0'):
                final_price = Decimal('0.00')

            if activation_record:
                # Update existing activation with discount applied
                activation_record.discount_applied = discount_amount
            else:
                # Create new activation record with applied discount
                activation = UserCouponActivation(
                    user_id=user_id,
                    coupon_id=coupon.id_cupon,
                    coupon=coupon_code,
                    discount_applied=discount_amount,
                    datestamp=datetime.utcnow()
                )
                session.add(activation)

            # Increment usage counter only when actually applying to purchase
            coupon.usage_quantity += 1

            # Flush changes (NO commit - caller handles transaction)
            await session.flush()

            logger.info(f"Applied coupon {coupon_code} for user {user_id}: discount {discount_amount}, final price {final_price}")
            return final_price, discount_amount, coupon.id_cupon

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error applying coupon {coupon_code} for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to apply coupon"
            )

    @staticmethod
    async def get_user_coupon_activations(
        session: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[UserCouponActivation], int]:
        """
        Get user's coupon activation history with pagination.

        Args:
            session: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of activations, total count)
        """
        try:
            # Count total activations
            count_result = await session.execute(
                select(func.count(UserCouponActivation.id)).where(
                    UserCouponActivation.user_id == user_id
                )
            )
            total = count_result.scalar() or 0

            # Get paginated activations
            offset = (page - 1) * page_size
            result = await session.execute(
                select(UserCouponActivation)
                .where(UserCouponActivation.user_id == user_id)
                .order_by(UserCouponActivation.datestamp.desc())
                .offset(offset)
                .limit(page_size)
            )
            activations = result.scalars().all()

            return list(activations), total

        except Exception as e:
            logger.error(f"Error fetching coupon activations for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch coupon activations"
            )