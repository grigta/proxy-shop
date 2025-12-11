from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String, Integer, and_, or_, text
from backend.models.product import Product
from backend.models.catalog import Catalog
from backend.models.environment_variable import EnvironmentVariable
from backend.core.utils import normalize_country
from fastapi import HTTPException
from typing import Optional, List, Tuple, Dict, Any
from decimal import Decimal
import logging


logger = logging.getLogger(__name__)


class ProductService:
    """Service for managing products catalog and filtering."""

    @staticmethod
    async def get_products_filtered(
        session: AsyncSession,
        proxy_type: str,
        country: str,
        state: Optional[str] = None,
        city: Optional[str] = None,
        zip_code: Optional[str] = None,
        catalog_id: Optional[int] = None,
        random: bool = False,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Product], int, Dict[str, Optional[str]]]:
        """
        Get filtered list of proxies with pagination.

        Args:
            session: Database session
            proxy_type: Type of proxy (SOCKS5/PPTP)
            country: Country filter (required)
            state: State/region filter (optional)
            city: City filter (optional)
            zip_code: ZIP code filter (optional)
            catalog_id: Catalog ID filter (optional)
            random: Return random proxy if True
            page: Page number (1-based)
            page_size: Items per page (default 10)

        Returns:
            Tuple of (products list, total count, applied filters)

        Raises:
            HTTPException: If query fails
        """
        try:
            # Build base query
            query = select(Product).where(Product.pre_lines_name == proxy_type)

            # Apply catalog filter if provided
            if catalog_id is not None:
                query = query.where(Product.catalog_id == catalog_id)

            # Check if filtering by region (Europe, USA) or by specific country
            normalized_country = None
            if country.upper() in ["EUROPE", "USA"]:
                # Filter by region field in JSONB
                region = country.upper()
                logger.debug(f"Filtering by region: {region}")
                query = query.where(Product.product.contains({"region": region}))
                normalized_country = region  # For response filters
            else:
                # Normalize country to full name (supports both codes and full names)
                normalized_country = normalize_country(country)
                logger.debug(f"Country filter: input='{country}' -> normalized='{normalized_country}'")

                # Apply country filter using JSONB contains
                query = query.where(Product.product.contains({"country": normalized_country}))

            # Apply state filter if provided
            if state:
                # Case insensitive match on 'state' field OR 'region_name' field
                query = query.where(
                    or_(
                        cast(Product.product["state"].astext, String).ilike(state),
                        cast(Product.product["region_name"].astext, String).ilike(state)
                    )
                )

            # Apply city filter if provided
            if city:
                query = query.where(cast(Product.product["city"].astext, String).ilike(city))

            # Apply ZIP filter if provided (range ±100)
            if zip_code:
                try:
                    # Try to parse as integer for range search
                    zip_int = int(zip_code)
                    zip_min = zip_int - 100
                    zip_max = zip_int + 100

                    # Query using BETWEEN for ZIP range
                    # Cast ZIP to integer for comparison (filter out non-numeric ZIPs)
                    query = query.where(
                        and_(
                            text("(product->>'zip') ~ '^[0-9]+$'"),
                            cast(Product.product["zip"].astext, Integer) >= zip_min,
                            cast(Product.product["zip"].astext, Integer) <= zip_max
                        )
                    )
                except (ValueError, TypeError):
                    # If not a valid integer, fall back to exact match
                    query = query.where(cast(Product.product["zip"].astext, String).ilike(zip_code))

            # If random selection requested
            if random:
                query = query.order_by(func.random()).limit(1)
                result = await session.execute(query)
                products = list(result.scalars().all())
                total = 1 if products else 0
            else:
                # Count total for pagination
                count_query = select(func.count()).select_from(query.subquery())
                total_result = await session.execute(count_query)
                total = total_result.scalar() or 0

                # Apply pagination
                query = query.order_by(Product.datestamp.desc())
                query = query.offset((page - 1) * page_size).limit(page_size)

                result = await session.execute(query)
                products = list(result.scalars().all())

            # Prepare applied filters
            filters = {
                "country": normalized_country,
                "state": state,
                "city": city,
                "zip": zip_code
            }

            logger.info(f"Found {len(products)} {proxy_type} products (total: {total}) with filters: {filters}")

            return products, total, filters

        except Exception as e:
            logger.error(f"Error filtering products: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve products: {str(e)}"
            )

    @staticmethod
    async def get_product_by_id(session: AsyncSession, product_id: int) -> Optional[Product]:
        """
        Get product by ID.

        Args:
            session: Database session
            product_id: Product ID

        Returns:
            Product or None if not found
        """
        try:
            result = await session.execute(
                select(Product).where(Product.product_id == product_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting product {product_id}: {str(e)}")
            return None

    @staticmethod
    async def get_available_countries(
        session: AsyncSession,
        proxy_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of available countries for proxy type.

        Args:
            session: Database session
            proxy_type: Type of proxy (SOCKS5/PPTP)

        Returns:
            List of countries with available count
        """
        try:
            # Query to group by country from JSONB field
            query = select(
                cast(Product.product["country"].astext, String).label("country"),
                func.count(Product.product_id).label("count")
            ).where(
                Product.pre_lines_name == proxy_type
            ).group_by(
                "country"
            ).order_by(
                "country"
            )

            result = await session.execute(query)
            countries = []

            for row in result:
                countries.append({
                    "country": row.country,
                    "count": row.count
                })

            logger.info(f"Found {len(countries)} countries for {proxy_type}")
            return countries

        except Exception as e:
            logger.error(f"Error getting countries: {str(e)}")
            return []

    @staticmethod
    async def get_available_states(
        session: AsyncSession,
        proxy_type: str,
        country: str,
        catalog_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of available states for country.

        Args:
            session: Database session
            proxy_type: Type of proxy (SOCKS5/PPTP)
            country: Country name or code
            catalog_id: Optional catalog ID filter (for PPTP)

        Returns:
            List of states with available count
        """
        try:
            # Normalize country to full name (supports both codes and full names)
            normalized_country = normalize_country(country)
            logger.debug(f"Getting states: country input='{country}' -> normalized='{normalized_country}', catalog_id={catalog_id}")

            # Build conditions
            conditions = [
                Product.pre_lines_name == proxy_type,
                Product.product.contains({"country": normalized_country})
            ]

            # Add catalog_id filter if provided
            if catalog_id is not None:
                conditions.append(Product.catalog_id == catalog_id)

            # Query to group by state from JSONB field (coalesce state and region_name)
            query = select(
                func.coalesce(
                    cast(Product.product["state"].astext, String),
                    cast(Product.product["region_name"].astext, String)
                ).label("state"),
                func.count(Product.product_id).label("count")
            ).where(
                and_(*conditions)
            ).group_by(
                "state"
            ).order_by(
                "state"
            )

            result = await session.execute(query)
            states = []

            for row in result:
                if row.state:  # Skip null states
                    states.append({
                        "state": row.state,
                        "count": row.count
                    })

            logger.info(f"Found {len(states)} states for {country} (catalog_id={catalog_id})")
            return states

        except Exception as e:
            logger.error(f"Error getting states: {str(e)}")
            return []

    @staticmethod
    async def get_available_cities(
        session: AsyncSession,
        proxy_type: str,
        country: str,
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of available cities for country and optionally state.

        Args:
            session: Database session
            proxy_type: Type of proxy (SOCKS5/PPTP)
            country: Country name or code
            state: Optional state/region name

        Returns:
            List of cities with available count
        """
        try:
            # Normalize country to full name
            normalized_country = normalize_country(country)
            logger.debug(f"Getting cities: country='{normalized_country}', state='{state}'")

            # Build query conditions
            conditions = [
                Product.pre_lines_name == proxy_type,
                Product.product.contains({"country": normalized_country})
            ]

            # Add state filter if provided
            if state:
                conditions.append(
                    or_(
                        cast(Product.product["state"].astext, String).ilike(state),
                        cast(Product.product["region_name"].astext, String).ilike(state)
                    )
                )

            # Query to group by city from JSONB field
            query = select(
                cast(Product.product["city"].astext, String).label("city"),
                func.count(Product.product_id).label("count")
            ).where(
                and_(*conditions)
            ).group_by(
                "city"
            ).order_by(
                "city"
            )

            result = await session.execute(query)
            cities = []

            for row in result:
                if row.city:  # Skip null cities
                    cities.append({
                        "city": row.city,
                        "count": row.count
                    })

            logger.info(f"Found {len(cities)} cities for {country}" + (f", {state}" if state else ""))
            return cities

        except Exception as e:
            logger.error(f"Error getting cities: {str(e)}")
            return []

    @staticmethod
    async def get_catalog_price(session: AsyncSession, proxy_type: str) -> Decimal:
        """
        Get price from catalog for proxy type.

        Args:
            session: Database session
            proxy_type: Type of proxy (SOCKS5/PPTP)

        Returns:
            Price as Decimal

        Raises:
            HTTPException: If price not found
        """
        try:
            # First try to get from Catalog table
            result = await session.execute(
                select(Catalog).where(Catalog.pre_lines_name == proxy_type)
            )
            catalog = result.scalar_one_or_none()

            if catalog and catalog.price:
                return Decimal(str(catalog.price))

            # If not in catalog, get from environment_variables
            env_var_name = f"{proxy_type}_PRICE_USD"
            result = await session.execute(
                select(EnvironmentVariable).where(EnvironmentVariable.name == env_var_name)
            )
            env_var = result.scalar_one_or_none()

            if env_var and env_var.data:
                return Decimal(str(env_var.data))

            # Default prices if not found
            default_prices = {
                "SOCKS5": Decimal("2.00"),
                "PPTP": Decimal("5.00")
            }

            if proxy_type in default_prices:
                return default_prices[proxy_type]

            raise HTTPException(
                status_code=404,
                detail=f"Price not found for {proxy_type}"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting price for {proxy_type}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve price: {str(e)}"
            )

    @staticmethod
    async def get_catalog_price_by_id(session: AsyncSession, catalog_id: int) -> Decimal:
        """
        Get price from specific catalog by ID.

        Args:
            session: Database session
            catalog_id: Catalog ID

        Returns:
            Price as Decimal

        Raises:
            HTTPException: If catalog or price not found
        """
        try:
            result = await session.execute(
                select(Catalog).where(Catalog.id == catalog_id)
            )
            catalog = result.scalar_one_or_none()

            if not catalog:
                raise HTTPException(
                    status_code=404,
                    detail=f"Catalog {catalog_id} not found"
                )

            if not catalog.price:
                raise HTTPException(
                    status_code=404,
                    detail=f"Price not set for catalog {catalog_id}"
                )

            return Decimal(str(catalog.price))

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting price for catalog {catalog_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve catalog price: {str(e)}"
            )
