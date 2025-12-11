from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete
from backend.models.user import User
from backend.models.product import Product
from backend.models.proxy_history import ProxyHistory
from backend.models.pptp_history import PptpHistory
from backend.models.environment_variable import EnvironmentVariable
from backend.services.product_service import ProductService
from backend.services.log_service import LogService
from backend.services.coupon_service import CouponService
from backend.services.referral_service import ReferralService
from backend.services.external_proxy_service import ExternalProxyService
from backend.scripts.generate_order_id import generate_unique_order_id
from backend.core.proxy_validator import proxy_validator
from backend.core.utils import (
    calculate_hours_left,
    calculate_minutes_since_purchase,
    is_refund_eligible,
    parse_proxy_json
)
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
from backend.core.config import settings
import logging
import json


logger = logging.getLogger(__name__)


class PurchaseService:
    """Service for handling proxy purchases, refunds, validation and extensions."""

    @staticmethod
    async def purchase_socks5(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        quantity: int = 1,
        coupon_code: Optional[str] = None,
        ip: Optional[str] = None
    ) -> Tuple[ProxyHistory, List[Dict[str, Any]]]:
        """
        Purchase SOCKS5 proxy.

        Args:
            session: Database session
            user_id: User ID making purchase
            product_id: Product ID to purchase
            quantity: Number of proxies to buy (must be 1)
            coupon_code: Optional discount coupon
            ip: Client IP address

        Returns:
            Tuple of (ProxyHistory record, list of proxy data)

        Raises:
            HTTPException: If purchase fails
        """
        try:
            # Validate quantity
            if quantity != 1:
                raise HTTPException(
                    status_code=400,
                    detail="Only single proxy purchase is supported. Quantity must be 1"
                )

            # Get user
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Get product
            product = await ProductService.get_product_by_id(session, product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            # Check if this is an external proxy - use ExternalProxyService for purchase
            if product.line_name == ExternalProxyService.EXTERNAL_SOURCE_MARKER:
                logger.info(f"Product {product_id} is external proxy, delegating to ExternalProxyService")
                proxy_history, proxy_credentials = await ExternalProxyService.purchase_external_proxy(
                    session=session,
                    user_id=user_id,
                    product_id=product_id,
                    ip=ip
                )
                # Return in same format as regular purchase
                proxies_data = [{
                    "ip": proxy_credentials.get("ip"),
                    "port": proxy_credentials.get("port"),
                    "login": proxy_credentials.get("login"),
                    "password": proxy_credentials.get("password")
                }]
                return proxy_history, proxies_data

            # Get price
            price = await ProductService.get_catalog_price(session, "SOCKS5")
            total_price = price * quantity

            # Apply coupon discount if provided
            discount_amount = Decimal("0.00")
            coupon_id = None

            if coupon_code:
                try:
                    final_price, discount_amount, coupon_id = await CouponService.apply_coupon_to_purchase(
                        session, user_id, coupon_code, total_price
                    )
                    # Log coupon application
                    await LogService.log_coupon_applied(
                        session=session,
                        user_id=user_id,
                        coupon_code=coupon_code,
                        discount_amount=discount_amount,
                        original_price=total_price,
                        final_price=final_price,
                        ip=ip
                    )
                except HTTPException:
                    raise  # Re-raise coupon-related errors
            else:
                final_price = total_price

            # Check balance
            if user.balance < final_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Required: {final_price}, Available: {user.balance}"
                )

            # Generate unique order ID
            order_id = await generate_unique_order_id(session)

            # Parse product data
            product_data = parse_proxy_json(product.product) if isinstance(product.product, str) else product.product

            # Prepare proxy data for storage
            proxies_data = [{
                "ip": product_data.get("ip"),
                "port": product_data.get("port"),
                "login": product_data.get("login"),
                "password": product_data.get("password")
            }]

            # Create ProxyHistory record
            proxy_history = ProxyHistory(
                user_id=user_id,
                product_id=product_id,
                order_id=order_id,
                quantity=quantity,
                price=final_price,
                country=product_data.get("country", "Unknown"),
                proxies=json.dumps(proxies_data),
                expires_at=datetime.utcnow() + timedelta(hours=settings.SOCKS5_DURATION_HOURS),
                isRefunded=False
            )

            # Check if we should award referral bonus (before creating purchase record)
            should_award_bonus = False
            if user.user_referal_id:
                # Get the REFERRAL_BONUS_ON_FIRST_PURCHASE setting
                bonus_on_first_only = await PurchaseService.get_environment_variable(
                    session, "REFERRAL_BONUS_ON_FIRST_PURCHASE", "true"
                )

                if bonus_on_first_only.lower() == "true":
                    # Award only on first purchase
                    is_first = await ReferralService.is_first_purchase(session, user_id)
                    should_award_bonus = is_first
                else:
                    # Award on every purchase
                    should_award_bonus = True

            # Atomically update balance
            user.balance -= final_price

            # Add and flush
            session.add(proxy_history)
            await session.flush()

            # Award referral bonus if applicable
            if should_award_bonus:
                bonus = await ReferralService.award_referral_bonus(
                    session=session,
                    referrer_id=user.user_referal_id,
                    referral_id=user_id,
                    purchase_amount=final_price,
                    ip=ip
                )
                if bonus > Decimal('0'):
                    logger.info(f"Awarded {bonus} referral bonus to user {user.user_referal_id}")

            # Log purchase
            await LogService.log_purchase(
                session=session,
                user_id=user_id,
                proxy_type="SOCKS5",
                product_id=product_id,
                order_id=order_id,
                quantity=quantity,
                price=final_price,
                country=product_data.get("country", "Unknown"),
                new_balance=user.balance,
                ip=ip
            )

            # Commit transaction
            await session.commit()

            # Refresh to get ID
            await session.refresh(proxy_history)

            logger.info(f"User {user_id} purchased SOCKS5 proxy {product_id}, order: {order_id}")

            return proxy_history, proxies_data

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error purchasing SOCKS5: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Purchase failed: {str(e)}"
            )

    @staticmethod
    async def purchase_pptp_by_product_id(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        coupon_code: Optional[str] = None,
        ip: Optional[str] = None
    ) -> Tuple[PptpHistory, Dict[str, Any]]:
        """
        Purchase PPTP proxy by direct product_id.

        Args:
            session: Database session
            user_id: User ID making purchase
            product_id: Product ID to purchase
            coupon_code: Optional discount coupon
            ip: Client IP address

        Returns:
            Tuple of (PptpHistory record, proxy data)
        """
        try:
            # Get user
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Get product
            product_result = await session.execute(
                select(Product).where(Product.product_id == product_id)
            )
            product = product_result.scalar_one_or_none()
            if not product:
                raise HTTPException(status_code=404, detail="Product not found or already sold")

            # Get price from catalog
            price = await ProductService.get_catalog_price_by_id(session, product.catalog_id)

            # Apply coupon discount if provided
            discount_amount = Decimal("0.00")
            if coupon_code:
                try:
                    final_price, discount_amount, coupon_id = await CouponService.apply_coupon_to_purchase(
                        session, user_id, coupon_code, price
                    )
                except HTTPException:
                    raise
            else:
                final_price = price

            # Check balance
            if user.balance < final_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Required: {final_price}, Available: {user.balance}"
                )

            # Parse product data
            product_data = parse_proxy_json(product.product) if isinstance(product.product, str) else product.product
            product_ip = product_data.get("ip")

            # Validate PPTP is online
            logger.info(f"Validating PPTP {product_ip} for user {user_id}")
            check_result = await proxy_validator.check_pptp_proxy(
                ip=product_ip,
                login=product_data.get("login", ""),
                password=product_data.get("password", ""),
                timeout=5.0
            )

            if not check_result["online"]:
                # Remove invalid product
                await session.delete(product)
                await session.commit()
                raise HTTPException(
                    status_code=400,
                    detail=f"Selected PPTP proxy is offline: {check_result.get('error', 'Connection failed')}"
                )

            logger.info(f"PPTP {product_ip} is valid (latency: {check_result.get('latency_ms', 'N/A')}ms)")

            # Prepare PPTP data
            pptp_data = {
                "ip": product_data.get("ip"),
                "login": product_data.get("login"),
                "password": product_data.get("password"),
                "country": product_data.get("country"),
                "state": product_data.get("state"),
                "city": product_data.get("city"),
                "zip": product_data.get("zip")
            }

            # Create PptpHistory record
            pptp_history = PptpHistory(
                user_id=user_id,
                product_id=product_id,
                price=final_price,
                pptp=json.dumps(pptp_data),
                expires_at=datetime.utcnow() + timedelta(hours=settings.PPTP_DURATION_HOURS),
                isRefunded=False,
                resaled=True
            )

            # Deduct balance
            user.balance -= final_price

            # Add and flush
            session.add(pptp_history)
            await session.flush()

            # Log purchase
            await LogService.log_purchase(
                session=session,
                user_id=user_id,
                proxy_type="PPTP",
                product_id=product_id,
                order_id=None,
                quantity=1,
                price=final_price,
                country=product_data.get("country", "Unknown"),
                new_balance=user.balance,
                ip=ip
            )

            # Commit transaction
            await session.commit()

            # Refresh to get ID
            await session.refresh(pptp_history)

            # Delete product from products table to prevent resale
            await session.execute(
                delete(Product).where(Product.product_id == product_id)
            )
            await session.commit()

            logger.info(f"User {user_id} purchased PPTP proxy {product_id} ({pptp_data['ip']})")

            return pptp_history, pptp_data

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error purchasing PPTP by product_id {product_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Purchase failed: {str(e)}"
            )

    @staticmethod
    async def purchase_pptp(
        session: AsyncSession,
        user_id: int,
        country: str,
        catalog_id: Optional[int] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        zip_code: Optional[str] = None,
        coupon_code: Optional[str] = None,
        ip: Optional[str] = None
    ) -> Tuple[PptpHistory, Dict[str, Any]]:
        """
        Purchase PPTP proxy with filter-validate-purchase flow.

        Args:
            session: Database session
            user_id: User ID making purchase
            country: Country/region filter (required)
            catalog_id: Catalog ID filter (optional)
            state: State filter (optional)
            city: City filter (optional)
            zip_code: ZIP code filter (optional)
            coupon_code: Optional discount coupon
            ip: Client IP address

        Returns:
            Tuple of (PptpHistory record, proxy data)

        Raises:
            HTTPException: If purchase fails
        """
        try:
            # Get user
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Get price from specific catalog or default
            if catalog_id:
                price = await ProductService.get_catalog_price_by_id(session, catalog_id)
            else:
                price = await ProductService.get_catalog_price(session, "PPTP")

            # Apply coupon discount if provided
            discount_amount = Decimal("0.00")
            coupon_id = None

            if coupon_code:
                try:
                    final_price, discount_amount, coupon_id = await CouponService.apply_coupon_to_purchase(
                        session, user_id, coupon_code, price
                    )
                    # Log coupon application
                    await LogService.log_coupon_applied(
                        session=session,
                        user_id=user_id,
                        coupon_code=coupon_code,
                        discount_amount=discount_amount,
                        original_price=price,
                        final_price=final_price,
                        ip=ip
                    )
                except HTTPException:
                    raise  # Re-raise coupon-related errors
            else:
                final_price = price

            # Check balance (preliminary check)
            if user.balance < final_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Required: {final_price}, Available: {user.balance}"
                )

            # Filter products by location criteria
            filtered_products, total, filters = await ProductService.get_products_filtered(
                session=session,
                proxy_type="PPTP",
                country=country,
                state=state,
                city=city,
                zip_code=zip_code,
                catalog_id=catalog_id,
                random=False,
                page=1,
                page_size=100
            )

            if not filtered_products:
                raise HTTPException(
                    status_code=404,
                    detail="No PPTP proxies found matching your criteria"
                )

            # Exclude already-purchased IPs for this user
            history_result = await session.execute(
                select(PptpHistory.pptp).where(PptpHistory.user_id == user_id)
            )
            purchased_ips = set()
            for record in history_result.scalars():
                pptp_data_dict = parse_proxy_json(record) if isinstance(record, str) else record
                if pptp_data_dict and "ip" in pptp_data_dict:
                    purchased_ips.add(pptp_data_dict["ip"])

            # Get all invalid IPs (marked with user_key="0")
            invalid_result = await session.execute(
                select(PptpHistory.pptp).where(
                    and_(
                        PptpHistory.resaled == False,
                        PptpHistory.user_key == "0"
                    )
                )
            )
            invalid_ips = set()
            for record in invalid_result.scalars():
                pptp_data_dict = parse_proxy_json(record) if isinstance(record, str) else record
                if pptp_data_dict and "ip" in pptp_data_dict:
                    invalid_ips.add(pptp_data_dict["ip"])

            # Filter out already-purchased IPs and invalid IPs
            available_products = []
            for product in filtered_products:
                product_data = parse_proxy_json(product.product) if isinstance(product.product, str) else product.product
                product_ip = product_data.get("ip")
                if product_ip not in purchased_ips and product_ip not in invalid_ips:
                    available_products.append(product)

            if not available_products:
                raise HTTPException(
                    status_code=400,
                    detail="All available PPTP proxies in this location have already been purchased by you"
                )

            logger.info(f"Validating PPTP from {len(available_products)} candidates for user {user_id}")

            # Validate each product until we find a working one
            # Invalid products are marked and removed from future sales
            import random
            random.shuffle(available_products)  # Randomize order for fairness

            valid_product = None
            valid_product_data = None

            for product in available_products:
                product_data = parse_proxy_json(product.product) if isinstance(product.product, str) else product.product
                product_ip = product_data.get("ip")

                logger.info(f"Checking PPTP {product_ip} for user {user_id}")

                # Validate PPTP by connecting to port 1723
                check_result = await proxy_validator.check_pptp_proxy(
                    ip=product_ip,
                    login=product_data.get("login", ""),
                    password=product_data.get("password", ""),
                    timeout=5.0  # 5 second timeout for validation
                )

                if check_result["online"]:
                    logger.info(f"PPTP {product_ip} is valid (latency: {check_result.get('latency_ms', 'N/A')}ms)")
                    valid_product = product
                    valid_product_data = product_data
                    break
                else:
                    # Mark as invalid and remove from products
                    logger.warning(f"PPTP {product_ip} is invalid: {check_result.get('error', 'Unknown error')}")
                    await PurchaseService.mark_pptp_as_invalid(
                        session=session,
                        product=product,
                        ip=product_ip,
                        reason=check_result.get("error", "Validation failed")
                    )

            if not valid_product:
                raise HTTPException(
                    status_code=400,
                    detail="No valid PPTP proxies available matching your criteria. All checked proxies were offline."
                )

            logger.info(f"Selected valid PPTP proxy: {valid_product_data.get('ip')}")

            # Re-check user balance (in case it changed during validation)
            await session.refresh(user)
            if user.balance < final_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Required: {final_price}, Available: {user.balance}"
                )

            # Prepare PPTP data
            pptp_data = {
                "ip": valid_product_data.get("ip"),
                "login": valid_product_data.get("login"),
                "password": valid_product_data.get("password"),
                "country": valid_product_data.get("country"),
                "state": valid_product_data.get("state"),
                "city": valid_product_data.get("city"),
                "zip": valid_product_data.get("zip")
            }

            # Create PptpHistory record
            pptp_history = PptpHistory(
                user_id=user_id,
                product_id=valid_product.product_id,
                price=final_price,
                pptp=json.dumps(pptp_data),
                expires_at=datetime.utcnow() + timedelta(hours=settings.PPTP_DURATION_HOURS),
                isRefunded=False,
                resaled=True
            )

            # Check if we should award referral bonus (before creating purchase record)
            should_award_bonus = False
            if user.user_referal_id:
                # Get the REFERRAL_BONUS_ON_FIRST_PURCHASE setting
                bonus_on_first_only = await PurchaseService.get_environment_variable(
                    session, "REFERRAL_BONUS_ON_FIRST_PURCHASE", "true"
                )

                if bonus_on_first_only.lower() == "true":
                    # Award only on first purchase
                    is_first = await ReferralService.is_first_purchase(session, user_id)
                    should_award_bonus = is_first
                else:
                    # Award on every purchase
                    should_award_bonus = True

            # Atomically update balance
            user.balance -= final_price

            # Add and flush
            session.add(pptp_history)
            await session.flush()

            # Award referral bonus if applicable
            if should_award_bonus:
                bonus = await ReferralService.award_referral_bonus(
                    session=session,
                    referrer_id=user.user_referal_id,
                    referral_id=user_id,
                    purchase_amount=final_price,
                    ip=ip
                )
                if bonus > Decimal('0'):
                    logger.info(f"Awarded {bonus} referral bonus to user {user.user_referal_id}")

            # Log purchase
            await LogService.log_purchase(
                session=session,
                user_id=user_id,
                proxy_type="PPTP",
                product_id=valid_product.product_id,
                order_id=None,  # PPTP doesn't use order_id
                quantity=1,
                price=final_price,
                country=valid_product_data.get("country", "Unknown"),
                new_balance=user.balance,
                ip=ip
            )

            # Commit transaction
            await session.commit()

            # Refresh to get ID
            await session.refresh(pptp_history)

            # Delete product from products table to prevent resale
            await session.execute(
                delete(Product).where(Product.product_id == valid_product.product_id)
            )
            await session.commit()

            logger.info(f"User {user_id} purchased PPTP proxy {valid_product.product_id} ({pptp_data['ip']})")

            return pptp_history, pptp_data

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error purchasing PPTP: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Purchase failed: {str(e)}"
            )

    @staticmethod
    async def mark_pptp_as_invalid(
        session: AsyncSession,
        product: Product,
        ip: str,
        reason: str = "Validation failed"
    ) -> None:
        """
        Mark PPTP as invalid - create record in pptp_history with resaled=False.
        The product will be removed from products table so it won't be sold again.

        Args:
            session: Database session
            product: Product record to mark as invalid
            ip: IP address of the PPTP proxy
            reason: Reason for marking as invalid
        """
        try:
            # Just delete the product - no need to track invalid proxies in history
            await session.delete(product)
            await session.flush()

            logger.info(f"Removed invalid PPTP {ip} from products ({reason})")

        except Exception as e:
            logger.error(f"Error removing invalid PPTP {ip}: {str(e)}")
            # Don't raise - just log and continue

    @staticmethod
    async def check_proxy_online(
        session: AsyncSession,
        proxy_id: int,
        proxy_type: str
    ) -> Dict[str, Any]:
        """
        Check proxy status without logging (internal use).

        Args:
            session: Database session
            proxy_id: Proxy ID from history
            proxy_type: Type (socks5/pptp)

        Returns:
            Check results dict

        Raises:
            HTTPException: If proxy not found
        """
        try:
            # Get proxy history record
            if proxy_type.lower() == "socks5":
                result = await session.execute(
                    select(ProxyHistory).where(ProxyHistory.id == proxy_id)
                )
                proxy_history = result.scalar_one_or_none()
                if not proxy_history:
                    raise HTTPException(status_code=404, detail="Proxy not found")

                # Parse proxy data
                proxies = parse_proxy_json(proxy_history.proxies) if isinstance(proxy_history.proxies, str) else proxy_history.proxies
                proxy_data = proxies[0] if proxies else {}

                # Check proxy status
                check_result = await proxy_validator.check_socks5_proxy(
                    ip=proxy_data["ip"],
                    port=int(proxy_data["port"]),
                    login=proxy_data["login"],
                    password=proxy_data["password"]
                )
            else:  # pptp
                result = await session.execute(
                    select(PptpHistory).where(PptpHistory.id == proxy_id)
                )
                proxy_history = result.scalar_one_or_none()
                if not proxy_history:
                    raise HTTPException(status_code=404, detail="Proxy not found")

                # Parse proxy data
                proxy_data = parse_proxy_json(proxy_history.pptp)

                # Check proxy status
                check_result = await proxy_validator.check_pptp_proxy(
                    ip=proxy_data["ip"],
                    login=proxy_data["login"],
                    password=proxy_data["password"]
                )

            return {
                "online": check_result["online"],
                "latency_ms": check_result.get("latency_ms"),
                "exit_ip": check_result.get("exit_ip"),
                "user_id": proxy_history.user_id
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking proxy {proxy_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Check failed: {str(e)}"
            )

    @staticmethod
    async def validate_proxy(
        session: AsyncSession,
        proxy_id: int,
        proxy_type: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Validate proxy status (online/offline).

        Args:
            session: Database session
            proxy_id: Proxy ID from history
            proxy_type: Type (socks5/pptp)
            user_id: User ID requesting validation

        Returns:
            Validation results dict

        Raises:
            HTTPException: If validation fails
        """
        try:
            # Get proxy history record
            if proxy_type.lower() == "socks5":
                result = await session.execute(
                    select(ProxyHistory).where(ProxyHistory.id == proxy_id)
                )
                proxy_history = result.scalar_one_or_none()
                if not proxy_history:
                    raise HTTPException(status_code=404, detail="Proxy not found")

                # Check ownership immediately
                if proxy_history.user_id != user_id:
                    raise HTTPException(status_code=403, detail="Access denied")

                # Parse proxy data
                proxies = parse_proxy_json(proxy_history.proxies) if isinstance(proxy_history.proxies, str) else proxy_history.proxies
                proxy_data = proxies[0] if proxies else {}

                # Check proxy status
                check_result = await proxy_validator.check_socks5_proxy(
                    ip=proxy_data["ip"],
                    port=int(proxy_data["port"]),
                    login=proxy_data["login"],
                    password=proxy_data["password"]
                )

                # Get refund window
                refund_window_result = await PurchaseService.get_environment_variable(
                    session, "SOCKS5_REFUND_MINUTES", "30"
                )
                refund_window = int(refund_window_result)

            else:  # pptp
                result = await session.execute(
                    select(PptpHistory).where(PptpHistory.id == proxy_id)
                )
                proxy_history = result.scalar_one_or_none()
                if not proxy_history:
                    raise HTTPException(status_code=404, detail="Proxy not found")

                # Check ownership immediately
                if proxy_history.user_id != user_id:
                    raise HTTPException(status_code=403, detail="Access denied")

                # Parse proxy data
                proxy_data = parse_proxy_json(proxy_history.pptp)

                # Check proxy status
                check_result = await proxy_validator.check_pptp_proxy(
                    ip=proxy_data["ip"],
                    login=proxy_data["login"],
                    password=proxy_data["password"]
                )

                # Get refund window
                refund_window_result = await PurchaseService.get_environment_variable(
                    session, "PPTP_REFUND_HOURS", "24"
                )
                refund_window = int(refund_window_result) * 60  # Convert to minutes

            # Calculate time since purchase
            minutes_since = calculate_minutes_since_purchase(proxy_history.datestamp)

            # Check refund eligibility
            refund_eligible = is_refund_eligible(proxy_history.datestamp, refund_window)

            # Prepare message
            if check_result["online"]:
                message = "Прокси онлайн!"
            elif refund_eligible:
                message = f"Прокси офлайн! С момента покупки прошло {minutes_since}м. -> REFOUND"
            else:
                hours = minutes_since // 60
                mins = minutes_since % 60
                message = f"Прокси офлайн! С момента покупки прошло {hours}ч {mins}м. -> GARANTY GONE"

            # Log validation
            await LogService.log_proxy_validation(
                session=session,
                user_id=proxy_history.user_id,
                proxy_type=proxy_type.upper(),
                proxy_id=proxy_id,
                online=check_result["online"],
                latency_ms=check_result.get("latency_ms"),
                minutes_since_purchase=minutes_since,
                ip=None
            )

            await session.commit()

            return {
                "proxy_id": proxy_id,
                "online": check_result["online"],
                "latency_ms": check_result.get("latency_ms"),
                "exit_ip": check_result.get("exit_ip"),
                "minutes_since_purchase": minutes_since,
                "refund_eligible": refund_eligible and not check_result["online"],
                "refund_window_minutes": refund_window,
                "message": message,
                "user_id": proxy_history.user_id
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating proxy {proxy_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Validation failed: {str(e)}"
            )

    @staticmethod
    async def process_refund(
        session: AsyncSession,
        proxy_id: int,
        proxy_type: str,
        user_id: int,
        ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process refund for offline proxy.

        Args:
            session: Database session
            proxy_id: Proxy ID from history
            proxy_type: Type (socks5/pptp)
            user_id: User ID requesting refund
            ip: Client IP address

        Returns:
            Refund result dict

        Raises:
            HTTPException: If refund fails
        """
        try:
            # Get proxy history
            if proxy_type.lower() == "socks5":
                result = await session.execute(
                    select(ProxyHistory).where(ProxyHistory.id == proxy_id)
                )
                proxy_history = result.scalar_one_or_none()
                refund_window_result = await PurchaseService.get_environment_variable(
                    session, "SOCKS5_REFUND_MINUTES", "30"
                )
                refund_window = int(refund_window_result)
            else:  # pptp
                result = await session.execute(
                    select(PptpHistory).where(PptpHistory.id == proxy_id)
                )
                proxy_history = result.scalar_one_or_none()
                refund_window_result = await PurchaseService.get_environment_variable(
                    session, "PPTP_REFUND_HOURS", "24"
                )
                refund_window = int(refund_window_result) * 60

            if not proxy_history:
                raise HTTPException(status_code=404, detail="Proxy not found")

            # Check ownership
            if proxy_history.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Check if already refunded
            if proxy_history.isRefunded:
                raise HTTPException(status_code=400, detail="Already refunded")

            # Check eligibility
            if not is_refund_eligible(proxy_history.datestamp, refund_window):
                raise HTTPException(status_code=400, detail="Refund window expired")

            # Get user
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()

            # Process refund atomically
            user.balance += proxy_history.price
            proxy_history.isRefunded = True

            await session.flush()

            # Log refund
            await LogService.log_refund(
                session=session,
                user_id=user_id,
                proxy_type=proxy_type.upper(),
                proxy_id=proxy_id,
                refunded_amount=proxy_history.price,
                reason="offline",
                new_balance=user.balance,
                ip=ip
            )

            await session.commit()

            await session.refresh(user)

            logger.info(f"Refund processed for proxy {proxy_id}, user {user_id}")

            return {
                "success": True,
                "proxy_id": proxy_id,
                "refunded_amount": proxy_history.price,
                "new_balance": user.balance,
                "message": f"Возврат успешно выполнен. Сумма {proxy_history.price} USD возвращена на баланс."
            }

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error processing refund: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Refund failed: {str(e)}"
            )

    @staticmethod
    async def extend_proxy(
        session: AsyncSession,
        proxy_id: int,
        proxy_type: str,
        user_id: int,
        hours: int = 24,
        ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extend proxy duration.

        Args:
            session: Database session
            proxy_id: Proxy ID from history
            proxy_type: Type (socks5/pptp)
            user_id: User ID requesting extension
            hours: Hours to extend
            ip: Client IP address

        Returns:
            Extension result dict

        Raises:
            HTTPException: If extension fails
        """
        try:
            # Get proxy history
            if proxy_type.lower() == "socks5":
                result = await session.execute(
                    select(ProxyHistory).where(ProxyHistory.id == proxy_id)
                )
                proxy_history = result.scalar_one_or_none()
                base_price = await ProductService.get_catalog_price(session, "SOCKS5")
                base_hours = settings.SOCKS5_DURATION_HOURS
            else:  # pptp
                result = await session.execute(
                    select(PptpHistory).where(PptpHistory.id == proxy_id)
                )
                proxy_history = result.scalar_one_or_none()
                base_price = await ProductService.get_catalog_price(session, "PPTP")
                base_hours = settings.PPTP_DURATION_HOURS

            if not proxy_history:
                raise HTTPException(status_code=404, detail="Proxy not found")

            # Check ownership
            if proxy_history.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Check not refunded
            if proxy_history.isRefunded:
                raise HTTPException(status_code=400, detail="Cannot extend refunded proxy")

            # Check proxy is online (without logging)
            check_result = await PurchaseService.check_proxy_online(session, proxy_id, proxy_type)
            if not check_result["online"]:
                raise HTTPException(status_code=400, detail="Proxy is offline, cannot extend")

            # Calculate extension price
            extend_price = base_price * Decimal(hours) / Decimal(base_hours)
            extend_price *= Decimal(settings.PROXY_EXTEND_PRICE_PERCENTAGE) / Decimal(100)
            extend_price = extend_price.quantize(Decimal("0.01"))  # Round to 2 decimals

            # Get user
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()

            # Check balance
            if user.balance < extend_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Required: {extend_price}, Available: {user.balance}"
                )

            # Process extension atomically
            user.balance -= extend_price
            proxy_history.expires_at += timedelta(hours=hours)

            await session.flush()

            # Log extension
            await LogService.log_extension(
                session=session,
                user_id=user_id,
                proxy_type=proxy_type.upper(),
                proxy_id=proxy_id,
                hours_added=hours,
                price=extend_price,
                new_expires_at=proxy_history.expires_at,
                new_balance=user.balance,
                ip=ip
            )

            await session.commit()

            await session.refresh(user)
            await session.refresh(proxy_history)

            logger.info(f"Extended proxy {proxy_id} by {hours} hours, user {user_id}")

            # Get proxy info for message
            if proxy_type.lower() == "socks5":
                proxies = parse_proxy_json(proxy_history.proxies) if isinstance(proxy_history.proxies, str) else proxy_history.proxies
                proxy_data = proxies[0] if proxies else {}
                proxy_str = f"{proxy_data.get('ip')}:{proxy_data.get('port')}"
            else:
                proxy_data = parse_proxy_json(proxy_history.pptp)
                proxy_str = proxy_data.get('ip')

            return {
                "success": True,
                "proxy_id": proxy_id,
                "price": extend_price,
                "new_expires_at": proxy_history.expires_at,
                "hours_added": hours,
                "new_balance": user.balance,
                "message": f"Прокси {proxy_str} успешно продлен. BALANCE: {user.balance}"
            }

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error extending proxy: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Extension failed: {str(e)}"
            )

    @staticmethod
    async def get_purchase_history(
        session: AsyncSession,
        user_id: int,
        proxy_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List, int]:
        """
        Get user's purchase history with pagination.

        Args:
            session: Database session
            user_id: User ID
            proxy_type: Optional filter by type
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (purchases list, total count)
        """
        try:
            purchases = []

            # Get SOCKS5 history if needed
            if not proxy_type or proxy_type.upper() == "SOCKS5":
                query = select(ProxyHistory).where(
                    ProxyHistory.user_id == user_id
                ).order_by(
                    ProxyHistory.datestamp.desc()
                )
                result = await session.execute(query)
                for record in result.scalars():
                    # Parse first proxy to get location details if available
                    proxies_data = parse_proxy_json(record.proxies)
                    first_proxy = proxies_data[0] if proxies_data and isinstance(proxies_data, list) else {}

                    purchases.append({
                        "id": record.id,
                        "order_id": record.order_id,
                        "proxy_type": "SOCKS5",
                        "quantity": record.quantity,
                        "price": record.price,
                        "country": record.country,
                        "state": first_proxy.get("state"),
                        "city": first_proxy.get("city"),
                        "zip": first_proxy.get("zip"),
                        "proxies": proxies_data,
                        "datestamp": record.datestamp,
                        "expires_at": record.expires_at,
                        "hours_left": calculate_hours_left(record.expires_at),
                        "isRefunded": record.isRefunded,
                        "resaled": False,
                        "user_key": None
                    })

            # Get PPTP history if needed
            if not proxy_type or proxy_type.upper() == "PPTP":
                query = select(PptpHistory).where(
                    PptpHistory.user_id == user_id
                ).order_by(
                    PptpHistory.datestamp.desc()
                )
                result = await session.execute(query)
                for record in result.scalars():
                    # Parse PPTP data
                    pptp_data = parse_proxy_json(record.pptp)

                    purchases.append({
                        "id": record.id,
                        "order_id": None,  # PPTP doesn't have order_id
                        "proxy_type": "PPTP",
                        "quantity": record.quantity,
                        "price": record.price,
                        "country": record.country,
                        "state": pptp_data.get("state"),
                        "city": pptp_data.get("city"),
                        "zip": pptp_data.get("zip"),
                        "proxies": [pptp_data],
                        "datestamp": record.datestamp,
                        "expires_at": record.expires_at,
                        "hours_left": calculate_hours_left(record.expires_at),
                        "isRefunded": record.isRefunded,
                        "resaled": record.resaled,
                        "user_key": record.user_key
                    })

            # Sort combined results by date
            purchases.sort(key=lambda x: x["datestamp"], reverse=True)

            # Calculate total count before pagination
            total = len(purchases)

            # Apply pagination
            start = (page - 1) * page_size
            end = start + page_size
            purchases = purchases[start:end]

            logger.info(f"Retrieved {len(purchases)} purchases for user {user_id}")

            return purchases, total

        except Exception as e:
            logger.error(f"Error getting purchase history: {str(e)}")
            return [], 0

    @staticmethod
    async def get_environment_variable(
        session: AsyncSession,
        name: str,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get environment variable value from database.

        Args:
            session: Database session
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        try:
            result = await session.execute(
                select(EnvironmentVariable).where(EnvironmentVariable.key == name)
            )
            env_var = result.scalar_one_or_none()

            if env_var and env_var.data:
                return env_var.data

            return default

        except Exception as e:
            logger.error(f"Error getting environment variable {name}: {str(e)}")
            return default

    @staticmethod
    async def validate_all_user_pptp(
        session: AsyncSession,
        user_id: int,
        ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate all user's PPTP proxies from last 24 hours.
        Non-working proxies are automatically refunded.

        Args:
            session: Database session
            user_id: User ID
            ip: Client IP address for logging

        Returns:
            Dict with validation results and refund info
        """
        try:
            # Get refund window from settings
            refund_window_result = await PurchaseService.get_environment_variable(
                session, "PPTP_REFUND_HOURS", "24"
            )
            refund_window_hours = int(refund_window_result)
            cutoff_time = datetime.utcnow() - timedelta(hours=refund_window_hours)

            # Get all PPTP purchases from last 24 hours that are not refunded
            result = await session.execute(
                select(PptpHistory).where(
                    and_(
                        PptpHistory.user_id == user_id,
                        PptpHistory.datestamp >= cutoff_time,
                        PptpHistory.isRefunded == False
                    )
                ).order_by(PptpHistory.datestamp.desc())
            )
            pptp_purchases = result.scalars().all()

            if not pptp_purchases:
                # Get user for balance
                user_result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = user_result.scalar_one_or_none()

                return {
                    "validated_count": 0,
                    "valid_count": 0,
                    "invalid_count": 0,
                    "refunded_amount": Decimal("0.00"),
                    "new_balance": user.balance if user else Decimal("0.00"),
                    "details": []
                }

            # Get user for balance updates
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            valid_count = 0
            invalid_count = 0
            refunded_amount = Decimal("0.00")
            details = []

            # Validate each proxy
            for pptp in pptp_purchases:
                proxy_data = parse_proxy_json(pptp.pptp)
                proxy_ip = proxy_data.get("ip") or proxy_data.get("IP")

                if not proxy_ip:
                    logger.warning(f"No IP found in PPTP data for record {pptp.id}")
                    continue

                # Check proxy status using proxy_validator
                check_result = await proxy_validator.check_pptp_proxy(
                    ip=proxy_ip,
                    login=proxy_data.get("login", ""),
                    password=proxy_data.get("password", "")
                )

                detail = {
                    "proxy_id": pptp.id,
                    "ip": proxy_ip,
                    "online": check_result["online"],
                    "refunded": False
                }

                if check_result["online"]:
                    valid_count += 1
                else:
                    invalid_count += 1
                    # Process refund
                    user.balance += pptp.price
                    pptp.isRefunded = True
                    refunded_amount += pptp.price
                    detail["refunded"] = True
                    detail["amount"] = str(pptp.price)

                    # Log refund
                    await LogService.log_refund(
                        session=session,
                        user_id=user_id,
                        proxy_type="PPTP",
                        proxy_id=pptp.id,
                        refunded_amount=pptp.price,
                        reason="bulk_validation_offline",
                        new_balance=user.balance,
                        ip=ip
                    )

                details.append(detail)

            await session.commit()
            await session.refresh(user)

            logger.info(
                f"Bulk PPTP validation for user {user_id}: "
                f"{len(pptp_purchases)} checked, {valid_count} valid, "
                f"{invalid_count} invalid, {refunded_amount} USD refunded"
            )

            return {
                "validated_count": len(pptp_purchases),
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "refunded_amount": refunded_amount,
                "new_balance": user.balance,
                "details": details
            }

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in bulk PPTP validation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Bulk validation failed: {str(e)}"
            )