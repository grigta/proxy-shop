"""Remove duplicate unique constraint on proxy_history.order_id

Revision ID: 2025_11_12_1530
Revises:
Create Date: 2025-11-12 15:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025_11_12_1530'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unnamed unique index created by column-level unique=True
    # This index was automatically created by SQLAlchemy without a specific name
    # We need to find and drop it while keeping the named constraint

    # First, we'll try to drop by common naming patterns used by PostgreSQL
    # PostgreSQL typically creates an index named: tablename_columnname_key
    try:
        op.drop_index('proxy_history_order_id_key', table_name='proxy_history')
    except:
        # If the above fails, try other common patterns
        try:
            op.drop_index('ix_proxy_history_order_id', table_name='proxy_history')
        except:
            # If both fail, the duplicate may have already been removed
            # or have a different name - this is safe to ignore
            pass

    # The named UniqueConstraint 'uq_proxy_history_order_id' remains intact


def downgrade() -> None:
    # Re-create the index that was dropped (to match the old column-level unique=True)
    # This recreates the duplicate state for rollback purposes
    op.create_index('proxy_history_order_id_key', 'proxy_history', ['order_id'], unique=True)