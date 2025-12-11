"""
Migration script to add 'region' field to existing PPTP proxies
"""
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import async_session_maker
from backend.models.product import Product


async def migrate_add_region():
    """Add region field to all existing PPTP proxies"""

    async with async_session_maker() as session:
        try:
            # Get all PPTP products
            result = await session.execute(
                select(Product).where(Product.pre_lines_name == 'PPTP')
            )
            products = result.scalars().all()

            print(f"Found {len(products)} PPTP proxies to migrate")

            updated_count = 0
            skipped_count = 0

            for product in products:
                # Check if region already exists
                if product.product and 'region' in product.product:
                    skipped_count += 1
                    continue

                # Get country from JSONB
                country = product.product.get('country', '') if product.product else ''

                # Determine region
                if country == "United States":
                    region = "USA"
                else:
                    region = "EUROPE"

                # Update product JSONB with region field
                product.product['region'] = region

                # Mark as modified to trigger SQLAlchemy update
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(product, 'product')

                updated_count += 1

                if updated_count % 100 == 0:
                    print(f"Progress: {updated_count} products updated...")
                    await session.flush()

            # Commit all changes
            await session.commit()

            print(f"\n✅ Migration completed!")
            print(f"   Updated: {updated_count}")
            print(f"   Skipped (already had region): {skipped_count}")
            print(f"   Total: {len(products)}")

        except Exception as e:
            await session.rollback()
            print(f"❌ Error during migration: {e}")
            raise


if __name__ == "__main__":
    print("Starting migration to add 'region' field to PPTP proxies...")
    asyncio.run(migrate_add_region())
