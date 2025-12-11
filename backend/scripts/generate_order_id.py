import secrets
import string
import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def generate_order_id() -> str:
    """
    Generate a unique order ID in format ORDER-YYYYMMDDHHMMSS-XXXXXX.

    Returns:
        A string in format "ORDER-20251112153045-A2B3C4" where:
        - ORDER is a prefix
        - YYYYMMDDHHMMSS is timestamp (14 characters)
        - XXXXXX is 6 random uppercase letters/digits (excluding confusing characters)
    """
    # Generate timestamp part
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    # Exclude confusing characters: 0/O, 1/I/l
    allowed_chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')

    # Generate random part (6 characters)
    random_part = ''.join(secrets.choice(allowed_chars) for _ in range(6))

    return f"ORDER-{timestamp}-{random_part}"


async def generate_unique_order_id(session: AsyncSession) -> str:
    """
    Generate a unique order ID that doesn't exist in the database.

    Args:
        session: AsyncSession for database queries

    Returns:
        A unique order ID string in format ORDER-YYYYMMDDHHMMSS-XXXXXX

    Raises:
        Exception: If unable to generate unique order ID after 10 attempts
    """
    from backend.models.proxy_history import ProxyHistory

    max_attempts = 10

    for attempt in range(max_attempts):
        order_id = generate_order_id()

        # Check if order_id exists in proxy_history
        result = await session.execute(
            select(ProxyHistory.id).where(ProxyHistory.order_id == order_id)
        )
        existing_order = result.scalar_one_or_none()

        if not existing_order:
            return order_id

    raise Exception(f"Failed to generate unique order ID after {max_attempts} attempts")


def main():
    """Main function for testing - generates sample order IDs"""
    print("Sample Order IDs:")
    print("-" * 50)
    print(f"Format: ORDER-YYYYMMDDHHMMSS-XXXXXX")
    print(f"Length: ~27 characters")
    print("-" * 50)

    for i in range(10):
        order_id = generate_order_id()
        print(f"{i + 1:2}. {order_id} (len: {len(order_id)})")


if __name__ == "__main__":
    main()