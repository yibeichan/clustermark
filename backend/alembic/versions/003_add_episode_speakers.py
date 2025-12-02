"""Add episode_speakers table for episode-specific speaker reference data

Revision ID: 003_add_episode_speakers
Revises: 002_uuid_cascade
Create Date: 2025-01-XX

This migration creates the episode_speakers table to store speaker data
from Friends TV show episodes. The data is loaded from backend/data/friends_speakers.tsv
and used to populate episode-specific dropdown options during annotation.

This is reference data (not user content) - no foreign keys to episodes table.
Denormalized season/episode columns enable fast lookups without joins.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003_add_episode_speakers"
down_revision = "002_uuid_cascade"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create episode_speakers table
    op.create_table(
        "episode_speakers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("speaker_name", sa.String(length=255), nullable=False),
        sa.Column("utterances", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "season",
            "episode_number",
            "speaker_name",
            name="uix_season_episode_speaker",
        ),
    )

    # Create composite index for fast episode lookups
    # Queries filter by (season, episode_number) to get speakers for an episode
    op.create_index(
        "idx_episode_speakers_season_episode",
        "episode_speakers",
        ["season", "episode_number"],
    )


def downgrade() -> None:
    # Drop index first, then table
    op.drop_index("idx_episode_speakers_season_episode", table_name="episode_speakers")
    op.drop_table("episode_speakers")
