"""add quality_attributes to images

Revision ID: 004_add_quality_attributes
Revises: 95fc7a05cf71
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_quality_attributes'
down_revision = '95fc7a05cf71'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use ARRAY(Text) for PostgreSQL - this migration is PostgreSQL-specific.
    # SQLite compatibility is handled by the TextArray TypeDecorator in models.py
    # which serializes the list to JSON/string, so no ARRAY type is needed there.
    op.add_column(
        'images',
        sa.Column(
            'quality_attributes',
            postgresql.ARRAY(Text()),
            nullable=True
        )
    )


def downgrade() -> None:
    op.drop_column('images', 'quality_attributes')
