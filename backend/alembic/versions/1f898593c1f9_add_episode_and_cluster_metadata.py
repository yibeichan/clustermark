"""add_episode_and_cluster_metadata

Revision ID: 1f898593c1f9
Revises: 001_add_images
Create Date: 2025-10-28 17:50:54.922546

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1f898593c1f9'
down_revision = '001_add_images'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add episode metadata columns
    op.add_column('episodes', sa.Column('season', sa.Integer(), nullable=True))
    op.add_column('episodes', sa.Column('episode_number', sa.Integer(), nullable=True))

    # Add cluster metadata columns
    op.add_column('clusters', sa.Column('cluster_number', sa.Integer(), nullable=True))
    op.add_column('clusters', sa.Column('has_outliers', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('clusters', sa.Column('outlier_count', sa.Integer(), nullable=True, server_default='0'))

    # Create indexes for performance
    op.create_index('idx_episodes_season_episode', 'episodes', ['season', 'episode_number'])
    op.create_index('idx_images_cluster_status', 'images', ['cluster_id', 'annotation_status'])
    op.create_index('idx_clusters_episode', 'clusters', ['episode_id'])
    op.create_index('idx_images_episode', 'images', ['episode_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_images_episode', 'images')
    op.drop_index('idx_clusters_episode', 'clusters')
    op.drop_index('idx_images_cluster_status', 'images')
    op.drop_index('idx_episodes_season_episode', 'episodes')

    # Remove cluster metadata columns
    op.drop_column('clusters', 'outlier_count')
    op.drop_column('clusters', 'has_outliers')
    op.drop_column('clusters', 'cluster_number')

    # Remove episode metadata columns
    op.drop_column('episodes', 'episode_number')
    op.drop_column('episodes', 'season')