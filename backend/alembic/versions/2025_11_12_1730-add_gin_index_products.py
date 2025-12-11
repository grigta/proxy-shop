"""Add GIN index on products.product JSONB column

Revision ID: 2025_11_12_1730
Revises: 2025_11_12_1530
Create Date: 2025-11-12 17:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2025_11_12_1730'
down_revision: Union[str, None] = '2025_11_12_1530'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add GIN index on products.product JSONB column for efficient filtering"""

    # Create GIN index for JSONB column
    # This significantly improves performance for queries using:
    # - @> operator (contains)
    # - -> operator (extract field)
    # - ->> operator (extract field as text)
    # - ? operator (has key)
    op.create_index(
        'idx_products_product_gin',
        'products',
        ['product'],
        unique=False,
        postgresql_using='gin'
    )

    print("✅ Added GIN index on products.product for optimized JSONB filtering")


def downgrade() -> None:
    """Remove GIN index from products.product column"""

    op.drop_index('idx_products_product_gin', table_name='products')

    print("✅ Removed GIN index from products.product")