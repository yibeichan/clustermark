"""Initial schema with base tables

Revision ID: 000_initial
Revises:
Create Date: 2025-10-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create episodes table
    op.create_table('episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('upload_timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('total_clusters', sa.Integer(), nullable=True),
        sa.Column('annotated_clusters', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create clusters table
    op.create_table('clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('episode_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_name', sa.String(length=100), nullable=False),
        sa.Column('image_paths', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('is_single_person', sa.Boolean(), nullable=True),
        sa.Column('person_name', sa.String(length=255), nullable=True),
        sa.Column('annotation_status', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], name='fk_clusters_episode_id_episodes'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create split_annotations table
    op.create_table('split_annotations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scene_track_pattern', sa.String(length=100), nullable=False),
        sa.Column('person_name', sa.String(length=255), nullable=False),
        sa.Column('image_paths', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id'], name='fk_split_annotations_cluster_id_clusters'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create annotators table
    op.create_table('annotators',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_tasks', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token')
    )


def downgrade() -> None:
    op.drop_table('annotators')
    op.drop_table('split_annotations')
    op.drop_table('clusters')
    op.drop_table('episodes')
