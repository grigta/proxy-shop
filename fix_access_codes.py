#!/usr/bin/env python3
"""
Script to fix access codes that were incorrectly generated during migration.
Updates access codes that don't match the XXX-XXX-XXX format.
"""

import re
import secrets
import string
import psycopg2

# PostgreSQL connection
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'proxy_shop',
    'user': 'postgres',
    'password': 'Secure_ProxyShop_Password_2024!'
}

# Correct format pattern: XXX-XXX-XXX (uppercase letters/digits with dashes)
CORRECT_FORMAT = re.compile(r'^[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}$')


def generate_access_code() -> str:
    """
    Generate a random access code in format XXX-XXX-XXX.
    Excludes confusing characters: 0/O, 1/I
    """
    allowed_chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')

    groups = []
    for _ in range(3):
        group = ''.join(secrets.choice(allowed_chars) for _ in range(3))
        groups.append(group)

    return '-'.join(groups)


def fix_access_codes():
    """Find and fix all incorrectly formatted access codes."""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    try:
        # Get all access codes
        cur.execute("SELECT user_id, access_code FROM users ORDER BY user_id")
        users = cur.fetchall()

        # Find users with incorrect access codes
        to_fix = []
        for user_id, access_code in users:
            if not CORRECT_FORMAT.match(access_code or ''):
                to_fix.append((user_id, access_code))

        print(f"Total users: {len(users)}")
        print(f"Users with incorrect access codes: {len(to_fix)}")

        if not to_fix:
            print("No access codes need fixing!")
            return

        print("\nUsers to fix:")
        for user_id, old_code in to_fix:
            print(f"  ID {user_id}: {old_code}")

        # Get existing codes to avoid duplicates
        cur.execute("SELECT access_code FROM users")
        existing_codes = set(row[0] for row in cur.fetchall())

        # Generate new codes and update
        print("\nFixing access codes...")
        fixed = 0

        for user_id, old_code in to_fix:
            # Generate unique new code
            new_code = generate_access_code()
            while new_code in existing_codes:
                new_code = generate_access_code()
            existing_codes.add(new_code)

            # Update in database
            cur.execute(
                "UPDATE users SET access_code = %s WHERE user_id = %s",
                (new_code, user_id)
            )
            print(f"  ID {user_id}: {old_code} -> {new_code}")
            fixed += 1

        conn.commit()
        print(f"\nFixed {fixed} access codes!")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    fix_access_codes()
