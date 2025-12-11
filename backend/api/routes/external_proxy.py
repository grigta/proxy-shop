"""
External Proxy API Routes

REST API endpoints for external SOCKS5 proxy integration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.core.database import get_async_session
from backend.api.dependencies import get_current_user, get_current_admin_user, get_client_ip
from backend.models.user import User
from backend.services.external_proxy_service import ExternalProxyService
from backend.schemas.external_proxy import (
    ExternalProxyFilterRequest,
    ExternalProxyListResponse,
    ExternalProxyPurchaseRequest,
    ExternalProxyPurchaseResponse,
    ExternalProxyRefundRequest,
    ExternalProxyRefundResponse,
    ExternalProxySyncRequest,
    ExternalProxySyncResponse,
    ExternalProxyResponse,
    ExternalProxyStatsResponse
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external-proxy", tags=["External Proxy"])


@router.get("/list", response_model=ExternalProxyListResponse)
async def list_external_proxies(
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    city: Optional[str] = Query(None, description="Filter by city"),
    page: int = Query(0, ge=0, description="Page number (0-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get list of available external SOCKS5 proxies.

    Returns proxies from local inventory that have been synced from external API.
    Use filters to narrow down results by location.
    """
    try:
        offset = page * page_size

        proxies = await ExternalProxyService.get_external_proxies_inventory(
            session=session,
            country_code=country_code,
            city=city,
            limit=page_size,
            offset=offset
        )

        # Get total count (simplified - could be optimized with count query)
        all_proxies = await ExternalProxyService.get_external_proxies_inventory(
            session=session,
            country_code=country_code,
            city=city,
            limit=1000,
            offset=0
        )
        total = len(all_proxies)

        return ExternalProxyListResponse(
            proxies=[ExternalProxyResponse(**p) for p in proxies],
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing external proxies: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch external proxies: {str(e)}"
        )


@router.post("/purchase", response_model=ExternalProxyPurchaseResponse)
async def purchase_external_proxy(
    request: ExternalProxyPurchaseRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    client_ip: Optional[str] = Depends(get_client_ip)
):
    """
    Purchase an external SOCKS5 proxy.

    Requires:
    - Sufficient balance ($2.00)
    - Valid product_id from external proxy inventory

    Returns proxy credentials including IP, port, username, and password.
    Proxy is valid for 24 hours and can be refunded within 1 hour if offline.
    """
    try:
        logger.info(f"User {current_user.user_id} purchasing external proxy {request.product_id}")

        proxy_history, credentials = await ExternalProxyService.purchase_external_proxy(
            session=session,
            user_id=current_user.user_id,
            product_id=request.product_id,
            ip=client_ip
        )

        return ExternalProxyPurchaseResponse(
            order_id=proxy_history.order_id,
            proxy_id=credentials.get('external_proxy_id'),
            credentials=credentials,
            price=proxy_history.price,
            expires_at=proxy_history.expires_at,
            refundable=credentials.get('refundable', True)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing external proxy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Purchase failed: {str(e)}"
        )


@router.post("/refund", response_model=ExternalProxyRefundResponse)
async def refund_external_proxy(
    request: ExternalProxyRefundRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Refund an external proxy purchase.

    Requirements:
    - Purchase must be within 1 hour
    - Proxy must be offline/non-working
    - Cannot have been previously refunded

    Returns refund amount to user balance.
    """
    try:
        logger.info(f"User {current_user.user_id} requesting refund for order {request.order_id}")

        result = await ExternalProxyService.refund_external_proxy(
            session=session,
            user_id=current_user.user_id,
            order_id=request.order_id
        )

        return ExternalProxyRefundResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refunding external proxy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Refund failed: {str(e)}"
        )


@router.post("/sync", response_model=ExternalProxySyncResponse)
async def sync_external_proxies(
    request: ExternalProxySyncRequest = ExternalProxySyncRequest(),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Manually sync proxies from external API to local inventory.

    **Admin only endpoint.**

    Fetches available proxies from external API and adds them to the Product table.
    Existing proxies are not duplicated. Use filters to sync specific locations.

    This operation runs automatically every 5 minutes via scheduler, but can be
    triggered manually for immediate updates.
    """
    try:
        logger.info(f"Admin {current_user.user_id} triggering manual sync")

        stats = await ExternalProxyService.sync_proxies_to_inventory(
            session=session,
            country_code=request.country_code,
            city=request.city,
            region=request.region,
            page_size=request.page_size
        )

        return ExternalProxySyncResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing external proxies: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_external_inventory(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Remove offline/unavailable proxies from inventory.

    **Admin only endpoint.**

    Checks each external proxy in inventory against the external API
    and removes those that are no longer available or offline.

    This runs automatically during sync, but can be triggered manually.
    """
    try:
        logger.info(f"Admin {current_user.user_id} triggering cleanup")

        removed_count = await ExternalProxyService.cleanup_expired_inventory(session)

        return {
            "status": "success",
            "removed_count": removed_count,
            "message": f"Removed {removed_count} expired proxies from inventory"
        }

    except Exception as e:
        logger.error(f"Error cleaning up inventory: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/stats", response_model=ExternalProxyStatsResponse)
async def get_external_proxy_stats(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get statistics about external proxy integration.

    **Admin only endpoint.**

    Returns metrics including:
    - Total proxies in inventory
    - Total sold
    - Total refunds
    - Revenue generated
    - Available countries
    """
    try:
        from sqlalchemy import select, func, and_
        from backend.models.product import Product
        from backend.models.proxy_history import ProxyHistory
        import json

        # Count inventory
        inventory_result = await session.execute(
            select(func.count(Product.product_id)).where(
                Product.line_name == ExternalProxyService.EXTERNAL_SOURCE_MARKER
            )
        )
        total_inventory = inventory_result.scalar() or 0

        # Count sold (proxy_history with external credentials)
        sold_result = await session.execute(
            select(func.count(ProxyHistory.id)).where(
                and_(
                    ProxyHistory.proxies.like('%external_proxy_id%'),
                    ProxyHistory.isRefunded == False
                )
            )
        )
        total_sold = sold_result.scalar() or 0

        # Count refunded
        refunded_result = await session.execute(
            select(func.count(ProxyHistory.id)).where(
                and_(
                    ProxyHistory.proxies.like('%external_proxy_id%'),
                    ProxyHistory.isRefunded == True
                )
            )
        )
        total_refunded = refunded_result.scalar() or 0

        # Calculate revenue
        revenue_result = await session.execute(
            select(func.sum(ProxyHistory.price)).where(
                and_(
                    ProxyHistory.proxies.like('%external_proxy_id%'),
                    ProxyHistory.isRefunded == False
                )
            )
        )
        revenue = float(revenue_result.scalar() or 0)

        # Count unique countries
        products_result = await session.execute(
            select(Product.product).where(
                Product.line_name == ExternalProxyService.EXTERNAL_SOURCE_MARKER
            )
        )
        products = products_result.scalars().all()
        countries = set()
        for product_json in products:
            try:
                data = json.loads(product_json)
                country = data.get('country_code')
                if country:
                    countries.add(country)
            except:
                continue

        return ExternalProxyStatsResponse(
            total_inventory=total_inventory,
            total_sold=total_sold,
            total_refunded=total_refunded,
            revenue=revenue,
            countries_available=len(countries),
            last_sync=None  # Could be tracked in a settings table
        )

    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )
