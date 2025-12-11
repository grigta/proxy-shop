import json
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user_log import UserLog


class LogService:
    """Service for logging user actions to the database"""

    @staticmethod
    async def create_log(
        session: AsyncSession,
        user_id: int,
        action_type: str,
        action_details: dict,
        full_name: Optional[str] = None
    ) -> UserLog:
        """
        Create a new log entry in user_logs table.

        Args:
            session: Database session
            user_id: ID of the user performing the action
            action_type: Type of action (REGISTER, LOGIN, LINK_TELEGRAM, TOKEN_REFRESH, LOGOUT)
            action_details: Dictionary with action details
            full_name: Optional full name of the user

        Returns:
            Created UserLog object
        """
        try:
            # Serialize action details to JSON string
            action_is = json.dumps(action_details, ensure_ascii=False)

            # Create new log entry
            log = UserLog(
                user_id=user_id,
                action_type=action_type,
                action_is=action_is,
                full_name=full_name
            )

            # Add to session (caller will commit)
            session.add(log)

            return log

        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Error creating log entry: {e}")
            # Don't rollback or raise - let caller handle transaction
            return None

    @staticmethod
    async def log_register(
        session: AsyncSession,
        user_id: int,
        platform: str,
        access_code: str,
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log user registration action.

        Args:
            session: Database session
            user_id: ID of the newly registered user
            platform: Registration platform (telegram/web)
            access_code: Generated access code
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "platform": platform,
            "access_code": access_code,
            "ip": ip,
            "action": "User registered"
        }

        return await LogService.create_log(
            session,
            user_id,
            "REGISTER",
            action_details
        )

    @staticmethod
    async def log_login(
        session: AsyncSession,
        user_id: int,
        platform: str,
        access_code: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserLog:
        """
        Log user login action.

        Args:
            session: Database session
            user_id: ID of the user logging in
            platform: Login platform
            access_code: User's access code
            ip: Client IP address
            user_agent: Client user agent string

        Returns:
            Created UserLog object
        """
        action_details = {
            "platform": platform,
            "access_code": access_code,
            "ip": ip,
            "user_agent": user_agent,
            "action": "User logged in"
        }

        return await LogService.create_log(
            session,
            user_id,
            "LOGIN",
            action_details
        )

    @staticmethod
    async def log_link_telegram(
        session: AsyncSession,
        user_id: int,
        telegram_id: int,
        access_code: str,
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log Telegram account linking action.

        Args:
            session: Database session
            user_id: ID of the user
            telegram_id: Telegram ID being linked
            access_code: User's access code
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "telegram_id": telegram_id,
            "access_code": access_code,
            "ip": ip,
            "action": "Telegram account linked"
        }

        return await LogService.create_log(
            session,
            user_id,
            "LINK_TELEGRAM",
            action_details
        )

    @staticmethod
    async def log_token_refresh(
        session: AsyncSession,
        user_id: int,
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log access token refresh action.

        Args:
            session: Database session
            user_id: ID of the user
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "ip": ip,
            "action": "Access token refreshed"
        }

        return await LogService.create_log(
            session,
            user_id,
            "TOKEN_REFRESH",
            action_details
        )

    @staticmethod
    async def log_address_generated(
        session: AsyncSession,
        user_id: int,
        chain: str,
        address: str,
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log crypto address generation action.

        Args:
            session: Database session
            user_id: ID of the user
            chain: Cryptocurrency chain (BTC, ETH, etc.)
            address: Generated address
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "chain": chain,
            "address": address,
            "ip": ip,
            "action": "Crypto address generated"
        }

        return await LogService.create_log(
            session,
            user_id,
            "ADDRESS_GENERATED",
            action_details
        )

    @staticmethod
    async def log_deposit(
        session: AsyncSession,
        user_id: int,
        chain: str,
        amount_usd,  # Decimal type
        coin_amount,  # Decimal type
        txid: str,
        new_balance,  # Decimal type
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log successful deposit action.

        Args:
            session: Database session
            user_id: ID of the user
            chain: Cryptocurrency chain
            amount_usd: Amount in USD
            coin_amount: Amount in cryptocurrency
            txid: Transaction ID
            new_balance: New user balance
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "chain": chain,
            "amount_usd": str(amount_usd),
            "coin_amount": str(coin_amount),
            "txid": txid,
            "new_balance": str(new_balance),
            "ip": ip,
            "action": f"Deposit {amount_usd} USD via {chain}"
        }

        return await LogService.create_log(
            session,
            user_id,
            "DEPOSIT",
            action_details
        )

    @staticmethod
    async def log_ipn_received(
        session: AsyncSession,
        user_id: int,
        txid: str,
        status: str,
        details: dict,
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log IPN webhook received action.

        Args:
            session: Database session
            user_id: ID of the user
            txid: Transaction ID
            status: Processing status (success/failed/duplicate)
            details: Additional details
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "txid": txid,
            "status": status,
            "details": details,
            "ip": ip,
            "action": f"IPN webhook received: {status}"
        }

        return await LogService.create_log(
            session,
            user_id,
            "IPN_RECEIVED",
            action_details
        )

    @staticmethod
    async def log_purchase(
        session: AsyncSession,
        user_id: int,
        proxy_type: str,
        product_id: int,
        order_id: Optional[str],
        quantity: int,
        price,  # Decimal type
        country: str,
        new_balance,  # Decimal type
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log proxy purchase action.

        Args:
            session: Database session
            user_id: ID of the user
            proxy_type: Type of proxy (SOCKS5/PPTP)
            product_id: Product ID purchased
            order_id: Order ID (for SOCKS5)
            quantity: Number of proxies purchased
            price: Total price
            country: Country of proxy
            new_balance: New user balance after purchase
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "proxy_type": proxy_type,
            "product_id": product_id,
            "order_id": order_id,
            "quantity": quantity,
            "price": str(price),
            "country": country,
            "new_balance": str(new_balance),
            "ip": ip,
            "action": f"Buy {proxy_type} {price}"
        }

        return await LogService.create_log(
            session,
            user_id,
            f"BUY_{proxy_type}",
            action_details
        )

    @staticmethod
    async def log_refund(
        session: AsyncSession,
        user_id: int,
        proxy_type: str,
        proxy_id: int,
        refunded_amount,  # Decimal type
        reason: str,
        new_balance,  # Decimal type
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log proxy refund action.

        Args:
            session: Database session
            user_id: ID of the user
            proxy_type: Type of proxy (SOCKS5/PPTP)
            proxy_id: Proxy ID being refunded
            refunded_amount: Amount refunded
            reason: Refund reason (offline/manual)
            new_balance: New user balance after refund
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "proxy_type": proxy_type,
            "proxy_id": proxy_id,
            "refunded_amount": str(refunded_amount),
            "reason": reason,
            "new_balance": str(new_balance),
            "ip": ip,
            "action": f"Refund {proxy_type} {refunded_amount}"
        }

        return await LogService.create_log(
            session,
            user_id,
            "REFUND",
            action_details
        )

    @staticmethod
    async def log_proxy_validation(
        session: AsyncSession,
        user_id: int,
        proxy_type: str,
        proxy_id: int,
        online: bool,
        latency_ms: Optional[float],
        minutes_since_purchase: int,
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log proxy validation check action.

        Args:
            session: Database session
            user_id: ID of the user
            proxy_type: Type of proxy (SOCKS5/PPTP)
            proxy_id: Proxy ID being validated
            online: Whether proxy is online
            latency_ms: Response time in milliseconds
            minutes_since_purchase: Minutes since proxy was purchased
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "proxy_type": proxy_type,
            "proxy_id": proxy_id,
            "online": online,
            "latency_ms": latency_ms,
            "minutes_since_purchase": minutes_since_purchase,
            "ip": ip,
            "action": f"Validate {proxy_type}: {'online' if online else 'offline'}"
        }

        return await LogService.create_log(
            session,
            user_id,
            "VALIDATE_PROXY",
            action_details
        )

    @staticmethod
    async def log_extension(
        session: AsyncSession,
        user_id: int,
        proxy_type: str,
        proxy_id: int,
        hours_added: int,
        price,  # Decimal type
        new_expires_at: datetime,
        new_balance,  # Decimal type
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log proxy extension action.

        Args:
            session: Database session
            user_id: ID of the user
            proxy_type: Type of proxy (SOCKS5/PPTP)
            proxy_id: Proxy ID being extended
            hours_added: Hours added to expiration
            price: Extension price
            new_expires_at: New expiration datetime
            new_balance: New user balance after extension
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "proxy_type": proxy_type,
            "proxy_id": proxy_id,
            "hours_added": hours_added,
            "price": str(price),
            "new_expires_at": new_expires_at.isoformat(),
            "new_balance": str(new_balance),
            "ip": ip,
            "action": f"Extend {proxy_type} +{hours_added}h for {price}"
        }

        return await LogService.create_log(
            session,
            user_id,
            "EXTEND_PROXY",
            action_details
        )

    @staticmethod
    async def log_coupon_activation(
        session: AsyncSession,
        user_id: int,
        coupon_code: str,
        discount_percentage,  # Decimal type
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log coupon activation action.

        Args:
            session: Database session
            user_id: ID of the user activating coupon
            coupon_code: Code of the activated coupon
            discount_percentage: Discount percentage (0-100)
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "coupon_code": coupon_code,
            "discount_percentage": str(discount_percentage),
            "ip": ip,
            "action": f"Coupon {coupon_code} activated ({discount_percentage}% discount)"
        }

        return await LogService.create_log(
            session,
            user_id,
            "COUPON_ACTIVATION",
            action_details
        )

    @staticmethod
    async def log_coupon_applied(
        session: AsyncSession,
        user_id: int,
        coupon_code: str,
        discount_amount,  # Decimal type
        original_price,  # Decimal type
        final_price,  # Decimal type
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log coupon application to a purchase.

        Args:
            session: Database session
            user_id: ID of the user using coupon
            coupon_code: Code of the applied coupon
            discount_amount: Amount discounted
            original_price: Original price before discount
            final_price: Final price after discount
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "coupon_code": coupon_code,
            "discount_amount": str(discount_amount),
            "original_price": str(original_price),
            "final_price": str(final_price),
            "ip": ip,
            "action": f"Coupon {coupon_code} applied: -{discount_amount} USD"
        }

        return await LogService.create_log(
            session,
            user_id,
            "COUPON_APPLIED",
            action_details
        )

    @staticmethod
    async def log_referral_bonus(
        session: AsyncSession,
        referrer_id: int,
        referral_id: int,
        bonus_amount,  # Decimal type
        purchase_amount,  # Decimal type
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log referral bonus award.

        Args:
            session: Database session
            referrer_id: ID of the referrer receiving bonus
            referral_id: ID of the referral who made purchase
            bonus_amount: Bonus amount awarded
            purchase_amount: Purchase amount that triggered bonus
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details = {
            "referral_id": referral_id,
            "bonus_amount": str(bonus_amount),
            "purchase_amount": str(purchase_amount),
            "ip": ip,
            "action": f"Referral bonus {bonus_amount} USD from user {referral_id} purchase"
        }

        return await LogService.create_log(
            session,
            referrer_id,
            "REFERRAL_BONUS",
            action_details
        )

    # Admin action logs

    @staticmethod
    async def log_admin_action(
        session: AsyncSession,
        admin_id: int,
        action_type: str,
        action_description: str,
        action_details: dict,
        ip: Optional[str] = None
    ) -> UserLog:
        """
        Log generic admin action.

        Args:
            session: Database session
            admin_id: ID of the admin user performing action
            action_type: Type of action (ADMIN_CREATE_COUPON, ADMIN_UPDATE_USER, etc.)
            action_description: Human-readable description
            action_details: Dictionary with action details
            ip: Client IP address

        Returns:
            Created UserLog object
        """
        action_details["ip"] = ip
        action_details["action"] = action_description

        return await LogService.create_log(
            session,
            admin_id,
            action_type,
            action_details
        )