"""add_heleket_payment_fields

Revision ID: 2025_11_14_0000
Revises: 2025_11_12_2000
Create Date: 2025-11-14 00:00:00.000000

Add Heleket payment fields to user_transactions table and make legacy address fields nullable.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025_11_14_0000'
down_revision: Union[str, None] = '2025_11_12_2000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Heleket payment fields and make address fields nullable for Heleket compatibility."""
    # Add new Heleket payment columns (nullable for backward compatibility with existing records)
    op.add_column('user_transactions', sa.Column('payment_uuid', sa.String(length=255), nullable=True, comment='Heleket payment UUID'))
    op.add_column('user_transactions', sa.Column('payment_url', sa.String(length=500), nullable=True, comment='Heleket payment URL'))
    op.add_column('user_transactions', sa.Column('order_id', sa.String(length=255), nullable=True, comment='Merchant order identifier'))
    
    # Create index for payment_uuid for fast webhook lookups
    op.create_index('idx_user_transactions_payment_uuid', 'user_transactions', ['payment_uuid'], unique=False)
    
    # Make existing address fields nullable for Heleket transactions
    # Heleket abstracts blockchain details, so these fields won't always be available
    op.alter_column('user_transactions', 'from_address',
                    existing_type=sa.String(length=255),
                    nullable=True)
    op.alter_column('user_transactions', 'to_address',
                    existing_type=sa.String(length=255),
                    nullable=True)


def downgrade() -> None:
    """Revert Heleket payment fields migration."""
    # Revert address fields to non-nullable
    # WARNING: This will fail if there are Heleket transactions with NULL addresses
    op.alter_column('user_transactions', 'to_address',
                    existing_type=sa.String(length=255),
                    nullable=False)
    op.alter_column('user_transactions', 'from_address',
                    existing_type=sa.String(length=255),
                    nullable=False)
    
    # Drop the payment_uuid index
    op.drop_index('idx_user_transactions_payment_uuid', table_name='user_transactions')
    
    # Drop Heleket payment columns
    op.drop_column('user_transactions', 'order_id')
    op.drop_column('user_transactions', 'payment_url')
    op.drop_column('user_transactions', 'payment_uuid')




