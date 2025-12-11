"""
Payment API routes for deposit transactions.

Primary integration is Heleket API for universal cryptocurrency payments.
Legacy cryptocurrencyapi.net endpoints are deprecated but maintained for backward compatibility.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_async_session
from backend.schemas.payment import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    HeleketWebhookPayload,
    TransactionHistoryItem,
    TransactionHistoryResponse,
    IPNWebhookResponse,
    IPNWebhookPayload  # Used only for legacy /webhook/ipn endpoint
)
from backend.services.payment_service import PaymentService
from backend.api.dependencies import get_current_user, get_client_ip
from backend.models.user import User
from backend.core.crypto_utils import verify_ipn_signature  # DEPRECATED: Only for legacy /webhook/ipn endpoint
from backend.core.config import settings
from typing import Optional, Dict, Any
from decimal import Decimal
import logging
import json

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/payment", tags=["Payment"])


@router.post(
    "/generate-address",
    response_model=CreatePaymentResponse,
    summary="Create payment invoice",
    description="Create a Heleket payment invoice with universal payment link (Mode B)"
)
async def generate_deposit_address(
    request_data: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> CreatePaymentResponse:
    """
    Create a Heleket payment invoice with universal payment link (Mode B).

    Args:
        request_data: Request with optional amount_usd (defaults to MIN_DEPOSIT_USD)
        current_user: Authenticated user
        session: Database session

    Returns:
        CreatePaymentResponse with payment_url, payment_uuid, order_id, expired_at

    Raises:
        HTTPException: If payment invoice creation fails
    """
    try:
        # Use provided amount or default to MIN_DEPOSIT_USD
        amount_usd = request_data.amount_usd if request_data.amount_usd else Decimal(str(settings.MIN_DEPOSIT_USD))
        
        # Create payment invoice via Heleket
        payment_url, payment_uuid, order_id, expired_at = await PaymentService.create_payment_invoice(
            session, current_user.user_id, amount_usd
        )
        
        # Commit the transaction after successful payment invoice creation
        await session.commit()

        # Return new response format with payment URL
        return CreatePaymentResponse(
            payment_url=payment_url,
            payment_uuid=payment_uuid,
            order_id=order_id,
            expired_at=expired_at,
            amount_usd=amount_usd,
            min_amount_usd=settings.MIN_DEPOSIT_USD
        )

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating payment invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment invoice"
        )


@router.post(
    "/webhook/ipn",
    response_model=IPNWebhookResponse,
    summary="Legacy IPN Webhook (DEPRECATED - DO NOT USE)",
    description="DEPRECATED: This endpoint is for legacy cryptocurrencyapi.net webhooks only. It is maintained solely for processing any pending transactions from the old system. All new integrations must use /webhook/heleket. This endpoint will be removed after confirming no pending legacy transactions exist."
)
async def process_ipn_webhook(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
) -> IPNWebhookResponse:
    """
    Process IPN webhook from cryptocurrencyapi.net.
    
    DEPRECATED: This endpoint is for legacy cryptocurrencyapi.net webhooks only.
    It is maintained solely for processing any pending transactions from the old system.
    
    All new integrations must use /webhook/heleket. This endpoint will be removed after
    confirming no pending legacy transactions exist.

    This endpoint is called by cryptocurrencyapi.net when a payment is received.
    It verifies the signature, processes the payment, and updates user balance.

    Args:
        request: Raw HTTP request
        session: Database session

    Returns:
        IPNWebhookResponse with status "ok"

    Note:
        Always returns 200 OK to prevent webhook retries
    """
    logger.warning("DEPRECATED: Legacy IPN webhook endpoint called - all new integrations must use /webhook/heleket")
    try:
        # Get raw body for signature verification
        raw_body = await request.body()
        raw_body_str = raw_body.decode('utf-8')

        # Parse JSON
        try:
            ipn_data = json.loads(raw_body_str)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in IPN webhook")
            return IPNWebhookResponse(
                status="ok",
                message="Invalid JSON format"
            )

        # Validate schema
        try:
            ipn_payload = IPNWebhookPayload(**ipn_data)
        except Exception as e:
            logger.error(f"IPN validation error: {str(e)}")
            return IPNWebhookResponse(
                status="ok",
                message="Validation error"
            )

        # Verify signature
        is_valid = verify_ipn_signature(
            raw_body_str,
            ipn_payload.sign,
            settings.CRYPTO_API_IPN_SECRET
        )

        if not is_valid:
            logger.warning(f"Invalid IPN signature for txid {ipn_payload.txid}")
            # Still return 200 OK but don't process
            return IPNWebhookResponse(
                status="ok",
                message="Invalid signature"
            )

        # Check transaction type
        if ipn_payload.type != "in":
            logger.info(f"Ignoring outgoing transaction {ipn_payload.txid}")
            return IPNWebhookResponse(
                status="ok",
                message="Ignored: not incoming transaction"
            )

        # Check confirmations
        if ipn_payload.confirmation < 1:
            logger.info(f"Waiting for confirmations for txid {ipn_payload.txid}")
            return IPNWebhookResponse(
                status="ok",
                message="Waiting for confirmations"
            )

        # Log IPN received
        await LogService.log_ipn_received(
            session,
            int(ipn_payload.label) if ipn_payload.label else 0,
            ipn_payload.txid,
            "processing",
            ipn_data
        )

        # Process payment
        result = await PaymentService.process_ipn_webhook(
            session,
            ipn_payload.model_dump()
        )

        logger.info(f"Successfully processed payment: {result}")

        # Log successful processing
        await LogService.log_ipn_received(
            session,
            int(ipn_payload.label) if ipn_payload.label else 0,
            ipn_payload.txid,
            "success",
            result
        )

        return IPNWebhookResponse(
            status="ok",
            message="Payment processed successfully"
        )

    except HTTPException as e:
        # Log but still return 200 OK
        logger.error(f"HTTP exception in IPN webhook: {str(e)}")

        # Try to log failure if we have necessary data
        if 'ipn_payload' in locals():
            try:
                await LogService.log_ipn_received(
                    session,
                    int(ipn_payload.label) if ipn_payload.label else 0,
                    ipn_payload.txid,
                    "failed",
                    {"error": str(e.detail)}
                )
            except:
                pass  # Don't fail on logging error

        return IPNWebhookResponse(
            status="ok",
            message=f"Error: {e.detail}"
        )
    except Exception as e:
        # Log error but always return 200 OK
        logger.error(f"Unexpected error in IPN webhook: {str(e)}")

        # Try to log failure if we have necessary data
        if 'ipn_payload' in locals():
            try:
                await LogService.log_ipn_received(
                    session,
                    int(ipn_payload.label) if ipn_payload.label else 0,
                    ipn_payload.txid,
                    "failed",
                    {"error": str(e)}
                )
            except:
                pass  # Don't fail on logging error

        return IPNWebhookResponse(
            status="ok",
            message="Error processing payment"
        )


@router.get(
    "/history/{user_id}",
    response_model=TransactionHistoryResponse,
    summary="Get transaction history",
    description="Get user's deposit transaction history with pagination"
)
async def get_transaction_history(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> TransactionHistoryResponse:
    """
    Get paginated transaction history for a user.

    Args:
        user_id: User ID to get history for
        page: Page number (1-based)
        page_size: Items per page (max 50)
        current_user: Authenticated user
        session: Database session

    Returns:
        Paginated transaction history

    Raises:
        HTTPException: If user tries to access another user's history
    """
    try:
        # Check access permission
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: cannot view other user's transactions"
            )

        # Validate and cap page_size
        if page_size > 50:
            page_size = 50
        if page_size < 1:
            page_size = 1
        if page < 1:
            page = 1

        # Get transaction history
        transactions, total = await PaymentService.get_transaction_history(
            session, user_id, page, page_size
        )

        # Convert to response model
        transaction_items = [
            TransactionHistoryItem(
                id_tranz=t.id_tranz,
                chain=t.chain,
                currency=t.currency,
                amount_in_dollar=t.amount_in_dollar,
                coin_amount=t.coin_amount,
                coin_course=t.coin_course,
                txid=t.txid,
                from_address=t.from_address or "",  # Default to empty string for Heleket transactions
                to_address=t.to_address or "",  # Default to empty string for Heleket transactions
                fee=t.fee,
                dateOfTransaction=t.dateOfTransaction,
                confirmation=None,  # Can be added if stored
                payment_uuid=t.payment_uuid,  # Include Heleket payment UUID (None for legacy)
                order_id=t.order_id,  # Include order ID (None for legacy)
                transaction_type=t.transaction_type or "legacy"  # Default to 'legacy' if not set (for old records)
            )
            for t in transactions
        ]

        return TransactionHistoryResponse(
            transactions=transaction_items,
            total=total,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction history"
        )


@router.get(
    "/addresses",
    summary="Get user's crypto addresses",
    description="NOTE: Returns legacy crypto addresses. New payments use universal payment links."
)
async def get_user_addresses(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Optional[str]]:
    """
    Get all cryptocurrency addresses for the current user.
    
    NOTE: Returns legacy crypto addresses. New payments use Heleket universal links.

    Args:
        current_user: Authenticated user
        session: Database session

    Returns:
        Dictionary of addresses by chain

    Example:
        {
            "btc_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "eth_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb7",
            "ltc_address": null,
            ...
        }
    """
    try:
        addresses = await PaymentService.get_user_addresses(
            session, current_user.user_id
        )

        if not addresses:
            return {
                "btc_address": None,
                "eth_address": None,
                "ltc_address": None,
                "bsc_address": None,
                "trc20usdt_address": None
            }

        return {
            "btc_address": addresses.btc_address,
            "eth_address": addresses.eth_address,
            "ltc_address": addresses.ltc_address,
            "bsc_address": addresses.bsc_address,
            "trc20usdt_address": addresses.trc20usdt_address
        }

    except Exception as e:
        logger.error(f"Error getting user addresses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve addresses"
        )


# Import LogService here to avoid circular imports
from backend.services.log_service import LogService


@router.post(
    "/webhook/heleket",
    summary="Heleket Payment Webhook",
    description="Receive and process payment notifications from Heleket"
)
async def process_heleket_webhook(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, str]:
    """
    Process Heleket payment webhook.
    
    This endpoint is called by Heleket when a payment status changes.
    It verifies the signature using string-based removal to preserve JSON fidelity,
    processes the payment, and updates user balance.
    
    HTTP Status Code Strategy:
    - 200 OK: For validation errors (invalid signature, malformed data) - prevents retries
    - 500 Internal Server Error: For internal issues (DB errors, service unavailability) - triggers retries
    
    Args:
        request: Raw HTTP request
        session: Database session
        
    Returns:
        Dict with status "ok"
        
    Raises:
        HTTPException with 500: For internal server errors that should trigger retry
    """
    try:
        # Get raw body for signature verification
        # This is critical: we need the exact string Heleket sent
        raw_body = await request.body()
        raw_body_str = raw_body.decode('utf-8')
        
        # Log raw body length for debugging (without exposing full content)
        logger.info(f"Heleket webhook received - Body length: {len(raw_body_str)} bytes")
        
        # Parse JSON to extract webhook data
        try:
            webhook_data = json.loads(raw_body_str)
        except json.JSONDecodeError as e:
            # Validation error - return 200 OK to prevent retries
            logger.error(f"Invalid JSON in Heleket webhook: {e}")
            return {"status": "ok", "message": "Invalid JSON format"}
        
        # Extract signature from webhook data
        received_sign = webhook_data.get("sign")
        if not received_sign:
            # Validation error - return 200 OK to prevent retries
            logger.error("Missing 'sign' field in Heleket webhook")
            return {"status": "ok", "message": "Missing signature"}
        
        # Get Heleket client and verify signature
        from backend.core.heleket_client import get_heleket_client
        heleket_client = get_heleket_client()
        
        is_valid = heleket_client.verify_webhook_signature(raw_body_str, received_sign)
        
        if not is_valid:
            # Validation error - return 200 OK to prevent retries
            # Log the failure with sanitized data (no sensitive info)
            logger.warning(
                f"Invalid Heleket webhook signature - "
                f"UUID: {webhook_data.get('uuid')}, "
                f"Order ID: {webhook_data.get('order_id')}, "
                f"Status: {webhook_data.get('status')}"
            )
            return {"status": "ok", "message": "Invalid signature"}
        
        # Validate webhook payload using HeleketWebhookPayload schema
        try:
            payload = HeleketWebhookPayload(**webhook_data)
        except Exception as e:
            # Validation error - return 200 OK to prevent retries
            logger.error(f"Heleket webhook validation error: {str(e)}")
            return {"status": "ok", "message": "Validation error"}
        
        # Extract webhook fields from validated payload
        payment_uuid = payload.uuid
        order_id = payload.order_id
        status = payload.status  # 'paid' or 'check'
        is_final = payload.is_final
        merchant_amount = payload.merchant_amount
        
        # Validate required fields
        if not payment_uuid or not order_id:
            # Validation error - return 200 OK to prevent retries
            logger.error(
                f"Missing required fields in Heleket webhook - "
                f"UUID: {payment_uuid}, Order ID: {order_id}"
            )
            return {"status": "ok", "message": "Invalid payload"}
        
        if not merchant_amount:
            # Validation error - return 200 OK to prevent retries
            logger.error(f"Missing merchant_amount in Heleket webhook: {merchant_amount}")
            return {"status": "ok", "message": "Invalid payload"}
        
        logger.info(
            f"Heleket webhook verified - UUID: {payment_uuid}, "
            f"Order: {order_id}, Status: {status}, Final: {is_final}, "
            f"Amount: {merchant_amount}"
        )
        
        # Only process if payment is finalized and successfully paid
        # Accept both 'paid' (exact amount) and 'paid_over' (overpayment)
        successful_statuses = ("paid", "paid_over")
        if status not in successful_statuses or not is_final:
            # Not an error - just not ready to process yet
            logger.info(
                f"Heleket webhook not processed - Status: {status}, "
                f"Final: {is_final} (waiting for final payment confirmation)"
            )
            return {"status": "ok", "message": "Waiting for final confirmation"}
        
        # Validate merchant_amount value
        try:
            amount_value = float(merchant_amount)
            if amount_value <= 0:
                # Validation error - return 200 OK to prevent retries
                logger.error(f"Invalid merchant_amount value in Heleket webhook: {merchant_amount}")
                return {"status": "ok", "message": "Invalid amount"}
        except (ValueError, TypeError):
            # Validation error - return 200 OK to prevent retries
            logger.error(f"Invalid merchant_amount format in Heleket webhook: {merchant_amount}")
            return {"status": "ok", "message": "Invalid amount"}
        
        # Process the payment via PaymentService
        # HTTPExceptions from PaymentService will propagate as 500 errors for retries
        result = await PaymentService.process_heleket_webhook(
            session,
            payment_uuid=payment_uuid,
            order_id=order_id,
            amount_usd=Decimal(str(merchant_amount)),
            webhook_data=webhook_data
        )
        
        logger.info(f"Heleket payment processed successfully: {result}")
        
        return {"status": "ok", "message": "Payment processed successfully"}
        
    except HTTPException:
        # Re-raise HTTPException to return proper status code (likely 500 for internal errors)
        # This allows Heleket to retry on genuine server issues
        raise
        
    except Exception as e:
        # Unexpected internal error - return 500 to trigger retry
        logger.error(f"Unexpected error in Heleket webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing payment"
        )