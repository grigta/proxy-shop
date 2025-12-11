"""
Admin service for dashboard statistics, user management, and reporting.
Provides business logic for admin panel operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, cast, String, desc
from backend.models.user import User, PlatformType
from backend.models.proxy_history import ProxyHistory
from backend.models.pptp_history import PptpHistory
from backend.models.user_transaction import UserTransaction
from backend.models.user_log import UserLog
from backend.models.coupon import Coupon
from backend.models.catalog import Catalog
from backend.models.product import Product
from backend.services.log_service import LogService
from fastapi import HTTPException
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
import logging
import csv
import io
import re
from ipaddress import ip_address

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin panel operations including statistics and user management."""

    @staticmethod
    async def get_dashboard_stats(
        session: AsyncSession, 
        period: str = 'all_time'
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics for admin panel.
        
        Args:
            session: Database session
            period: Time period ('1d', '7d', '30d', 'all_time')
            
        Returns:
            Dictionary with total statistics and period-specific stats
            
        Example:
            {
                "total_users": 1500,
                "total_revenue": Decimal("125000.50"),
                "total_purchases": 3500,
                "total_deposits": Decimal("150000.00"),
                "active_proxies": 450,
                "refunded_count": 50,
                "period_stats": {
                    "1d": {...},
                    "7d": {...},
                    "30d": {...},
                    "all_time": {...}
                }
            }
        """
        try:
            # Total users count
            result = await session.execute(select(func.count(User.user_id)))
            total_users = result.scalar() or 0

            # Total revenue (proxy + pptp, not refunded)
            proxy_revenue = await session.execute(
                select(func.coalesce(func.sum(ProxyHistory.price), Decimal('0')))
                .where(ProxyHistory.isRefunded == False)
            )
            pptp_revenue = await session.execute(
                select(func.coalesce(func.sum(PptpHistory.price), Decimal('0')))
                .where(PptpHistory.isRefunded == False)
            )
            total_revenue = (proxy_revenue.scalar() or Decimal('0')) + (pptp_revenue.scalar() or Decimal('0'))

            # Total purchases count
            proxy_count = await session.execute(
                select(func.count(ProxyHistory.id))
            )
            pptp_count = await session.execute(
                select(func.count(PptpHistory.id))
            )
            total_purchases = (proxy_count.scalar() or 0) + (pptp_count.scalar() or 0)

            # Total deposits
            deposits_result = await session.execute(
                select(func.coalesce(func.sum(UserTransaction.amount_in_dollar), Decimal('0')))
            )
            total_deposits = deposits_result.scalar() or Decimal('0')

            # Active proxies (not expired, not refunded)
            now = datetime.utcnow()
            active_proxy = await session.execute(
                select(func.count(ProxyHistory.id))
                .where(and_(
                    ProxyHistory.expires_at > now,
                    ProxyHistory.isRefunded == False
                ))
            )
            active_pptp = await session.execute(
                select(func.count(PptpHistory.id))
                .where(and_(
                    PptpHistory.expires_at > now,
                    PptpHistory.isRefunded == False
                ))
            )
            active_proxies = (active_proxy.scalar() or 0) + (active_pptp.scalar() or 0)

            # Refunded count
            refunded_proxy = await session.execute(
                select(func.count(ProxyHistory.id))
                .where(ProxyHistory.isRefunded == True)
            )
            refunded_pptp = await session.execute(
                select(func.count(PptpHistory.id))
                .where(PptpHistory.isRefunded == True)
            )
            refunded_count = (refunded_proxy.scalar() or 0) + (refunded_pptp.scalar() or 0)

            # Calculate period-specific statistics
            periods = ['1d', '7d', '30d', 'all_time']
            period_stats = {}
            
            for p in periods:
                period_stats[p] = await AdminService._get_period_stats(session, p)

            return {
                "total_users": total_users,
                "total_revenue": total_revenue,
                "total_purchases": total_purchases,
                "total_deposits": total_deposits,
                "active_proxies": active_proxies,
                "refunded_count": refunded_count,
                "period_stats": period_stats
            }

        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to get dashboard statistics")

    @staticmethod
    async def _get_period_stats(
        session: AsyncSession,
        period: str
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific period with percentage changes.

        Args:
            session: Database session
            period: Period ('1d', '7d', '30d', 'all_time')

        Returns:
            Dictionary with period statistics and percentage changes
        """
        try:
            # Determine date filter
            date_filter = None
            prev_date_filter = None
            now = datetime.utcnow()

            if period == '1d':
                date_filter = now - timedelta(days=1)
                prev_date_filter = now - timedelta(days=2)
            elif period == '7d':
                date_filter = now - timedelta(days=7)
                prev_date_filter = now - timedelta(days=14)
            elif period == '30d':
                date_filter = now - timedelta(days=30)
                prev_date_filter = now - timedelta(days=60)
            # 'all_time' - no filter, no percentage calculation

            # Revenue for period (separated by type)
            proxy_revenue_query = select(func.coalesce(func.sum(ProxyHistory.price), Decimal('0')))
            pptp_revenue_query = select(func.coalesce(func.sum(PptpHistory.price), Decimal('0')))

            if date_filter:
                proxy_revenue_query = proxy_revenue_query.where(and_(
                    ProxyHistory.datestamp >= date_filter,
                    ProxyHistory.isRefunded == False
                ))
                pptp_revenue_query = pptp_revenue_query.where(and_(
                    PptpHistory.datestamp >= date_filter,
                    PptpHistory.isRefunded == False
                ))
            else:
                proxy_revenue_query = proxy_revenue_query.where(ProxyHistory.isRefunded == False)
                pptp_revenue_query = pptp_revenue_query.where(PptpHistory.isRefunded == False)

            proxy_rev = await session.execute(proxy_revenue_query)
            pptp_rev = await session.execute(pptp_revenue_query)
            proxy_revenue = proxy_rev.scalar() or Decimal('0')
            pptp_revenue = pptp_rev.scalar() or Decimal('0')
            revenue = proxy_revenue + pptp_revenue

            # Purchases count for period
            proxy_count_query = select(func.count(ProxyHistory.id))
            pptp_count_query = select(func.count(PptpHistory.id))
            
            if date_filter:
                proxy_count_query = proxy_count_query.where(ProxyHistory.datestamp >= date_filter)
                pptp_count_query = pptp_count_query.where(PptpHistory.datestamp >= date_filter)

            proxy_cnt = await session.execute(proxy_count_query)
            pptp_cnt = await session.execute(pptp_count_query)
            purchases = (proxy_cnt.scalar() or 0) + (pptp_cnt.scalar() or 0)

            # Deposits for period
            deposits_query = select(func.coalesce(func.sum(UserTransaction.amount_in_dollar), Decimal('0')))
            if date_filter:
                deposits_query = deposits_query.where(UserTransaction.dateOfTransaction >= date_filter)

            dep_result = await session.execute(deposits_query)
            deposits = dep_result.scalar() or Decimal('0')

            # Deposits count for period
            deposits_count_query = select(func.count(UserTransaction.id_tranz))
            if date_filter:
                deposits_count_query = deposits_count_query.where(UserTransaction.dateOfTransaction >= date_filter)

            deposits_count_result = await session.execute(deposits_count_query)
            deposits_count = deposits_count_result.scalar() or 0

            # New users for period
            users_query = select(func.count(User.user_id))
            if date_filter:
                users_query = users_query.where(User.datestamp >= date_filter)

            users_result = await session.execute(users_query)
            new_users = users_result.scalar() or 0

            # Refunds for period
            refunds_proxy_query = select(func.count(ProxyHistory.id))
            refunds_pptp_query = select(func.count(PptpHistory.id))
            refunds_amount_proxy_query = select(func.coalesce(func.sum(ProxyHistory.price), Decimal('0')))
            refunds_amount_pptp_query = select(func.coalesce(func.sum(PptpHistory.price), Decimal('0')))
            
            if date_filter:
                refunds_proxy_query = refunds_proxy_query.where(and_(
                    ProxyHistory.isRefunded == True,
                    ProxyHistory.datestamp >= date_filter
                ))
                refunds_pptp_query = refunds_pptp_query.where(and_(
                    PptpHistory.isRefunded == True,
                    PptpHistory.datestamp >= date_filter
                ))
                refunds_amount_proxy_query = refunds_amount_proxy_query.where(and_(
                    ProxyHistory.isRefunded == True,
                    ProxyHistory.datestamp >= date_filter
                ))
                refunds_amount_pptp_query = refunds_amount_pptp_query.where(and_(
                    PptpHistory.isRefunded == True,
                    PptpHistory.datestamp >= date_filter
                ))
            else:
                refunds_proxy_query = refunds_proxy_query.where(ProxyHistory.isRefunded == True)
                refunds_pptp_query = refunds_pptp_query.where(PptpHistory.isRefunded == True)
                refunds_amount_proxy_query = refunds_amount_proxy_query.where(ProxyHistory.isRefunded == True)
                refunds_amount_pptp_query = refunds_amount_pptp_query.where(PptpHistory.isRefunded == True)

            ref_proxy = await session.execute(refunds_proxy_query)
            ref_pptp = await session.execute(refunds_pptp_query)
            refunds = (ref_proxy.scalar() or 0) + (ref_pptp.scalar() or 0)

            ref_amt_proxy = await session.execute(refunds_amount_proxy_query)
            ref_amt_pptp = await session.execute(refunds_amount_pptp_query)
            refunds_amount = (ref_amt_proxy.scalar() or Decimal('0')) + (ref_amt_pptp.scalar() or Decimal('0'))

            # Calculate net profit
            net_profit = revenue - refunds_amount

            # Calculate percentage changes if previous period exists
            percentages = {}
            if prev_date_filter and date_filter:
                # Get previous period stats
                prev_proxy_rev_query = select(func.coalesce(func.sum(ProxyHistory.price), Decimal('0'))).where(and_(
                    ProxyHistory.datestamp >= prev_date_filter,
                    ProxyHistory.datestamp < date_filter,
                    ProxyHistory.isRefunded == False
                ))
                prev_pptp_rev_query = select(func.coalesce(func.sum(PptpHistory.price), Decimal('0'))).where(and_(
                    PptpHistory.datestamp >= prev_date_filter,
                    PptpHistory.datestamp < date_filter,
                    PptpHistory.isRefunded == False
                ))
                prev_deposits_query = select(func.coalesce(func.sum(UserTransaction.amount_in_dollar), Decimal('0'))).where(and_(
                    UserTransaction.dateOfTransaction >= prev_date_filter,
                    UserTransaction.dateOfTransaction < date_filter
                ))
                prev_users_query = select(func.count(User.user_id)).where(and_(
                    User.datestamp >= prev_date_filter,
                    User.datestamp < date_filter
                ))
                prev_refunds_query = select(func.count(ProxyHistory.id)).where(and_(
                    ProxyHistory.isRefunded == True,
                    ProxyHistory.datestamp >= prev_date_filter,
                    ProxyHistory.datestamp < date_filter
                ))
                prev_refunds_query2 = select(func.count(PptpHistory.id)).where(and_(
                    PptpHistory.isRefunded == True,
                    PptpHistory.datestamp >= prev_date_filter,
                    PptpHistory.datestamp < date_filter
                ))
                prev_refunds_amt_query = select(func.coalesce(func.sum(ProxyHistory.price), Decimal('0'))).where(and_(
                    ProxyHistory.isRefunded == True,
                    ProxyHistory.datestamp >= prev_date_filter,
                    ProxyHistory.datestamp < date_filter
                ))
                prev_refunds_amt_query2 = select(func.coalesce(func.sum(PptpHistory.price), Decimal('0'))).where(and_(
                    PptpHistory.isRefunded == True,
                    PptpHistory.datestamp >= prev_date_filter,
                    PptpHistory.datestamp < date_filter
                ))

                prev_proxy_rev_result = await session.execute(prev_proxy_rev_query)
                prev_pptp_rev_result = await session.execute(prev_pptp_rev_query)
                prev_proxy_revenue = prev_proxy_rev_result.scalar() or Decimal('0')
                prev_pptp_revenue = prev_pptp_rev_result.scalar() or Decimal('0')

                prev_deposits_result = await session.execute(prev_deposits_query)
                prev_deposits = prev_deposits_result.scalar() or Decimal('0')

                prev_users_result = await session.execute(prev_users_query)
                prev_new_users = prev_users_result.scalar() or 0

                prev_refunds_result1 = await session.execute(prev_refunds_query)
                prev_refunds_result2 = await session.execute(prev_refunds_query2)
                prev_refunds = (prev_refunds_result1.scalar() or 0) + (prev_refunds_result2.scalar() or 0)

                prev_refunds_amt_result1 = await session.execute(prev_refunds_amt_query)
                prev_refunds_amt_result2 = await session.execute(prev_refunds_amt_query2)
                prev_refunds_amount = (prev_refunds_amt_result1.scalar() or Decimal('0')) + (prev_refunds_amt_result2.scalar() or Decimal('0'))

                prev_net_profit = (prev_proxy_revenue + prev_pptp_revenue) - prev_refunds_amount

                # Calculate percentage changes
                def calc_percent(current, previous):
                    if previous == 0:
                        return 100.0 if current > 0 else 0.0
                    return round(float((current - previous) / previous * 100), 1)

                percentages = {
                    'deposits_change_percent': calc_percent(deposits, prev_deposits),
                    'users_change_percent': calc_percent(new_users, prev_new_users),
                    'proxy_revenue_change_percent': calc_percent(proxy_revenue, prev_proxy_revenue),
                    'pptp_revenue_change_percent': calc_percent(pptp_revenue, prev_pptp_revenue),
                    'refunds_change_percent': calc_percent(refunds, prev_refunds),
                    'net_profit_change_percent': calc_percent(net_profit, prev_net_profit)
                }
            else:
                # No percentage calculations for all_time
                percentages = {
                    'deposits_change_percent': 0.0,
                    'users_change_percent': 0.0,
                    'proxy_revenue_change_percent': 0.0,
                    'pptp_revenue_change_percent': 0.0,
                    'refunds_change_percent': 0.0,
                    'net_profit_change_percent': 0.0
                }

            return {
                "revenue": revenue,
                "proxy_revenue": proxy_revenue,
                "pptp_revenue": pptp_revenue,
                "purchases": purchases,
                "deposits": deposits,
                "deposits_count": deposits_count,
                "new_users": new_users,
                "refunds": refunds,
                "refunds_amount": refunds_amount,
                "net_profit": net_profit,
                **percentages
            }

        except Exception as e:
            logger.error(f"Error getting period stats for {period}: {e}")
            return {
                "revenue": Decimal('0'),
                "proxy_revenue": Decimal('0'),
                "pptp_revenue": Decimal('0'),
                "purchases": 0,
                "deposits": Decimal('0'),
                "deposits_count": 0,
                "new_users": 0,
                "refunds": 0,
                "refunds_amount": Decimal('0'),
                "net_profit": Decimal('0'),
                "deposits_change_percent": 0.0,
                "users_change_percent": 0.0,
                "proxy_revenue_change_percent": 0.0,
                "pptp_revenue_change_percent": 0.0,
                "refunds_change_percent": 0.0,
                "net_profit_change_percent": 0.0
            }

    @staticmethod
    async def get_revenue_chart_data(
        session: AsyncSession,
        period: str = '30d',
        granularity: str = 'day'
    ) -> List[Dict[str, Any]]:
        """
        Get revenue chart data grouped by time period.
        
        Args:
            session: Database session
            period: Time period ('7d', '30d', 'all_time')
            granularity: Grouping ('day', 'week', 'month')
            
        Returns:
            List of dictionaries with date, revenue, purchases, deposits, socks5_count, pptp_count
            
        Example:
            [
                {
                    "date": "2025-11-12",
                    "revenue": Decimal("5000.50"),
                    "purchases": 50,
                    "deposits": Decimal("6000.00"),
                    "socks5_count": 30,
                    "pptp_count": 20
                },
                ...
            ]
        """
        try:
            # Determine date range
            now = datetime.utcnow()
            date_filter = None
            
            if period == '7d':
                date_filter = now - timedelta(days=7)
            elif period == '30d':
                date_filter = now - timedelta(days=30)
            # 'all_time' - no filter

            # For simplicity, we'll aggregate by day and return raw data
            # Frontend can group by week/month if needed
            
            # Get proxy purchases grouped by date
            proxy_query = select(
                func.date(ProxyHistory.datestamp).label('date'),
                func.coalesce(func.sum(ProxyHistory.price), Decimal('0')).label('proxy_revenue'),
                func.count(ProxyHistory.id).label('proxy_count')
            ).where(ProxyHistory.isRefunded == False)
            
            if date_filter:
                proxy_query = proxy_query.where(ProxyHistory.datestamp >= date_filter)
            
            proxy_query = proxy_query.group_by(func.date(ProxyHistory.datestamp)).order_by('date')
            proxy_result = await session.execute(proxy_query)
            proxy_data = proxy_result.all()

            # Get PPTP purchases grouped by date
            pptp_query = select(
                func.date(PptpHistory.datestamp).label('date'),
                func.coalesce(func.sum(PptpHistory.price), Decimal('0')).label('pptp_revenue'),
                func.count(PptpHistory.id).label('pptp_count')
            ).where(PptpHistory.isRefunded == False)
            
            if date_filter:
                pptp_query = pptp_query.where(PptpHistory.datestamp >= date_filter)
            
            pptp_query = pptp_query.group_by(func.date(PptpHistory.datestamp)).order_by('date')
            pptp_result = await session.execute(pptp_query)
            pptp_data = pptp_result.all()

            # Get deposits grouped by date
            deposits_query = select(
                func.date(UserTransaction.dateOfTransaction).label('date'),
                func.coalesce(func.sum(UserTransaction.amount_in_dollar), Decimal('0')).label('deposits')
            )
            
            if date_filter:
                deposits_query = deposits_query.where(UserTransaction.dateOfTransaction >= date_filter)
            
            deposits_query = deposits_query.group_by(func.date(UserTransaction.dateOfTransaction)).order_by('date')
            deposits_result = await session.execute(deposits_query)
            deposits_data = deposits_result.all()

            # Merge data by date
            data_by_date = {}
            
            for row in proxy_data:
                date_str = row.date.strftime('%Y-%m-%d')
                if date_str not in data_by_date:
                    data_by_date[date_str] = {
                        "date": date_str,
                        "revenue": Decimal('0'),
                        "purchases": 0,
                        "deposits": Decimal('0'),
                        "socks5_count": 0,
                        "pptp_count": 0
                    }
                data_by_date[date_str]["revenue"] += row.proxy_revenue
                data_by_date[date_str]["purchases"] += row.proxy_count
                data_by_date[date_str]["socks5_count"] = row.proxy_count

            for row in pptp_data:
                date_str = row.date.strftime('%Y-%m-%d')
                if date_str not in data_by_date:
                    data_by_date[date_str] = {
                        "date": date_str,
                        "revenue": Decimal('0'),
                        "purchases": 0,
                        "deposits": Decimal('0'),
                        "socks5_count": 0,
                        "pptp_count": 0
                    }
                data_by_date[date_str]["revenue"] += row.pptp_revenue
                data_by_date[date_str]["purchases"] += row.pptp_count
                data_by_date[date_str]["pptp_count"] = row.pptp_count

            for row in deposits_data:
                date_str = row.date.strftime('%Y-%m-%d')
                if date_str not in data_by_date:
                    data_by_date[date_str] = {
                        "date": date_str,
                        "revenue": Decimal('0'),
                        "purchases": 0,
                        "deposits": Decimal('0'),
                        "socks5_count": 0,
                        "pptp_count": 0
                    }
                data_by_date[date_str]["deposits"] = row.deposits

            # Convert to sorted list
            result = sorted(data_by_date.values(), key=lambda x: x['date'])
            return result

        except Exception as e:
            logger.error(f"Error getting revenue chart data: {e}")
            raise HTTPException(status_code=500, detail="Failed to get chart data")

    @staticmethod
    async def get_users_list(
        session: AsyncSession,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get paginated users list with filters and statistics.
        
        Args:
            session: Database session
            filters: Dictionary with filter parameters (search, platform, dates, balance, is_blocked)
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            Tuple of (users list, total count)
        """
        try:
            # Build base query
            query = select(User)

            # Apply filters
            conditions = []
            
            if filters.get('search'):
                search = filters['search']
                conditions.append(
                    or_(
                        User.username.ilike(f'%{search}%'),
                        User.access_code.ilike(f'%{search}%'),
                        cast(User.telegram_id, String).ilike(f'%{search}%')
                    )
                )
            
            if filters.get('platform'):
                conditions.append(User.platform_registered == filters['platform'])
            
            if filters.get('date_from'):
                conditions.append(User.datestamp >= filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append(User.datestamp <= filters['date_to'])
            
            if filters.get('min_balance') is not None:
                conditions.append(User.balance >= filters['min_balance'])
            
            if filters.get('max_balance') is not None:
                conditions.append(User.balance <= filters['max_balance'])
            
            if filters.get('is_blocked') is not None:
                conditions.append(User.is_blocked == filters['is_blocked'])

            if conditions:
                query = query.where(and_(*conditions))

            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            # Apply pagination
            query = query.offset((page - 1) * page_size).limit(page_size)
            query = query.order_by(desc(User.datestamp))

            # Execute query
            result = await session.execute(query)
            users = result.scalars().all()

            # Enrich with statistics (optimize with subqueries)
            users_data = []
            for user in users:
                # Total spent
                spent_proxy = await session.execute(
                    select(func.coalesce(func.sum(ProxyHistory.price), Decimal('0')))
                    .where(and_(
                        ProxyHistory.user_id == user.user_id,
                        ProxyHistory.isRefunded == False
                    ))
                )
                spent_pptp = await session.execute(
                    select(func.coalesce(func.sum(PptpHistory.price), Decimal('0')))
                    .where(and_(
                        PptpHistory.user_id == user.user_id,
                        PptpHistory.isRefunded == False
                    ))
                )
                total_spent = (spent_proxy.scalar() or Decimal('0')) + (spent_pptp.scalar() or Decimal('0'))

                # Total deposited
                deposited_result = await session.execute(
                    select(func.coalesce(func.sum(UserTransaction.amount_in_dollar), Decimal('0')))
                    .where(UserTransaction.user_id == user.user_id)
                )
                total_deposited = deposited_result.scalar() or Decimal('0')

                # Purchases count
                purchases_proxy = await session.execute(
                    select(func.count(ProxyHistory.id))
                    .where(ProxyHistory.user_id == user.user_id)
                )
                purchases_pptp = await session.execute(
                    select(func.count(PptpHistory.id))
                    .where(PptpHistory.user_id == user.user_id)
                )
                purchases_count = (purchases_proxy.scalar() or 0) + (purchases_pptp.scalar() or 0)

                # Last activity
                last_activity_result = await session.execute(
                    select(func.max(UserLog.date_of_action))
                    .where(UserLog.user_id == user.user_id)
                )
                last_activity = last_activity_result.scalar()

                users_data.append({
                    "user_id": user.user_id,
                    "access_code": user.access_code,
                    "balance": user.balance,
                    "datestamp": user.datestamp,
                    "platform_registered": user.platform_registered,
                    "language": user.language,
                    "username": user.username,
                    "telegram_id": user.telegram_id[0] if user.telegram_id and len(user.telegram_id) > 0 else None,
                    "telegram_id_list": user.telegram_id if user.telegram_id else None,
                    "total_spent": total_spent,
                    "total_deposited": total_deposited,
                    "purchases_count": purchases_count,
                    "last_activity": last_activity,
                    "is_blocked": user.is_blocked,
                    "blocked_at": user.blocked_at,
                    "referrals_count": user.referal_quantity
                })

            return users_data, total

        except Exception as e:
            logger.error(f"Error getting users list: {e}")
            raise HTTPException(status_code=500, detail="Failed to get users list")

    @staticmethod
    async def update_user(
        session: AsyncSession,
        user_id: int,
        admin_id: int,
        updates: Dict[str, Any]
    ) -> User:
        """
        Update user data (admin only).
        
        Args:
            session: Database session
            user_id: User ID to update
            admin_id: Admin user ID performing the action
            updates: Dictionary with fields to update
            
        Returns:
            Updated User object
            
        Raises:
            HTTPException: If user not found or update fails
        """
        try:
            # Get user
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Determine action type for logging
            action_types = []
            action_details = {"target_user_id": user_id, "updates": {}}

            # Apply updates
            if 'balance' in updates:
                old_balance = user.balance
                user.balance = Decimal(str(updates['balance']))
                action_types.append("ADMIN_UPDATE_BALANCE")
                action_details["updates"]["balance"] = {"old": str(old_balance), "new": str(user.balance)}

            if 'is_blocked' in updates:
                old_blocked = user.is_blocked
                user.is_blocked = updates['is_blocked']
                
                if user.is_blocked:
                    user.blocked_at = datetime.utcnow()
                    user.blocked_reason = updates.get('blocked_reason')
                    action_types.append("ADMIN_BLOCK_USER")
                    action_details["updates"]["block"] = {
                        "reason": user.blocked_reason
                    }
                else:
                    user.blocked_at = None
                    user.blocked_reason = None
                    action_types.append("ADMIN_UNBLOCK_USER")

            if 'language' in updates:
                old_language = user.language
                user.language = updates['language']
                action_types.append("ADMIN_UPDATE_LANGUAGE")
                action_details["updates"]["language"] = {"old": old_language, "new": user.language}

            # Flush changes
            await session.flush()

            # Log admin action
            for action_type in action_types:
                await LogService.create_log(
                    session=session,
                    user_id=admin_id,
                    action_type=action_type,
                    action_details=action_details
                )

            await session.commit()
            await session.refresh(user)

            logger.info(f"Admin {admin_id} updated user {user_id}: {updates}")
            return user

        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update user")

    @staticmethod
    async def get_top_users(
        session: AsyncSession,
        metric: str = 'revenue',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top users by specified metric.
        
        Args:
            session: Database session
            metric: Metric to sort by ('revenue', 'purchases', 'deposits', 'referrals')
            limit: Number of users to return
            
        Returns:
            List of top users with their metrics
        """
        try:
            if metric == 'revenue':
                # Top by total spent (revenue from user's purchases)
                # Aggregate both proxy and pptp purchases
                # This is complex - simplified version for now
                query = select(
                    User,
                    (
                        select(func.coalesce(func.sum(ProxyHistory.price), Decimal('0')))
                        .where(and_(
                            ProxyHistory.user_id == User.user_id,
                            ProxyHistory.isRefunded == False
                        ))
                        .scalar_subquery()
                    ).label('total_spent')
                ).order_by(desc('total_spent')).limit(limit)
                
            elif metric == 'purchases':
                query = select(
                    User,
                    (
                        select(func.count(ProxyHistory.id))
                        .where(ProxyHistory.user_id == User.user_id)
                        .scalar_subquery()
                    ).label('purchases_count')
                ).order_by(desc('purchases_count')).limit(limit)
                
            elif metric == 'deposits':
                query = select(
                    User,
                    (
                        select(func.coalesce(func.sum(UserTransaction.amount_in_dollar), Decimal('0')))
                        .where(UserTransaction.user_id == User.user_id)
                        .scalar_subquery()
                    ).label('total_deposited')
                ).order_by(desc('total_deposited')).limit(limit)
                
            elif metric == 'referrals':
                query = select(User).order_by(desc(User.referal_quantity)).limit(limit)
            else:
                raise HTTPException(status_code=400, detail="Invalid metric")

            result = await session.execute(query)
            rows = result.all()

            # Format results
            top_users = []
            for row in rows:
                if isinstance(row, tuple):
                    user = row[0]
                    metric_value = row[1]
                else:
                    user = row
                    metric_value = user.referal_quantity if metric == 'referrals' else 0

                top_users.append({
                    "user_id": user.user_id,
                    "username": user.username,
                    "access_code": user.access_code,
                    "metric_value": metric_value
                })

            return top_users

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting top users by {metric}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get top users")

    @staticmethod
    async def get_user_details(
        session: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed information about specific user for admin.
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            Dictionary with complete user information
            
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
                raise HTTPException(status_code=404, detail="User not found")

            # Get purchase history (proxy + pptp)
            proxy_purchases = await session.execute(
                select(ProxyHistory)
                .where(ProxyHistory.user_id == user_id)
                .order_by(desc(ProxyHistory.datestamp))
            )
            pptp_purchases = await session.execute(
                select(PptpHistory)
                .where(PptpHistory.user_id == user_id)
                .order_by(desc(PptpHistory.datestamp))
            )

            # Get payment history
            transactions = await session.execute(
                select(UserTransaction)
                .where(UserTransaction.user_id == user_id)
                .order_by(desc(UserTransaction.dateOfTransaction))
            )

            # Get user logs
            logs = await session.execute(
                select(UserLog)
                .where(UserLog.user_id == user_id)
                .order_by(desc(UserLog.date_of_action))
                .limit(100)
            )

            # Get referrals
            referrals = await session.execute(
                select(User)
                .where(User.user_referal_id == user_id)
            )

            # Calculate statistics
            total_spent_proxy = await session.execute(
                select(func.coalesce(func.sum(ProxyHistory.price), Decimal('0')))
                .where(and_(
                    ProxyHistory.user_id == user_id,
                    ProxyHistory.isRefunded == False
                ))
            )
            total_spent_pptp = await session.execute(
                select(func.coalesce(func.sum(PptpHistory.price), Decimal('0')))
                .where(and_(
                    PptpHistory.user_id == user_id,
                    PptpHistory.isRefunded == False
                ))
            )
            total_spent = (total_spent_proxy.scalar() or Decimal('0')) + (total_spent_pptp.scalar() or Decimal('0'))

            total_deposited = await session.execute(
                select(func.coalesce(func.sum(UserTransaction.amount_in_dollar), Decimal('0')))
                .where(UserTransaction.user_id == user_id)
            )

            purchases_count = (len(proxy_purchases.all()) + len(pptp_purchases.all()))

            return {
                "user": {
                    "user_id": user.user_id,
                    "access_code": user.access_code,
                    "username": user.username,
                    "telegram_id": user.telegram_id,
                    "balance": user.balance,
                    "datestamp": user.datestamp,
                    "platform_registered": user.platform_registered.value,
                    "language": user.language,
                    "myreferal_id": user.myreferal_id,
                    "referal_quantity": user.referal_quantity,
                    "is_admin": user.is_admin,
                    "is_blocked": user.is_blocked,
                    "blocked_at": user.blocked_at,
                    "blocked_reason": user.blocked_reason
                },
                "statistics": {
                    "total_spent": total_spent,
                    "total_deposited": total_deposited.scalar() or Decimal('0'),
                    "purchases_count": purchases_count,
                    "referrals_count": user.referal_quantity
                },
                "proxy_purchases": [p for p in proxy_purchases.scalars().all()],
                "pptp_purchases": [p for p in pptp_purchases.scalars().all()],
                "transactions": [t for t in transactions.scalars().all()],
                "logs": [l for l in logs.scalars().all()],
                "referrals": [r for r in referrals.scalars().all()]
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting user details for {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user details")

    # Coupon management methods

    @staticmethod
    async def get_coupons_list(
        session: AsyncSession,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get paginated coupons list with filters.
        
        Args:
            session: Database session
            filters: Dictionary with filter parameters
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            Tuple of (coupons list, total count)
        """
        try:
            # Build base query
            query = select(Coupon)
            conditions = []

            # Apply filters
            if filters.get('search'):
                conditions.append(Coupon.coupon.ilike(f'%{filters["search"]}%'))
            
            if filters.get('is_active') is not None:
                conditions.append(Coupon.is_active == filters['is_active'])
            
            if filters.get('date_from'):
                conditions.append(Coupon.datestamp >= filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append(Coupon.datestamp <= filters['date_to'])

            if conditions:
                query = query.where(and_(*conditions))

            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            # Apply pagination
            query = query.order_by(desc(Coupon.datestamp))
            query = query.offset((page - 1) * page_size).limit(page_size)

            # Execute
            result = await session.execute(query)
            coupons = result.scalars().all()

            # Format results
            coupons_data = []
            for coupon in coupons:
                coupons_data.append({
                    "id": coupon.id_cupon,
                    "code": coupon.coupon,
                    "discount_percent": coupon.discount_percentage,
                    "max_uses": coupon.max_usage,
                    "used_count": coupon.usage_quantity,
                    "is_active": coupon.is_active,
                    "created_at": coupon.datestamp,
                    "expires_at": coupon.expires_at
                })

            return coupons_data, total

        except Exception as e:
            logger.error(f"Error getting coupons list: {e}")
            raise HTTPException(status_code=500, detail="Failed to get coupons list")

    @staticmethod
    async def create_coupon(
        session: AsyncSession,
        admin_id: int,
        coupon_data: Dict[str, Any]
    ) -> Coupon:
        """
        Create new coupon.
        
        Args:
            session: Database session
            admin_id: Admin user ID performing the action
            coupon_data: Dictionary with coupon fields
            
        Returns:
            Created Coupon object
            
        Raises:
            HTTPException: If coupon code already exists or creation fails
        """
        try:
            # Check if coupon code already exists
            existing = await session.execute(
                select(Coupon).where(Coupon.coupon == coupon_data['code'])
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Coupon with code '{coupon_data['code']}' already exists"
                )

            # Create coupon
            coupon = Coupon(
                coupon=coupon_data['code'],
                discount_percentage=coupon_data['discount_percent'],
                max_usage=coupon_data['max_uses'],
                expires_at=coupon_data.get('expires_at'),
                is_active=coupon_data.get('is_active', True)
            )
            session.add(coupon)
            await session.flush()

            # Log admin action
            await LogService.create_log(
                session=session,
                user_id=admin_id,
                action_type="ADMIN_CREATE_COUPON",
                action_details=coupon_data
            )

            await session.commit()
            await session.refresh(coupon)

            logger.info(f"Admin {admin_id} created coupon {coupon.coupon}")
            return coupon

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating coupon: {e}")
            raise HTTPException(status_code=500, detail="Failed to create coupon")

    @staticmethod
    async def update_coupon(
        session: AsyncSession,
        admin_id: int,
        coupon_id: int,
        updates: Dict[str, Any]
    ) -> Coupon:
        """
        Update existing coupon.
        
        Args:
            session: Database session
            admin_id: Admin user ID performing the action
            coupon_id: Coupon ID
            updates: Dictionary with fields to update
            
        Returns:
            Updated Coupon object
            
        Raises:
            HTTPException: If coupon not found or update fails
        """
        try:
            # Get coupon
            result = await session.execute(
                select(Coupon).where(Coupon.id_cupon == coupon_id)
            )
            coupon = result.scalar_one_or_none()

            if not coupon:
                raise HTTPException(status_code=404, detail="Coupon not found")

            # Apply updates
            if 'discount_percent' in updates:
                coupon.discount_percentage = updates['discount_percent']
            
            if 'max_uses' in updates:
                coupon.max_usage = updates['max_uses']
            
            if 'is_active' in updates:
                coupon.is_active = updates['is_active']
            
            if 'expires_at' in updates:
                coupon.expires_at = updates['expires_at']

            await session.flush()

            # Log admin action
            await LogService.create_log(
                session=session,
                user_id=admin_id,
                action_type="ADMIN_UPDATE_COUPON",
                action_details={"coupon_id": coupon_id, "updates": updates}
            )

            await session.commit()
            await session.refresh(coupon)

            logger.info(f"Admin {admin_id} updated coupon {coupon_id}: {updates}")
            return coupon

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating coupon {coupon_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update coupon")

    @staticmethod
    async def delete_coupon(
        session: AsyncSession,
        admin_id: int,
        coupon_id: int
    ) -> bool:
        """
        Delete coupon (soft delete: set is_active=False).
        
        Args:
            session: Database session
            admin_id: Admin user ID performing the action
            coupon_id: Coupon ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: If coupon not found or deletion fails
        """
        try:
            # Get coupon
            result = await session.execute(
                select(Coupon).where(Coupon.id_cupon == coupon_id)
            )
            coupon = result.scalar_one_or_none()

            if not coupon:
                raise HTTPException(status_code=404, detail="Coupon not found")

            # Soft delete
            coupon.is_active = False
            await session.flush()

            # Log admin action
            await LogService.create_log(
                session=session,
                user_id=admin_id,
                action_type="ADMIN_DELETE_COUPON",
                action_details={"coupon_id": coupon_id, "code": coupon.coupon}
            )

            await session.commit()

            logger.info(f"Admin {admin_id} deleted coupon {coupon_id}")
            return True

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting coupon {coupon_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete coupon")

    @staticmethod
    async def get_coupon_stats(
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get coupon statistics.
        
        Args:
            session: Database session
            
        Returns:
            Dictionary with coupon statistics
        """
        try:
            # Total coupons
            total_result = await session.execute(
                select(func.count(Coupon.id_cupon))
            )
            total_created = total_result.scalar() or 0

            # Active coupons
            active_result = await session.execute(
                select(func.count(Coupon.id_cupon))
                .where(Coupon.is_active == True)
            )
            active_coupons = active_result.scalar() or 0

            # Total usage
            usage_result = await session.execute(
                select(func.coalesce(func.sum(Coupon.usage_quantity), 0))
            )
            total_used = usage_result.scalar() or 0

            # Expired coupons
            now = datetime.utcnow()
            expired_result = await session.execute(
                select(func.count(Coupon.id_cupon))
                .where(and_(
                    Coupon.expires_at.isnot(None),
                    Coupon.expires_at < now
                ))
            )
            expired_coupons = expired_result.scalar() or 0

            return {
                "total_created": total_created,
                "active_coupons": active_coupons,
                "total_used": total_used,
                "expired_coupons": expired_coupons
            }

        except Exception as e:
            logger.error(f"Error getting coupon stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to get coupon statistics")

    # PPTP bulk upload methods

    # US state to country mapping
    US_STATES = {
        'AL': 'United States', 'AK': 'United States', 'AZ': 'United States', 'AR': 'United States',
        'CA': 'United States', 'CO': 'United States', 'CT': 'United States', 'DE': 'United States',
        'FL': 'United States', 'GA': 'United States', 'HI': 'United States', 'ID': 'United States',
        'IL': 'United States', 'IN': 'United States', 'IA': 'United States', 'KS': 'United States',
        'KY': 'United States', 'LA': 'United States', 'ME': 'United States', 'MD': 'United States',
        'MA': 'United States', 'MI': 'United States', 'MN': 'United States', 'MS': 'United States',
        'MO': 'United States', 'MT': 'United States', 'NE': 'United States', 'NV': 'United States',
        'NH': 'United States', 'NJ': 'United States', 'NM': 'United States', 'NY': 'United States',
        'NC': 'United States', 'ND': 'United States', 'OH': 'United States', 'OK': 'United States',
        'OR': 'United States', 'PA': 'United States', 'RI': 'United States', 'SC': 'United States',
        'SD': 'United States', 'TN': 'United States', 'TX': 'United States', 'UT': 'United States',
        'VT': 'United States', 'VA': 'United States', 'WA': 'United States', 'WV': 'United States',
        'WI': 'United States', 'WY': 'United States'
    }

    @staticmethod
    async def bulk_create_pptp_products(
        session: AsyncSession,
        admin_user_id: int,
        data: str,
        format: Optional[str] = None,
        catalog_id: Optional[int] = None,
        catalog_name: Optional[str] = None,
        catalog_price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Bulk create PPTP proxy products from line or CSV format.

        Args:
            session: Database session
            admin_user_id: Admin user ID performing the action
            data: Proxy data in line or CSV format
            format: Format type ('line' or 'csv'). Auto-detect if None.
            catalog_id: Existing catalog ID to add proxies to
            catalog_name: Name for new catalog (if creating)
            catalog_price: Price for new catalog (if creating)

        Returns:
            Dictionary with created_count, failed_count, products, errors

        Line format: IP:LOGIN:PASS:COUNTRY:STATE:CITY:ZIP (colon-separated)
        Example: 104.11.157.41:user1:pass123:United States:TX:Houston:77001

        CSV format: ip,login,password,country,state,city,zip
        Example:
            ip,login,password,country,state,city,zip
            104.11.157.41,user1,pass123,United States,TX,Houston,77001
        """
        try:
            created_products = []
            errors = []
            parsed_entries = []

            # Auto-detect format if not specified
            if format is None:
                # CSV likely has commas and newlines, line format has spaces and newlines
                # Enhanced logic: check for CSV header or multiple commas indicating CSV structure
                has_comma = ',' in data
                has_newline = '\n' in data
                has_csv_header = 'ip,login,password' in data.lower() or 'ip,login,pass' in data.lower()

                # If there's a CSV header, it's definitely CSV
                if has_csv_header:
                    format = 'csv'
                # If there are commas (even without newlines), treat as CSV for safety
                # This handles single-line CSV input better
                elif has_comma:
                    format = 'csv'
                else:
                    format = 'line'

            logger.info(f"Bulk PPTP upload started by admin {admin_user_id}, format: {format}")

            # Parse data based on format
            if format == 'line':
                # Split by newlines to get individual entries
                lines = [line.strip() for line in data.strip().split('\n') if line.strip()]
                for idx, line in enumerate(lines, start=1):
                    try:
                        # Split by colon to get 6-7 fields: IP:LOGIN:PASS:COUNTRY:STATE:CITY[:ZIP]
                        parts = line.split(':')
                        if len(parts) < 6:
                            errors.append(f"Line {idx}: Invalid format, expected IP:LOGIN:PASS:COUNTRY:STATE:CITY[:ZIP] (6-7 fields)")
                            continue

                        ip = parts[0].strip()
                        login = parts[1].strip()
                        password = parts[2].strip()
                        country = parts[3].strip()
                        state = parts[4].strip().upper()
                        city = parts[5].strip()
                        zip_code = parts[6].strip() if len(parts) > 6 else ''

                        parsed_entries.append({
                            'ip': ip,
                            'login': login,
                            'password': password,
                            'country': country,
                            'state': state,
                            'city': city,
                            'zip': zip_code,
                            'line_num': idx
                        })
                    except Exception as e:
                        errors.append(f"Line {idx}: Parse error - {str(e)}")

            elif format == 'csv':
                # Parse CSV
                try:
                    csv_reader = csv.DictReader(io.StringIO(data))
                    for idx, row in enumerate(csv_reader, start=2):  # Start from 2 (after header)
                        try:
                            ip = row.get('ip', '').strip()
                            login = row.get('login', '').strip()
                            password = row.get('password', '').strip()
                            country = row.get('country', '').strip()
                            state = row.get('state', '').strip().upper()
                            city = row.get('city', '').strip()
                            zip_code = row.get('zip', '').strip()

                            if not all([ip, login, password, country, state]):
                                errors.append(f"Row {idx}: Missing required fields (ip, login, password, country, state)")
                                continue

                            parsed_entries.append({
                                'ip': ip,
                                'login': login,
                                'password': password,
                                'country': country,
                                'state': state,
                                'city': city,
                                'zip': zip_code,
                                'line_num': idx
                            })
                        except Exception as e:
                            errors.append(f"Row {idx}: Parse error - {str(e)}")
                except Exception as e:
                    errors.append(f"CSV parsing error: {str(e)}")
                    return {
                        'created_count': 0,
                        'failed_count': len(errors),
                        'products': [],
                        'errors': errors
                    }

            # Validate and create products
            valid_entries = []
            for entry in parsed_entries:
                line_num = entry['line_num']

                # Validate required fields
                if not entry['ip']:
                    errors.append(f"Entry {line_num}: Missing IP")
                    continue
                if not entry['login']:
                    errors.append(f"Entry {line_num}: Missing login")
                    continue
                if not entry['password']:
                    errors.append(f"Entry {line_num}: Missing password")
                    continue
                if not entry['country']:
                    errors.append(f"Entry {line_num}: Missing country")
                    continue
                if not entry['state']:
                    errors.append(f"Entry {line_num}: Missing state")
                    continue

                # Validate IP address
                try:
                    ip_address(entry['ip'])
                except ValueError:
                    errors.append(f"Entry {line_num}: Invalid IP address '{entry['ip']}'")
                    continue

                valid_entries.append({
                    'ip': entry['ip'],
                    'login': entry['login'],
                    'password': entry['password'],
                    'country': entry['country'],
                    'state': entry['state'],
                    'city': entry['city'] or '',
                    'zip': entry['zip'] or ''
                })

            # Get or create PPTP catalog
            catalog = None

            # Case 1: Use existing catalog by ID
            if catalog_id is not None:
                catalog_result = await session.execute(
                    select(Catalog).where(Catalog.id == catalog_id)
                )
                catalog = catalog_result.scalar_one_or_none()
                if not catalog:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Catalog with ID {catalog_id} not found"
                    )
                logger.info(f"Using existing catalog ID {catalog.id}: {catalog.line_name}")

            # Case 2: Create new catalog with name and price
            elif catalog_name is not None and catalog_price is not None:
                # Generate unique ig_catalog identifier
                import time
                unique_id = f"PPTP_CATALOG_{int(time.time())}"

                catalog = Catalog(
                    ig_catalog=unique_id,
                    pre_lines_name='PPTP',
                    line_name=catalog_name,
                    price=catalog_price
                )
                session.add(catalog)
                await session.flush()
                logger.info(f"Created new PPTP catalog '{catalog_name}' with ID {catalog.id}, price ${catalog_price}")

            # Case 3: Default behavior - find or create default PPTP catalog
            else:
                catalog_result = await session.execute(
                    select(Catalog).where(Catalog.pre_lines_name == 'PPTP')
                )
                catalog = catalog_result.scalar_one_or_none()

                if not catalog:
                    # Create default PPTP catalog
                    catalog = Catalog(
                        ig_catalog='PPTP_CATALOG',
                        pre_lines_name='PPTP',
                        line_name='PPTP',
                        price=Decimal('5.00')  # Default price
                    )
                    session.add(catalog)
                    await session.flush()
                    logger.info(f"Created new default PPTP catalog with ID {catalog.id}")
                else:
                    logger.info(f"Using default PPTP catalog ID {catalog.id}")

            # Create products
            for entry in valid_entries:
                # Auto-detect region based on country
                region = "USA" if entry['country'] == "United States" else "EUROPE"

                product = Product(
                    catalog_id=catalog.id,
                    pre_lines_name='PPTP',
                    line_name='PPTP',
                    product={
                        'ip': entry['ip'],
                        'login': entry['login'],
                        'password': entry['password'],
                        'country': entry['country'],
                        'state': entry['state'],
                        'city': entry['city'],
                        'zip': entry['zip'],
                        'region': region
                    }
                )
                session.add(product)
                created_products.append(product)

            # Commit all products
            if created_products:
                await session.flush()

                # Log admin action
                await LogService.create_log(
                    session=session,
                    user_id=admin_user_id,
                    action_type="ADMIN_BULK_CREATE_PPTP",
                    action_details={
                        'created_count': len(created_products),
                        'failed_count': len(errors),
                        'format': format
                    }
                )

                await session.commit()

                # Refresh products to get IDs
                for product in created_products:
                    await session.refresh(product)

            logger.info(f"Bulk PPTP upload completed: {len(created_products)} created, {len(errors)} errors")

            # Format response
            products_data = []
            for product in created_products:
                product_json = product.product
                products_data.append({
                    'product_id': product.product_id,
                    'ip': product_json.get('ip', ''),
                    'login': product_json.get('login', ''),
                    'password': product_json.get('password', ''),
                    'country': product_json.get('country', ''),
                    'state': product_json.get('state', ''),
                    'city': product_json.get('city', ''),
                    'zip': product_json.get('zip', ''),
                    'created_at': product.datestamp
                })

            return {
                'created_count': len(created_products),
                'failed_count': len(errors),
                'products': products_data,
                'errors': errors
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error in bulk PPTP upload: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to bulk create PPTP proxies: {str(e)}")

    @staticmethod
    async def get_recent_activity(
        session: AsyncSession,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity across all users for admin dashboard.

        Args:
            session: Database session
            limit: Maximum number of activities to return (default: 20)

        Returns:
            List of recent activities with formatted data
        """
        try:
            # Query recent user logs with user information
            query = (
                select(UserLog, User.username)
                .join(User, UserLog.user_id == User.user_id)
                .order_by(desc(UserLog.date_of_action))
                .limit(limit)
            )

            result = await session.execute(query)
            logs_with_users = result.all()

            activities = []
            for log, username in logs_with_users:
                # Parse action_is JSON to extract amount if available
                amount_change = None
                try:
                    import json
                    action_data = json.loads(log.action_is) if log.action_is else {}
                except (json.JSONDecodeError, TypeError):
                    action_data = {}

                # Determine amount change based on action type
                if log.action_type == 'DEPOSIT':
                    amount_change = float(action_data.get('amount', 0))
                elif log.action_type in ['BUY_SOCKS5', 'BUY_PPTP']:
                    # Negative for purchases
                    amount_change = -float(action_data.get('price', action_data.get('amount', 0)))
                elif log.action_type == 'REFUND':
                    # Positive for refunds
                    amount_change = float(action_data.get('refund_amount', action_data.get('amount', 0)))

                # Create description from action_type and action_data
                description = log.action_type.replace('_', ' ').title()
                if action_data:
                    # Add relevant details from action_data
                    if 'message' in action_data:
                        description = action_data['message']
                    elif 'proxy_id' in action_data:
                        description = f"{description} (Proxy #{action_data['proxy_id']})"

                activities.append({
                    'id': log.id_log,
                    'user_id': log.user_id,
                    'username': username or f'User#{log.user_id}',
                    'action_type': log.action_type,
                    'description': description,
                    'amount_change': amount_change,
                    'timestamp': log.date_of_action.isoformat() if log.date_of_action else None
                })

            return activities

        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            raise HTTPException(status_code=500, detail="Failed to get recent activity")

    @staticmethod
    async def get_pptp_proxies(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        catalog_id: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get paginated list of PPTP proxies.

        Args:
            session: Database session
            page: Page number (1-indexed)
            page_size: Items per page
            search: Optional search query for IP, country, state, or city
            catalog_id: Optional catalog ID filter

        Returns:
            Tuple of (list of proxies, total count)
        """
        try:
            from backend.models.product import Product
            from sqlalchemy import select, func, or_

            # Build base query
            query = select(Product).where(Product.pre_lines_name == 'PPTP')

            # Apply catalog filter if provided
            if catalog_id:
                query = query.where(Product.catalog_id == catalog_id)

            # Apply search filter if provided
            if search:
                search_lower = search.lower()
                # Search in product JSON fields
                query = query.where(
                    or_(
                        func.lower(Product.product['ip'].astext).contains(search_lower),
                        func.lower(Product.product['country'].astext).contains(search_lower),
                        func.lower(Product.product['state'].astext).contains(search_lower),
                        func.lower(Product.product['city'].astext).contains(search_lower)
                    )
                )

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()

            # Apply pagination and order by newest first
            query = query.order_by(Product.datestamp.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)

            # Execute query
            result = await session.execute(query)
            products = result.scalars().all()

            # Format products
            proxies = []
            for product in products:
                product_data = product.product
                proxies.append({
                    'product_id': product.product_id,
                    'ip': product_data.get('ip', ''),
                    'login': product_data.get('login', ''),
                    'password': product_data.get('password', ''),
                    'country': product_data.get('country', ''),
                    'state': product_data.get('state', ''),
                    'city': product_data.get('city', ''),
                    'zip': product_data.get('zip', ''),
                    'created_at': product.datestamp
                })

            return proxies, total

        except Exception as e:
            logger.error(f"Error getting PPTP proxies: {e}")
            raise HTTPException(status_code=500, detail="Failed to get PPTP proxies")

    @staticmethod
    async def delete_pptp_proxy(
        session: AsyncSession,
        product_id: int
    ) -> None:
        """
        Delete single PPTP proxy.

        Args:
            session: Database session
            product_id: Product ID to delete

        Raises:
            HTTPException: If product not found or deletion fails
        """
        try:
            from backend.models.product import Product
            from sqlalchemy import select, delete

            # Check if product exists and is PPTP
            query = select(Product).where(
                Product.product_id == product_id,
                Product.pre_lines_name == 'PPTP'
            )
            result = await session.execute(query)
            product = result.scalar_one_or_none()

            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"PPTP proxy with ID {product_id} not found"
                )

            # Delete product
            await session.delete(product)
            await session.commit()

            logger.info(f"Deleted PPTP proxy {product_id}")

        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting PPTP proxy {product_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete PPTP proxy")

    @staticmethod
    async def bulk_delete_pptp_proxies(
        session: AsyncSession,
        product_ids: List[int],
        admin_user_id: int
    ) -> Dict[str, Any]:
        """
        Bulk delete PPTP proxies.

        Args:
            session: Database session
            product_ids: List of product IDs to delete
            admin_user_id: ID of admin performing the action

        Returns:
            Dictionary with statistics: deleted_count, failed_count, errors
        """
        deleted_count = 0
        failed_count = 0
        errors = []

        try:
            from backend.models.product import Product
            from sqlalchemy import select

            for product_id in product_ids:
                try:
                    # Check if product exists and is PPTP
                    query = select(Product).where(
                        Product.product_id == product_id,
                        Product.pre_lines_name == 'PPTP'
                    )
                    result = await session.execute(query)
                    product = result.scalar_one_or_none()

                    if not product:
                        errors.append(f"Product {product_id}: Not found or not PPTP")
                        failed_count += 1
                        continue

                    # Delete product
                    await session.delete(product)
                    deleted_count += 1

                except Exception as e:
                    errors.append(f"Product {product_id}: {str(e)}")
                    failed_count += 1
                    logger.error(f"Error deleting PPTP proxy {product_id}: {e}")

            # Commit all deletions
            if deleted_count > 0:
                await session.commit()
                logger.info(f"Bulk deleted {deleted_count} PPTP proxies by admin {admin_user_id}")
            else:
                await session.rollback()

            return {
                'deleted_count': deleted_count,
                'failed_count': failed_count,
                'errors': errors[:5]  # Return first 5 errors
            }

        except Exception as e:
            await session.rollback()
            logger.error(f"Error in bulk PPTP deletion: {e}")
            raise HTTPException(status_code=500, detail="Failed to bulk delete PPTP proxies")

