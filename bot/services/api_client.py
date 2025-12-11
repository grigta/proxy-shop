"""Backend API client for bot integration."""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

from bot.core.config import bot_settings
from bot.core.logging_config import get_logger

logger = get_logger(__name__)


# Custom exceptions for better error handling
class APIError(Exception):
    """Base exception for API errors."""
    pass


class APITimeoutError(APIError):
    """Raised when API request times out."""
    pass


class APINetworkError(APIError):
    """Raised when network error occurs."""
    pass


class BackendAPIClient:
    """HTTP client for backend REST API integration."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize API client.
        
        Args:
            base_url: Base URL for API (defaults to bot_settings.BACKEND_API_URL)
        """
        self.base_url = base_url or bot_settings.BACKEND_API_URL
        self._client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client instance."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                follow_redirects=True
            )
        return self._client
    
    def set_access_token(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """Set authentication tokens.
        
        Args:
            access_token: JWT access token
            refresh_token: JWT refresh token
        """
        self._access_token = access_token
        if refresh_token:
            self._refresh_token = refresh_token
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        auth_required: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with automatic token refresh on 401.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            auth_required: Whether auth token is required
            **kwargs: Additional arguments for httpx request

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: On HTTP error
        """
        client = await self._get_client()

        # Add authorization header if token is available
        headers = kwargs.pop("headers", {})
        if auth_required and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        # Log request details for debugging
        params = kwargs.get("params", {})
        if params:
            logger.debug(f"API Request: {method} {endpoint} params={params}")

        try:
            response = await client.request(
                method=method,
                url=endpoint,
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"API request timeout: {method} {endpoint} - {e}")
            raise APITimeoutError(f"Сервер не отвечает. Попробуйте позже.") from e

        except httpx.NetworkError as e:
            logger.error(f"Network error: {method} {endpoint} - {e}")
            raise APINetworkError(f"Ошибка сети. Проверьте подключение.") from e

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and self._refresh_token:
                # Try to refresh token
                logger.info("Access token expired, attempting refresh")
                try:
                    new_tokens = await self.refresh_access_token(self._refresh_token)
                    self.set_access_token(
                        new_tokens["access_token"],
                        new_tokens.get("refresh_token")
                    )

                    # Retry original request
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    response = await client.request(
                        method=method,
                        url=endpoint,
                        headers=headers,
                        **kwargs
                    )
                    response.raise_for_status()
                    return response.json()

                except Exception as refresh_error:
                    logger.error(f"Token refresh failed: {refresh_error}")
                    raise e

            # Log detailed error info
            logger.error(
                f"HTTP error: {method} {endpoint} - "
                f"Status: {e.response.status_code}, "
                f"Response: {e.response.text[:200]}"
            )
            raise
    
    async def close(self) -> None:
        """Close HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # Auth endpoints
    
    async def authenticate_telegram(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        language: str = "ru",
        referral_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate or register user via Telegram ID.
        
        This method handles both new and existing users in a single call.
        For existing users, returns their access code and new tokens.
        For new users, creates account and returns access code and tokens.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            language: User language (ru/en)
            referral_code: Optional referral code
            
        Returns:
            Response with access_token, refresh_token, access_code, is_new_user, etc.
        """
        return await self._make_request(
            "POST",
            "/api/auth/telegram-auth",
            auth_required=False,
            json={
                "telegram_id": telegram_id,
                "username": username,
                "language": language,
                "referral_code": referral_code
            }
        )
    
    async def login_by_access_code(self, access_code: str) -> Dict[str, Any]:
        """Login user by access code.
        
        Args:
            access_code: Access code in format XXX-XXX-XXX
            
        Returns:
            Login response with tokens
        """
        return await self._make_request(
            "POST",
            "/api/auth/login",
            auth_required=False,
            json={
                "access_code": access_code
            }
        )
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New tokens
        """
        return await self._make_request(
            "POST",
            "/api/auth/refresh",
            auth_required=False,
            json={"refresh_token": refresh_token}
        )
    
    async def link_telegram(self, telegram_id: int, username: Optional[str] = None) -> Dict[str, Any]:
        """Link Telegram account to user profile.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            
        Returns:
            Link response
        """
        return await self._make_request(
            "POST",
            "/api/auth/link-telegram",
            json={
                "telegram_id": telegram_id,
                "username": username
            }
        )
    
    # User endpoints
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile.
        
        Returns:
            User profile data
        """
        return await self._make_request("GET", "/api/user/profile")
    
    async def get_user_balance(self) -> Dict[str, Any]:
        """Get user balance.
        
        Returns:
            Balance data
        """
        return await self._make_request("GET", "/api/user/balance")
    
    async def get_user_history(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get user transaction history.

        Args:
            limit: Number of records to return
            offset: Offset for pagination

        Returns:
            History records
        """
        return await self._make_request(
            "GET",
            "/api/user/history",
            params={"limit": limit, "offset": offset}
        )

    async def link_telegram_by_key(
        self,
        access_code: str,
        telegram_id: int,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Link Telegram account to user by access code (for users who registered on website first).

        Args:
            access_code: Access code in format XXX-XXX-XXX
            telegram_id: Telegram user ID to link
            username: Optional Telegram username

        Returns:
            Response with success, message, access_token, refresh_token
        """
        return await self._make_request(
            "POST",
            "/api/user/link-by-key",
            auth_required=False,
            json={
                "access_code": access_code,
                "telegram_id": telegram_id,
                "username": username
            }
        )

    async def add_linked_user(self, telegram_id: int) -> Dict[str, Any]:
        """Add a Telegram ID to the list of linked users for balance sharing.

        Args:
            telegram_id: Telegram ID to add to linked users

        Returns:
            Response with success, message, linked_telegram_ids
        """
        return await self._make_request(
            "POST",
            "/api/user/linked-users/add",
            json={"telegram_id": telegram_id}
        )

    async def remove_linked_user(self, telegram_id: int) -> Dict[str, Any]:
        """Remove a Telegram ID from the list of linked users.

        Args:
            telegram_id: Telegram ID to remove from linked users

        Returns:
            Response with success, message, linked_telegram_ids
        """
        return await self._make_request(
            "POST",
            "/api/user/linked-users/remove",
            json={"telegram_id": telegram_id}
        )

    async def get_linked_users(self) -> Dict[str, Any]:
        """Get list of linked Telegram users.

        Returns:
            Response with telegram_id_owner, linked_telegram_ids, total
        """
        return await self._make_request(
            "GET",
            "/api/user/linked-users"
        )

    # Payment endpoints
    
    async def create_payment_invoice(self, amount_usd: Optional[float] = None) -> Dict[str, Any]:
        """Create Heleket payment invoice with universal payment link (Mode B).
        
        Creates a payment invoice using Heleket's universal payment link system.
        Users select cryptocurrency on Heleket's hosted payment page, not in the bot.
        
        Args:
            amount_usd: Optional deposit amount in USD (defaults to backend's MIN_DEPOSIT_USD if None)
            
        Returns:
            Dict with CreatePaymentResponse fields:
                - payment_url: str - Universal payment link for user
                - payment_uuid: str - Unique payment identifier
                - order_id: str - Order/invoice ID for reference
                - expired_at: Optional[str] - ISO format expiration timestamp
                - amount_usd: float - Invoice amount
                - min_amount_usd: float - Minimum deposit requirement
                
        Example response:
            {
                "payment_url": "https://heleket.com/pay/xxx",
                "payment_uuid": "uuid-xxx",
                "order_id": "INV-12345",
                "expired_at": "2025-11-14T12:00:00Z",
                "amount_usd": 10.0,
                "min_amount_usd": 10.0
            }
        """
        # Build payload with amount_usd only if it's explicitly provided
        payload = {}
        if amount_usd is not None:
            payload["amount_usd"] = str(amount_usd)
        
        return await self._make_request(
            "POST",
            "/api/payment/generate-address",
            json=payload
        )
    
    # Products endpoints
    
    async def get_socks5_products(
        self,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        zip_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Get SOCKS5 proxy products with filters.
        
        Args:
            country: Country code filter
            state: State/region filter
            city: City filter
            zip_code: ZIP code filter
            page: Page number (1-based)
            page_size: Number of records per page
            
        Returns:
            Dict with products, total, page, page_size, has_more, filters
        """
        params = {"page": page, "page_size": page_size}
        if country:
            params["country"] = country
        if state:
            params["state"] = state
        if city:
            params["city"] = city
        if zip_code:
            params["zip_code"] = zip_code
        
        return await self._make_request("GET", "/api/products/socks5", params=params)
    
    async def get_pptp_products(
        self,
        region: Optional[str] = None,
        catalog_id: Optional[int] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        zip_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Get PPTP proxy products with filters.

        Args:
            region: Region (USA/EUROPE)
            catalog_id: Catalog ID filter
            state: State filter
            city: City filter
            zip_code: ZIP code filter
            page: Page number (1-based)
            page_size: Number of records per page

        Returns:
            Dict with products, total, page, page_size, has_more, filters
        """
        params = {"page": page, "page_size": page_size}
        if region:
            params["country"] = region  # Backend expects "country" parameter
        if catalog_id is not None:
            params["catalog_id"] = catalog_id
        if state:
            params["state"] = state
        if city:
            params["city"] = city
        if zip_code:
            params["zip_code"] = zip_code

        return await self._make_request("GET", "/api/products/pptp", params=params)
    
    async def get_available_countries(self, proxy_type: str = "socks5") -> List[str]:
        """Get list of available countries for proxy type.

        Args:
            proxy_type: Type of proxy (socks5/pptp)

        Returns:
            List of country codes
        """
        result = await self._make_request(
            "GET",
            f"/api/products/{proxy_type}/countries"
        )
        return result.get("countries", [])

    async def get_catalogs(self, proxy_type: str = "PPTP") -> Dict[str, Any]:
        """Get list of available catalogs for proxy type.

        Args:
            proxy_type: Type of proxy (PPTP/SOCKS5)

        Returns:
            Dict with catalogs list and total count
        """
        return await self._make_request(
            "GET",
            "/api/products/catalogs",
            params={"proxy_type": proxy_type}
        )

    async def get_available_states(
        self,
        proxy_type: str,
        country: str,
        catalog_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get list of available states for country with proxy counts.

        Args:
            proxy_type: Type of proxy (SOCKS5/PPTP)
            country: Country code
            catalog_id: Optional catalog ID filter (for PPTP)

        Returns:
            List of dicts with state and count: [{"state": "California", "count": 77}, ...]
        """
        params = {"proxy_type": proxy_type}
        if catalog_id is not None:
            params["catalog_id"] = catalog_id

        result = await self._make_request(
            "GET",
            f"/api/products/states/{country}",
            params=params
        )
        # Return full data with counts
        return result if isinstance(result, list) else []

    async def get_available_cities(
        self,
        proxy_type: str,
        country: str,
        state: Optional[str] = None
    ) -> List[str]:
        """Get list of available cities for country and optionally state.

        Args:
            proxy_type: Type of proxy
            country: Country code
            state: Optional state/region name

        Returns:
            List of city names
        """
        params = {"proxy_type": proxy_type}
        if state:
            params["state"] = state

        result = await self._make_request(
            "GET",
            f"/api/products/cities/{country}",
            params=params
        )
        return [item['city'] for item in result if 'city' in item]

    # Purchase endpoints

    async def purchase_socks5(self, product_id: int) -> Dict[str, Any]:
        """Purchase SOCKS5 proxy.
        
        Args:
            product_id: Product ID to purchase
            
        Returns:
            Purchase result
        """
        return await self._make_request(
            "POST",
            "/api/purchase/socks5",
            json={"product_id": product_id}
        )
    
    async def purchase_pptp(
        self,
        region: Optional[str] = None,
        catalog_id: Optional[int] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        zip_code: Optional[str] = None,
        product_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Purchase PPTP proxy.

        Args:
            region: Region (USA/EUROPE) - for filter-based purchase
            catalog_id: Optional catalog ID filter
            state: Optional state filter
            city: Optional city filter
            zip_code: Optional ZIP filter
            product_id: Direct product ID - for direct purchase

        Returns:
            Purchase result
        """
        json_data = {}

        # Direct purchase by product_id takes priority
        if product_id:
            json_data["product_id"] = product_id
        else:
            # Filter-based purchase
            if region:
                json_data["country"] = region
            if catalog_id is not None:
                json_data["catalog_id"] = catalog_id
            if state:
                json_data["state"] = state
            if city:
                json_data["city"] = city
            if zip_code:
                json_data["zip_code"] = zip_code

        return await self._make_request(
            "POST",
            "/api/purchase/pptp",
            json=json_data
        )
    
    async def get_purchase_history(
        self,
        proxy_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get purchase history.
        
        Args:
            proxy_type: Filter by proxy type (socks5/pptp)
            limit: Number of records
            offset: Offset for pagination
            
        Returns:
            Purchase history
        """
        params = {"limit": limit, "offset": offset}
        if proxy_type:
            params["type"] = proxy_type
        
        return await self._make_request("GET", "/api/purchase/history", params=params)
    
    async def validate_proxy(self, proxy_id: int, proxy_type: str) -> Dict[str, Any]:
        """Validate proxy status.
        
        Args:
            proxy_id: Proxy purchase ID
            proxy_type: Type of proxy (socks5/pptp)
            
        Returns:
            Validation result
        """
        return await self._make_request(
            "POST",
            f"/api/purchase/validate/{proxy_id}",
            params={"proxy_type": proxy_type}
        )
    
    async def extend_proxy(self, proxy_id: int, proxy_type: str) -> Dict[str, Any]:
        """Extend proxy subscription.

        Args:
            proxy_id: Proxy purchase ID
            proxy_type: Type of proxy (socks5/pptp)

        Returns:
            Extension result
        """
        return await self._make_request(
            "POST",
            f"/api/purchase/extend/{proxy_id}",
            params={"proxy_type": proxy_type},
            json={}  # ExtendProxyRequest может быть пустым
        )

    async def validate_all_pptp(self) -> Dict[str, Any]:
        """Validate all user's PPTP proxies from last 24 hours.

        Checks each PPTP proxy by connecting to port 1723
        and automatically refunds non-working ones.

        Returns:
            Dict with validation results:
            - validated_count: Total proxies checked
            - valid_count: Working proxies
            - invalid_count: Non-working proxies
            - refunded_amount: Total refunded amount
            - new_balance: User's new balance
            - details: List of per-proxy results
        """
        return await self._make_request(
            "POST",
            "/api/purchase/validate-pptp"
        )

    # External Proxy endpoints

    async def get_external_proxies(
        self,
        country_code: Optional[str] = None,
        city: Optional[str] = None,
        page: int = 0,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Get list of external SOCKS5 proxies.

        Args:
            country_code: Filter by country code
            city: Filter by city
            page: Page number
            page_size: Items per page

        Returns:
            External proxies list response
        """
        params = {"page": page, "page_size": page_size}
        if country_code:
            params["country_code"] = country_code
        if city:
            params["city"] = city

        return await self._make_request(
            "GET",
            "/api/external-proxy/list",
            params=params
        )

    async def purchase_external_proxy(self, product_id: int) -> Dict[str, Any]:
        """Purchase external SOCKS5 proxy.

        Args:
            product_id: Internal product ID to purchase

        Returns:
            Purchase result with credentials
        """
        return await self._make_request(
            "POST",
            "/api/external-proxy/purchase",
            json={"product_id": product_id}
        )

    async def refund_external_proxy(self, order_id: str) -> Dict[str, Any]:
        """Refund external proxy purchase.

        Args:
            order_id: Order ID to refund

        Returns:
            Refund result
        """
        return await self._make_request(
            "POST",
            "/api/external-proxy/refund",
            json={"order_id": order_id}
        )
