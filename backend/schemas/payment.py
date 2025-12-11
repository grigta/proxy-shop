"""
Pydantic schemas for Payment API.
Defines request/response models for cryptocurrency payment operations.
"""

from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from enum import Enum


# ============================================================
# NEW SCHEMAS FOR HELEKET INTEGRATION
# ============================================================

class CreatePaymentRequest(BaseModel):
    """Request model for creating a Heleket payment invoice."""
    amount_usd: Optional[Decimal] = Field(
        None, 
        description="Payment amount in USD (defaults to MIN_DEPOSIT_USD if not provided)",
        ge=Decimal('1.00'),
        le=Decimal('100000.00')
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "amount_usd": "10.00"
            }
        }
    )


class CreatePaymentResponse(BaseModel):
    """Response model for created payment invoice."""
    payment_url: str = Field(..., description="Universal payment link for user")
    payment_uuid: str = Field(..., description="Unique Heleket payment identifier")
    order_id: str = Field(..., description="Order identifier for tracking")
    expired_at: Optional[datetime] = Field(None, description="Payment expiration timestamp")
    amount_usd: Decimal = Field(..., description="Invoice amount in USD")
    min_amount_usd: Decimal = Field(..., description="Global minimum deposit amount in USD")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "payment_url": "https://heleket.com/payment/abc123",
                "payment_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "order_id": "DEPOSIT-123-1699564800",
                "expired_at": "2024-11-12T12:30:00Z",
                "amount_usd": "25.00",
                "min_amount_usd": "10.00"
            }
        }
    )


class HeleketWebhookPayload(BaseModel):
    """
    Schema for validating incoming webhooks from Heleket payment system.
    
    This is the ACTIVE schema for all new Heleket payment webhooks.
    For legacy cryptocurrencyapi.net webhooks, see IPNWebhookPayload.
    """
    uuid: str = Field(..., description="Heleket payment UUID")
    order_id: str = Field(..., description="Merchant order identifier")
    status: str = Field(..., description="Payment status: 'paid' or 'check'")
    is_final: bool = Field(..., description="Whether payment is finalized")
    merchant_amount: str = Field(..., description="Amount received by merchant in USD")
    payment_amount: Optional[str] = Field(None, description="Amount paid by user in crypto")
    currency: Optional[str] = Field(None, description="Cryptocurrency used (BTC, ETH, etc.)")
    network: Optional[str] = Field(None, description="Blockchain network")
    txid: Optional[str] = Field(None, description="Blockchain transaction ID")
    convert: Optional[bool] = Field(None, description="Whether auto-conversion was used")
    sign: str = Field(..., description="MD5 signature for verification")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "order_id": "DEPOSIT-123-1699564800",
                "status": "paid",
                "is_final": True,
                "merchant_amount": "10.00",
                "payment_amount": "0.00027",
                "currency": "BTC",
                "network": "bitcoin",
                "txid": "abcd1234...",
                "convert": False,
                "sign": "1a2b3c4d5e6f7g8h9i0j..."
            }
        }
    )


# ============================================================
# DEPRECATED LEGACY SCHEMAS (for backward compatibility)
# ============================================================

class CryptoChain(str, Enum):
    """
    DEPRECATED: Supported cryptocurrency chains.
    
    This enum is for legacy cryptocurrencyapi.net integration only.
    New payments use Heleket universal payment links.
    """
    BTC = "BTC"
    ETH = "ETH"
    LTC = "LTC"
    BNB = "BNB"
    USDT_TRC20 = "USDT_TRC20"
    USDT_ERC20 = "USDT_ERC20"
    USDT_BEP20 = "USDT_BEP20"


class GenerateAddressRequest(BaseModel):
    """
    DEPRECATED: Use CreatePaymentRequest instead.
    
    Request model for generating a deposit address (legacy cryptocurrencyapi.net).
    """
    chain: CryptoChain = Field(..., description="Cryptocurrency chain to generate address for")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "chain": "BTC"
            }
        }
    )


class GenerateAddressResponse(BaseModel):
    """
    DEPRECATED: Use CreatePaymentResponse instead.
    
    Response model for generated deposit address (legacy cryptocurrencyapi.net).
    """
    address: str = Field(..., description="Generated cryptocurrency address")
    chain: CryptoChain = Field(..., description="Cryptocurrency chain")
    qr_code: str = Field(..., description="QR code as base64 data URI")
    valid_until: Optional[datetime] = Field(None, description="Address expiration (for USDT_TRC20)")
    min_amount_usd: Decimal = Field(..., description="Minimum deposit amount in USD")
    network_name: str = Field(..., description="Human-readable network name")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
                "chain": "BTC",
                "qr_code": "data:image/png;base64,iVBORw0KGgoAAAA...",
                "valid_until": None,
                "min_amount_usd": "10.00",
                "network_name": "Bitcoin"
            }
        }
    )


