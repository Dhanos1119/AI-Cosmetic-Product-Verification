"""Add integrity fields to marketplace_listings

Revision ID: 63a19b8820f1
Revises: 52c257924574
Create Date: 2026-09-25 11:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '63a19b8820f1'
down_revision: Union[str, Sequence[str], None] = '52c257924574'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add non-destructive integrity fields to marketplace_listings
    op.add_column('marketplace_listings', sa.Column('search_query', sa.String(length=500), nullable=True))
    op.add_column('marketplace_listings', sa.Column('listing_status', sa.String(length=50), nullable=False, server_default='UNAVAILABLE'))
    op.add_column('marketplace_listings', sa.Column('passed_match_threshold', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('marketplace_listings', 'passed_match_threshold')
    op.drop_column('marketplace_listings', 'listing_status')
    op.drop_column('marketplace_listings', 'search_query')
