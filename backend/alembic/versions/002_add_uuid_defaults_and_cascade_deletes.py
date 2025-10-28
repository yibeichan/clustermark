"""add_uuid_defaults_and_cascade_deletes

Revision ID: 002_uuid_cascade
Revises: 864dc2c3e6c1
Create Date: 2025-10-28

Addresses Codex code review P0 and P1 issues:
- P0: Add server_default for UUID primary keys (gen_random_uuid())
- P1: Add CASCADE deletes to all foreign key constraints
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_uuid_cascade'
down_revision = '864dc2c3e6c1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================
    # Part 1: Add UUID server defaults
    # ========================================

    # Enable pgcrypto extension for gen_random_uuid() if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Add server defaults for all UUID primary key columns
    op.alter_column('episodes', 'id',
                    server_default=sa.text('gen_random_uuid()'),
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)

    op.alter_column('clusters', 'id',
                    server_default=sa.text('gen_random_uuid()'),
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)

    op.alter_column('images', 'id',
                    server_default=sa.text('gen_random_uuid()'),
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)

    op.alter_column('split_annotations', 'id',
                    server_default=sa.text('gen_random_uuid()'),
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)

    op.alter_column('annotators', 'id',
                    server_default=sa.text('gen_random_uuid()'),
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)

    # ========================================
    # Part 2: Add CASCADE deletes to foreign keys
    # ========================================

    # Drop existing foreign key constraints (without CASCADE)
    op.drop_constraint('clusters_episode_id_fkey', 'clusters', type_='foreignkey')
    op.drop_constraint('images_cluster_id_fkey', 'images', type_='foreignkey')
    op.drop_constraint('images_episode_id_fkey', 'images', type_='foreignkey')
    op.drop_constraint('split_annotations_cluster_id_fkey', 'split_annotations', type_='foreignkey')

    # Recreate foreign key constraints with CASCADE
    op.create_foreign_key(
        'clusters_episode_id_fkey',
        'clusters', 'episodes',
        ['episode_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'images_cluster_id_fkey',
        'images', 'clusters',
        ['cluster_id'], ['id'],
        ondelete='CASCADE'
    )

    # images.episode_id without CASCADE - deletion cascades through Cluster (single path)
    op.create_foreign_key(
        'images_episode_id_fkey',
        'images', 'episodes',
        ['episode_id'], ['id']
    )

    op.create_foreign_key(
        'split_annotations_cluster_id_fkey',
        'split_annotations', 'clusters',
        ['cluster_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # ========================================
    # Part 1: Remove CASCADE from foreign keys
    # ========================================

    # Drop CASCADE foreign key constraints
    op.drop_constraint('split_annotations_cluster_id_fkey', 'split_annotations', type_='foreignkey')
    op.drop_constraint('images_episode_id_fkey', 'images', type_='foreignkey')
    op.drop_constraint('images_cluster_id_fkey', 'images', type_='foreignkey')
    op.drop_constraint('clusters_episode_id_fkey', 'clusters', type_='foreignkey')

    # Recreate foreign key constraints without CASCADE
    op.create_foreign_key(
        'clusters_episode_id_fkey',
        'clusters', 'episodes',
        ['episode_id'], ['id']
    )

    op.create_foreign_key(
        'images_cluster_id_fkey',
        'images', 'clusters',
        ['cluster_id'], ['id']
    )

    op.create_foreign_key(
        'images_episode_id_fkey',
        'images', 'episodes',
        ['episode_id'], ['id']
    )

    op.create_foreign_key(
        'split_annotations_cluster_id_fkey',
        'split_annotations', 'clusters',
        ['cluster_id'], ['id']
    )

    # ========================================
    # Part 2: Remove UUID server defaults
    # ========================================

    # Remove server defaults from UUID columns
    op.alter_column('annotators', 'id',
                    server_default=None,
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)

    op.alter_column('split_annotations', 'id',
                    server_default=None,
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)

    op.alter_column('images', 'id',
                    server_default=None,
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)

    op.alter_column('clusters', 'id',
                    server_default=None,
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)

    op.alter_column('episodes', 'id',
                    server_default=None,
                    existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
                    existing_nullable=False)
