"""
Unit tests for Heleket API client webhook signature verification.

Tests focus on the critical signature verification process, especially
the string-based removal of the 'sign' field to ensure 100% JSON fidelity.
"""

import pytest
import hashlib
import base64
import json
from backend.core.heleket_client import HeleketAPIClient
from unittest.mock import patch, MagicMock


class TestHeleketWebhookSignature:
    """Tests for Heleket webhook signature verification."""
    
    @pytest.fixture
    def heleket_client(self):
        """Create a Heleket client instance for testing."""
        with patch('backend.core.heleket_client.settings') as mock_settings:
            mock_settings.HELEKET_MERCHANT_UUID = "test-merchant-uuid"
            mock_settings.HELEKET_API_KEY = "test-api-key-123"
            mock_settings.HELEKET_API_TIMEOUT = 30.0
            client = HeleketAPIClient()
            return client
    
    def calculate_expected_signature(self, json_without_sign: str, api_key: str = "test-api-key-123") -> str:
        """
        Calculate expected signature manually using Heleket's algorithm.
        
        Algorithm: MD5(base64(JSON_with_escaped_slashes) + api_key)
        """
        # Escape forward slashes
        json_escaped = json_without_sign.replace("/", "\\/")
        
        # Base64 encode
        json_base64 = base64.b64encode(json_escaped.encode('utf-8')).decode('utf-8')
        
        # Concatenate with API key and MD5 hash
        signature_string = json_base64 + api_key
        md5_hash = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
        
        return md5_hash
    
    def test_remove_sign_from_json_minified(self, heleket_client):
        """Test removing 'sign' field from minified JSON (no spaces)."""
        # Minified JSON with sign in the middle
        original = '{"uuid":"abc-123","order_id":"order-456","status":"paid","sign":"signature123","amount":100.50}'
        expected = '{"uuid":"abc-123","order_id":"order-456","status":"paid","amount":100.50}'
        
        result = heleket_client._remove_sign_from_json(original)
        
        assert result == expected
        # Verify it's still valid JSON
        parsed = json.loads(result)
        assert "sign" not in parsed
        assert parsed["uuid"] == "abc-123"
        assert parsed["order_id"] == "order-456"
    
    def test_remove_sign_from_json_pretty_printed(self, heleket_client):
        """Test removing 'sign' field from pretty-printed JSON (with spaces)."""
        original = '{"uuid": "abc-123", "order_id": "order-456", "sign": "signature123", "amount": 100.50}'
        expected = '{"uuid": "abc-123", "order_id": "order-456", "amount": 100.50}'
        
        result = heleket_client._remove_sign_from_json(original)
        
        assert result == expected
        parsed = json.loads(result)
        assert "sign" not in parsed
    
    def test_remove_sign_from_json_sign_at_end(self, heleket_client):
        """Test removing 'sign' field when it's the last field (no trailing comma)."""
        original = '{"uuid":"abc-123","order_id":"order-456","amount":100.50,"sign":"signature123"}'
        expected = '{"uuid":"abc-123","order_id":"order-456","amount":100.50}'
        
        result = heleket_client._remove_sign_from_json(original)
        
        assert result == expected
        parsed = json.loads(result)
        assert "sign" not in parsed
    
    def test_remove_sign_from_json_sign_at_beginning(self, heleket_client):
        """Test removing 'sign' field when it's the first field."""
        original = '{"sign":"signature123","uuid":"abc-123","order_id":"order-456","amount":100.50}'
        expected = '{"uuid":"abc-123","order_id":"order-456","amount":100.50}'
        
        result = heleket_client._remove_sign_from_json(original)
        
        assert result == expected
        parsed = json.loads(result)
        assert "sign" not in parsed
    
    def test_remove_sign_from_json_extra_whitespace(self, heleket_client):
        """Test removing 'sign' field with extra whitespace variations."""
        original = '{"uuid": "abc-123" , "sign" : "signature123" , "amount" : 100.50}'
        
        result = heleket_client._remove_sign_from_json(original)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert "sign" not in parsed
        assert parsed["uuid"] == "abc-123"
        assert parsed["amount"] == 100.50
    
    def test_remove_sign_from_json_preserves_number_format(self, heleket_client):
        """Test that number formatting is preserved exactly."""
        # Integer without decimal
        original1 = '{"amount":100,"sign":"sig123"}'
        result1 = heleket_client._remove_sign_from_json(original1)
        assert result1 == '{"amount":100}'
        
        # Float with decimal
        original2 = '{"amount":100.50,"sign":"sig123"}'
        result2 = heleket_client._remove_sign_from_json(original2)
        assert result2 == '{"amount":100.50}'
        
        # Scientific notation
        original3 = '{"amount":1.5e2,"sign":"sig123"}'
        result3 = heleket_client._remove_sign_from_json(original3)
        assert result3 == '{"amount":1.5e2}'
    
    def test_remove_sign_from_json_preserves_boolean_format(self, heleket_client):
        """Test that boolean formatting is preserved exactly."""
        original = '{"is_final":true,"paid":false,"sign":"sig123"}'
        result = heleket_client._remove_sign_from_json(original)
        assert result == '{"is_final":true,"paid":false}'
        
        parsed = json.loads(result)
        assert parsed["is_final"] is True
        assert parsed["paid"] is False
    
    def test_remove_sign_from_json_with_escaped_characters(self, heleket_client):
        """Test handling of escaped characters in JSON values."""
        original = '{"url":"https://example.com/payment","sign":"sig123","note":"Line1\\nLine2"}'
        result = heleket_client._remove_sign_from_json(original)
        
        # Should preserve escaped characters
        assert "https://example.com/payment" in result or "https:\\/\\/example.com\\/payment" in result
        assert "\\n" in result
        parsed = json.loads(result)
        assert "sign" not in parsed
    
    def test_verify_webhook_signature_valid(self, heleket_client):
        """Test webhook signature verification with valid signature."""
        # Create a webhook payload
        webhook_data = {
            "uuid": "test-uuid-123",
            "order_id": "order-456",
            "status": "paid",
            "is_final": True,
            "merchant_amount": 100.50
        }
        
        # Serialize to JSON (simulating Heleket's format)
        json_without_sign = json.dumps(webhook_data, separators=(',', ':'))
        
        # Calculate expected signature
        expected_sign = self.calculate_expected_signature(json_without_sign)
        
        # Add sign to create full webhook body
        webhook_data["sign"] = expected_sign
        raw_body = json.dumps(webhook_data, separators=(',', ':'))
        
        # Verify signature
        is_valid = heleket_client.verify_webhook_signature(raw_body, expected_sign)
        
        assert is_valid is True
    
    def test_verify_webhook_signature_invalid(self, heleket_client):
        """Test webhook signature verification with invalid signature."""
        webhook_data = {
            "uuid": "test-uuid-123",
            "order_id": "order-456",
            "status": "paid",
            "sign": "invalid-signature-xyz"
        }
        
        raw_body = json.dumps(webhook_data, separators=(',', ':'))
        
        # Verify with wrong signature
        is_valid = heleket_client.verify_webhook_signature(raw_body, "wrong-signature")
        
        assert is_valid is False
    
    def test_verify_webhook_signature_missing_sign_field(self, heleket_client):
        """Test webhook signature verification when sign field is missing."""
        webhook_data = {
            "uuid": "test-uuid-123",
            "order_id": "order-456",
            "status": "paid"
        }
        
        raw_body = json.dumps(webhook_data, separators=(',', ':'))
        
        # Should handle gracefully
        is_valid = heleket_client.verify_webhook_signature(raw_body, "some-signature")
        
        # Should still work (sign field optional in removal, mandatory in verification logic)
        assert isinstance(is_valid, bool)
    
    def test_verify_webhook_signature_malformed_json(self, heleket_client):
        """Test webhook signature verification with malformed JSON."""
        raw_body = '{"uuid": "test", invalid json here}'
        
        is_valid = heleket_client.verify_webhook_signature(raw_body, "some-signature")
        
        # Should return False for invalid JSON
        assert is_valid is False
    
    def test_verify_webhook_signature_field_order_independence(self, heleket_client):
        """
        Test that signature verification works regardless of field order.
        This tests the core issue: we use the exact string Heleket sent.
        """
        # Payload with fields in order A
        order_a = '{"uuid":"123","order_id":"456","status":"paid","sign":"sig"}'
        
        # Same data but different field order (simulating potential dict reordering)
        order_b = '{"status":"paid","uuid":"123","order_id":"456","sign":"sig"}'
        
        # After removing sign, they should be different strings
        result_a = heleket_client._remove_sign_from_json(order_a)
        result_b = heleket_client._remove_sign_from_json(order_b)
        
        # The key insight: we preserve the original order
        assert result_a == '{"uuid":"123","order_id":"456","status":"paid"}'
        assert result_b == '{"status":"paid","uuid":"123","order_id":"456"}'
        assert result_a != result_b  # Order matters for signature!
    
    def test_calculate_signature_with_escaped_slashes(self, heleket_client):
        """Test that signature calculation properly escapes forward slashes."""
        json_body = '{"url":"https://example.com/callback"}'
        
        signature = heleket_client._calculate_signature(json_body)
        
        # Manually calculate expected signature with escaped slashes
        json_escaped = json_body.replace("/", "\\/")
        json_base64 = base64.b64encode(json_escaped.encode('utf-8')).decode('utf-8')
        signature_string = json_base64 + "test-api-key-123"
        expected_signature = hashlib.md5(signature_string.encode('utf-8')).hexdigest()
        
        assert signature == expected_signature
    
    def test_heleket_webhook_payload_structure(self, heleket_client):
        """
        Test with realistic Heleket webhook payload structure.
        
        Based on Heleket API docs: {uuid, order_id, status, is_final, merchant_amount, sign}
        """
        webhook_payload = {
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "order_id": "ORDER-2024-001",
            "status": "paid",
            "is_final": True,
            "merchant_amount": 99.99
        }
        
        # Serialize without sign
        json_without_sign = json.dumps(webhook_payload, separators=(',', ':'))
        
        # Calculate signature
        expected_sign = self.calculate_expected_signature(json_without_sign)
        
        # Create full webhook body with sign
        webhook_payload["sign"] = expected_sign
        raw_body = json.dumps(webhook_payload, separators=(',', ':'))
        
        # Verify
        is_valid = heleket_client.verify_webhook_signature(raw_body, expected_sign)
        
        assert is_valid is True
    
    def test_edge_case_sign_with_special_characters(self, heleket_client):
        """Test removing sign field when signature contains special regex characters."""
        # Signature with special characters that could break regex
        original = '{"uuid":"test","sign":"sig+with/special=chars","amount":100}'
        
        result = heleket_client._remove_sign_from_json(original)
        
        expected = '{"uuid":"test","amount":100}'
        assert result == expected
        parsed = json.loads(result)
        assert "sign" not in parsed
    
    def test_remove_sign_does_not_affect_create_payment(self, heleket_client):
        """
        Verify that create_payment signature calculation is not affected.
        create_payment uses controlled json.dumps() and doesn't need string manipulation.
        """
        # This test ensures our changes don't break the create_payment flow
        request_body = {
            "amount": "10.50",
            "currency": "USD",
            "order_id": "test-order"
        }
        
        json_body = json.dumps(request_body, separators=(',', ':'), ensure_ascii=False)
        signature = heleket_client._calculate_signature(json_body)
        
        # Should produce consistent signature
        assert isinstance(signature, str)
        assert len(signature) == 32  # MD5 hash is 32 hex characters


