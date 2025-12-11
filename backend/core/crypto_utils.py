"""
Utility functions for QR code generation and legacy crypto operations.

Legacy cryptocurrency utilities have been deprecated after Heleket migration.
This module is retained for:
- QR code generation functionality (may be useful for future features)
- Legacy IPN signature verification (for backward compatibility only)
"""

import qrcode
from io import BytesIO
import base64
import hmac
import hashlib
import json
import secrets
import logging

logger = logging.getLogger(__name__)


def generate_qr_code(data: str, size: int = 10) -> str:
    """
    Generate a QR code for the given data (typically a crypto address).

    Args:
        data: The string to encode (crypto address)
        size: Box size for QR code (default 10)

    Returns:
        Base64 encoded PNG image string with data URI format

    Example:
        >>> qr_code = generate_qr_code("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh")
        >>> # Returns: "data:image/png;base64,iVBORw0KGgoAAAA..."
    """
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,  # Controls size, 1 is smallest
            box_size=size,
            border=4,
        )

        # Add data and optimize
        qr.add_data(data)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Encode to base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Return as data URI
        return f"data:image/png;base64,{img_base64}"

    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        # Return empty data URI on error
        return "data:image/png;base64,"


def verify_ipn_signature(raw_body: str, received_sign: str, secret: str) -> bool:
    """
    DEPRECATED: Verify HMAC signature from cryptocurrencyapi.net IPN webhook.
    
    This function is maintained only for backward compatibility with legacy
    /webhook/ipn endpoint. All new integrations should use Heleket webhooks
    which have their own signature verification.

    IMPORTANT: Different providers may use different signing methods:
    - Some sign the raw body as-is
    - Some sign JSON with sorted keys
    - Some remove the 'sign' field before signing

    Check cryptocurrencyapi.net documentation for the exact method.
    Current implementation tries multiple approaches.

    Args:
        raw_body: Raw JSON body of the HTTP request
        received_sign: Signature from 'sign' field in IPN payload
        secret: Secret key from settings.CRYPTO_API_IPN_SECRET

    Returns:
        True if signature is valid, False otherwise
    """
    logger.warning("DEPRECATED: verify_ipn_signature called - use Heleket signature verification for new integrations")
    try:
        # Method 1: Sign raw body as-is (most common)
        algorithms = [hashlib.sha256, hashlib.sha1, hashlib.sha512]

        for algo in algorithms:
            # Try signing raw body directly
            raw_sign = hmac.new(
                secret.encode('utf-8'),
                raw_body.encode('utf-8'),
                algo
            ).hexdigest()

            if secrets.compare_digest(raw_sign, received_sign):
                logger.debug(f"IPN signature verified with {algo.__name__} (raw body)")
                return True

        # Method 2: Sign JSON with 'sign' field removed
        data = json.loads(raw_body)
        data.pop('sign', None)

        # Try with sorted keys (canonical form)
        canonical_sorted = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

        for algo in algorithms:
            sorted_sign = hmac.new(
                secret.encode('utf-8'),
                canonical_sorted.encode('utf-8'),
                algo
            ).hexdigest()

            if secrets.compare_digest(sorted_sign, received_sign):
                logger.debug(f"IPN signature verified with {algo.__name__} (sorted keys)")
                return True

        # Try without sorted keys (original order)
        canonical_unsorted = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

        for algo in algorithms:
            unsorted_sign = hmac.new(
                secret.encode('utf-8'),
                canonical_unsorted.encode('utf-8'),
                algo
            ).hexdigest()

            if secrets.compare_digest(unsorted_sign, received_sign):
                logger.debug(f"IPN signature verified with {algo.__name__} (original order)")
                return True

        # If no method matched
        logger.warning(f"IPN signature verification failed for all methods")
        logger.debug(f"Received sign: {received_sign[:10]}...")
        return False

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse IPN JSON: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error verifying IPN signature: {str(e)}")
        return False