import secrets
import string
import asyncio
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def generate_access_code() -> str:
    """
    Generate a random access code in format XXX-XXX-XXX.

    Returns:
        A string in format "XXX-XXX-XXX" where X is uppercase letter or digit
    """
    # Exclude confusing characters: 0/O, 1/I/l
    allowed_chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')

    # Generate three groups of 3 characters each
    groups = []
    for _ in range(3):
        group = ''.join(secrets.choice(allowed_chars) for _ in range(3))
        groups.append(group)

    return '-'.join(groups)


async def generate_unique_access_code(session: AsyncSession) -> str:
    """
    Generate a unique access code that doesn't exist in the database.

    Args:
        session: AsyncSession for database queries

    Returns:
        A unique access code string in format XXX-XXX-XXX

    Raises:
        Exception: If unable to generate unique code after 10 attempts
    """
    from backend.models.user import User

    max_attempts = 10

    for attempt in range(max_attempts):
        code = generate_access_code()

        # Check if code exists in database
        result = await session.execute(
            select(User.user_id).where(User.access_code == code)
        )
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            return code

    raise Exception(f"Failed to generate unique access code after {max_attempts} attempts")


def main():
    """Main function for testing - generates sample access codes"""
    print("Sample Access Codes (format: XXX-XXX-XXX):")
    print("-" * 40)

    for i in range(10):
        code = generate_access_code()
        print(f"{i + 1:2}. {code}")


if __name__ == "__main__":
    main()