from backend.core.database import Base

from backend.models.user import User
from backend.models.user_address import UserAddress  # DEPRECATED: Legacy model, kept for historical data only
from backend.models.user_transaction import UserTransaction
from backend.models.user_log import UserLog
from backend.models.catalog import Catalog
from backend.models.product import Product
from backend.models.pptp_history import PptpHistory
from backend.models.proxy_history import ProxyHistory
from backend.models.coupon import Coupon
from backend.models.user_coupon_activation import UserCouponActivation
from backend.models.environment_variable import EnvironmentVariable
from backend.models.broadcast import Broadcast, BroadcastStatus
from backend.models.pending_invoice import PendingInvoice

__all__ = [
    "Base",
    "User",
    "UserAddress",
    "UserTransaction",
    "UserLog",
    "Catalog",
    "Product",
    "PptpHistory",
    "ProxyHistory",
    "Coupon",
    "UserCouponActivation",
    "EnvironmentVariable",
    "Broadcast",
    "BroadcastStatus",
    "PendingInvoice"
]