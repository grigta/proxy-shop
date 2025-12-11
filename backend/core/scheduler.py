"""
Background Scheduler for External Proxy Sync and PPTP Validation

Automatically syncs proxies from external API every 5 minutes.
Validates recent PPTP purchases every minute (first hour auto-refund).
Returns expired PPTP proxies to shop monthly.
Uses APScheduler with Background mode (thread-based).
"""

import logging
import asyncio
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from decimal import Decimal

from backend.core.config import settings
from backend.services.external_proxy_service import ExternalProxyService

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: BackgroundScheduler = None


async def _async_sync_external_proxies():
    """
    Async coroutine to sync external proxies.
    Called by the background scheduler wrapper.
    """
    try:
        logger.info("Starting scheduled external proxy sync")

        # Create database session for this job
        engine = create_async_engine(
            settings.get_database_url(),
            echo=False,
            pool_pre_ping=True
        )

        async_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session_factory() as session:
            # Sync all proxies (no filters)
            stats = await ExternalProxyService.sync_proxies_to_inventory(
                session=session,
                page_size=200  # Fetch more proxies in background
            )

            logger.info(f"Scheduled sync completed: {stats}")

            # Also cleanup expired inventory
            removed = await ExternalProxyService.cleanup_expired_inventory(session)
            logger.info(f"Cleaned up {removed} expired proxies")

        await engine.dispose()

    except Exception as e:
        logger.error(f"Error in scheduled sync job: {str(e)}", exc_info=True)


def sync_external_proxies_job():
    """
    Background job wrapper to sync external proxies.

    This function runs in a background thread and creates a new event loop
    to execute the async coroutine.

    Runs every 5 minutes to fetch new proxies from external API
    and update local inventory.
    """
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the async coroutine
        loop.run_until_complete(_async_sync_external_proxies())

        # Clean up
        loop.close()

    except Exception as e:
        logger.error(f"Error in scheduler thread: {str(e)}", exc_info=True)


async def _async_check_recent_pptp_purchases():
    """
    Check all PPTP purchases from the last hour.
    Auto-refund any that are offline.
    """
    try:
        from backend.models.pptp_history import PptpHistory
        from backend.models.user import User
        from backend.core.proxy_validator import proxy_validator
        from backend.core.utils import parse_proxy_json

        logger.info("Starting scheduled PPTP validation for recent purchases")

        engine = create_async_engine(
            settings.get_database_url(),
            echo=False,
            pool_pre_ping=True
        )

        async_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session_factory() as session:
            # Get PPTP purchases from last hour (not refunded, valid sales)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)

            result = await session.execute(
                select(PptpHistory).where(
                    and_(
                        PptpHistory.datestamp >= one_hour_ago,
                        PptpHistory.isRefunded == False,
                        PptpHistory.resaled == True,  # Only valid sales
                        PptpHistory.user_key != "0"   # Not invalid
                    )
                )
            )
            recent_purchases = result.scalars().all()

            if not recent_purchases:
                logger.info("No recent PPTP purchases to validate")
                await engine.dispose()
                return

            logger.info(f"Validating {len(recent_purchases)} recent PPTP purchases")
            refunded_count = 0
            refunded_amount = Decimal("0.00")

            for pptp in recent_purchases:
                try:
                    pptp_data = parse_proxy_json(pptp.pptp) if isinstance(pptp.pptp, str) else pptp.pptp
                    ip = pptp_data.get("ip")

                    if not ip:
                        continue

                    # Check if PPTP is online
                    check_result = await proxy_validator.check_pptp_proxy(
                        ip=ip,
                        login=pptp_data.get("login", ""),
                        password=pptp_data.get("password", ""),
                        timeout=5.0
                    )

                    if not check_result["online"]:
                        # Proxy is offline - refund user
                        user = await session.get(User, pptp.user_id)
                        if user:
                            user.balance += pptp.price
                            pptp.isRefunded = True
                            refunded_count += 1
                            refunded_amount += pptp.price
                            logger.info(f"Auto-refunded PPTP {ip} for user {pptp.user_id}: ${pptp.price}")

                except Exception as e:
                    logger.error(f"Error validating PPTP {pptp.id}: {str(e)}")
                    continue

            await session.commit()
            logger.info(f"PPTP validation complete: {refunded_count} refunded, ${refunded_amount} returned")

        await engine.dispose()

    except Exception as e:
        logger.error(f"Error in PPTP validation job: {str(e)}", exc_info=True)