class IPNWebhookPayload(BaseModel):
    """
    DEPRECATED: Use HeleketWebhookPayload instead.
    
    Schema for validating incoming IPN webhooks from cryptocurrencyapi.net (legacy).
    """
    cryptocurrencyapi_net: Optional[str] = Field(None, alias="cryptocurrencyapi.net", description="API version")
    chain: str = Field(..., description="Blockchain network (bitcoin, ethereum, bsc, tron, litecoin)")
    currency: str = Field(..., description="Currency code (BTC, ETH, BNB, LTC, TRX)")
    type: str = Field(..., description="Transaction type (in/out)")
    date: int = Field(..., description="Unix timestamp of transaction")
    from_address: str = Field(..., alias="from", description="Sender address")
    to_address: str = Field(..., alias="to", description="Receiver address")
    token: Optional[str] = Field(None, description="Token symbol for token transactions (e.g., USDT)")
    tokenContract: Optional[str] = Field(None, description="Token contract address")
    amount: str = Field(..., description="Transaction amount in cryptocurrency")
    fee: str = Field(..., description="Network fee")
    txid: str = Field(..., description="Blockchain transaction ID")
    pos: Optional[int] = Field(None, description="Position in block")
    confirmation: int = Field(..., description="Number of confirmations")
    label: Optional[str] = Field(None, description="User label (user_id)")
    sign: str = Field(..., description="HMAC signature for verification")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
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
                "label": "123",
                "sign": "1a2b3c4d..."
            }
        }
    )


class TransactionHistoryItem(BaseModel):
    """Model for a single transaction in history."""
    id_tranz: int = Field(..., description="Transaction ID")
    chain: str = Field(..., description="Blockchain network")
    currency: str = Field(..., description="Currency code")
    amount_in_dollar: Decimal = Field(..., description="Amount in USD")
    coin_amount: Decimal = Field(..., description="Amount in cryptocurrency")
    coin_course: Decimal = Field(..., description="Exchange rate at time of transaction")
    txid: str = Field(..., description="Blockchain transaction ID")
    from_address: str = Field(..., description="Sender address")
    to_address: str = Field(..., description="Receiver address")
    fee: Decimal = Field(..., description="Network fee")
    dateOfTransaction: datetime = Field(..., description="Transaction timestamp")
    confirmation: Optional[int] = Field(None, description="Number of confirmations")
    payment_uuid: Optional[str] = Field(None, description="Heleket payment UUID if applicable")
    order_id: Optional[str] = Field(None, description="Order identifier if applicable")
    transaction_type: Optional[str] = Field(None, description="Transaction source: 'legacy' or 'heleket'")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id_tranz": 1,
                    "chain": "bitcoin",
                    "currency": "BTC",
                    "amount_in_dollar": "50.00",
                    "coin_amount": "0.001",
                    "coin_course": "50000.00",
                    "txid": "abcd1234legacy...",
                    "from_address": "bc1qsender...",
                    "to_address": "bc1qreceiver...",
                    "fee": "0.00001",
                    "dateOfTransaction": "2024-11-12T10:30:00",
                    "confirmation": 6,
                    "payment_uuid": None,
                    "order_id": None,
                    "transaction_type": "legacy"
                },
                {
                    "id_tranz": 2,
                    "chain": "heleket",
                    "currency": "BTC",
                    "amount_in_dollar": "25.00",
                    "coin_amount": "0.0005",
                    "coin_course": "50000.00",
                    "txid": "heleket-txid-123",
                    "from_address": "",
                    "to_address": "",
                    "fee": "0.00",
                    "dateOfTransaction": "2024-11-12T12:00:00",
                    "confirmation": None,
                    "payment_uuid": "550e8400-e29b-41d4-a716-446655440000",
                    "order_id": "DEPOSIT-123-1699564800",
                    "transaction_type": "heleket"
                }
            ]
        }
    )


class TransactionHistoryResponse(BaseModel):
    """Response model for transaction history with pagination."""
    transactions: List[TransactionHistoryItem] = Field(..., description="List of transactions")
    total: int = Field(..., description="Total number of transactions")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of items per page")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "transactions": [],
                "total": 25,
                "page": 1,
                "page_size": 10
            }
        }
    )


class IPNWebhookResponse(BaseModel):
    """Response model for IPN webhook processing."""
    status: str = Field("ok", description="Processing status")
    message: str = Field(..., description="Result message")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "status": "ok",
                "message": "Payment processed successfully"
            }
        }
    )


class DepositSuccessNotification(BaseModel):
    """Model for notifying user about successful deposit (for Telegram bot)."""
    user_id: int = Field(..., description="User ID")
    currency: str = Field(..., description="Currency code")
    coin_amount: Decimal = Field(..., description="Amount in cryptocurrency")
    amount_usd: Decimal = Field(..., description="Amount in USD")
    txid: str = Field(..., description="Transaction ID")
    date: datetime = Field(..., description="Transaction date")
    new_balance: Decimal = Field(..., description="Updated user balance")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 123,
                "currency": "BTC",
                "coin_amount": "0.001",
                "amount_usd": "50.00",
                "txid": "abcd1234...",
                "date": "2024-11-12T10:30:00",
                "new_balance": "150.00"
            }
        }
    )