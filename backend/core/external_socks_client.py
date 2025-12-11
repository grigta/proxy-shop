"""
External SOCKS API Client

HTTP client for integrating with external SOCKS5 proxy provider API.
Provides methods for fetching, purchasing, and managing proxies from external source.
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

from backend.core.config import settings

logger = logging.getLogger(__name__)


class ExternalSocksAPIClient:
    """
    Client for external SOCKS proxy provider API.

    Base URL: http://91.142.73.7:8080/api/v1/authorized
    Authentication: Bearer token in Authorization header
    """

    def __init__(self):
        self.base_url = settings.EXTERNAL_SOCKS_API_URL.rstrip('/')
        self.api_token = settings.EXTERNAL_SOCKS_API_TOKEN
        self.timeout = settings.EXTERNAL_SOCKS_API_TIMEOUT
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": self.api_token,
                "Content-Type": "application/json"
            }
        )
        logger.info(f"ExternalSocksAPIClient initialized with base URL: {self.base_url}")

    async def get_proxies(
        self,
        page: int = 0,
        page_size: int = 50,
        status: int = 1,  # 1 for online, 0 for offline
        country_code: Optional[str] = None,
        city: Optional[str] = None,
        region: Optional[str] = None,
        zip_code: Optional[str] = None,
        radius: Optional[int] = None,
        residential: bool = True,
        mobile: bool = True,
        hosting: bool = True,
        isp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get filtered proxy table from external API.

        Args:
            page: Page number (0-indexed)
            page_size: Number of proxies per page
            status: Proxy status (1=online, 0=offline)
            country_code: Country code filter (US, UK, etc.)
            city: City filter
            region: Region filter
            zip_code: ZIP code filter
            radius: Radius for US proxies
            residential: Include residential proxies
            mobile: Include mobile proxies
            hosting: Include hosting proxies
            isp: ISP name filter

        Returns:
            Dict with 'proxies' (list) and 'total' (int)
        """
        params = {
            "page": page,
            "page_size": page_size,
            "status": status,
            "residential": residential,
            "mobile": mobile,
            "hosting": hosting
        }

        # Add optional filters
        if country_code:
            params["country_code"] = country_code
        if city:
            params["city"] = city
        if region:
            params["region"] = region
        if zip_code:
            params["zip"] = zip_code
        if radius:
            params["radius"] = radius
        if isp:
            params["isp"] = isp

        try:
            logger.info(f"Fetching proxies from external API: {params}")
            response = await self.client.get(
                f"{self.base_url}/proxy",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Fetched {len(data.get('proxies', []))} proxies, total: {data.get('total', 0)}")
            return data
        except httpx.TimeoutException as e:
            logger.error(f"Timeout connecting to external API: {self.base_url} - {str(e)}")
            raise ConnectionError(f"External API timeout: сервер не отвечает. Проверьте доступность API.")
        except httpx.ConnectTimeout as e:
            logger.error(f"Connection timeout to external API: {self.base_url} - {str(e)}")
            raise ConnectionError(f"External API connection timeout: не удается подключиться к серверу.")
        except httpx.NetworkError as e:
            logger.error(f"Network error connecting to external API: {self.base_url} - {str(e)}")
            raise ConnectionError(f"External API network error: ошибка сети при подключении к API.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching proxies: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error fetching proxies from external API: {str(e)}")
            raise

    async def buy_proxy(self, proxy_id: int) -> Dict[str, Any]:
        """
        Purchase a proxy from external API.

        Args:
            proxy_id: The ID of the proxy to purchase

        Returns:
            Dict with proxy credentials and details:
            - credentials_id: int
            - proxy_id: int
            - proxy_ip: str
            - server_ip: str
            - server_listening_port: str
            - username: str
            - password: str
            - price: float
            - expiration_time: str
            - refundable: bool
        """
        try:
            logger.info(f"Purchasing proxy {proxy_id} from external API")
            response = await self.client.get(
                f"{self.base_url}/proxy/buy",
                params={"proxy_id": proxy_id}
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully purchased proxy {proxy_id}, credentials_id: {data.get('credentials_id')}")
            return data
        except httpx.TimeoutException as e:
            logger.error(f"Timeout purchasing proxy {proxy_id} from external API: {str(e)}")
            raise ConnectionError(f"External API timeout: сервер не отвечает при покупке прокси.")
        except httpx.ConnectTimeout as e:
            logger.error(f"Connection timeout purchasing proxy {proxy_id}: {str(e)}")
            raise ConnectionError(f"External API connection timeout: не удается подключиться к серверу.")
        except httpx.NetworkError as e:
            logger.error(f"Network error purchasing proxy {proxy_id}: {str(e)}")
            raise ConnectionError(f"External API network error: ошибка сети при покупке прокси.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error purchasing proxy {proxy_id}: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 403:
                raise ValueError("Insufficient balance on external API")
            elif e.response.status_code == 503:
                raise ValueError("Remote proxy server error")
            raise
        except Exception as e:
            logger.error(f"Error purchasing proxy {proxy_id}: {str(e)}")
            raise

    async def get_bought_proxies(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of proxies bought from external API.

        Args:
            page: Optional page number for pagination
            page_size: Optional page size for pagination

        Returns:
            List of bought proxies with credentials and geo data
        """
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size

        try:
            logger.info(f"Fetching bought proxies from external API")
            response = await self.client.get(
                f"{self.base_url}/proxy/bought",
                params=params if params else None
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Fetched {len(data)} bought proxies")
            return data
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching bought proxies from external API: {str(e)}")
            raise ConnectionError(f"External API timeout: сервер не отвечает.")
        except httpx.ConnectTimeout as e:
            logger.error(f"Connection timeout fetching bought proxies: {str(e)}")
            raise ConnectionError(f"External API connection timeout: не удается подключиться к серверу.")
        except httpx.NetworkError as e:
            logger.error(f"Network error fetching bought proxies: {str(e)}")
            raise ConnectionError(f"External API network error: ошибка сети.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching bought proxies: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error fetching bought proxies: {str(e)}")
            raise

    async def lookup_proxy(self, proxy_id: int) -> Dict[str, Any]:
        """
        Lookup detailed information about a specific proxy.

        Args:
            proxy_id: The proxy ID to lookup

        Returns:
            Dict with detailed proxy information including geo data
        """
        try:
            logger.info(f"Looking up proxy {proxy_id}")
            response = await self.client.get(
                f"{self.base_url}/proxy/lookup",
                params={"proxy_id": proxy_id}
            )
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.TimeoutException as e:
            logger.error(f"Timeout looking up proxy {proxy_id}: {str(e)}")
            raise ConnectionError(f"External API timeout: сервер не отвечает.")
        except httpx.ConnectTimeout as e:
            logger.error(f"Connection timeout looking up proxy {proxy_id}: {str(e)}")
            raise ConnectionError(f"External API connection timeout: не удается подключиться к серверу.")
        except httpx.NetworkError as e:
            logger.error(f"Network error looking up proxy {proxy_id}: {str(e)}")
            raise ConnectionError(f"External API network error: ошибка сети.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error looking up proxy {proxy_id}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error looking up proxy {proxy_id}: {str(e)}")
            raise

    async def check_refundable(self, credentials_id: int) -> Dict[str, Any]:
        """
        Check if a proxy is refundable.

        Args:
            credentials_id: The credentials ID to check

        Returns:
            Dict with refundable status and message
        """
        try:
            logger.info(f"Checking if credentials {credentials_id} is refundable")
            response = await self.client.post(
                f"{self.base_url}/proxy/check-refundable",
                json={"credentials_id": credentials_id}
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Credentials {credentials_id} refundable: {data.get('refundable')}")
            return data
        except httpx.TimeoutException as e:
            logger.error(f"Timeout checking refundable status for credentials {credentials_id}: {str(e)}")
            raise ConnectionError(f"External API timeout: сервер не отвечает.")
        except httpx.ConnectTimeout as e:
            logger.error(f"Connection timeout checking refundable status: {str(e)}")
            raise ConnectionError(f"External API connection timeout: не удается подключиться к серверу.")
        except httpx.NetworkError as e:
            logger.error(f"Network error checking refundable status: {str(e)}")
            raise ConnectionError(f"External API network error: ошибка сети.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error checking refundable status: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error checking refundable status: {str(e)}")
            raise

    async def refund_proxy(self, credentials_id: int) -> Dict[str, Any]:
        """
        Refund a proxy purchase.

        Args:
            credentials_id: The credentials ID to refund

        Returns:
            Dict with refund status
        """
        try:
            logger.info(f"Refunding proxy with credentials_id {credentials_id}")
            response = await self.client.post(
                f"{self.base_url}/proxy/refund",
                json={"credentials_id": credentials_id}
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully refunded credentials {credentials_id}")
            return data
        except httpx.TimeoutException as e:
            logger.error(f"Timeout refunding proxy with credentials_id {credentials_id}: {str(e)}")
            raise ConnectionError(f"External API timeout: сервер не отвечает при возврате прокси.")
        except httpx.ConnectTimeout as e:
            logger.error(f"Connection timeout refunding proxy: {str(e)}")
            raise ConnectionError(f"External API connection timeout: не удается подключиться к серверу.")
        except httpx.NetworkError as e:
            logger.error(f"Network error refunding proxy: {str(e)}")
            raise ConnectionError(f"External API network error: ошибка сети при возврате прокси.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error refunding proxy: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 400:
                raise ValueError("Proxy not refundable or is still live")
            raise
        except Exception as e:
            logger.error(f"Error refunding proxy: {str(e)}")
            raise

    async def get_credentials(self, credentials_id: int) -> Dict[str, Any]:
        """
        Get proxy credentials by credentials ID.

        Args:
            credentials_id: The credentials ID

        Returns:
            Dict with proxy credentials
        """
        try:
            logger.info(f"Fetching credentials {credentials_id}")
            response = await self.client.get(
                f"{self.base_url}/proxy/credentials",
                params={"credentials_id": credentials_id}
            )
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching credentials {credentials_id}: {str(e)}")
            raise ConnectionError(f"External API timeout: сервер не отвечает.")
        except httpx.ConnectTimeout as e:
            logger.error(f"Connection timeout fetching credentials: {str(e)}")
            raise ConnectionError(f"External API connection timeout: не удается подключиться к серверу.")
        except httpx.NetworkError as e:
            logger.error(f"Network error fetching credentials: {str(e)}")
            raise ConnectionError(f"External API network error: ошибка сети.")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching credentials: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error fetching credentials: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.info("ExternalSocksAPIClient closed")


# Singleton instance
_external_socks_client: Optional[ExternalSocksAPIClient] = None


def get_external_socks_client() -> ExternalSocksAPIClient:
    """Get the global ExternalSocksAPIClient instance."""
    global _external_socks_client
    if _external_socks_client is None:
        raise RuntimeError("ExternalSocksAPIClient not initialized. Call initialize_external_socks_client() first.")
    return _external_socks_client


async def initialize_external_socks_client():
    """Initialize the global ExternalSocksAPIClient instance."""
    global _external_socks_client
    _external_socks_client = ExternalSocksAPIClient()
    logger.info("Global ExternalSocksAPIClient initialized")


async def close_external_socks_client():
    """Close the global ExternalSocksAPIClient instance."""
    global _external_socks_client
    if _external_socks_client:
        await _external_socks_client.close()
        _external_socks_client = None
        logger.info("Global ExternalSocksAPIClient closed")