def check_recent_pptp_job():
    """Background job wrapper for PPTP validation."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_async_check_recent_pptp_purchases())
        loop.close()
    except Exception as e:
        logger.error(f"Error in PPTP validation thread: {str(e)}", exc_info=True)


async def _async_return_expired_pptp_to_shop():
    """
    Return expired PPTP proxies back to shop.
    Check if still valid before returning.
    Invalid proxies are permanently marked.
    """
    try:
        from backend.models.pptp_history import PptpHistory
        from backend.models.product import Product
        from backend.core.proxy_validator import proxy_validator
        from backend.core.utils import parse_proxy_json

        logger.info("Starting monthly PPTP return to shop")

        engine = create_async_engine(
            settings.get_database_url(),
            echo=False,
            pool_pre_ping=True
        )

        async_session_factory = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session_factory() as session:
            # Get PPTP purchases older than 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            result = await session.execute(
                select(PptpHistory).where(
                    and_(
                        PptpHistory.datestamp <= thirty_days_ago,
                        PptpHistory.resaled == True,    # Valid sales
                        PptpHistory.user_key != "0",    # Not invalid
                        PptpHistory.user_key.isnot(None)  # Has user_key
                    )
                )
            )
            expired_pptps = result.scalars().all()

            if not expired_pptps:
                logger.info("No expired PPTP proxies to return")
                await engine.dispose()
                return

            logger.info(f"Checking {len(expired_pptps)} expired PPTP proxies for return")
            returned_count = 0
            invalid_count = 0

            for pptp in expired_pptps:
                try:
                    pptp_data = parse_proxy_json(pptp.pptp) if isinstance(pptp.pptp, str) else pptp.pptp
                    ip = pptp_data.get("ip")

                    if not ip:
                        continue

                    # Check if PPTP is still valid
                    check_result = await proxy_validator.check_pptp_proxy(
                        ip=ip,
                        login=pptp_data.get("login", ""),
                        password=pptp_data.get("password", ""),
                        timeout=5.0
                    )

                    if check_result["online"]:
                        # Still valid - return to shop
                        # Check if product already exists
                        existing = await session.execute(
                            select(Product).where(
                                Product.product.contains(ip)
                            )
                        )
                        if existing.scalar_one_or_none():
                            logger.info(f"PPTP {ip} already exists in products, skipping")
                            pptp.user_key = None  # Clear user key
                            continue

                        # Create new product
                        new_product = Product(
                            catalog_id=pptp.product_id if pptp.product_id else 1,
                            pre_lines_name="PPTP",
                            line_name=pptp_data.get("country", "USA"),
                            product=pptp.pptp
                        )
                        session.add(new_product)

                        # Clear user_key to allow resale
                        pptp.user_key = None

                        returned_count += 1
                        logger.info(f"Returned PPTP {ip} to shop")
                    else:
                        # Invalid - mark permanently
                        pptp.resaled = False
                        pptp.user_key = "0"
                        invalid_count += 1
                        logger.info(f"Marked PPTP {ip} as permanently invalid")

                except Exception as e:
                    logger.error(f"Error processing expired PPTP {pptp.id}: {str(e)}")
                    continue

            await session.commit()
            logger.info(f"Monthly PPTP return complete: {returned_count} returned, {invalid_count} marked invalid")

        await engine.dispose()

    except Exception as e:
        logger.error(f"Error in monthly PPTP return job: {str(e)}", exc_info=True)


def return_expired_pptp_job():
    """Background job wrapper for monthly PPTP return."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_async_return_expired_pptp_to_shop())
        loop.close()
    except Exception as e:
        logger.error(f"Error in monthly PPTP return thread: {str(e)}", exc_info=True)


def start_scheduler():
    """
    Start the background scheduler.

    Registers:
    - External proxy sync every 5 minutes
    - PPTP validation every minute (for purchases in last hour)
    - Monthly PPTP return to shop (1st of each month at 3:00 AM)
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already started")
        return

    _scheduler = BackgroundScheduler()

    # Add sync job - runs every 5 minutes
    _scheduler.add_job(
        sync_external_proxies_job,
        trigger=IntervalTrigger(minutes=settings.EXTERNAL_SOCKS_SYNC_INTERVAL_MINUTES),
        id='sync_external_proxies',
        name='Sync external proxies from API',
        replace_existing=True,
        max_instances=1  # Only one instance at a time
    )

    # Add PPTP validation job - runs every minute
    # Checks purchases from last hour and auto-refunds offline proxies
    _scheduler.add_job(
        check_recent_pptp_job,
        trigger=IntervalTrigger(minutes=1),
        id='check_recent_pptp',
        name='Validate recent PPTP purchases (auto-refund)',
        replace_existing=True,
        max_instances=1
    )

    # Add monthly PPTP return job - runs on 1st of each month at 3:00 AM
    # Returns valid expired PPTP back to shop, marks invalid ones
    _scheduler.add_job(
        return_expired_pptp_job,
        trigger=CronTrigger(day=1, hour=3, minute=0),
        id='return_expired_pptp',
        name='Return expired PPTP to shop (monthly)',
        replace_existing=True,
        max_instances=1
    )

    _scheduler.start()
    logger.info(f"Scheduler started with 3 jobs:")
    logger.info(f"  - External proxy sync every {settings.EXTERNAL_SOCKS_SYNC_INTERVAL_MINUTES} minutes")
    logger.info(f"  - PPTP validation every 1 minute")
    logger.info(f"  - Monthly PPTP return on 1st at 3:00 AM")


def stop_scheduler():
    """
    Stop the background scheduler.
    """
    global _scheduler

    if _scheduler is None:
        logger.warning("Scheduler not running")
        return

    _scheduler.shutdown(wait=True)
    _scheduler = None
    logger.info("Scheduler stopped")


def get_scheduler_status():
    """
    Get scheduler status and job information.

    Returns:
        Dict with scheduler status
    """
    if _scheduler is None:
        return {
            "running": False,
            "jobs": []
        }

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {
        "running": True,
        "jobs": jobs
    }
