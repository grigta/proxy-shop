"""
Proxy Inventory service for managing proxy IP/port catalog.
Used by admin panel to add/remove/update available proxies.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, cast, String, desc
from sqlalchemy.exc import IntegrityError
from backend.models.proxy_inventory import ProxyInventory
from fastapi import HTTPException
from decimal import Decimal
from typing import List, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ProxyInventoryService:
    """Service for managing proxy inventory (admin operations)."""

    @staticmethod
    async def get_proxies(
        session: AsyncSession,
        filters: Dict[str, Any] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ProxyInventory], int]:
        """
        Get paginated list of proxies with filters.
        
        Args:
            session: Database session
            filters: Dictionary with filter parameters
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            Tuple of (proxies list, total count)
        """
        try:
            if filters is None:
                filters = {}

            # Build base query
            query = select(ProxyInventory)
            conditions = []

            # Apply filters
            if filters.get('country'):
                conditions.append(ProxyInventory.country.ilike(f'%{filters["country"]}%'))
            
            if filters.get('state'):
                conditions.append(ProxyInventory.state.ilike(f'%{filters["state"]}%'))
            
            if filters.get('city'):
                conditions.append(ProxyInventory.city.ilike(f'%{filters["city"]}%'))
            
            if filters.get('is_available') is not None:
                conditions.append(ProxyInventory.is_available == filters['is_available'])
            
            if filters.get('search'):
                search = filters['search']
                conditions.append(
                    or_(
                        ProxyInventory.ip.ilike(f'%{search}%'),
                        ProxyInventory.city.ilike(f'%{search}%'),
                        ProxyInventory.country.ilike(f'%{search}%')
                    )
                )

            if conditions:
                query = query.where(and_(*conditions))

            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            # Apply pagination
            query = query.order_by(desc(ProxyInventory.created_at))
            query = query.offset((page - 1) * page_size).limit(page_size)

            # Execute
            result = await session.execute(query)
            proxies = result.scalars().all()

            return list(proxies), total

        except Exception as e:
            logger.error(f"Error getting proxies list: {e}")
            raise HTTPException(status_code=500, detail="Failed to get proxies list")

    @staticmethod
    async def create_proxy(
        session: AsyncSession,
        proxy_data: Dict[str, Any]
    ) -> ProxyInventory:
        """
        Create single proxy.
        
        Args:
            session: Database session
            proxy_data: Dictionary with proxy fields
            
        Returns:
            Created ProxyInventory object
            
        Raises:
            HTTPException: If proxy with same IP:port already exists or creation fails
        """
        try:
            # Check if proxy with same IP:port already exists
            existing = await session.execute(
                select(ProxyInventory).where(and_(
                    ProxyInventory.ip == proxy_data['ip'],
                    ProxyInventory.port == proxy_data['port']
                ))
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Proxy with IP {proxy_data['ip']}:{proxy_data['port']} already exists"
                )

            # Create proxy
            proxy = ProxyInventory(**proxy_data)
            session.add(proxy)
            await session.flush()
            await session.refresh(proxy)

            logger.info(f"Created proxy {proxy.ip}:{proxy.port} in {proxy.country}")
            return proxy

        except HTTPException:
            raise
        except IntegrityError as e:
            logger.error(f"Integrity error creating proxy: {e}")
            raise HTTPException(
                status_code=400,
                detail="Proxy with this IP:port combination already exists"
            )
        except Exception as e:
            logger.error(f"Error creating proxy: {e}")
            raise HTTPException(status_code=500, detail="Failed to create proxy")

    @staticmethod
    async def bulk_create_proxies(
        session: AsyncSession,
        proxies_data: List[Dict[str, Any]]
    ) -> List[ProxyInventory]:
        """
        Create multiple proxies in bulk.
        
        Args:
            session: Database session
            proxies_data: List of dictionaries with proxy fields
            
        Returns:
            List of created ProxyInventory objects
            
        Raises:
            HTTPException: If bulk creation fails
        """
        try:
            created_proxies = []
            errors = []

            for idx, proxy_data in enumerate(proxies_data):
                try:
                    # Check uniqueness
                    existing = await session.execute(
                        select(ProxyInventory).where(and_(
                            ProxyInventory.ip == proxy_data['ip'],
                            ProxyInventory.port == proxy_data['port']
                        ))
                    )
                    if existing.scalar_one_or_none():
                        errors.append(f"Row {idx + 1}: Proxy {proxy_data['ip']}:{proxy_data['port']} already exists")
                        continue

                    proxy = ProxyInventory(**proxy_data)
                    session.add(proxy)
                    created_proxies.append(proxy)

                except Exception as e:
                    errors.append(f"Row {idx + 1}: {str(e)}")

            # Flush all
            await session.flush()

            # Refresh all
            for proxy in created_proxies:
                await session.refresh(proxy)

            logger.info(f"Bulk created {len(created_proxies)} proxies, {len(errors)} errors")

            if errors and not created_proxies:
                raise HTTPException(
                    status_code=400,
                    detail=f"All proxies failed: {'; '.join(errors)}"
                )

            return created_proxies

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in bulk create proxies: {e}")
            raise HTTPException(status_code=500, detail="Failed to bulk create proxies")

    @staticmethod
    async def update_proxy(
        session: AsyncSession,
        proxy_id: int,
        updates: Dict[str, Any]
    ) -> ProxyInventory:
        """
        Update proxy availability and price.
        
        Args:
            session: Database session
            proxy_id: Proxy ID
            updates: Dictionary with fields to update
            
        Returns:
            Updated ProxyInventory object
            
        Raises:
            HTTPException: If proxy not found or update fails
        """
        try:
            # Get proxy
            result = await session.execute(
                select(ProxyInventory).where(ProxyInventory.id == proxy_id)
            )
            proxy = result.scalar_one_or_none()

            if not proxy:
                raise HTTPException(status_code=404, detail="Proxy not found")

            # Apply updates
            if 'is_available' in updates:
                proxy.is_available = updates['is_available']
            
            if 'price_per_hour' in updates:
                proxy.price_per_hour = Decimal(str(updates['price_per_hour']))
            
            if 'notes' in updates:
                proxy.notes = updates['notes']

            await session.flush()
            await session.refresh(proxy)

            logger.info(f"Updated proxy {proxy_id}: {updates}")
            return proxy

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating proxy {proxy_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update proxy")

    @staticmethod
    async def delete_proxy(
        session: AsyncSession,
        proxy_id: int
    ) -> bool:
        """
        Delete proxy from inventory.
        
        Args:
            session: Database session
            proxy_id: Proxy ID
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: If proxy not found or deletion fails
        """
        try:
            # Get proxy
            result = await session.execute(
                select(ProxyInventory).where(ProxyInventory.id == proxy_id)
            )
            proxy = result.scalar_one_or_none()

            if not proxy:
                raise HTTPException(status_code=404, detail="Proxy not found")

            # Delete
            await session.delete(proxy)
            await session.flush()

            logger.info(f"Deleted proxy {proxy_id} ({proxy.ip}:{proxy.port})")
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting proxy {proxy_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete proxy")

    @staticmethod
    async def get_proxy_stats(
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get proxy inventory statistics.
        
        Args:
            session: Database session
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Total proxies
            total_result = await session.execute(
                select(func.count(ProxyInventory.id))
            )
            total_proxies = total_result.scalar() or 0

            # Available proxies
            available_result = await session.execute(
                select(func.count(ProxyInventory.id))
                .where(ProxyInventory.is_available == True)
            )
            available_proxies = available_result.scalar() or 0

            # By country
            by_country_result = await session.execute(
                select(
                    ProxyInventory.country,
                    func.count(ProxyInventory.id).label('count')
                )
                .group_by(ProxyInventory.country)
                .order_by(desc('count'))
            )
            by_country = [{"country": row[0], "count": row[1]} for row in by_country_result.all()]

            # Average price
            avg_price_result = await session.execute(
                select(func.avg(ProxyInventory.price_per_hour))
            )
            avg_price = avg_price_result.scalar() or Decimal('0')

            return {
                "total_proxies": total_proxies,
                "available_proxies": available_proxies,
                "by_country": by_country,
                "avg_price": avg_price
            }

        except Exception as e:
            logger.error(f"Error getting proxy stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to get proxy statistics")

