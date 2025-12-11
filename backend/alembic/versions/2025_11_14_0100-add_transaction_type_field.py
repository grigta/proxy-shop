"""add transaction_type field

Revision ID: 2025_11_14_0100
Revises: 2025_11_14_0000
Create Date: 2025-11-14 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025_11_14_0100'
down_revision: Union[str, None] = '2025_11_14_0000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add transaction_type field to user_transactions table."""
    # Add transaction_type column with default value 'legacy' for existing rows
    op.add_column(
        'user_transactions',
        sa.Column(
            'transaction_type',
            sa.String(length=20),
            nullable=True,
            comment='Transaction source: legacy or heleket'
        )
    )
    
    # Update existing rows to have 'legacy' as default
    op.execute(
        """
        UPDATE user_transactions 
        SET transaction_type = 'legacy' 
        WHERE transaction_type IS NULL
        """
    )
    
    # Update rows with payment_uuid to be 'heleket'
    op.execute(
        """
        UPDATE user_transactions 
        SET transaction_type = 'heleket' 
        WHERE payment_uuid IS NOT NULL
        """
    )


def downgrade() -> None:
    """Remove transaction_type field from user_transactions table."""
    op.drop_column('user_transactions', 'transaction_type')

