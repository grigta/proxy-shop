from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_async_session
from backend.schemas.purchase import (
    PurchaseRequest,
    PurchaseResponse,
    PurchaseHistoryItem,
    PurchaseHistoryResponse,
    ValidateProxyResponse,
    ExtendProxyRequest,
    ExtendProxyResponse,
    RefundResponse,
    BulkValidatePPTPResponse
)
from backend.services.purchase_service import PurchaseService
from backend.api.dependencies import get_current_user, get_client_ip
from backend.models.user import User
from backend.core.utils import calculate_hours_left
from typing import Optional
import logging
import json


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/purchase", tags=["Purchase"])


@router.post(
    "/socks5",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Purchase SOCKS5 proxy",
    description="Buy SOCKS5 proxy with balance deduction"
)
async def purchase_socks5(
    request_data: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """Purchase SOCKS5 proxy."""
    try:
        # Process purchase
        proxy_history, proxies_data = await PurchaseService.purchase_socks5(
            session=session,
            user_id=current_user.user_id,
            product_id=request_data.product_id,
            quantity=request_data.quantity,
            coupon_code=request_data.coupon_code,
            ip=client_ip
        )

        # Calculate hours left
        hours_left = calculate_hours_left(proxy_history.expires_at)

        # Get updated user balance
        await session.refresh(current_user)

        # Parse proxy data for response
        proxies_full = json.loads(proxy_history.proxies)

        return PurchaseResponse(
            success=True,
            order_id=proxy_history.order_id,
            product_id=proxy_history.product_id,
            quantity=proxy_history.quantity,
            price=proxy_history.price,
            original_price=proxy_history.price,  # TODO: Calculate original price before discount
            discount_applied=None,  # TODO: Calculate discount amount
            country=proxy_history.country,
            state=None,  # TODO: Extract from product data
            city=None,  # TODO: Extract from product data
            zip=None,  # TODO: Extract from product data
            proxies=proxies_full,
            expires_at=proxy_history.expires_at,
            hours_left=hours_left,
            new_balance=current_user.balance
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing SOCKS5: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Purchase failed: {str(e)}"
        )


@router.post(
    "/pptp",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Purchase PPTP proxy",
    description="Buy PPTP proxy by specifying location filters (country, state, city, zip). System will find and validate available proxies."
)
async def purchase_pptp(
    request_data: PurchaseRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """Purchase PPTP proxy."""
    try:
        # Check if direct product_id purchase
        if request_data.product_id:
            # Direct purchase by product_id
            pptp_history, pptp_data = await PurchaseService.purchase_pptp_by_product_id(
                session=session,
                user_id=current_user.user_id,
                product_id=request_data.product_id,
                coupon_code=request_data.coupon_code,
                ip=client_ip
            )
        else:
            # Extract filter parameters
            country = request_data.country
            catalog_id = request_data.catalog_id
            state = request_data.state
            city = request_data.city
            zip_code = request_data.zip_code

            # Validate required parameters
            if not country:
                raise HTTPException(
                    status_code=400,
                    detail="Country/region is required for PPTP purchase"
                )

            # Process purchase by filters
            pptp_history, pptp_data = await PurchaseService.purchase_pptp(
                session=session,
                user_id=current_user.user_id,
                country=country,
                catalog_id=catalog_id,
                state=state,
                city=city,
                zip_code=zip_code,
                coupon_code=request_data.coupon_code,
                ip=client_ip
            )

        # Calculate hours left
        hours_left = calculate_hours_left(pptp_history.expires_at)

        # Get updated user balance
        await session.refresh(current_user)

        return PurchaseResponse(
            success=True,
            order_id=None,  # PPTP doesn't use order_id
            product_id=pptp_history.product_id,
            quantity=1,
            price=pptp_history.price,
            original_price=pptp_history.price,
            discount_applied=None,
            country=pptp_data.get("country", request_data.country),
            state=pptp_data.get("state"),
            city=pptp_data.get("city"),
            zip=pptp_data.get("zip"),
            proxies=[pptp_data],
            expires_at=pptp_history.expires_at,
            hours_left=hours_left,
            new_balance=current_user.balance
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing PPTP with filters {request_data.country}/{request_data.state}/{request_data.city}/{request_data.zip_code}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Purchase failed: {str(e)}"
        )


@router.get(
    "/history/{user_id}",
    response_model=PurchaseHistoryResponse,
    summary="Get purchase history",
    description="Get user's proxy purchase history with pagination"
)
async def get_purchase_history(
    user_id: int = Path(..., description="User ID"),
    proxy_type: Optional[str] = Query(None, description="Filter by proxy type (SOCKS5/PPTP)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user's purchase history."""
    try:
        # Check access
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

        # Get purchase history
        purchases, total = await PurchaseService.get_purchase_history(
            session=session,
            user_id=user_id,
            proxy_type=proxy_type,
            page=page,
            page_size=page_size
        )

        # Convert to response models
        history_items = []
        for purchase in purchases:
            history_item = PurchaseHistoryItem(
                id=purchase["id"],
                order_id=purchase.get("order_id"),
                proxy_type=purchase["proxy_type"],
                quantity=purchase["quantity"],
                price=purchase["price"],
                country=purchase["country"],
                state=purchase.get("state"),
                city=purchase.get("city"),
                zip=purchase.get("zip"),
                proxies=purchase["proxies"],
                datestamp=purchase["datestamp"],
                expires_at=purchase["expires_at"],
                hours_left=purchase["hours_left"],
                isRefunded=purchase["isRefunded"],
                resaled=purchase.get("resaled", False),
                user_key=purchase.get("user_key")
            )
            history_items.append(history_item)

        return PurchaseHistoryResponse(
            purchases=history_items,
            total=total,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting purchase history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.post(
    "/validate/{proxy_id}",
    response_model=ValidateProxyResponse,
    summary="Validate proxy status",
    description="Check if proxy is online/offline and eligible for refund"
)
async def validate_proxy(
    proxy_id: int = Path(..., description="Proxy ID from purchase history"),
    proxy_type: str = Query(..., description="Proxy type (socks5/pptp)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """Validate proxy status and process refund if eligible."""
    try:
        # Validate proxy (ownership check is now inside)
        result = await PurchaseService.validate_proxy(
            session=session,
            proxy_id=proxy_id,
            proxy_type=proxy_type.lower(),
            user_id=current_user.user_id
        )

        # If proxy is offline and eligible for refund, process it
        if not result["online"] and result["refund_eligible"]:
            refund_result = await PurchaseService.process_refund(
                session=session,
                proxy_id=proxy_id,
                proxy_type=proxy_type.lower(),
                user_id=current_user.user_id,
                ip=client_ip
            )

            # Update message to include refund info
            result["message"] += f" Возврат {refund_result['refunded_amount']} USD выполнен."

        return ValidateProxyResponse(
            proxy_id=proxy_id,
            online=result["online"],
            latency_ms=result.get("latency_ms"),
            exit_ip=result.get("exit_ip"),
            minutes_since_purchase=result["minutes_since_purchase"],
            refund_eligible=result["refund_eligible"],
            refund_window_minutes=result["refund_window_minutes"],
            message=result["message"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating proxy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.post(
    "/extend/{proxy_id}",
    response_model=ExtendProxyResponse,
    summary="Extend proxy duration",
    description="Extend proxy expiration time (only if proxy is online)"
)
async def extend_proxy(
    request_data: ExtendProxyRequest,
    proxy_id: int = Path(..., description="Proxy ID from purchase history"),
    proxy_type: str = Query(..., description="Proxy type (socks5/pptp)"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """Extend proxy duration."""
    try:
        # Process extension
        result = await PurchaseService.extend_proxy(
            session=session,
            proxy_id=proxy_id,
            proxy_type=proxy_type.lower(),
            user_id=current_user.user_id,
            hours=request_data.hours,
            ip=client_ip
        )

        return ExtendProxyResponse(
            success=result["success"],
            proxy_id=proxy_id,
            price=result["price"],
            new_expires_at=result["new_expires_at"],
            hours_added=result["hours_added"],
            new_balance=result["new_balance"],
            message=result["message"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extending proxy: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Extension failed: {str(e)}"
        )


@router.post(
    "/validate-pptp",
    response_model=BulkValidatePPTPResponse,
    summary="Validate all user's PPTP proxies",
    description="Check all user's PPTP proxies from last 24 hours and automatically refund non-working ones"
)
async def validate_all_pptp(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    Validate all user's PPTP proxies from last 24 hours.

    This endpoint checks each PPTP proxy by connecting to port 1723
    and automatically refunds any that are not responding.
    """
    try:
        result = await PurchaseService.validate_all_user_pptp(
            session=session,
            user_id=current_user.user_id,
            ip=client_ip
        )

        return BulkValidatePPTPResponse(
            validated_count=result["validated_count"],
            valid_count=result["valid_count"],
            invalid_count=result["invalid_count"],
            refunded_amount=result["refunded_amount"],
            new_balance=result["new_balance"],
            details=result["details"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk PPTP validation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Bulk validation failed: {str(e)}"
        )