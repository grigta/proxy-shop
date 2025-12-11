import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from backend.core.database import engine, Base, async_session_maker
from backend.models import (
    User, UserAddress, UserTransaction, UserLog,
    Catalog, Product, ProxyHistory, PptpHistory,
    Coupon, UserCouponActivation, EnvironmentVariable
)
from backend.models.user import PlatformType


async def init_database():
    """Initialize database and create all tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ All database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


async def seed_environment_variables():
    """Seed initial environment variables"""
    try:
        async with async_session_maker() as session:
            variables = [
                {
                    "name": "SUPPORT_TELEGRAM_ID",
                    "data": "8171638354",
                    "description": "Telegram ID of support agent"
                },
                {
                    "name": "MIN_DEPOSIT_USD",
                    "data": "10",
                    "description": "Minimum deposit amount in USD"
                },
                {
                    "name": "RULES_TELEGRAPH_URL",
                    "data": "https://telegra.ph/proxy-shop-rules",
                    "description": "URL to shop rules on Telegraph"
                },
                {
                    "name": "TELEGRAM_NEWS_CHANNEL",
                    "data": "https://t.me/",
                    "description": "Telegram news channel URL"
                },
                {
                    "name": "TELEGRAM_MIRROR_CHANNEL",
                    "data": "https://t.me/",
                    "description": "Telegram mirror channel URL"
                },
                {
                    "name": "SOCKS5_PRICE_USD",
                    "data": "2.0",
                    "description": "Price for SOCKS5 proxy in USD"
                },
                {
                    "name": "PPTP_PRICE_USD",
                    "data": "5.0",
                    "description": "Price for PPTP proxy in USD"
                },
                {
                    "name": "SOCKS5_REFUND_MINUTES",
                    "data": "30",
                    "description": "Refund window for SOCKS5 in minutes"
                },
                {
                    "name": "PPTP_REFUND_HOURS",
                    "data": "24",
                    "description": "Refund window for PPTP in hours"
                },
                {
                    "name": "REFERRAL_BONUS_PERCENTAGE",
                    "data": "10",
                    "description": "Referral bonus percentage"
                },
                {
                    "name": "BOT_USERNAME",
                    "data": "proxy_shop_bot",
                    "description": "Telegram bot username (without @) for referral links"
                },
                {
                    "name": "WEB_REFERRAL_BASE_URL",
                    "data": "https://proxy-shop.com/register",
                    "description": "Base URL for web referral links"
                },
                {
                    "name": "REFERRAL_BONUS_ON_FIRST_PURCHASE",
                    "data": "true",
                    "description": "Award referral bonus only on first purchase (true/false)"
                },
                {
                    "name": "ADMIN_ACCESS_CODES",
                    "data": "",
                    "description": "Comma-separated list of admin access codes"
                }
            ]

            for var_data in variables:
                stmt = select(EnvironmentVariable).where(EnvironmentVariable.name == var_data["name"])
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if not existing:
                    var = EnvironmentVariable(**var_data)
                    session.add(var)
                else:
                    # Update existing variable
                    for key, value in var_data.items():
                        setattr(existing, key, value)

            await session.commit()
            print(f"✅ Seeded {len(variables)} environment variables")

    except Exception as e:
        print(f"❌ Error seeding environment variables: {e}")
        raise


async def seed_admin_user():
    """Create first admin user if none exists"""
    try:
        async with async_session_maker() as session:
            # Check if admin already exists
            stmt = select(User).where(User.is_admin == True)
            result = await session.execute(stmt)
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print(f"✅ Admin user already exists (user_id: {existing_admin.user_id}, access_code: {existing_admin.access_code})")
                return

            # Generate unique access code for admin
            from backend.scripts.generate_access_code import generate_unique_access_code
            access_code = await generate_unique_access_code(session)

            # Create admin user
            admin_user = User(
                access_code=access_code,
                platform_registered=PlatformType.web,
                language='ru',
                is_admin=True,
                balance=Decimal('0.00'),
                username='admin',
                myreferal_id=f"ref_{access_code.replace('-', '')}"
            )
            session.add(admin_user)
            await session.flush()

            # Update ADMIN_ACCESS_CODES environment variable
            env_var_stmt = select(EnvironmentVariable).where(EnvironmentVariable.name == "ADMIN_ACCESS_CODES")
            env_var_result = await session.execute(env_var_stmt)
            admin_codes_var = env_var_result.scalar_one_or_none()
            
            if admin_codes_var:
                admin_codes_var.data = access_code
            
            await session.commit()

            print("\n" + "="*60)
            print("✅ Admin user created successfully!")
            print("="*60)
            print(f"📋 Admin Access Code: {access_code}")
            print(f"👤 User ID: {admin_user.user_id}")
            print(f"🌐 Platform: Web")
            print(f"🗣️ Language: Russian")
            print("\n⚠️  IMPORTANT: Save this access code securely!")
            print("   You'll need it to login to the admin panel at http://localhost:3001")
            print("="*60 + "\n")

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        raise


async def main():
    """Main function to initialize database and seed data"""
    print("🚀 Starting database initialization...")

    try:
        await init_database()
        await seed_environment_variables()
        await seed_admin_user()
        print("\n✅ Database initialization completed successfully!")
        print("\n📝 Note: This script is for development only.")
        print("For production, use Alembic migrations:")
        print("  alembic upgrade head")

    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())