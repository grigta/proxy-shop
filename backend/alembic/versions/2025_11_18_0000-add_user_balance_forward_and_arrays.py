"""add user balance_forward and convert telegram_id/myreferal_id to arrays

Revision ID: 2025_11_18_0000
Revises: 2025_11_14_0100
Create Date: 2025-11-18 00:00:00.000000

IMPORTANT SEMANTICS CHANGES:
1. telegram_id and myreferal_id are converted from scalar unique fields to ARRAY types.
   - The previous UNIQUE constraints on these fields are REMOVED.
   - Uniqueness is NO LONGER enforced at the database level after this migration.
   - Business logic in subsequent phases MUST handle duplicate detection if needed.
   - GIN indexes are added for efficient array containment queries.

2. Constraint name 'users_myreferal_id_key' is the expected unique constraint name
   from the previous schema. If your database uses a different constraint name,
   this migration will fail and must be adjusted to match the actual constraint name.

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision = '2025_11_18_0000'
down_revision = '2025_11_14_0100'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Convert users.telegram_id to ARRAY(BigInteger)
    op.add_column('users', sa.Column('telegram_id_array', ARRAY(sa.BigInteger()), nullable=True))
    op.execute('UPDATE users SET telegram_id_array = ARRAY[telegram_id] WHERE telegram_id IS NOT NULL')
    op.drop_column('users', 'telegram_id')
    op.alter_column('users', 'telegram_id_array', new_column_name='telegram_id')
    op.create_index('idx_users_telegram_id_gin', 'users', ['telegram_id'], unique=False, postgresql_using='gin')

    # 2. Add users.balance_forward with foreign key
    # NULL means user has their own balance; non-NULL references another user's user_id for balance forwarding
    op.add_column('users', sa.Column('balance_forward', sa.Integer(), nullable=True, comment='User key for balance forwarding (NULL = own balance, non-NULL = user_id to forward to)'))
    op.create_foreign_key('fk_users_balance_forward', 'users', 'users', ['balance_forward'], ['user_id'])
    op.create_index('idx_users_balance_forward', 'users', ['balance_forward'], unique=False)

    # 3. Convert users.myreferal_id to ARRAY(String(50))
    op.add_column('users', sa.Column('myreferal_id_array', ARRAY(sa.String(50)), nullable=True))
    op.execute('UPDATE users SET myreferal_id_array = ARRAY[myreferal_id] WHERE myreferal_id IS NOT NULL')
    op.drop_constraint('users_myreferal_id_key', 'users', type_='unique')
    op.drop_column('users', 'myreferal_id')
    op.alter_column('users', 'myreferal_id_array', new_column_name='myreferal_id')
    op.create_index('idx_users_myreferal_id_gin', 'users', ['myreferal_id'], unique=False, postgresql_using='gin')

    # 4. Add pptp_history fields
    op.add_column('pptp_history', sa.Column('resaled', sa.Boolean(), nullable=False, server_default='false', comment='Whether PPTP was resold (1) or invalid (0)'))
    op.add_column('pptp_history', sa.Column('user_key', sa.String(50), nullable=True, comment='User key (0 for invalid PPTP)'))
    op.create_index('idx_pptp_history_resaled', 'pptp_history', ['resaled'], unique=False)
    op.create_index('idx_pptp_history_user_key', 'pptp_history', ['user_key'], unique=False)


def downgrade():
    # 1. Rollback pptp_history changes
    op.drop_index('idx_pptp_history_user_key', table_name='pptp_history')
    op.drop_index('idx_pptp_history_resaled', table_name='pptp_history')
    op.drop_column('pptp_history', 'user_key')
    op.drop_column('pptp_history', 'resaled')

    # 2. Rollback users.myreferal_id to single String
    op.drop_index('idx_users_myreferal_id_gin', table_name='users')
    op.add_column('users', sa.Column('myreferal_id_single', sa.String(50), nullable=True))
    op.execute('UPDATE users SET myreferal_id_single = myreferal_id[1] WHERE myreferal_id IS NOT NULL AND array_length(myreferal_id, 1) > 0')
    op.drop_column('users', 'myreferal_id')
    op.alter_column('users', 'myreferal_id_single', new_column_name='myreferal_id')
    op.create_unique_constraint('users_myreferal_id_key', 'users', ['myreferal_id'])

    # 3. Rollback users.balance_forward
    op.drop_index('idx_users_balance_forward', table_name='users')
    op.drop_constraint('fk_users_balance_forward', 'users', type_='foreignkey')
    op.drop_column('users', 'balance_forward')

    # 4. Rollback users.telegram_id to single BigInteger
    op.drop_index('idx_users_telegram_id_gin', table_name='users')
    op.add_column('users', sa.Column('telegram_id_single', sa.BigInteger(), nullable=True))
    op.execute('UPDATE users SET telegram_id_single = telegram_id[1] WHERE telegram_id IS NOT NULL AND array_length(telegram_id, 1) > 0')
    op.drop_column('users', 'telegram_id')
    op.alter_column('users', 'telegram_id_single', new_column_name='telegram_id')
    op.create_unique_constraint('users_telegram_id_key', 'users', ['telegram_id'])