class TestHeleketClientEdgeCases:
    """Additional edge case tests for Heleket client."""
    
    @pytest.fixture
    def heleket_client(self):
        """Create a Heleket client instance for testing."""
        with patch('backend.core.heleket_client.settings') as mock_settings:
            mock_settings.HELEKET_MERCHANT_UUID = "test-merchant-uuid"
            mock_settings.HELEKET_API_KEY = "test-api-key-456"
            mock_settings.HELEKET_API_TIMEOUT = 30.0
            client = HeleketAPIClient()
            return client
    
    def test_remove_sign_with_unicode_characters(self, heleket_client):
        """Test handling of Unicode characters in JSON."""
        original = '{"note":"Платеж получен","sign":"sig123","amount":500}'
        
        result = heleket_client._remove_sign_from_json(original)
        
        parsed = json.loads(result)
        assert "sign" not in parsed
        assert parsed["note"] == "Платеж получен"
    
    def test_remove_sign_with_nested_json(self, heleket_client):
        """Test that nested objects don't confuse the sign removal."""
        original = '{"data":{"inner_sign":"not-removed"},"sign":"sig123","id":1}'
        
        result = heleket_client._remove_sign_from_json(original)
        
        parsed = json.loads(result)
        assert "sign" not in parsed
        assert parsed["data"]["inner_sign"] == "not-removed"  # Only top-level sign removed
    
    def test_verify_signature_logs_on_mismatch(self, heleket_client, caplog):
        """Test that signature mismatches are properly logged."""
        import logging
        
        webhook_data = {
            "uuid": "test-uuid",
            "order_id": "test-order",
            "sign": "invalid-sig"
        }
        
        raw_body = json.dumps(webhook_data)
        
        with caplog.at_level(logging.WARNING):
            is_valid = heleket_client.verify_webhook_signature(raw_body, "wrong-signature")
        
        assert is_valid is False
        # Check that warning was logged
        assert any("signature mismatch" in record.message.lower() for record in caplog.records)


# Integration test markers for running against real API (optional, requires env vars)
@pytest.mark.skip(reason="Integration test - requires real Heleket credentials")
class TestHeleketIntegration:
    """Integration tests for Heleket API (requires real credentials)."""
    
    def test_real_webhook_verification(self):
        """Test with real webhook data from Heleket (requires manual setup)."""
        # This would test with actual webhook data captured from Heleket
        # Useful for debugging real signature mismatch issues
        pass

