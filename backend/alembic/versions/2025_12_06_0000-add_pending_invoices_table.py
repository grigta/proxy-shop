"""add_pending_invoices_table

Revision ID: 2025_12_06_0000
Revises: 2025_11_18_0000
Create Date: 2025-12-06 00:00:00.000000

Add pending_invoices table to store original invoice amounts.
This fixes the issue where Heleket sends crypto amounts in merchant_amount
instead of USD, causing incorrect crediting (e.g., $0.00 instead of $35).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025_12_06_0000'
down_revision: Union[str, None] = '2025_11_18_0000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pending_invoices table for tracking original invoice amounts."""
    op.create_table(
        'pending_invoices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('payment_uuid', sa.String(length=255), nullable=False, comment='Heleket payment UUID'),
        sa.Column('order_id', sa.String(length=255), nullable=False, comment='Merchant order identifier'),
        sa.Column('amount_usd', sa.Numeric(precision=10, scale=2), nullable=False, comment='Original invoice amount in USD'),
        sa.Column('status', sa.String(length=20), server_default='pending', comment='pending/completed/expired'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expired_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('webhook_amount', sa.Numeric(precision=20, scale=8), nullable=True, comment='Amount from webhook for comparison'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_uuid'),
        sa.UniqueConstraint('order_id')
    )

    # Create indexes for fast lookups
    op.create_index('idx_pending_invoices_user_id', 'pending_invoices', ['user_id'], unique=False)
    op.create_index('idx_pending_invoices_status', 'pending_invoices', ['status'], unique=False)
    op.create_index('idx_pending_invoices_created_at', 'pending_invoices', ['created_at'], unique=False)


def downgrade() -> None:
    """Drop pending_invoices table."""
    op.drop_index('idx_pending_invoices_created_at', table_name='pending_invoices')
    op.drop_index('idx_pending_invoices_status', table_name='pending_invoices')
    op.drop_index('idx_pending_invoices_user_id', table_name='pending_invoices')
    op.drop_table('pending_invoices')
