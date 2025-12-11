"""
Payment service for handling cryptocurrency deposits and transactions.
Primary integration is Heleket API for universal crypto payments.
Legacy cryptocurrencyapi.net methods are deprecated.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.exc import IntegrityError
from backend.models.user import User
from backend.models.user_address import UserAddress
from backend.models.user_transaction import UserTransaction
from backend.models.pending_invoice import PendingInvoice
from backend.core.heleket_client import get_heleket_client
from backend.services.log_service import LogService
from backend.services.notification_service import NotificationService
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service for managing payment deposits and transactions.
    
    Primary integration is Heleket API for universal crypto payments.
    Legacy cryptocurrencyapi.net methods are deprecated.
    """

    @staticmethod
    def _generate_payment_order_id(user_id: int) -> str:
        """
        Generate a payment order ID in the format DEPOSIT-{user_id}-{timestamp}.
        
        This format allows easy extraction of user_id in webhook handler.
        
        Args:
            user_id: User ID
            
        Returns:
            Order ID string in format "DEPOSIT-{user_id}-{timestamp}"
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"DEPOSIT-{user_id}-{timestamp}"

    @staticmethod
    async def create_payment_invoice(
        session: AsyncSession, user_id: int, amount_usd: Decimal
    ) -> Tuple[str, str, str, Optional[datetime]]:
        """
        Create a Heleket payment invoice with universal payment link (Mode B).
        
        Args:
            session: Database session
            user_id: ID of the user
            amount_usd: Payment amount in USD
            
        Returns:
            Tuple of (payment_url, payment_uuid, order_id, expired_at)
            
        Raises:
            HTTPException: On payment creation failure
        """
        try:
            # Generate order ID
            order_id = PaymentService._generate_payment_order_id(user_id)
            
            # Call Heleket API to create payment
            heleket_client = get_heleket_client()
            payment_data = await heleket_client.create_payment(
                amount_usd=amount_usd,
                order_id=order_id
            )
            
            # Extract response data
            payment_url = payment_data.get("payment_url")
            payment_uuid = payment_data.get("payment_uuid")
            expired_at_str = payment_data.get("expired_at")
            
            # Validate required fields
            if not payment_url or not payment_uuid:
                logger.error(f"Missing payment_url or payment_uuid in Heleket response: {payment_data}")
                raise HTTPException(
                    status_code=500,
                    detail="Invalid payment API response: missing payment_url or payment_uuid"
                )
            
            # Parse expired_at if present
            expired_at = None
            if expired_at_str:
                try:
                    # Heleket returns ISO format datetime
                    expired_at = datetime.fromisoformat(expired_at_str.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    logger.warning(f"Failed to parse expired_at: {expired_at_str}")
            
            # Log payment invoice creation
            await LogService.create_log(
                session=session,
                user_id=user_id,
                action_type="PAYMENT_INVOICE_CREATED",
                action_details={
                    "order_id": order_id,
                    "payment_uuid": payment_uuid,
                    "amount_usd": str(amount_usd),
                    "payment_url": payment_url,
                    "expired_at": expired_at_str
                }
            )

            # Save pending invoice with ORIGINAL amount for webhook processing
            # This fixes the issue where Heleket sends crypto amounts instead of USD
            pending_invoice = PendingInvoice(
                user_id=user_id,
                payment_uuid=payment_uuid,
                order_id=order_id,
                amount_usd=amount_usd,
                expired_at=expired_at
            )
            session.add(pending_invoice)
            await session.flush()

            logger.info(f"Pending invoice created: order_id={order_id}, amount_usd={amount_usd}")

            return payment_url, payment_uuid, order_id, expired_at
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating payment invoice: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to create payment invoice: {str(e)}"
            )

    @staticmethod
    async def process_ipn_webhook(
        session: AsyncSession, ipn_data: dict
    ) -> Dict[str, Any]:
        """
        Process incoming IPN webhook from cryptocurrencyapi.net.
        
        CRITICAL: This method is DEPRECATED and maintained only for processing any pending
        legacy transactions. All new payments use process_heleket_webhook(). This method
        will be removed in a future version after confirming no pending legacy transactions exist.
        
        DO NOT USE FOR NEW INTEGRATIONS.

        Args:
            session: Database session
            ipn_data: Parsed IPN payload

        Returns:
            Dict with transaction details and new balance

        Raises:
            HTTPException: On processing errors
        """
        logger.warning("DEPRECATED: process_ipn_webhook called - this endpoint is for legacy transactions only")
        try:
            # Extract user_id from label
            label = ipn_data.get("label")
            if not label:
                raise HTTPException(status_code=400, detail="Missing user label in IPN")

            try:
                user_id = int(label)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user label format")

            # Get user
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Check for duplicate transaction (idempotency)
            txid = ipn_data["txid"]
            existing = await session.execute(
                select(UserTransaction).where(UserTransaction.txid == txid)
            )
            if existing.scalar_one_or_none():
                logger.info(f"Duplicate IPN for txid {txid}, ignoring")

                # Log duplicate attempt
                await LogService.log_ipn_received(
                    session,
                    user_id,
                    txid,
                    "duplicate",
                    {"message": "Transaction already processed"}
                )

                return {
                    "status": "success",
                    "message": "Transaction already processed",
                    "txid": txid
                }

            # Calculate USD amount
            coin_amount = Decimal(ipn_data["amount"])

            # For now, we'll use a placeholder exchange rate
            # In production, you'd fetch real-time rates from an API
            exchange_rates = {
                "BTC": Decimal("50000"),
                "ETH": Decimal("3000"),
                "LTC": Decimal("100"),
                "BNB": Decimal("300"),
                "USDT": Decimal("1"),
            }

            currency = ipn_data.get("token") or ipn_data["currency"]
            coin_course = exchange_rates.get(currency, Decimal("1"))
            amount_in_dollar = await PaymentService.calculate_usd_amount(
                coin_amount, coin_course
            )

            # Validate minimum deposit amount
            if not await PaymentService.validate_minimum_deposit(amount_in_dollar):
                raise HTTPException(
                    status_code=400,
                    detail=f"Deposit amount ${amount_in_dollar} is below minimum ${settings.MIN_DEPOSIT_USD}"
                )

            # Create transaction record
            transaction = UserTransaction(
                user_id=user_id,
                chain=ipn_data["chain"],
                currency=currency,
                from_address=ipn_data["from_address"],
                to_address=ipn_data["to_address"],
                txid=txid,
                fee=Decimal(ipn_data["fee"]),
                amount_in_dollar=amount_in_dollar,
                coin_amount=coin_amount,
                coin_course=coin_course,
                dateOfTransaction=datetime.fromtimestamp(ipn_data["date"]),
                transaction_type="legacy"  # Mark as legacy transaction
            )

            session.add(transaction)
            await session.flush()

            # Update user balance atomically
            old_balance = user.balance
            user.balance += amount_in_dollar
            await session.flush()

            # Log deposit
            await LogService.log_deposit(
                session,
                user_id,
                ipn_data["chain"],
                amount_in_dollar,
                coin_amount,
                txid,
                user.balance
            )

            await session.commit()

            # Refresh user to get updated balance
            await session.refresh(user)

            return {
                "user_id": user_id,
                "currency": currency,
                "coin_amount": coin_amount,
                "amount_usd": amount_in_dollar,
                "txid": txid,
                "date": transaction.dateOfTransaction,
                "new_balance": user.balance,
                "old_balance": old_balance
            }

        except IntegrityError as e:
            await session.rollback()
            # Handle duplicate transaction
            logger.warning(f"Integrity error processing IPN: {str(e)}")
            return {
                "status": "success",
                "message": "Transaction already processed"
            }
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error processing IPN webhook: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to process payment"
            )

    @staticmethod
    async def get_transaction_history(
        session: AsyncSession, user_id: int, page: int = 1, page_size: int = 10
    ) -> Tuple[List[UserTransaction], int]:
        """
        Get user's transaction history with pagination.

        Args:
            session: Database session
            user_id: User ID
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Tuple of (transactions list, total count)
        """
        try:
            # Get total count
            count_result = await session.execute(
                select(func.count(UserTransaction.id_tranz)).where(
                    UserTransaction.user_id == user_id
                )
            )
            total = count_result.scalar() or 0

            # Get paginated transactions
            offset = (page - 1) * page_size
            result = await session.execute(
                select(UserTransaction)
                .where(UserTransaction.user_id == user_id)
                .order_by(UserTransaction.dateOfTransaction.desc())
                .offset(offset)
                .limit(page_size)
            )
            transactions = result.scalars().all()

            return transactions, total

        except Exception as e:
            logger.error(f"Error getting transaction history: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve transaction history"
            )

    @staticmethod
    async def get_user_addresses(
        session: AsyncSession, user_id: int
    ) -> Optional[UserAddress]:
        """
        Get all cryptocurrency addresses for a user.
        
        Returns legacy cryptocurrency addresses for historical reference only.
        New payments do not generate or use these addresses.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            UserAddress object or None
        """
        try:
            result = await session.execute(
                select(UserAddress).where(UserAddress.user_id == user_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting user addresses: {str(e)}")
            return None

    @staticmethod
    async def calculate_usd_amount(
        coin_amount: Decimal, coin_course: Decimal
    ) -> Decimal:
        """
        Calculate USD amount from cryptocurrency amount and exchange rate.

        Args:
            coin_amount: Amount in cryptocurrency
            coin_course: Exchange rate to USD

        Returns:
            Amount in USD rounded to 2 decimal places
        """
        usd_amount = coin_amount * coin_course
        return usd_amount.quantize(Decimal("0.01"))

    @staticmethod
    async def validate_minimum_deposit(amount_usd: Decimal) -> bool:
        """
        Validate that deposit amount meets minimum requirement.

        Args:
            amount_usd: Deposit amount in USD

        Returns:
            True if valid, False otherwise
        """
        return amount_usd >= settings.MIN_DEPOSIT_USD
    
    @staticmethod
    async def process_heleket_webhook(
        session: AsyncSession,
        payment_uuid: str,
        order_id: str,
        amount_usd: Decimal,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process incoming Heleket payment webhook.
        
        This method handles Heleket webhook payments by:
        1. Extracting user_id from order_id
        2. Checking for duplicate payments (idempotency)
        3. Validating minimum deposit amount
        4. Updating user balance
        5. Creating transaction record
        6. Logging the deposit
        
        Args:
            session: Database session
            payment_uuid: Heleket payment UUID
            order_id: Order identifier (contains user_id)
            amount_usd: Payment amount in USD
            webhook_data: Full webhook payload for logging
            
        Returns:
            Dict with transaction details and new balance
            
        Raises:
            HTTPException: On processing errors
        """
        try:
            # Validate required parameters
            if not payment_uuid or not order_id:
                logger.error(f"Missing payment_uuid or order_id: uuid={payment_uuid}, order_id={order_id}")
                raise HTTPException(
                    status_code=400,
                    detail="Missing payment_uuid or order_id"
                )
            
            # Extract user_id from order_id
            # Order ID format should be something like "user-{user_id}-{timestamp}"
            # or just the user_id if that's the format used
            try:
                # Try to parse user_id from order_id
                # Assuming format like "DEPOSIT-123-1234567890" or just "123"
                if order_id.startswith("DEPOSIT-"):
                    user_id = int(order_id.split("-")[1])
                else:
                    user_id = int(order_id)
            except (ValueError, IndexError) as e:
                logger.error(f"Failed to extract user_id from order_id '{order_id}': {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid order_id format: {order_id}"
                )
            
            # Get user
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail=f"User not found: {user_id}"
                )
            
            # Check for duplicate transaction using payment_uuid (idempotency)
            existing = await session.execute(
                select(UserTransaction).where(UserTransaction.txid == payment_uuid)
            )
            if existing.scalar_one_or_none():
                logger.info(f"Duplicate Heleket webhook for payment UUID {payment_uuid}, ignoring")
                
                # Log duplicate attempt
                await LogService.log_ipn_received(
                    session,
                    user_id,
                    payment_uuid,
                    "duplicate",
                    {"message": "Payment already processed", "order_id": order_id}
                )
                
                return {
                    "status": "success",
                    "message": "Payment already processed",
                    "payment_uuid": payment_uuid,
                    "order_id": order_id
                }

            # Find pending invoice to get ORIGINAL amount (not crypto amount from webhook)
            pending_result = await session.execute(
                select(PendingInvoice).where(PendingInvoice.payment_uuid == payment_uuid)
            )
            pending_invoice = pending_result.scalar_one_or_none()

            if pending_invoice:
                # Use ORIGINAL amount from invoice, not merchant_amount (which may be crypto)
                original_amount = pending_invoice.amount_usd

                logger.warning(
                    f"Amount comparison - Original invoice: {original_amount}, "
                    f"Webhook merchant_amount: {amount_usd}, Order: {order_id}"
                )

                # Update pending invoice status
                pending_invoice.status = "completed"
                pending_invoice.webhook_amount = amount_usd  # Save webhook amount for analysis
                pending_invoice.completed_at = datetime.utcnow()

                # USE ORIGINAL AMOUNT for crediting, not the webhook amount!
                amount_usd = original_amount
            else:
                # Fallback: no pending invoice found (legacy payment or data issue)
                logger.error(
                    f"No pending invoice found for payment_uuid {payment_uuid}. "
                    f"Using webhook amount: {amount_usd}"
                )

            # Create transaction record
            # Using Heleket payment UUID as txid
            transaction = UserTransaction(
                user_id=user_id,
                chain="Heleket",  # Heleket handles multiple chains internally
                currency="USD",  # Heleket converts to USD
                from_address="heleket",  # Placeholder as Heleket abstracts this
                to_address=order_id,  # Store order_id for reference
                txid=payment_uuid,  # Use Heleket's payment UUID
                fee=Decimal("0.00"),  # Fee is handled by Heleket
                amount_in_dollar=amount_usd,
                coin_amount=amount_usd,  # Same as USD for Heleket
                coin_course=Decimal("1.00"),  # 1:1 for USD
                dateOfTransaction=datetime.utcnow(),
                # Heleket-specific fields for proper history display
                payment_uuid=payment_uuid,
                order_id=order_id,
                transaction_type="heleket"
            )
            
            session.add(transaction)
            await session.flush()
            
            # Update user balance atomically
            old_balance = user.balance
            user.balance += amount_usd
            await session.flush()
            
            # Log deposit
            await LogService.log_deposit(
                session,
                user_id,
                "Heleket",
                amount_usd,
                amount_usd,  # coin_amount same as USD
                payment_uuid,
                user.balance
            )
            
            # Log webhook received
            await LogService.log_ipn_received(
                session,
                user_id,
                payment_uuid,
                "success",
                {
                    "order_id": order_id,
                    "amount_usd": str(amount_usd),
                    "status": webhook_data.get("status"),
                    "is_final": webhook_data.get("is_final")
                }
            )
            
            await session.commit()

            # Refresh user to get updated balance
            await session.refresh(user)

            # Send notification to user's Telegram accounts
            if user.telegram_id:
                for tg_id in user.telegram_id:
                    try:
                        await NotificationService.notify_payment_received(
                            user_id=tg_id,
                            amount_usd=amount_usd,
                            new_balance=user.balance,
                            payment_uuid=payment_uuid
                        )
                    except Exception as e:
                        # Don't fail the webhook if notification fails
                        logger.error(f"Failed to send payment notification to Telegram {tg_id}: {e}")

            return {
                "user_id": user_id,
                "payment_uuid": payment_uuid,
                "order_id": order_id,
                "amount_usd": amount_usd,
                "new_balance": user.balance,
                "old_balance": old_balance,
                "currency": "USD",
                "date": transaction.dateOfTransaction
            }
            
        except IntegrityError as e:
            await session.rollback()
            # Handle duplicate transaction
            logger.warning(f"Integrity error processing Heleket webhook: {str(e)}")
            return {
                "status": "success",
                "message": "Payment already processed"
            }
        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error processing Heleket webhook: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Failed to process payment"
            )