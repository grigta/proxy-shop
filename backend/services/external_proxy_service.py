"""
External Proxy Service

Service layer for integrating external SOCKS5 API with internal inventory.
Handles proxy synchronization, purchasing, and refunds.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete
from fastapi import HTTPException

from backend.core.external_socks_client import get_external_socks_client
from backend.core.config import settings
from backend.models.product import Product
from backend.models.catalog import Catalog
from backend.models.proxy_history import ProxyHistory
from backend.models.user import User
from backend.services.log_service import LogService
from backend.scripts.generate_order_id import generate_unique_order_id

logger = logging.getLogger(__name__)


class ExternalProxyService:
    """Service for managing external SOCKS5 proxy integration."""

    # Marker to identify external proxies in the database
    EXTERNAL_SOURCE_MARKER = "EXTERNAL_API"

    @staticmethod
    async def sync_proxies_to_inventory(
        session: AsyncSession,
        country_code: Optional[str] = None,
        city: Optional[str] = None,
        region: Optional[str] = None,
        page_size: int = 100,
        max_pages: int = 100  # Safety limit to prevent infinite loops
    ) -> Dict[str, Any]:
        """
        Sync proxies from external API to local Product table.

        Fetches ALL available proxies from external API using pagination
        and creates Product records with fixed price ($2.00) for each proxy.

        Args:
            session: Database session
            country_code: Optional country filter
            city: Optional city filter
            region: Optional region filter
            page_size: Number of proxies to fetch per page
            max_pages: Maximum number of pages to fetch (safety limit)

        Returns:
            Dict with sync statistics
        """
        try:
            client = get_external_socks_client()

            # Get or create catalog for external SOCKS5
            catalog = await ExternalProxyService._get_or_create_external_catalog(session)

            # Get existing external products to avoid duplicates (before pagination loop)
            existing_result = await session.execute(
                select(Product).where(
                    and_(
                        Product.catalog_id == catalog.id,
                        Product.line_name == ExternalProxyService.EXTERNAL_SOURCE_MARKER
                    )
                )
            )
            existing_products = existing_result.scalars().all()
            existing_proxy_ids = set()
            for p in existing_products:
                if p.product:
                    # Handle both dict (from JSONB) and string formats
                    product_data = p.product if isinstance(p.product, dict) else json.loads(p.product)
                    proxy_id = product_data.get('proxy_id')
                    if proxy_id:
                        existing_proxy_ids.add(proxy_id)

            logger.info(f"Found {len(existing_proxy_ids)} existing external proxies in inventory")

            # Track statistics
            added_count = 0
            updated_count = 0
            skipped_count = 0
            total_fetched = 0
            total_available = 0

            # Pagination loop - fetch all pages
            current_page = 0
            while current_page < max_pages:
                logger.info(f"Fetching external proxies page {current_page}: country={country_code}, city={city}, region={region}")

                api_response = await client.get_proxies(
                    page=current_page,
                    page_size=page_size,
                    status=1,  # Only online proxies
                    country_code=country_code,
                    city=city,
                    region=region,
                    residential=True,
                    mobile=True,
                    hosting=True
                )

                external_proxies = api_response.get('proxies', [])
                total_available = api_response.get('total', 0)
                total_fetched += len(external_proxies)

                logger.info(f"Page {current_page}: fetched {len(external_proxies)} proxies (total available: {total_available})")

                # If no proxies returned, we've reached the end
                if not external_proxies:
                    logger.info(f"No more proxies on page {current_page}, stopping pagination")
                    break

                # Process each external proxy on this page
                for proxy_data in external_proxies:
                    proxy_id = proxy_data.get('proxy_id')

                    if not proxy_id:
                        logger.warning(f"Skipping proxy without proxy_id: {proxy_data}")
                        skipped_count += 1
                        continue

                    # Check if already exists
                    if proxy_id in existing_proxy_ids:
                        logger.debug(f"Proxy {proxy_id} already exists, skipping")
                        skipped_count += 1
                        continue

                    # Transform external proxy data to internal format
                    product_data = {
                        "proxy_id": proxy_id,
                        "ip": proxy_data.get('proxy_ip'),
                        "country": proxy_data.get('country'),
                        "country_code": proxy_data.get('country_code'),
                        "city": proxy_data.get('city'),
                        "region": proxy_data.get('region'),
                        "region_name": proxy_data.get('region_name'),
                        "zip": proxy_data.get('zip'),
                        "ISP": proxy_data.get('isp'),
                        "ORG": proxy_data.get('org'),
                        "speed": str(proxy_data.get('speed', 0)),
                        "lat": proxy_data.get('lat'),
                        "lon": proxy_data.get('lon'),
                        "mobile": proxy_data.get('mobile', False),
                        "hosting": proxy_data.get('hosting', False),
                        "status": proxy_data.get('status', 1),
                        "price": float(settings.EXTERNAL_SOCKS_PRICE),
                        "source": "external_api",
                        "as_name": proxy_data.get('as_name'),
                        "continent": proxy_data.get('continent'),
                        "continent_code": proxy_data.get('continent_code'),
                    }

                    # Create Product record
                    new_product = Product(
                        catalog_id=catalog.id,
                        pre_lines_name="SOCKS5",
                        line_name=ExternalProxyService.EXTERNAL_SOURCE_MARKER,
                        product=product_data,  # Store as dict, not JSON string - PostgreSQL jsonb will handle it
                        datestamp=datetime.utcnow()
                    )

                    session.add(new_product)
                    existing_proxy_ids.add(proxy_id)  # Track to avoid duplicates within same sync
                    added_count += 1
                    logger.debug(f"Added external proxy {proxy_id} to inventory")

                # Check if we've reached the last page (fewer proxies than page_size)
                # Note: API returns "total" as page count, not total available, so we can't rely on it
                if len(external_proxies) < page_size:
                    logger.info(f"Last page reached (got {len(external_proxies)} < {page_size}), stopping pagination")
                    break

                # Move to next page
                current_page += 1

            # Commit all changes after pagination completes
            await session.commit()

            stats = {
                "total_fetched": total_fetched,
                "total_available_external": total_available,
                "added": added_count,
                "updated": updated_count,
                "skipped": skipped_count,
                "pages_fetched": current_page + 1,
                "sync_time": datetime.utcnow().isoformat()
            }

            logger.info(f"External proxy sync completed: {stats}")
            return stats

        except ConnectionError as e:
            logger.warning(f"External API unavailable during sync: {str(e)}")
            await session.rollback()
            # Return empty stats instead of raising error - allows scheduler to continue
            return {
                "total_fetched": 0,
                "total_available_external": 0,
                "added": 0,
                "updated": 0,
                "skipped": 0,
                "sync_time": datetime.utcnow().isoformat(),
                "error": "External API unavailable"
            }
        except Exception as e:
            logger.error(f"Error syncing external proxies: {str(e)}", exc_info=True)
            await session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to sync external proxies: {str(e)}"
            )

    @staticmethod
    async def purchase_external_proxy(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        ip: Optional[str] = None
    ) -> Tuple[ProxyHistory, Dict[str, Any]]:
        """
        Purchase a proxy from external API.

        Args:
            session: Database session
            user_id: User ID making purchase
            product_id: Internal product ID (from Product table)
            ip: Client IP address for logging

        Returns:
            Tuple of (ProxyHistory record, proxy credentials dict)
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
                raise HTTPException(status_code=404, detail="Product not found")

            # Verify this is an external proxy
            if product.line_name != ExternalProxyService.EXTERNAL_SOURCE_MARKER:
                raise HTTPException(
                    status_code=400,
                    detail="This product is not an external proxy"
                )

            # Parse product data to get external proxy_id
            product_data = product.product if isinstance(product.product, dict) else json.loads(product.product)
            external_proxy_id = product_data.get('proxy_id')

            if not external_proxy_id:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid external proxy data"
                )

            # Check user balance
            price = settings.EXTERNAL_SOCKS_PRICE
            if user.balance < price:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient balance. Required: ${price}, Available: ${user.balance}"
                )

            # Purchase from external API
            logger.info(f"Purchasing external proxy {external_proxy_id} for user {user_id}")
            client = get_external_socks_client()

            try:
                purchase_response = await client.buy_proxy(external_proxy_id)
            except ConnectionError as e:
                # Handle external API connection errors
                logger.error(f"External API unavailable during purchase: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail="Внешний API прокси временно недоступен. Попробуйте позже."
                )
            except ValueError as e:
                # Handle external API errors
                raise HTTPException(status_code=503, detail=str(e))

            # Deduct balance
            user.balance -= price

            # Generate order ID
            order_id = await generate_unique_order_id(session)

            # Calculate expiration (24 hours from now)
            expires_at = datetime.utcnow() + timedelta(hours=settings.SOCKS5_DURATION_HOURS)

            # Prepare proxy credentials for storage
            # NOTE: "ip" uses server_ip (connection address), "exit_ip" stores the residential proxy_ip
            proxy_credentials = {
                "ip": purchase_response.get('server_ip'),  # IP for connection (where port is open)
                "exit_ip": purchase_response.get('proxy_ip'),  # Exit IP (residential IP for reference)
                "port": purchase_response.get('server_listening_port'),
                "login": purchase_response.get('username'),
                "password": purchase_response.get('password'),
                "country": product_data.get('country'),
                "city": product_data.get('city'),
                "region": product_data.get('region'),
                "zip": product_data.get('zip'),
                "ISP": product_data.get('ISP'),
                "ORG": product_data.get('ORG'),
                "speed": product_data.get('speed'),
                "external_credentials_id": purchase_response.get('credentials_id'),
                "external_proxy_id": external_proxy_id,
                "server_ip": purchase_response.get('server_ip'),
                "refundable": purchase_response.get('refundable', True)
            }

            # Create ProxyHistory record
            proxy_history = ProxyHistory(
                user_id=user_id,
                product_id=product_id,
                order_id=order_id,
                quantity=1,
                price=price,
                country=product_data.get('country', 'Unknown'),
                proxies=json.dumps([proxy_credentials]),
                isRefunded=False,
                expires_at=expires_at,
                datestamp=datetime.utcnow()
            )

            session.add(proxy_history)

            # Log purchase
            await LogService.log_purchase(
                session=session,
                user_id=user_id,
                proxy_type="SOCKS5",
                product_id=product_id,
                order_id=order_id,
                quantity=1,
                price=price,
                country=product_data.get('country', 'Unknown'),
                new_balance=user.balance,
                ip=ip
            )

            # Remove product from inventory (sold)
            await session.delete(product)

            # Commit transaction
            await session.commit()
            await session.refresh(proxy_history)

            logger.info(f"Successfully purchased external proxy {external_proxy_id} for user {user_id}, order {order_id}")

            return proxy_history, proxy_credentials

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error purchasing external proxy: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to purchase proxy: {str(e)}"
            )

    @staticmethod
    async def refund_external_proxy(
        session: AsyncSession,
        user_id: int,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Refund an external proxy purchase.

        Args:
            session: Database session
            user_id: User ID requesting refund
            order_id: Order ID to refund

        Returns:
            Dict with refund status
        """
        try:
            # Get proxy history record
            history_result = await session.execute(
                select(ProxyHistory).where(
                    and_(
                        ProxyHistory.order_id == order_id,
                        ProxyHistory.user_id == user_id
                    )
                )
            )
            proxy_history = history_result.scalar_one_or_none()

            if not proxy_history:
                raise HTTPException(
                    status_code=404,
                    detail="Purchase not found"
                )

            # Check if already refunded
            if proxy_history.isRefunded:
                raise HTTPException(
                    status_code=400,
                    detail="This purchase has already been refunded"
                )

            # Parse proxy credentials
            proxies_data = json.loads(proxy_history.proxies)
            if not proxies_data:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid proxy data"
                )

            proxy_creds = proxies_data[0]
            external_credentials_id = proxy_creds.get('external_credentials_id')

            if not external_credentials_id:
                raise HTTPException(
                    status_code=400,
                    detail="This is not an external proxy purchase"
                )

            # Check refund eligibility (1 hour limit)
            purchase_time = proxy_history.datestamp
            time_since_purchase = datetime.utcnow() - purchase_time

            if time_since_purchase > timedelta(hours=1):
                raise HTTPException(
                    status_code=400,
                    detail="Refund period expired (1 hour limit)"
                )

            # Check with external API if refundable
            client = get_external_socks_client()

            try:
                refund_check = await client.check_refundable(external_credentials_id)
                if not refund_check.get('refundable'):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Proxy not refundable: {refund_check.get('message', 'Proxy is still live')}"
                    )

                # Perform refund on external API
                await client.refund_proxy(external_credentials_id)

            except ConnectionError as e:
                logger.error(f"External API unavailable during refund: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail="Внешний API прокси временно недоступен. Невозможно выполнить возврат."
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            # Refund user balance
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                user.balance += proxy_history.price

            # Mark as refunded
            proxy_history.isRefunded = True

            # Log refund
            await LogService.log_refund(
                session=session,
                user_id=user_id,
                product_type="SOCKS5_EXTERNAL",
                amount=proxy_history.price,
                order_id=order_id
            )

            await session.commit()

            logger.info(f"Successfully refunded external proxy order {order_id} for user {user_id}")

            return {
                "status": "success",
                "message": "Proxy refunded successfully",
                "refund_amount": float(proxy_history.price)
            }

        except HTTPException:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error refunding external proxy: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to refund proxy: {str(e)}"
            )

    @staticmethod
    async def get_external_proxies_inventory(
        session: AsyncSession,
        country_code: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get list of available external proxies from local inventory.

        Args:
            session: Database session
            country_code: Optional country filter
            city: Optional city filter
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of external proxy products
        """
        try:
            # Build query
            query = select(Product).where(
                Product.line_name == ExternalProxyService.EXTERNAL_SOURCE_MARKER
            )

            # Apply filters using JSONB queries
            if country_code:
                query = query.where(
                    Product.product.op('->>')('country_code') == country_code
                )

            if city:
                query = query.where(
                    Product.product.op('->>')('city') == city
                )

            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            products = result.scalars().all()

            # Transform to response format
            proxies = []
            for product in products:
                product_data = product.product if isinstance(product.product, dict) else json.loads(product.product)
                proxies.append({
                    "product_id": product.product_id,
                    "proxy_id": product_data.get('proxy_id'),
                    "country": product_data.get('country'),
                    "country_code": product_data.get('country_code'),
                    "city": product_data.get('city'),
                    "region": product_data.get('region'),
                    "zip": product_data.get('zip'),
                    "ISP": product_data.get('ISP'),
                    "speed": product_data.get('speed'),
                    "mobile": product_data.get('mobile'),
                    "hosting": product_data.get('hosting'),
                    "price": product_data.get('price'),
                    "status": product_data.get('status'),
                })

            return proxies

        except Exception as e:
            logger.error(f"Error fetching external proxies inventory: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch proxies: {str(e)}"
            )

    @staticmethod
    async def _get_or_create_external_catalog(session: AsyncSession) -> Catalog:
        """Get or create catalog for external SOCKS5 proxies."""
        result = await session.execute(
            select(Catalog).where(Catalog.ig_catalog == "SOCKS5_EXTERNAL")
        )
        catalog = result.scalar_one_or_none()

        if not catalog:
            catalog = Catalog(
                ig_catalog="SOCKS5_EXTERNAL",
                pre_lines_name="SOCKS5",
                line_name="EXTERNAL",
                price=settings.EXTERNAL_SOCKS_PRICE
            )
            session.add(catalog)
            await session.commit()
            await session.refresh(catalog)
            logger.info("Created SOCKS5_EXTERNAL catalog")

        return catalog

    @staticmethod
    async def cleanup_expired_inventory(session: AsyncSession) -> int:
        """
        Remove external proxies from inventory that are no longer available.
        This should be called periodically by the sync scheduler.

        Returns:
            Number of products removed
        """
        try:
            # Get all external products
            result = await session.execute(
                select(Product).where(
                    Product.line_name == ExternalProxyService.EXTERNAL_SOURCE_MARKER
                )
            )
            products = result.scalars().all()

            client = get_external_socks_client()
            removed_count = 0

            # Check each proxy with external API
            for product in products:
                try:
                    product_data = product.product if isinstance(product.product, dict) else json.loads(product.product)
                    proxy_id = product_data.get('proxy_id')

                    if not proxy_id:
                        continue

                    # Try to lookup proxy in external API
                    try:
                        proxy_info = await client.lookup_proxy(proxy_id)
                        # If status is offline, remove from inventory
                        if proxy_info.get('status') != 1:
                            await session.delete(product)
                            removed_count += 1
                            logger.debug(f"Removed offline proxy {proxy_id} from inventory")
                    except ConnectionError:
                        # If API is unavailable, skip cleanup for this proxy
                        logger.debug(f"Skipping cleanup for proxy {proxy_id} - external API unavailable")
                        continue
                    except Exception:
                        # If lookup fails, proxy might not exist anymore
                        await session.delete(product)
                        removed_count += 1
                        logger.debug(f"Removed unavailable proxy {proxy_id} from inventory")

                except Exception as e:
                    logger.warning(f"Error checking proxy {product.product_id}: {str(e)}")
                    continue

            await session.commit()
            logger.info(f"Cleaned up {removed_count} expired external proxies from inventory")
            return removed_count

        except Exception as e:
            logger.error(f"Error cleaning up inventory: {str(e)}", exc_info=True)
            await session.rollback()
            return 0
