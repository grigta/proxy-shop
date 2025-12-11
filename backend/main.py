from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from backend.api.routes.auth import router as auth_router
from backend.api.routes.payment import router as payment_router
from backend.api.routes.products import router as products_router
from backend.api.routes.purchase import router as purchase_router
from backend.api.routes.user import router as user_router
from backend.api.routes.admin import router as admin_router
from backend.api.routes.external_proxy import router as external_proxy_router
from backend.core.config import settings

# Configure logging to ensure output goes to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown tasks.
    This replaces deprecated @app.on_event("startup") and @app.on_event("shutdown")
    """
    # STARTUP
    logger.info("=" * 60)
    logger.info("Starting Proxy Shop API v1.0.0")
    logger.info("=" * 60)
    logger.info(f"Database URL: {settings.get_database_url()}")
    logger.info(f"External SOCKS API: {settings.EXTERNAL_SOCKS_API_URL}")
    logger.info(f"API Documentation: http://localhost:8000/api/docs")

    # Initialize Heleket payment client
    from backend.core.heleket_client import initialize_heleket_client
    await initialize_heleket_client()
    logger.info("✓ Heleket payment client initialized")

    # Initialize External SOCKS API client
    from backend.core.external_socks_client import initialize_external_socks_client
    await initialize_external_socks_client()
    logger.info("✓ External SOCKS API client initialized")

    # Start background scheduler for external proxy sync
    from backend.core.scheduler import start_scheduler
    start_scheduler()
    logger.info(f"✓ Scheduler started - sync every {settings.EXTERNAL_SOCKS_SYNC_INTERVAL_MINUTES} minutes")

    logger.info("\nPayment API endpoints:")
    logger.info("  - POST /api/payment/generate-address (Heleket payment invoice)")
    logger.info("  - POST /api/payment/webhook/heleket (Heleket webhook)")
    logger.info("  - POST /api/payment/webhook/ipn (Legacy - deprecated)")
    logger.info("  - GET /api/payment/history/{user_id}")
    logger.info("  - GET /api/payment/addresses")
    logger.info("\nProducts API endpoints:")
    logger.info("  - GET /api/products/socks5")
    logger.info("  - GET /api/products/pptp")
    logger.info("  - GET /api/products/countries")
    logger.info("  - GET /api/products/states/{country}")
    logger.info("\nPurchase API endpoints:")
    logger.info("  - POST /api/purchase/socks5")
    logger.info("  - POST /api/purchase/pptp")
    logger.info("  - GET /api/purchase/history/{user_id}")
    logger.info("  - POST /api/purchase/validate/{proxy_id}")
    logger.info("  - POST /api/purchase/extend/{proxy_id}")
    logger.info("\nUser Profile & Referral API endpoints:")
    logger.info("  - GET /api/user/profile")
    logger.info("  - GET /api/user/history")
    logger.info("  - POST /api/user/coupon/activate")
    logger.info("  - GET /api/user/referrals/{user_id}")
    logger.info("\nAdmin API endpoints (requires admin authentication):")
    logger.info("  - GET /api/admin/stats")
    logger.info("  - GET /api/admin/revenue-chart")
    logger.info("  - GET /api/admin/users")
    logger.info("  - GET /api/admin/users/{user_id}")
    logger.info("  - PATCH /api/admin/users/{user_id}")
    logger.info("  - GET /api/admin/top-users")
    logger.info("  - GET /api/admin/coupons")
    logger.info("  - POST /api/admin/coupons")
    logger.info("  - GET /api/admin/proxies")
    logger.info("  - POST /api/admin/proxies")
    logger.info("\nExternal Proxy API endpoints:")
    logger.info("  - GET /api/external-proxy/list")
    logger.info("  - POST /api/external-proxy/purchase")
    logger.info("  - POST /api/external-proxy/refund")
    logger.info("  - POST /api/external-proxy/sync (admin only)")
    logger.info("  - POST /api/external-proxy/cleanup (admin only)")
    logger.info("  - GET /api/external-proxy/stats (admin only)")
    logger.info("=" * 60)
    logger.info("🚀 Proxy Shop API is ready!")
    logger.info("=" * 60)

    yield  # Application runs here

    # SHUTDOWN
    logger.info("=" * 60)
    logger.info("Shutting down Proxy Shop API")
    logger.info("=" * 60)

    # Close Heleket payment client
    from backend.core.heleket_client import close_heleket_client
    await close_heleket_client()
    logger.info("✓ Heleket payment client closed")

    # Close External SOCKS API client
    from backend.core.external_socks_client import close_external_socks_client
    await close_external_socks_client()
    logger.info("✓ External SOCKS API client closed")

    # Stop background scheduler
    from backend.core.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("✓ Scheduler stopped")
    logger.info("=" * 60)
    logger.info("👋 Proxy Shop API shutdown complete")
    logger.info("=" * 60)


# Create FastAPI application with lifespan
app = FastAPI(
    title="Proxy Shop API",
    description="API for proxy shop with cross-platform authentication",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(purchase_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(external_proxy_router, prefix="/api")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Proxy Shop API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }

# Global exception handler for HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Global handler for HTTP exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code
        }
    )

# Note: Startup and shutdown events are now handled by lifespan context manager above

# Main entry point for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )