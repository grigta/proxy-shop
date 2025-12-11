#!/usr/bin/env python3
"""
Migration script to transfer users from MySQL dump to PostgreSQL.
Maps MySQL structure to PostgreSQL structure.
"""

import re
import secrets
import string
import psycopg2
from psycopg2.extras import execute_values
from decimal import Decimal

# PostgreSQL connection
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'proxy_shop',
    'user': 'postgres',
    'password': 'Secure_ProxyShop_Password_2024!'
}

def generate_access_code():
    """Generate access code in format XXX-XXX-XXX (uppercase letters/digits, excluding confusing chars)"""
    # Exclude confusing characters: 0/O, 1/I
    allowed_chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')

    groups = []
    for _ in range(3):
        group = ''.join(secrets.choice(allowed_chars) for _ in range(3))
        groups.append(group)

    return '-'.join(groups)

def parse_mysql_dump(dump_path):
    """Parse MySQL dump and extract users data"""
    users = []

    with open(dump_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find INSERT INTO users VALUES
    pattern = r"INSERT INTO `users` VALUES (.+?);"
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print("No users data found in dump")
        return []

    values_str = match.group(1)

    # Parse individual user records
    # Format: (id,username,language,balance,user_referal_id,myreferal_id,referal_quantity,referal_profit,token)
    record_pattern = r"\((\d+),'([^']*|null)','([^']*|empty)','?([0-9.]+)'?,'([^']*|null)','([^']*|null)',(\d+),([0-9.]+),([^)]*)\)"

    for match in re.finditer(record_pattern, values_str):
        telegram_id = int(match.group(1))
        username = match.group(2) if match.group(2) != 'null' else None
        language = match.group(3)
        if language == 'empty':
            language = 'ru'  # Default to Russian
        balance = Decimal(match.group(4))
        user_referal_id = match.group(5) if match.group(5) != 'null' else None
        myreferal_id = match.group(6) if match.group(6) != 'null' else None
        referal_quantity = int(match.group(7))

        users.append({
            'telegram_id': telegram_id,
            'username': username,
            'language': language[:10] if language else 'ru',  # Limit to 10 chars
            'balance': balance,
            'user_referal_id': user_referal_id,
            'myreferal_id': myreferal_id,
            'referal_quantity': referal_quantity
        })

    return users

def deduplicate_users(users):
    """Remove duplicate telegram_ids, keeping the one with highest balance"""
    seen = {}
    for user in users:
        tid = user['telegram_id']
        if tid not in seen or user['balance'] > seen[tid]['balance']:
            seen[tid] = user
    return list(seen.values())

def migrate_users(users):
    """Insert users into PostgreSQL"""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    try:
        # Get existing telegram_ids to avoid duplicates
        cur.execute("SELECT unnest(telegram_id) FROM users WHERE telegram_id IS NOT NULL")
        existing_tids = set(row[0] for row in cur.fetchall())
        print(f"Found {len(existing_tids)} existing telegram IDs in database")

        # Filter out users that already exist
        new_users = [u for u in users if u['telegram_id'] not in existing_tids]
        print(f"New users to migrate: {len(new_users)}")

        if not new_users:
            print("No new users to migrate")
            return

        # Generate unique access codes
        cur.execute("SELECT access_code FROM users")
        existing_codes = set(row[0] for row in cur.fetchall())

        inserted = 0
        skipped = 0

        for user in new_users:
            # Generate unique access code
            access_code = generate_access_code()
            while access_code in existing_codes:
                access_code = generate_access_code()
            existing_codes.add(access_code)

            try:
                # Map language properly
                lang = user['language']
                if lang in ['eng', 'en']:
                    lang = 'en'
                elif lang in ['ru', 'rus']:
                    lang = 'ru'
                else:
                    lang = 'ru'

                # Prepare myreferal_id as array
                myreferal_array = None
                if user['myreferal_id'] and user['myreferal_id'] != 'null':
                    myreferal_array = [user['myreferal_id']]

                cur.execute("""
                    INSERT INTO users (
                        telegram_id, username, language, balance,
                        referal_quantity, access_code, platform_registered,
                        is_admin, is_blocked, myreferal_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, 'telegram', false, false, %s
                    )
                    ON CONFLICT DO NOTHING
                """, (
                    [user['telegram_id']],  # telegram_id as array
                    user['username'],
                    lang,
                    user['balance'],
                    user['referal_quantity'],
                    access_code,
                    myreferal_array
                ))

                if cur.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1

            except Exception as e:
                print(f"Error inserting user {user['telegram_id']}: {e}")
                skipped += 1
                continue

        conn.commit()
        print(f"\nMigration complete!")
        print(f"Inserted: {inserted}")
        print(f"Skipped: {skipped}")

        # Verify
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        print(f"Total users in database: {total}")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def main():
    dump_path = '/root/proxy-shop/pptp_dump.sql'

    print("Parsing MySQL dump...")
    users = parse_mysql_dump(dump_path)
    print(f"Found {len(users)} user records in dump")

    print("\nDeduplicating users...")
    users = deduplicate_users(users)
    print(f"Unique users: {len(users)}")

    print("\nMigrating to PostgreSQL...")
    migrate_users(users)

if __name__ == '__main__':
    main()
