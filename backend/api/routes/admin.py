"""
Admin API routes for dashboard statistics, user management, coupons, and proxy inventory.
All endpoints require admin authentication (is_admin=True).
"""

import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_async_session
from backend.models.user import User
from backend.models.proxy_inventory import ProxyInventory
from backend.models.coupon import Coupon
from backend.schemas.admin import (
    DashboardStatsResponse,
    RevenueChartData,
    AdminUserListResponse,
    AdminUserListItem,
    UpdateUserRequest,
    UserFilters,
    AdminCouponListResponse,
    AdminCouponListItem,
    CreateCouponRequest,
    UpdateCouponRequest,
    CouponFilters,
    AdminProxyListResponse,
    ProxyInventoryItem,
    CreateProxyRequest,
    BulkCreateProxiesRequest,
    UpdateProxyAvailabilityRequest,
    ProxyInventoryFilters,
    BulkCreatePptpRequest,
    BulkCreatePptpResponse,
    PptpProductItem,
    PptpProxyListResponse,
    BulkDeletePptpRequest,
    BulkDeletePptpResponse,
    CatalogItem,
    CatalogListResponse,
    UpdateCatalogRequest
)
from backend.services.admin_service import AdminService
from backend.services.proxy_inventory_service import ProxyInventoryService
from backend.services.broadcast_service import BroadcastService
from backend.api.dependencies import get_current_admin_user

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["Admin"])


# Statistics endpoints

