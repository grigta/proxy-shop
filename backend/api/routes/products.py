from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_async_session
from backend.schemas.products import (
    ProxyItem,
    ProductsListResponse,
    CountryListItem,
    StateListItem
)
from backend.services.product_service import ProductService
from backend.api.dependencies import get_current_user_optional
from backend.models.user import User
from backend.core.utils import parse_proxy_json, convert_speed_to_category
from typing import Optional, List
import logging
import json


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "/socks5",
    response_model=ProductsListResponse,
    summary="Get SOCKS5 proxies",
    description="Get filtered list of SOCKS5 proxies with pagination"
)
async def get_socks5_proxies(
    country: str = Query(..., description="Country filter (required)"),
    state: Optional[str] = Query(None, description="State/Region filter"),
    city: Optional[str] = Query(None, description="City filter"),
    zip_code: Optional[str] = Query(None, alias="zip", description="ZIP code filter"),
    random: bool = Query(False, description="Get random proxy from filtered results"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page (max 50)"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get filtered list of SOCKS5 proxies."""
    try:
        # Get filtered products
        products, total, filters = await ProductService.get_products_filtered(
            session=session,
            proxy_type="SOCKS5",
            country=country,
            state=state,
            city=city,
            zip_code=zip_code,
            random=random,
            page=page,
            page_size=page_size
        )

        # Get price from catalog
        price = await ProductService.get_catalog_price(session, "SOCKS5")

        # Convert Product objects to ProxyItem schemas
        proxy_items = []
        for product in products:
            # Parse JSONB data
            product_data = parse_proxy_json(product.product) if isinstance(product.product, str) else product.product

            proxy_item = ProxyItem(
                product_id=product.product_id,
                ip=product_data.get("ip", ""),
                port=product_data.get("port"),
                login=product_data.get("login"),
                password=product_data.get("password"),
                country=product_data.get("country", ""),
                # Use region_name for full region/state name, fallback to state for US proxies
                state=product_data.get("region_name") or product_data.get("state"),
                city=product_data.get("city"),
                zip=product_data.get("zip"),
                ISP=product_data.get("ISP"),
                ORG=product_data.get("ORG"),
                speed=convert_speed_to_category(product_data.get("speed")),
                price=price,
                datestamp=product.datestamp
            )
            proxy_items.append(proxy_item)

        # Calculate has_more
        has_more = (page * page_size) < total

        return ProductsListResponse(
            products=proxy_items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
            filters=filters
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SOCKS5 proxies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve SOCKS5 proxies: {str(e)}"
        )


@router.get(
    "/pptp",
    response_model=ProductsListResponse,
    summary="Get PPTP proxies",
    description="Get filtered list of PPTP proxies with pagination"
)
async def get_pptp_proxies(
    country: str = Query(..., description="Country filter (required)"),
    catalog_id: Optional[int] = Query(None, description="Catalog ID filter"),
    state: Optional[str] = Query(None, description="State/Region filter"),
    city: Optional[str] = Query(None, description="City filter"),
    zip_code: Optional[str] = Query(None, alias="zip", description="ZIP code filter"),
    random: bool = Query(False, description="Get random proxy from filtered results"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page (max 50)"),
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get filtered list of PPTP proxies."""
    try:
        # Get filtered products
        products, total, filters = await ProductService.get_products_filtered(
            session=session,
            proxy_type="PPTP",
            country=country,
            state=state,
            city=city,
            zip_code=zip_code,
            catalog_id=catalog_id,
            random=random,
            page=page,
            page_size=page_size
        )

        # Get price from catalog (specific catalog if catalog_id provided, otherwise default)
        if catalog_id:
            price = await ProductService.get_catalog_price_by_id(session, catalog_id)
        else:
            price = await ProductService.get_catalog_price(session, "PPTP")

        # Convert Product objects to ProxyItem schemas
        proxy_items = []
        for product in products:
            # Parse JSONB data
            product_data = parse_proxy_json(product.product) if isinstance(product.product, str) else product.product

            proxy_item = ProxyItem(
                product_id=product.product_id,
                ip=product_data.get("ip", ""),
                port=None,  # PPTP doesn't have port
                login=product_data.get("login"),
                password=product_data.get("password"),
                country=product_data.get("country", ""),
                # Use region_name for full region/state name, fallback to state for US proxies
                state=product_data.get("region_name") or product_data.get("state"),
                city=product_data.get("city"),
                zip=product_data.get("zip"),
                ISP=product_data.get("ISP"),
                ORG=product_data.get("ORG"),
                speed=convert_speed_to_category(product_data.get("speed")),
                price=price,
                datestamp=product.datestamp
            )
            proxy_items.append(proxy_item)

        # Calculate has_more
        has_more = (page * page_size) < total

        return ProductsListResponse(
            products=proxy_items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
            filters=filters
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PPTP proxies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve PPTP proxies: {str(e)}"
        )


@router.get(
    "/countries",
    summary="Get available countries",
    description="Get list of countries with available proxies"
)
async def get_available_countries(
    proxy_type: str = Query("SOCKS5", description="Proxy type (SOCKS5/PPTP)"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get list of countries with available proxies."""
    try:
        countries = await ProductService.get_available_countries(session, proxy_type)

        # Map country names to codes and flags
        country_map = {
            "Albania": ("AL", "🇦🇱"),
            "Argentina": ("AR", "🇦🇷"),
            "Australia": ("AU", "🇦🇺"),
            "Austria": ("AT", "🇦🇹"),
            "Bangladesh": ("BD", "🇧🇩"),
            "Barbados": ("BB", "🇧🇧"),
            "Belgium": ("BE", "🇧🇪"),
            "Brazil": ("BR", "🇧🇷"),
            "Bulgaria": ("BG", "🇧🇬"),
            "Canada": ("CA", "🇨🇦"),
            "China": ("CN", "🇨🇳"),
            "Colombia": ("CO", "🇨🇴"),
            "Croatia": ("HR", "🇭🇷"),
            "Czechia": ("CZ", "🇨🇿"),
            "Denmark": ("DK", "🇩🇰"),
            "Ecuador": ("EC", "🇪🇨"),
            "Egypt": ("EG", "🇪🇬"),
            "El Salvador": ("SV", "🇸🇻"),
            "Ethiopia": ("ET", "🇪🇹"),
            "France": ("FR", "🇫🇷"),
            "Georgia": ("GE", "🇬🇪"),
            "Germany": ("DE", "🇩🇪"),
            "Greece": ("GR", "🇬🇷"),
            "Honduras": ("HN", "🇭🇳"),
            "Hungary": ("HU", "🇭🇺"),
            "India": ("IN", "🇮🇳"),
            "Indonesia": ("ID", "🇮🇩"),
            "Iran": ("IR", "🇮🇷"),
            "Iraq": ("IQ", "🇮🇶"),
            "Israel": ("IL", "🇮🇱"),
            "Italy": ("IT", "🇮🇹"),
            "Japan": ("JP", "🇯🇵"),
            "Kenya": ("KE", "🇰🇪"),
            "Kuwait": ("KW", "🇰🇼"),
            "Latvia": ("LV", "🇱🇻"),
            "Lebanon": ("LB", "🇱🇧"),
            "Lithuania": ("LT", "🇱🇹"),
            "Mali": ("ML", "🇲🇱"),
            "Mexico": ("MX", "🇲🇽"),
            "Moldova": ("MD", "🇲🇩"),
            "Morocco": ("MA", "🇲🇦"),
            "Netherlands": ("NL", "🇳🇱"),
            "The Netherlands": ("NL", "🇳🇱"),
            "Nicaragua": ("NI", "🇳🇮"),
            "Norway": ("NO", "🇳🇴"),
            "Pakistan": ("PK", "🇵🇰"),
            "Palestine": ("PS", "🇵🇸"),
            "Paraguay": ("PY", "🇵🇾"),
            "Peru": ("PE", "🇵🇪"),
            "Philippines": ("PH", "🇵🇭"),
            "Portugal": ("PT", "🇵🇹"),
            "Qatar": ("QA", "🇶🇦"),
            "Romania": ("RO", "🇷🇴"),
            "Russia": ("RU", "🇷🇺"),
            "Rwanda": ("RW", "🇷🇼"),
            "Saudi Arabia": ("SA", "🇸🇦"),
            "Serbia": ("RS", "🇷🇸"),
            "Singapore": ("SG", "🇸🇬"),
            "Slovakia": ("SK", "🇸🇰"),
            "South Africa": ("ZA", "🇿🇦"),
            "Spain": ("ES", "🇪🇸"),
            "Switzerland": ("CH", "🇨🇭"),
            "Taiwan": ("TW", "🇹🇼"),
            "Tanzania": ("TZ", "🇹🇿"),
            "Thailand": ("TH", "🇹🇭"),
            "Türkiye": ("TR", "🇹🇷"),
            "Turkey": ("TR", "🇹🇷"),
            "Ukraine": ("UA", "🇺🇦"),
            "United Kingdom": ("GB", "🇬🇧"),
            "United States": ("US", "🇺🇸"),
            "Venezuela": ("VE", "🇻🇪"),
            "Vietnam": ("VN", "🇻🇳"),
        }

        result = []
        for country_data in countries:
            country_name = country_data["country"]
            code, flag = country_map.get(country_name, ("", "🏳️"))

            result.append({
                "country": country_name,
                "country_code": code,
                "flag": flag,
                "available_count": country_data["count"]
            })

        return result

    except Exception as e:
        logger.error(f"Error getting countries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve countries: {str(e)}"
        )


@router.get(
    "/states/{country}",
    summary="Get available states",
    description="Get list of states/regions for a country"
)
async def get_available_states(
    country: str,
    proxy_type: str = Query("SOCKS5", description="Proxy type"),
    catalog_id: Optional[int] = Query(None, description="Catalog ID filter (for PPTP)"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get list of states/regions for a country."""
    try:
        states = await ProductService.get_available_states(
            session, proxy_type, country, catalog_id=catalog_id
        )

        result = []
        for state_data in states:
            result.append({
                "state": state_data["state"],
                "count": state_data["count"]
            })

        return result

    except Exception as e:
        logger.error(f"Error getting states: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve states: {str(e)}"
        )


@router.get(
    "/cities/{country}",
    summary="Get available cities",
    description="Get list of cities for a country and optionally state"
)
async def get_available_cities(
    country: str,
    proxy_type: str = Query("SOCKS5", description="Proxy type"),
    state: Optional[str] = Query(None, description="State/region name"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get list of cities for a country and optionally state."""
    try:
        cities = await ProductService.get_available_cities(session, proxy_type, country, state)

        result = []
        for city_data in cities:
            result.append({
                "city": city_data["city"],
                "available_count": city_data["count"]
            })

        return result

    except Exception as e:
        logger.error(f"Error getting cities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cities: {str(e)}"
        )


@router.get(
    "/catalogs",
    summary="Get available catalogs",
    description="Get list of catalogs for proxy type (public endpoint for bot)"
)
async def get_catalogs(
    proxy_type: str = Query("PPTP", description="Proxy type (PPTP or SOCKS5)"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get list of catalogs for proxy type."""
    try:
        from backend.models.catalog import Catalog
        from sqlalchemy import select, func
        from backend.models.product import Product

        # Get catalogs with product counts
        result = await session.execute(
            select(
                Catalog.id,
                Catalog.line_name,
                Catalog.price,
                Catalog.ig_catalog,
                func.count(Product.product_id).label('product_count')
            )
            .outerjoin(Product, Catalog.id == Product.catalog_id)
            .where(Catalog.pre_lines_name == proxy_type.upper())
            .group_by(Catalog.id, Catalog.line_name, Catalog.price, Catalog.ig_catalog)
            .order_by(Catalog.line_name)
        )

        catalogs_data = result.all()

        catalogs = []
        for catalog_row in catalogs_data:
            catalogs.append({
                "id": catalog_row.id,
                "name": catalog_row.line_name,
                "price": float(catalog_row.price),
                "ig_catalog": catalog_row.ig_catalog,
                "proxy_type": proxy_type.upper(),
                "product_count": catalog_row.product_count
            })

        return {
            "catalogs": catalogs,
            "total": len(catalogs)
        }

    except Exception as e:
        logger.error(f"Error getting catalogs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve catalogs: {str(e)}"
        )