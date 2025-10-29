"""fix_server_defaults_and_constraints

Revision ID: 864dc2c3e6c1
Revises: 1f898593c1f9
Create Date: 2025-10-28 19:04:58.289989

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '864dc2c3e6c1'
down_revision = '1f898593c1f9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add server defaults for episodes
    op.alter_column('episodes', 'status',
                    server_default=sa.text("'pending'"),
                    existing_type=sa.String(20))
    op.alter_column('episodes', 'annotated_clusters',
                    server_default=sa.text('0'),
                    existing_type=sa.Integer())

    # Add server defaults for clusters
    op.alter_column('clusters', 'annotation_status',
                    server_default=sa.text("'pending'"),
                    existing_type=sa.String(20))

    # Add server defaults for images
    op.alter_column('images', 'annotation_status',
                    server_default=sa.text("'pending'"),
                    existing_type=sa.String(20))

    # Add server defaults for annotators
    op.alter_column('annotators', 'completed_tasks',
                    server_default=sa.text('0'),
                    existing_type=sa.Integer())

    # Add unique constraint for images (cluster_id, file_path)
    op.create_unique_constraint('uix_cluster_filepath', 'images', ['cluster_id', 'file_path'])

    # Add index for filename lookups
    op.create_index('idx_images_filename', 'images', ['filename'])


def downgrade() -> None:
    # Drop indexes and constraints
    op.drop_index('idx_images_filename', 'images')
    op.drop_constraint('uix_cluster_filepath', 'images', type_='unique')

    # Remove server defaults
    op.alter_column('annotators', 'completed_tasks',
                    server_default=None,
                    existing_type=sa.Integer())
    op.alter_column('images', 'annotation_status',
                    server_default=None,
                    existing_type=sa.String(20))
    op.alter_column('clusters', 'annotation_status',
                    server_default=None,
                    existing_type=sa.String(20))
    op.alter_column('episodes', 'annotated_clusters',
                    server_default=None,
                    existing_type=sa.Integer())
    op.alter_column('episodes', 'status',
                    server_default=None,
                    existing_type=sa.String(20))