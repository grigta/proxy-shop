"""
HTTP client for Heleket API (Mode B) integration.
Provides methods for creating universal payment links and verifying webhook signatures.
"""

import httpx
import hashlib
import base64
import json
import secrets
import re
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from fastapi import HTTPException
from backend.core.config import settings

logger = logging.getLogger(__name__)


class HeleketAPIClient:
    """Client for interacting with Heleket Payment API (Mode B)."""

    def __init__(self):
        """Initialize the Heleket API client."""
        self.base_url = "https://api.heleket.com/v1"
        self.merchant_uuid = settings.HELEKET_MERCHANT_UUID
        self.api_key = settings.HELEKET_API_KEY
        self.webhook_url = settings.HELEKET_WEBHOOK_URL
        self.timeout = settings.HELEKET_API_TIMEOUT
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout=self.timeout))

    def _prepare_json_body(self, json_body: str) -> str:
        """
        Prepare JSON body with PHP-style slash escaping.

        Heleket uses PHP which escapes forward slashes in json_encode().
        We must match this for signature verification.

        Args:
            json_body: JSON string

        Returns:
            JSON string with escaped forward slashes
        """
        return json_body.replace("/", "\\/")

    def _calculate_signature(self, json_body: str) -> str:
        """
        Calculate MD5 signature for Heleket API request.

        Algorithm: MD5(base64(JSON) + api_key)

        Args:
            json_body: JSON string (already with escaped slashes if needed)

        Returns:
            MD5 hash as hexadecimal string
        """
        # Base64 encode the JSON string
        json_base64 = base64.b64encode(json_body.encode('utf-8')).decode('utf-8')

        # Concatenate with API key and compute MD5
        signature_string = json_base64 + self.api_key
        md5_hash = hashlib.md5(signature_string.encode('utf-8')).hexdigest()

        logger.debug(f"Signature calculation - JSON length: {len(json_body)}, Base64 length: {len(json_base64)}")

        return md5_hash

    async def create_payment(self, amount_usd: Decimal, order_id: str) -> Dict[str, Any]:
        """
        Create a universal payment link in Heleket (Mode B).
        
        Args:
            amount_usd: Amount in USD (Heleket handles crypto conversion)
            order_id: Unique order identifier for tracking
            
        Returns:
            Dict containing:
                - payment_url: Universal payment link for the user
                - payment_uuid: Unique payment identifier
                - expired_at: Payment expiration timestamp
                
        Raises:
            HTTPException: On API error or invalid response
        """
        try:
            # Build request body with url_callback for webhook notifications
            request_body = {
                "amount": str(amount_usd),
                "currency": "USD",
                "order_id": order_id,
                "url_callback": self.webhook_url
            }

            # Serialize JSON with consistent formatting (no spaces)
            json_body_raw = json.dumps(request_body, separators=(',', ':'), ensure_ascii=False)

            # Escape slashes for PHP compatibility (Heleket uses PHP)
            # IMPORTANT: Both signature and request body must use escaped slashes
            json_body = self._prepare_json_body(json_body_raw)

            # Calculate signature from escaped JSON
            signature = self._calculate_signature(json_body)

            # Set request headers
            headers = {
                "merchant": self.merchant_uuid,
                "sign": signature,
                "Content-Type": "application/json"
            }

            logger.info(f"Creating Heleket payment for order {order_id}, amount: ${amount_usd}, callback: {self.webhook_url}")
            logger.debug(f"Request body (escaped): {json_body}")

            # Make API request with escaped JSON body
            response = await self.client.post(
                f"{self.base_url}/payment",
                content=json_body,
                headers=headers
            )
            
            response.raise_for_status()
            data = response.json()

            # Extract result from Heleket API response wrapper
            # Heleket API returns: {"state": 0, "result": {...}}
            if "result" in data:
                result_data = data["result"]
            else:
                result_data = data

            # Validate response fields
            if "url" not in result_data or "uuid" not in result_data:
                logger.error(f"Invalid Heleket API response: missing required fields - {data}")
                raise HTTPException(
                    status_code=500,
                    detail="Invalid payment API response"
                )

            logger.info(f"Payment created successfully - UUID: {result_data.get('uuid')}, Order: {order_id}")

            # Convert expired_at from Unix timestamp to ISO string if it's an integer
            expired_at = result_data.get("expired_at")
            if isinstance(expired_at, int):
                from datetime import datetime, timezone
                expired_at = datetime.fromtimestamp(expired_at, tz=timezone.utc).isoformat()

            return {
                "payment_url": result_data["url"],
                "payment_uuid": result_data["uuid"],
                "expired_at": expired_at
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating payment: Status {e.response.status_code}, Response: {e.response.text}")
            # Don't propagate 401/403 from payment provider to client
            # These are configuration errors, not authentication errors
            if e.response.status_code in (401, 403):
                raise HTTPException(
                    status_code=500,
                    detail="Ошибка конфигурации платежной системы. Обратитесь к администратору."
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Payment API error: {e.response.text}"
            )
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating payment: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create payment")
        except Exception as e:
            logger.error(f"Unexpected error creating payment: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal error creating payment")

    def verify_webhook_signature(self, raw_body: str, received_sign: str) -> bool:
        """
        Verify webhook signature from Heleket.
        
        Algorithm: MD5(base64(JSON without 'sign' field) + api_key)
        
        Args:
            raw_body: Raw JSON string from webhook request body
            received_sign: Signature from webhook 'sign' field
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Parse JSON to extract order_id and uuid for logging only
            webhook_data = json.loads(raw_body)
            order_id = webhook_data.get('order_id')
            uuid = webhook_data.get('uuid')
            
            # Remove 'sign' field from the raw JSON string without full deserialization/reserialization
            # This preserves the original field order and formatting that Heleket used
            json_body_without_sign = self._remove_sign_from_json(raw_body)
            
            # Calculate expected signature based on original JSON structure
            expected_sign = self._calculate_signature(json_body_without_sign)
            
            # Timing-safe comparison
            is_valid = secrets.compare_digest(expected_sign, received_sign)
            
            if not is_valid:
                logger.warning(
                    f"Webhook signature mismatch - "
                    f"Expected: {expected_sign}, "
                    f"Received: {received_sign}, "
                    f"Order ID: {order_id}, "
                    f"UUID: {uuid}"
                )
            else:
                logger.info(f"Webhook signature verified successfully for order {order_id}")
            
            return is_valid
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook body: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}", exc_info=True)
            return False

    def _remove_sign_from_json(self, json_string: str) -> str:
        """
        Remove 'sign' field from JSON string using regex string manipulation.
        
        This method uses string-based removal to preserve 100% fidelity to Heleket's
        original JSON formatting (field order, spacing, number representations) except
        for the removal of the 'sign' field itself. This is critical for webhook
        signature verification as re-serialization could alter formatting and cause
        signature mismatches.
        
        Algorithm:
        - Uses regex to match "sign":"<value>" with optional whitespace and comma
        - Handles both minified and pretty-printed JSON
        - Removes the field and any trailing comma/whitespace
        - Preserves all other JSON structure exactly as sent by Heleket
        
        Reference: Heleket API webhook signature = MD5(base64(escaped_JSON_without_sign) + api_key)
        
        Args:
            json_string: Original JSON string containing 'sign' field
            
        Returns:
            JSON string with 'sign' field removed, preserving all other formatting
            
        Raises:
            Exception: If regex removal fails or resulting JSON is invalid
        """
        try:
            # Pattern explanation:
            # "sign"       - literal field name with quotes
            # \s*:\s*      - colon with optional whitespace
            # "[^"]*"      - string value (handles escaped quotes within)
            # \s*,?\s*     - optional trailing comma with whitespace
            #
            # This handles cases like:
            # - "sign":"abc123",       (with trailing comma)
            # - "sign": "abc123",      (with spaces)
            # - "sign":"abc123"        (no trailing comma, last field)
            # - "sign" : "abc123" ,    (extra spaces)
            pattern = r'"sign"\s*:\s*"[^"]*"\s*,?\s*'
            
            # Remove the sign field
            result = re.sub(pattern, '', json_string)
            
            # Clean up potential double commas or trailing commas before closing brace
            # This handles edge cases where sign was in the middle
            result = re.sub(r',\s*,', ',', result)  # Remove double commas
            result = re.sub(r',\s*}', '}', result)  # Remove trailing comma before }
            
            # Validate that result is still valid JSON (for logging/debugging)
            # This doesn't modify the string, just validates it
            try:
                json.loads(result)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Result after sign removal is not valid JSON: {e}. "
                    f"Original length: {len(json_string)}, Result length: {len(result)}"
                )
                raise ValueError(f"Invalid JSON after sign removal: {e}")
            
            logger.debug(
                f"Successfully removed 'sign' field. "
                f"Original length: {len(json_string)}, "
                f"Result length: {len(result)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error removing sign from JSON: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client to free resources."""
        await self.client.aclose()


# Global client instance (initialized on application startup)
_heleket_client_instance: Optional[HeleketAPIClient] = None


def get_heleket_client() -> HeleketAPIClient:
    """
    Get the global Heleket client instance.
    
    Returns:
        HeleketAPIClient instance
        
    Raises:
        RuntimeError: If client is not initialized (app startup event not triggered)
    """
    if _heleket_client_instance is None:
        raise RuntimeError(
            "Heleket client is not initialized. "
            "Make sure the application startup event has been triggered."
        )
    return _heleket_client_instance


async def initialize_heleket_client() -> None:
    """
    Initialize the global Heleket client instance.
    Should be called during application startup.
    """
    global _heleket_client_instance
    if _heleket_client_instance is None:
        _heleket_client_instance = HeleketAPIClient()
        logger.info("Heleket API client initialized successfully")


async def close_heleket_client() -> None:
    """
    Close the global Heleket client instance and free resources.
    Should be called during application shutdown.
    """
    global _heleket_client_instance
    if _heleket_client_instance is not None:
        await _heleket_client_instance.close()
        _heleket_client_instance = None
        logger.info("Heleket API client closed successfully")

