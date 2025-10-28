"""Add image-level annotations and label tracking

Revision ID: 001_add_images
Revises:
Create Date: 2025-10-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_images'
down_revision = '000_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add initial_label column to clusters table
    op.add_column('clusters', sa.Column('initial_label', sa.String(length=255), nullable=True))

    # Create images table
    op.create_table('images',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('initial_label', sa.String(length=255), nullable=True),
        sa.Column('current_label', sa.String(length=255), nullable=True),
        sa.Column('annotation_status', sa.String(length=20), nullable=True),
        sa.Column('annotated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], ),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop images table
    op.drop_table('images')

    # Remove initial_label column from clusters table
    op.drop_column('clusters', 'initial_label')
