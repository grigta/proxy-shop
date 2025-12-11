"""
Tests for IPN signature verification.
Test various signing methods to ensure compatibility with cryptocurrencyapi.net.
"""

import json
import hmac
import hashlib
from backend.core.crypto_utils import verify_ipn_signature


def test_ipn_signature_verification():
    """
    Test IPN signature verification with sample data.

    NOTE: Replace with actual sample data from cryptocurrencyapi.net documentation.
    This test covers common signing methods used by cryptocurrency APIs.
    """

    # Sample IPN data (example structure)
    ipn_data = {
        "cryptocurrencyapi.net": "2.0",
        "chain": "bitcoin",
        "currency": "BTC",
        "type": "in",
        "date": 1699564800,
        "from": "bc1qsender...",
        "to": "bc1qreceiver...",
        "amount": "0.001",
        "fee": "0.00001",
        "txid": "abcd1234...",
        "confirmation": 3,
        "label": "123"
    }

    secret = "test_secret_key"

    # Method 1: Sign raw body with sign included
    ipn_with_sign = ipn_data.copy()
    raw_body = json.dumps(ipn_with_sign, separators=(',', ':'), ensure_ascii=False)
    sign_raw = hmac.new(
        secret.encode('utf-8'),
        raw_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    ipn_with_sign['sign'] = sign_raw

    # Test raw body signing
    raw_body_with_sign = json.dumps(ipn_with_sign, separators=(',', ':'), ensure_ascii=False)
    assert verify_ipn_signature(raw_body_with_sign, sign_raw, secret), \
        "Failed to verify signature for raw body method"

    # Method 2: Sign with sorted keys and sign removed
    ipn_sorted = ipn_data.copy()
    canonical_sorted = json.dumps(ipn_sorted, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    sign_sorted = hmac.new(
        secret.encode('utf-8'),
        canonical_sorted.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    ipn_sorted['sign'] = sign_sorted

    # Test sorted keys signing
    body_with_sign_sorted = json.dumps(ipn_sorted)
    assert verify_ipn_signature(body_with_sign_sorted, sign_sorted, secret), \
        "Failed to verify signature for sorted keys method"

    print("All IPN signature verification tests passed!")


def test_ipn_with_actual_sample():
    """
    Test with actual sample from cryptocurrencyapi.net documentation.

    TODO: Add actual sample data from the API documentation here.
    Visit: https://cryptocurrencyapi.net/docs/ipn
    """
    pass


if __name__ == "__main__":
    test_ipn_signature_verification()
    print("IPN signature tests completed successfully!")