@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get dashboard statistics",
    description="Get comprehensive statistics for admin dashboard including users, revenue, purchases, deposits"
)
async def get_dashboard_stats(
    period: str = Query('all_time', description="Period: 1d, 7d, 30d, all_time"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> DashboardStatsResponse:
    """
    Get comprehensive dashboard statistics.
    
    Returns:
        - Total users, revenue, purchases, deposits, active proxies
        - Period-specific statistics (1d, 7d, 30d, all_time)
        - Refunds count and amount
        
    Requires: Admin authentication
    """
    try:
        stats = await AdminService.get_dashboard_stats(session, period)
        return DashboardStatsResponse(**stats)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard statistics"
        )


@router.get(
    "/revenue-chart",
    response_model=List[RevenueChartData],
    summary="Get revenue chart data",
    description="Get revenue and purchases data for charts with time series aggregation"
)
async def get_revenue_chart(
    period: str = Query('30d', description="Period: 7d, 30d, all_time"),
    granularity: str = Query('day', description="Granularity: day, week, month"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> List[RevenueChartData]:
    """
    Get revenue chart data grouped by time period.
    
    Args:
        period: Time period to analyze
        granularity: Grouping granularity (day/week/month)
        
    Returns:
        List of data points with date, revenue, purchases, deposits, socks5_count, pptp_count
        
    Requires: Admin authentication
    """
    try:
        chart_data = await AdminService.get_revenue_chart_data(session, period, granularity)
        return [RevenueChartData(**item) for item in chart_data]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revenue chart data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get revenue chart data"
        )


@router.get(
    "/activity-log",
    response_model=List[Dict[str, Any]],
    summary="Get recent activity log",
    description="Get recent user activities across all users for admin dashboard"
)
async def get_activity_log(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of activities to return"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """
    Get recent activity log for admin dashboard.

    Returns list of recent user activities including:
    - Deposits
    - Proxy purchases (SOCKS5 and PPTP)
    - Refunds
    - Other significant actions

    Requires: Admin authentication
    """
    try:
        activities = await AdminService.get_recent_activity(session, limit)
        return activities

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity log"
        )


# User management endpoints

@router.get(
    "/users",
    response_model=AdminUserListResponse,
    summary="Get users list",
    description="Get paginated users list with filters and aggregated statistics"
)
async def get_users_list(
    search: Optional[str] = Query(None, description="Search by username, access_code, telegram_id"),
    platform: Optional[str] = Query(None, description="Filter by platform (telegram/web)"),
    date_from: Optional[datetime] = Query(None, description="Registration date from"),
    date_to: Optional[datetime] = Query(None, description="Registration date to"),
    min_balance: Optional[Decimal] = Query(None, description="Minimum balance"),
    max_balance: Optional[Decimal] = Query(None, description="Maximum balance"),
    is_blocked: Optional[bool] = Query(None, description="Filter by blocked status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> AdminUserListResponse:
    """
    Get paginated users list with filters and statistics.
    
    Each user includes:
        - Basic profile info
        - Total spent, deposited, purchases count
        - Last activity, blocked status
        - Referrals count
        
    Requires: Admin authentication
    """
    try:
        # Build filters dict
        filters = {}
        if search:
            filters['search'] = search
        if platform:
            filters['platform'] = platform
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        if min_balance is not None:
            filters['min_balance'] = min_balance
        if max_balance is not None:
            filters['max_balance'] = max_balance
        if is_blocked is not None:
            filters['is_blocked'] = is_blocked

        users, total = await AdminService.get_users_list(session, filters, page, page_size)
        
        return AdminUserListResponse(
            users=[AdminUserListItem(**user) for user in users],
            total=total,
            page=page,
            page_size=page_size
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting users list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users list"
        )


@router.get(
    "/users/{user_id}",
    summary="Get user details",
    description="Get detailed information about specific user including all purchases, transactions, logs, referrals"
)
async def get_user_details(
    user_id: int = Path(..., description="User ID"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get comprehensive user details.
    
    Returns:
        - User profile
        - Statistics (total_spent, total_deposited, purchases_count, referrals_count)
        - Purchase history (proxy + pptp)
        - Payment history (transactions)
        - Action logs
        - Referrals list
        
    Requires: Admin authentication
    """
    try:
        user_details = await AdminService.get_user_details(session, user_id)
        return user_details
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user details for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user details"
        )


@router.patch(
    "/users/{user_id}",
    summary="Update user",
    description="Update user data (balance, blocked status, language). All actions are logged."
)
async def update_user(
    user_id: int = Path(..., description="User ID"),
    updates: UpdateUserRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Update user data (admin only).
    
    Supported updates:
        - balance: Set new balance (must be >= 0)
        - is_blocked: Block/unblock user (requires blocked_reason if blocking)
        - blocked_reason: Reason for blocking
        - language: Change interface language
        
    All admin actions are logged for audit trail.
    
    Requires: Admin authentication
    """
    try:
        updated_user = await AdminService.update_user(
            session,
            user_id,
            current_user.user_id,
            updates.model_dump(exclude_unset=True)
        )
        
        return {
            "success": True,
            "message": "User updated successfully",
            "user": {
                "user_id": updated_user.user_id,
                "access_code": updated_user.access_code,
                "balance": updated_user.balance,
                "is_blocked": updated_user.is_blocked,
                "blocked_at": updated_user.blocked_at,
                "language": updated_user.language
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.get(
    "/top-users",
    summary="Get top users",
    description="Get top users by specified metric (revenue, purchases, deposits, referrals)"
)
async def get_top_users(
    metric: str = Query('revenue', description="Metric: revenue, purchases, deposits, referrals"),
    limit: int = Query(10, ge=1, le=50, description="Number of users to return"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """
    Get top users by specified metric.
    
    Metrics:
        - revenue: Total spent on purchases
        - purchases: Number of purchases
        - deposits: Total deposited amount
        - referrals: Number of referrals
        
    Requires: Admin authentication
    """
    try:
        top_users = await AdminService.get_top_users(session, metric, limit)
        return top_users
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top users by {metric}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get top users"
        )


# Coupon management endpoints

@router.get(
    "/coupons",
    response_model=AdminCouponListResponse,
    summary="Get coupons list",
    description="Get paginated coupons list with filters"
)
async def get_coupons_list(
    search: Optional[str] = Query(None, description="Search by coupon code"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    date_from: Optional[datetime] = Query(None, description="Created date from"),
    date_to: Optional[datetime] = Query(None, description="Created date to"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> AdminCouponListResponse:
    """
    Get paginated coupons list with filters.
    
    Returns coupons with:
        - Code, discount percentage, max uses, used count
        - Active status, creation/expiration dates
        
    Requires: Admin authentication
    """
    try:
        # Build filters dict
        filters = {}
        if search:
            filters['search'] = search
        if is_active is not None:
            filters['is_active'] = is_active
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to

        coupons, total = await AdminService.get_coupons_list(session, filters, page, page_size)
        
        return AdminCouponListResponse(
            coupons=[AdminCouponListItem(**coupon) for coupon in coupons],
            total=total,
            page=page,
            page_size=page_size
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coupons list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get coupons list"
        )


@router.post(
    "/coupons",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create coupon",
    description="Create new discount coupon"
)
async def create_coupon(
    coupon: CreateCouponRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Create new discount coupon.
    
    Fields:
        - code: Unique coupon code
        - discount_percent: Discount percentage (0-100)
        - max_uses: Maximum number of uses
        - expires_at: Optional expiration date
        - is_active: Active status (default: true)
        
    Requires: Admin authentication
    """
    try:
        created_coupon = await AdminService.create_coupon(
            session,
            current_user.user_id,
            coupon.model_dump()
        )
        
        return {
            "success": True,
            "message": f"Coupon '{created_coupon.coupon}' created successfully",
            "coupon": {
                "id": created_coupon.id_cupon,
                "code": created_coupon.coupon,
                "discount_percent": created_coupon.discount_percentage,
                "max_uses": created_coupon.max_usage,
                "is_active": created_coupon.is_active,
                "expires_at": created_coupon.expires_at
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating coupon: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create coupon"
        )


@router.patch(
    "/coupons/{coupon_id}",
    summary="Update coupon",
    description="Update existing coupon"
)
async def update_coupon(
    coupon_id: int = Path(..., description="Coupon ID"),
    updates: UpdateCouponRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Update existing coupon.
    
    Updatable fields:
        - discount_percent
        - max_uses
        - is_active
        - expires_at
        
    Requires: Admin authentication
    """
    try:
        updated_coupon = await AdminService.update_coupon(
            session,
            current_user.user_id,
            coupon_id,
            updates.model_dump(exclude_unset=True)
        )
        
        return {
            "success": True,
            "message": "Coupon updated successfully",
            "coupon": {
                "id": updated_coupon.id_cupon,
                "code": updated_coupon.coupon,
                "discount_percent": updated_coupon.discount_percentage,
                "max_uses": updated_coupon.max_usage,
                "is_active": updated_coupon.is_active
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating coupon {coupon_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update coupon"
        )


@router.delete(
    "/coupons/{coupon_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete coupon",
    description="Delete coupon (soft delete: set is_active=false)"
)
async def delete_coupon(
    coupon_id: int = Path(..., description="Coupon ID"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete coupon (soft delete).
    
    Sets is_active=false instead of actually deleting.
    
    Requires: Admin authentication
    """
    try:
        await AdminService.delete_coupon(session, current_user.user_id, coupon_id)
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting coupon {coupon_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete coupon"
        )


@router.get(
    "/coupons/stats",
    summary="Get coupon statistics",
    description="Get coupon statistics (total, active, used, expired)"
)
async def get_coupon_stats(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get coupon statistics.
    
    Returns:
        - total_created: Total coupons created
        - active_coupons: Currently active coupons
        - total_used: Total usage count
        - expired_coupons: Expired coupons count
        
    Requires: Admin authentication
    """
    try:
        stats = await AdminService.get_coupon_stats(session)
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coupon stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get coupon statistics"
        )


# Proxy inventory management endpoints

@router.get(
    "/proxies",
    response_model=AdminProxyListResponse,
    summary="Get proxies list",
    description="Get paginated proxy inventory list with filters"
)
async def get_proxies_list(
    country: Optional[str] = Query(None, description="Filter by country"),
    state: Optional[str] = Query(None, description="Filter by state"),
    city: Optional[str] = Query(None, description="Filter by city"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    search: Optional[str] = Query(None, description="Search by IP or city"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> AdminProxyListResponse:
    """
    Get paginated proxy inventory list with filters.
    
    Returns proxies with:
        - IP, port, location (country/state/city)
        - Availability status, price per hour
        - Creation date, notes
        
    Requires: Admin authentication
    """
    try:
        # Build filters dict
        filters = {}
        if country:
            filters['country'] = country
        if state:
            filters['state'] = state
        if city:
            filters['city'] = city
        if is_available is not None:
            filters['is_available'] = is_available
        if search:
            filters['search'] = search

        proxies, total = await ProxyInventoryService.get_proxies(session, filters, page, page_size)
        
        return AdminProxyListResponse(
            proxies=[ProxyInventoryItem.model_validate(proxy) for proxy in proxies],
            total=total,
            page=page,
            page_size=page_size
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting proxies list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get proxies list"
        )


@router.post(
    "/proxies",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create proxy",
    description="Add single proxy to inventory"
)
async def create_proxy(
    proxy: CreateProxyRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Add single proxy to inventory.
    
    Fields:
        - ip: IP address (IPv4 or IPv6)
        - port: Port (1-65535)
        - country, state, city: Location
        - price_per_hour: Price in USD
        - notes: Optional notes
        
    Requires: Admin authentication
    """
    try:
        created_proxy = await ProxyInventoryService.create_proxy(
            session,
            proxy.model_dump()
        )
        
        return {
            "success": True,
            "message": f"Proxy {created_proxy.ip}:{created_proxy.port} created successfully",
            "proxy": ProxyInventoryItem.model_validate(created_proxy)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating proxy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create proxy"
        )


@router.post(
    "/proxies/bulk",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create proxies",
    description="Add multiple proxies to inventory at once"
)
async def bulk_create_proxies(
    bulk_request: BulkCreateProxiesRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Bulk create proxies.
    
    Provide array of proxy objects in request body.
    Returns list of created proxies.
    
    Requires: Admin authentication
    """
    try:
        proxies_data = [p.model_dump() for p in bulk_request.proxies]
        created_proxies = await ProxyInventoryService.bulk_create_proxies(
            session,
            proxies_data
        )
        
        return {
            "success": True,
            "message": f"{len(created_proxies)} proxies created successfully",
            "proxies": [ProxyInventoryItem.model_validate(p) for p in created_proxies]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk creating proxies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create proxies"
        )


@router.patch(
    "/proxies/{proxy_id}",
    summary="Update proxy",
    description="Update proxy availability and price"
)
async def update_proxy(
    proxy_id: int = Path(..., description="Proxy ID"),
    updates: UpdateProxyAvailabilityRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Update proxy availability and price.
    
    Updatable fields:
        - is_available: Availability status
        - price_per_hour: Price per hour in USD
        - notes: Additional notes
        
    Requires: Admin authentication
    """
    try:
        updated_proxy = await ProxyInventoryService.update_proxy(
            session,
            proxy_id,
            updates.model_dump(exclude_unset=True)
        )
        
        return {
            "success": True,
            "message": "Proxy updated successfully",
            "proxy": ProxyInventoryItem.model_validate(updated_proxy)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating proxy {proxy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update proxy"
        )


@router.delete(
    "/proxies/{proxy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete proxy",
    description="Delete proxy from inventory"
)
async def delete_proxy(
    proxy_id: int = Path(..., description="Proxy ID"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete proxy from inventory.
    
    Permanently removes proxy from database.
    
    Requires: Admin authentication
    """
    try:
        await ProxyInventoryService.delete_proxy(session, proxy_id)
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting proxy {proxy_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete proxy"
        )


@router.get(
    "/proxies/stats",
    summary="Get proxy statistics",
    description="Get proxy inventory statistics"
)
async def get_proxy_stats(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get proxy inventory statistics.
    
    Returns:
        - total_proxies: Total proxies in inventory
        - available_proxies: Currently available proxies
        - by_country: Proxies count by country
        - avg_price: Average price per hour
        
    Requires: Admin authentication
    """
    try:
        stats = await ProxyInventoryService.get_proxy_stats(session)
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting proxy stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get proxy statistics"
        )


# PPTP bulk upload endpoint

@router.post(
    "/pptp/bulk",
    response_model=BulkCreatePptpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create PPTP proxies",
    description="""
    Upload multiple PPTP proxies at once using line or CSV format.

    **Line format:**
    STATE_IP_LOGIN_PASSWORD_CITY_ZIP (separated by underscores, multiple entries separated by spaces/newlines)

    Example:
    ```
    TX_104.11.157.41_user1_pass123_Houston_77001 NY_100.12.0.17_admin_secret_NewYork_10001
    ```

    **CSV format:**
    state,ip,login,password,city,zip (with header row)

    Example:
    ```
    state,ip,login,password,city,zip
    TX,104.11.157.41,user1,pass123,Houston,77001
    NY,100.12.0.17,admin,secret,NewYork,10001
    ```

    **Format auto-detection:**
    The system will auto-detect the format if not specified. The detection logic:
    - If CSV header is present (state,ip,login or ip,login,password), format is CSV
    - If commas are present in data, format is CSV
    - Otherwise, format is line

    **Recommendation:**
    For ambiguous input or when in doubt, explicitly specify the `format` parameter ('line' or 'csv')
    to ensure correct parsing and avoid potential misinterpretation of the data format.
    """
)
async def bulk_create_pptp(
    bulk_request: BulkCreatePptpRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> BulkCreatePptpResponse:
    """
    Bulk create PPTP proxies from line or CSV format.

    Args:
        bulk_request: Request with proxy data and optional format
        current_user: Admin user performing the action
        session: Database session

    Returns:
        Response with created products, counts, and any errors

    Requires: Admin authentication
    """
    try:
        result = await AdminService.bulk_create_pptp_products(
            session=session,
            admin_user_id=current_user.user_id,
            data=bulk_request.data,
            format=bulk_request.format,
            catalog_id=bulk_request.catalog_id,
            catalog_name=bulk_request.catalog_name,
            catalog_price=bulk_request.catalog_price
        )

        # Determine success status and message
        created_count = result['created_count']
        failed_count = result['failed_count']

        if created_count > 0 and failed_count == 0:
            success = True
            message = f"Successfully created {created_count} PPTP proxies"
        elif created_count > 0 and failed_count > 0:
            success = True
            message = f"Created {created_count} PPTP proxies with {failed_count} errors"
        else:
            success = False
            message = f"Failed to create proxies: {failed_count} errors"

        return BulkCreatePptpResponse(
            success=success,
            message=message,
            created_count=created_count,
            failed_count=failed_count,
            products=[PptpProductItem(**p) for p in result['products']],
            errors=result['errors']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk PPTP upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create PPTP proxies: {str(e)}"
        )


@router.get(
    "/pptp",
    response_model=PptpProxyListResponse,
    summary="Get PPTP proxies list",
    description="Get paginated list of all PPTP proxies with optional filters"
)
async def get_pptp_proxies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=5000, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by IP, country, state, or city"),
    catalog_id: Optional[int] = Query(None, description="Filter by catalog ID"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> PptpProxyListResponse:
    """
    Get paginated list of PPTP proxies.

    Returns:
        - List of PPTP proxies with IP, login, password, location
        - Total count and pagination info

    Requires: Admin authentication
    """
    try:
        proxies, total = await AdminService.get_pptp_proxies(
            session,
            page=page,
            page_size=page_size,
            search=search,
            catalog_id=catalog_id
        )

        return PptpProxyListResponse(
            proxies=proxies,
            total=total,
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PPTP proxies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get PPTP proxies"
        )


@router.delete(
    "/pptp/{product_id}",
    response_model=Dict[str, Any],
    summary="Delete single PPTP proxy",
    description="Delete one PPTP proxy by product ID"
)
async def delete_pptp_proxy(
    product_id: int = Path(..., description="Product ID to delete"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Delete single PPTP proxy.

    Args:
        product_id: Product ID to delete

    Returns:
        Success message

    Requires: Admin authentication
    """
    try:
        await AdminService.delete_pptp_proxy(session, product_id)

        return {
            "success": True,
            "message": f"PPTP proxy {product_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting PPTP proxy {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete PPTP proxy: {str(e)}"
        )


@router.post(
    "/pptp/bulk-delete",
    response_model=BulkDeletePptpResponse,
    summary="Bulk delete PPTP proxies",
    description="Delete multiple PPTP proxies at once"
)
async def bulk_delete_pptp(
    request: BulkDeletePptpRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> BulkDeletePptpResponse:
    """
    Bulk delete PPTP proxies.

    Args:
        request: List of product IDs to delete

    Returns:
        Statistics about deletion operation

    Requires: Admin authentication
    """
    try:
        result = await AdminService.bulk_delete_pptp_proxies(
            session,
            product_ids=request.product_ids,
            admin_user_id=current_user.user_id
        )

        deleted_count = result['deleted_count']
        failed_count = result['failed_count']
        errors = result['errors']

        if deleted_count > 0 and failed_count == 0:
            message = f"Successfully deleted {deleted_count} PPTP proxies"
        elif deleted_count > 0 and failed_count > 0:
            message = f"Deleted {deleted_count} PPTP proxies with {failed_count} errors"
        else:
            message = f"Failed to delete proxies: {failed_count} errors"

        return BulkDeletePptpResponse(
            success=(deleted_count > 0),
            message=message,
            deleted_count=deleted_count,
            failed_count=failed_count,
            errors=errors
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk PPTP delete: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk delete PPTP proxies: {str(e)}"
        )


@router.get(
    "/catalogs",
    response_model=CatalogListResponse,
    summary="Get catalogs list",
    description="Get list of available catalogs for proxy type (PPTP or SOCKS5)"
)
async def get_catalogs(
    proxy_type: str = Query("PPTP", description="Proxy type (PPTP or SOCKS5)"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> CatalogListResponse:
    """
    Get list of catalogs for dropdown selection.

    Args:
        proxy_type: Proxy type to filter catalogs (PPTP or SOCKS5)

    Returns:
        List of catalogs with id, name, price

    Requires: Admin authentication
    """
    try:
        from backend.models.catalog import Catalog
        from sqlalchemy import select, func

        # Query catalogs by proxy type
        query = select(Catalog).where(Catalog.pre_lines_name == proxy_type).order_by(Catalog.line_name)
        result = await session.execute(query)
        catalogs = result.scalars().all()

        # Get total count
        count_query = select(func.count()).select_from(Catalog).where(Catalog.pre_lines_name == proxy_type)
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Format response
        catalog_items = [
            CatalogItem(
                id=cat.id,
                name=cat.line_name,
                price=cat.price,
                ig_catalog=cat.ig_catalog,
                proxy_type=cat.pre_lines_name
            )
            for cat in catalogs
        ]

        return CatalogListResponse(
            catalogs=catalog_items,
            total=total or 0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting catalogs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get catalogs"
        )


@router.patch(
    "/catalogs/{catalog_id}",
    summary="Update catalog",
    description="Update catalog name, price, or description"
)
async def update_catalog(
    catalog_id: int = Path(..., description="Catalog ID"),
    updates: UpdateCatalogRequest = Body(...),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Update catalog details.

    Updatable fields:
        - line_name: Catalog display name
        - price: Price in USD
        - description_ru: Russian description
        - description_eng: English description

    Requires: Admin authentication
    """
    try:
        from backend.models.catalog import Catalog
        from sqlalchemy import select

        # Get catalog
        result = await session.execute(
            select(Catalog).where(Catalog.id == catalog_id)
        )
        catalog = result.scalar_one_or_none()

        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog not found"
            )

        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(catalog, field):
                setattr(catalog, field, value)

        await session.commit()
        await session.refresh(catalog)

        logger.info(f"Admin {current_user.user_id} updated catalog {catalog_id}: {update_data}")

        return {
            "success": True,
            "message": "Catalog updated successfully",
            "catalog": {
                "id": catalog.id,
                "name": catalog.line_name,
                "price": catalog.price,
                "description_ru": catalog.description_ru,
                "description_eng": catalog.description_eng,
                "proxy_type": catalog.pre_lines_name
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating catalog {catalog_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update catalog"
        )


@router.delete(
    "/catalogs/{catalog_id}",
    summary="Delete catalog",
    description="Delete catalog and all its proxies (cascade delete)"
)
async def delete_catalog(
    catalog_id: int = Path(..., description="Catalog ID"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Delete a catalog and all its associated proxies.

    The cascade delete is configured in the database model,
    so all products belonging to this catalog will be automatically deleted.

    Requires: Admin authentication
    """
    try:
        from backend.models.catalog import Catalog
        from sqlalchemy import select

        # Get catalog
        result = await session.execute(
            select(Catalog).where(Catalog.id == catalog_id)
        )
        catalog = result.scalar_one_or_none()

        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Catalog not found"
            )

        catalog_name = catalog.line_name
        proxy_type = catalog.pre_lines_name

        # Delete catalog (cascade will delete all products)
        await session.delete(catalog)
        await session.commit()

        logger.info(f"Admin {current_user.user_id} deleted catalog {catalog_id} ({catalog_name})")

        return {
            "success": True,
            "message": f"Catalog '{catalog_name}' and all its proxies deleted successfully",
            "deleted_catalog": {
                "id": catalog_id,
                "name": catalog_name,
                "proxy_type": proxy_type
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting catalog {catalog_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete catalog"
        )


# Broadcast management endpoints

@router.post(
    "/broadcast",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Create and start broadcast",
    description="Create a new broadcast message and start sending to users"
)
async def create_broadcast(
    message_text: str = Body(..., embed=True, description="Message text (HTML supported)"),
    message_photo: Optional[str] = Body(None, embed=True, description="Photo URL or file_id"),
    filter_language: Optional[str] = Body(None, embed=True, description="Filter by language (ru/en)"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Create and start a broadcast message.

    The broadcast will be sent to all active users (or filtered by language).
    Messages are sent with rate limiting (~25 msg/sec) to avoid Telegram flood control.

    Args:
        message_text: Message text with HTML formatting support
        message_photo: Optional photo URL or Telegram file_id
        filter_language: Optional language filter (ru or en)

    Returns:
        Broadcast ID and initial status

    Requires: Admin authentication
    """
    import asyncio

    try:
        broadcast_service = BroadcastService(session)

        # Create broadcast record
        broadcast = await broadcast_service.create_broadcast(
            message_text=message_text,
            created_by=current_user.user_id,
            filter_language=filter_language,
            message_photo=message_photo
        )

        logger.info(f"Admin {current_user.user_id} created broadcast {broadcast.id} for {broadcast.total_users} users")

        # Start sending in background
        asyncio.create_task(broadcast_service.send_broadcast(broadcast.id))

        return {
            "success": True,
            "message": f"Broadcast created and started. Sending to {broadcast.total_users} users.",
            "broadcast": {
                "id": broadcast.id,
                "status": broadcast.status,
                "total_users": broadcast.total_users,
                "filter_language": broadcast.filter_language,
                "created_at": broadcast.created_at.isoformat() if broadcast.created_at else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating broadcast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create broadcast: {str(e)}"
        )


@router.get(
    "/broadcast",
    response_model=Dict[str, Any],
    summary="Get broadcasts list",
    description="Get list of all broadcasts with pagination"
)
async def get_broadcasts(
    limit: int = Query(20, ge=1, le=100, description="Number of broadcasts to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get list of all broadcasts with pagination.

    Returns:
        List of broadcasts with status, counts, and timestamps

    Requires: Admin authentication
    """
    try:
        broadcast_service = BroadcastService(session)
        broadcasts = await broadcast_service.get_broadcasts_list(limit=limit, offset=offset)

        return {
            "success": True,
            "broadcasts": broadcasts,
            "limit": limit,
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting broadcasts list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get broadcasts list"
        )


@router.get(
    "/broadcast/{broadcast_id}",
    response_model=Dict[str, Any],
    summary="Get broadcast status",
    description="Get current status and progress of a broadcast"
)
async def get_broadcast_status(
    broadcast_id: int = Path(..., description="Broadcast ID"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get current status and progress of a broadcast.

    Returns:
        - Status (pending, running, completed, cancelled)
        - Total users, sent count, failed count
        - Progress percentage
        - Timestamps

    Requires: Admin authentication
    """
    try:
        broadcast_service = BroadcastService(session)
        broadcast_status = await broadcast_service.get_broadcast_status(broadcast_id)

        if not broadcast_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broadcast not found"
            )

        return {
            "success": True,
            "broadcast": broadcast_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting broadcast status for {broadcast_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get broadcast status"
        )


@router.post(
    "/broadcast/{broadcast_id}/cancel",
    response_model=Dict[str, Any],
    summary="Cancel broadcast",
    description="Cancel a running or pending broadcast"
)
async def cancel_broadcast(
    broadcast_id: int = Path(..., description="Broadcast ID"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Cancel a running or pending broadcast.

    The broadcast will stop sending messages and be marked as cancelled.

    Requires: Admin authentication
    """
    try:
        broadcast_service = BroadcastService(session)
        cancelled = await broadcast_service.cancel_broadcast(broadcast_id)

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Broadcast cannot be cancelled (not found or already completed)"
            )

        logger.info(f"Admin {current_user.user_id} cancelled broadcast {broadcast_id}")

        return {
            "success": True,
            "message": f"Broadcast {broadcast_id} cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling broadcast {broadcast_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel broadcast"
        )


@router.post(
    "/broadcast/test",
    response_model=Dict[str, Any],
    summary="Send test message",
    description="Send a test broadcast message to your own Telegram"
)
async def send_test_broadcast(
    message_text: str = Body(..., embed=True, description="Message text (HTML supported)"),
    message_photo: Optional[str] = Body(None, embed=True, description="Photo URL or file_id"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Send a test broadcast message to your own Telegram account.

    Use this to preview how the message will look before sending to all users.

    Args:
        message_text: Message text with HTML formatting support
        message_photo: Optional photo URL or Telegram file_id

    Returns:
        Success status

    Requires: Admin authentication with linked Telegram account
    """
    try:
        # Get admin's telegram_id
        if not current_user.telegram_id or len(current_user.telegram_id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your account has no linked Telegram ID. Please link your Telegram first."
            )

        admin_telegram_id = current_user.telegram_id[0]  # First telegram_id

        broadcast_service = BroadcastService(session)
        success = await broadcast_service.send_test_message(
            telegram_id=admin_telegram_id,
            message_text=message_text,
            message_photo=message_photo
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test message. Check your Telegram bot settings."
            )

        logger.info(f"Admin {current_user.user_id} sent test broadcast to {admin_telegram_id}")

        return {
            "success": True,
            "message": f"Test message sent to your Telegram ({admin_telegram_id})"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test broadcast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test message: {str(e)}"
        )

