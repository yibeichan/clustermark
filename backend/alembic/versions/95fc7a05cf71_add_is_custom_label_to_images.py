"""add is_custom_label to images

Revision ID: 95fc7a05cf71
Revises: 003_add_episode_speakers
Create Date: 2026-01-09 23:35:10.060807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95fc7a05cf71'
down_revision = '003_add_episode_speakers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('images', sa.Column('is_custom_label', sa.Boolean(), server_default=sa.text('false'), nullable=True))


def downgrade() -> None:
    op.drop_column('images', 'is_custom_label')