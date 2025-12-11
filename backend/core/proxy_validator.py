import aiohttp
from aiohttp import ClientTimeout, ClientSession
from aiohttp_socks import ProxyConnector
import asyncio
import subprocess
import time
import logging
from typing import Optional, Dict, Any, List
from backend.core.config import settings


logger = logging.getLogger(__name__)


class ProxyValidator:
    """Service for validating proxy server status and connectivity."""

    async def check_socks5_proxy(
        self,
        ip: str,
        port: int,
        login: str,
        password: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Check if SOCKS5 proxy is online and working.

        Args:
            ip: Proxy IP address
            port: Proxy port number
            login: Authentication username
            password: Authentication password
            timeout: Check timeout in seconds (default from settings)

        Returns:
            Dict with validation results:
            {
                "online": bool,  # True if proxy is working
                "latency_ms": float,  # Response time in milliseconds
                "exit_ip": str,  # Exit IP address of proxy
                "status_code": int,  # HTTP status code
                "error": str | None  # Error description if any
            }
        """
        timeout = timeout or settings.PROXY_CHECK_TIMEOUT

        # Format proxy URL with credentials (use socks5h for remote DNS resolution)
        proxy_url = f"socks5h://{login}:{password}@{ip}:{port}"

        try:
            # Create proxy connector
            connector = ProxyConnector.from_url(proxy_url)

            # Setup timeout
            client_timeout = ClientTimeout(total=timeout)

            # Measure request time
            start_time = time.time()

            async with ClientSession(
                connector=connector,
                timeout=client_timeout
            ) as session:
                # Perform test request
                async with session.get(settings.PROXY_CHECK_URL) as response:
                    latency_ms = (time.time() - start_time) * 1000

                    # Check status code
                    if response.status != 200:
                        logger.warning(f"SOCKS5 proxy {ip}:{port} returned status {response.status}")
                        return {
                            "online": False,
                            "latency_ms": latency_ms,
                            "exit_ip": None,
                            "status_code": response.status,
                            "error": f"HTTP status {response.status}"
                        }

                    # Try to parse JSON response
                    try:
                        data = await response.json()
                        exit_ip = data.get("origin", ip)
                    except Exception:
                        # If can't parse JSON, still consider proxy working
                        exit_ip = ip

                    logger.info(f"SOCKS5 proxy {ip}:{port} is online (latency: {latency_ms:.0f}ms)")

                    return {
                        "online": True,
                        "latency_ms": latency_ms,
                        "exit_ip": exit_ip,
                        "status_code": response.status,
                        "error": None
                    }

        except asyncio.TimeoutError:
            logger.warning(f"SOCKS5 proxy {ip}:{port} timed out after {timeout}s")
            return {
                "online": False,
                "latency_ms": None,
                "exit_ip": None,
                "status_code": None,
                "error": f"Connection timeout after {timeout}s"
            }

        except aiohttp.ClientError as e:
            logger.warning(f"SOCKS5 proxy {ip}:{port} connection error: {str(e)}")
            return {
                "online": False,
                "latency_ms": None,
                "exit_ip": None,
                "status_code": None,
                "error": f"Connection error: {str(e)}"
            }

        except Exception as e:
            logger.error(f"SOCKS5 proxy {ip}:{port} unexpected error: {str(e)}")
            return {
                "online": False,
                "latency_ms": None,
                "exit_ip": None,
                "status_code": None,
                "error": f"Unexpected error: {str(e)}"
            }

    async def check_pptp_proxy(
        self,
        ip: str,
        login: str,
        password: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Check if PPTP proxy is online and working.

        Args:
            ip: Proxy IP address
            login: Authentication username
            password: Authentication password
            timeout: Check timeout in seconds (default from settings)

        Returns:
            Dict with validation results:
            {
                "online": bool,  # True if proxy is working
                "latency_ms": float,  # Response time in milliseconds
                "exit_ip": str,  # Exit IP address of proxy
                "status_code": int,  # HTTP/TCP status
                "error": str | None  # Error description if any
            }
        """
        timeout = timeout or settings.PROXY_CHECK_TIMEOUT

        # TODO: Implement full PPTP validation with pppd or similar
        # For MVP, we'll do a simple TCP port check to port 1723 (PPTP port)

        try:
            start_time = time.time()

            # Try to connect to PPTP port 1723
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, 1723),
                timeout=timeout
            )

            latency_ms = (time.time() - start_time) * 1000

            # Connection successful, close it
            writer.close()
            await writer.wait_closed()

            logger.info(f"PPTP proxy {ip} port 1723 is reachable (latency: {latency_ms:.0f}ms)")

            return {
                "online": True,
                "latency_ms": latency_ms,
                "exit_ip": ip,  # Can't determine exit IP without full VPN connection
                "status_code": 200,  # Mock status for consistency
                "error": None
            }

        except asyncio.TimeoutError:
            logger.warning(f"PPTP proxy {ip} timed out after {timeout}s")
            return {
                "online": False,
                "latency_ms": None,
                "exit_ip": None,
                "status_code": None,
                "error": f"Connection timeout after {timeout}s"
            }

        except (OSError, ConnectionError) as e:
            logger.warning(f"PPTP proxy {ip} connection error: {str(e)}")
            return {
                "online": False,
                "latency_ms": None,
                "exit_ip": None,
                "status_code": None,
                "error": f"Connection error: {str(e)}"
            }

        except Exception as e:
            logger.error(f"PPTP proxy {ip} unexpected error: {str(e)}")
            return {
                "online": False,
                "latency_ms": None,
                "exit_ip": None,
                "status_code": None,
                "error": f"Unexpected error: {str(e)}"
            }

    async def validate_pptp_with_nc(
        self,
        ip: str,
        timeout: float = 2.5
    ) -> Dict[str, Any]:
        """
        Validate PPTP proxy using nc (netcat) command.

        Args:
            ip: Proxy IP address
            timeout: Check timeout in seconds (default 2.5)

        Returns:
            Dict with validation results:
            {
                "valid": bool,  # True if [tcp/pptp] found in output
                "output": str,  # Combined stdout/stderr output
                "error": str | None  # Error description if any
            }
        """
        try:
            # Execute nc command with timeout
            process = await asyncio.create_subprocess_exec(
                "nc", "-vs", ip, "1732",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            try:
                # Wait for process with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                # Combine output
                output = (stdout.decode('utf-8', errors='ignore') +
                         stderr.decode('utf-8', errors='ignore'))

                # Check for PPTP pattern (case-insensitive)
                output_lower = output.lower()
                is_valid = ('[tcp/pptp]' in output_lower or
                           'tcp/pptp' in output_lower)

                if is_valid:
                    logger.info(f"PPTP {ip} validation succeeded: [tcp/pptp] pattern found")
                    return {
                        "valid": True,
                        "output": output,
                        "error": None
                    }
                else:
                    logger.warning(f"PPTP {ip} validation failed: [tcp/pptp] pattern not found")
                    return {
                        "valid": False,
                        "output": output,
                        "error": "PPTP pattern not found in output"
                    }

            except asyncio.TimeoutError:
                # Kill process if still running
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass

                logger.warning(f"PPTP {ip} validation timeout after {timeout}s")
                return {
                    "valid": False,
                    "output": "",
                    "error": f"Timeout after {timeout}s"
                }

        except OSError as e:
            logger.error(f"PPTP {ip} validation OS error: {str(e)}")
            return {
                "valid": False,
                "output": "",
                "error": f"OS error: {str(e)}"
            }

        except Exception as e:
            logger.error(f"PPTP {ip} validation unexpected error: {str(e)}")
            return {
                "valid": False,
                "output": "",
                "error": f"Unexpected error: {str(e)}"
            }

    async def bulk_check_proxies(
        self,
        proxies: List[Dict[str, Any]],
        proxy_type: str = "socks5",
        max_concurrent: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Check multiple proxies in parallel with concurrency limit.

        Args:
            proxies: List of proxy configurations
            proxy_type: Type of proxy ("socks5" or "pptp")
            max_concurrent: Maximum concurrent checks

        Returns:
            List of validation results for each proxy
        """
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def check_with_semaphore(proxy_data: Dict[str, Any]) -> Dict[str, Any]:
            """Check single proxy with semaphore control."""
            async with semaphore:
                try:
                    if proxy_type.lower() == "socks5":
                        result = await self.check_socks5_proxy(
                            ip=proxy_data["ip"],
                            port=int(proxy_data["port"]),
                            login=proxy_data["login"],
                            password=proxy_data["password"]
                        )
                    else:  # pptp
                        result = await self.check_pptp_proxy(
                            ip=proxy_data["ip"],
                            login=proxy_data["login"],
                            password=proxy_data["password"]
                        )

                    # Add proxy identifier to result
                    result["proxy_id"] = proxy_data.get("id")
                    return result

                except Exception as e:
                    logger.error(f"Error checking proxy {proxy_data.get('ip')}: {str(e)}")
                    return {
                        "proxy_id": proxy_data.get("id"),
                        "online": False,
                        "latency_ms": None,
                        "exit_ip": None,
                        "status_code": None,
                        "error": str(e)
                    }

        # Run all checks in parallel
        tasks = [check_with_semaphore(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks)

        return results


# Create singleton instance
proxy_validator = ProxyValidator()