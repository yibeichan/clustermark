"""increase_status_col_length

Revision ID: 5f9b4c0e64cd
Revises: 95fc7a05cf71
Create Date: 2026-01-15 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f9b4c0e64cd'
down_revision = '004_add_quality_attributes'
branch_labels = None
depends_on = None


def upgrade():
    # Increase length of status columns to 50 characters
    op.alter_column('episodes', 'status',
               existing_type=sa.String(length=20),
               type_=sa.String(length=50),
               existing_nullable=True,
               existing_server_default=sa.text("'pending'"))
               
    op.alter_column('clusters', 'annotation_status',
               existing_type=sa.String(length=20),
               type_=sa.String(length=50),
               existing_nullable=True,
               existing_server_default=sa.text("'pending'"))

    op.alter_column('images', 'annotation_status',
               existing_type=sa.String(length=20),
               type_=sa.String(length=50),
               existing_nullable=True,
               existing_server_default=sa.text("'pending'"))


def downgrade():
    # Revert length to 20 characters
    # Note: This may fail if there are values > 20 chars
    op.alter_column('episodes', 'status',
               existing_type=sa.String(length=50),
               type_=sa.String(length=20),
               existing_nullable=True,
               existing_server_default=sa.text("'pending'"))
               
    op.alter_column('clusters', 'annotation_status',
               existing_type=sa.String(length=50),
               type_=sa.String(length=20),
               existing_nullable=True,
               existing_server_default=sa.text("'pending'"))

    op.alter_column('images', 'annotation_status',
               existing_type=sa.String(length=50),
               type_=sa.String(length=20),
               existing_nullable=True,
               existing_server_default=sa.text("'pending'"))
