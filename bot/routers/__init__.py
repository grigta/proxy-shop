"""Bot routers exports."""
from bot.routers.start import router as start_router
from bot.routers.common import router as common_router
from bot.routers.account import router as account_router
from bot.routers.payment import router as payment_router
from bot.routers.socks5 import router as socks5_router
from bot.routers.pptp import router as pptp_router
from bot.routers.proxy_actions import router as proxy_actions_router
from bot.routers.support import router as support_router
from bot.routers.rules import router as rules_router

# List of routers to include in dispatcher
# Order matters: more specific handlers should come first
routers_list = [
    start_router,
    account_router,
    payment_router,
    socks5_router,
    pptp_router,
    proxy_actions_router,
    support_router,
    rules_router,
    common_router,  # Common (catch-all) should be last
]

__all__ = ["routers_list"]
