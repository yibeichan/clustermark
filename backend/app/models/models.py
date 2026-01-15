import json
import uuid as uuid_pkg

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.database import Base


class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses
    Text(36) storing as stringified hex values for SQLite compatibility.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLUUID())
        else:
            return dialect.type_descriptor(Text(36))

    def process_bind_param(self, value, dialect):
        """Convert UUID to string for storage (works for both PostgreSQL and SQLite)."""
        if value is None:
            return value
        return str(value) if isinstance(value, uuid_pkg.UUID) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid_pkg.UUID):
            return uuid_pkg.UUID(value)
        return value


class TextArray(TypeDecorator):
    """
    Platform-independent text array.

    Stores PostgreSQL ARRAY(Text) natively. For SQLite (tests), stores JSON string.
    """

    impl = ARRAY(Text)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(Text))
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return json.loads(value)


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String(255), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), server_default=text("'pending'"))
    total_clusters = Column(Integer, nullable=True)
    annotated_clusters = Column(Integer, server_default=text("0"))
    season = Column(Integer, nullable=True)
    episode_number = Column(Integer, nullable=True)

    clusters = relationship(
        "Cluster", back_populates="episode", cascade="all, delete-orphan"
    )
    # Images belong to Cluster (primary parent). Episode relationship for queries only.
    # No cascade - deletion happens through Cluster (single cascade path: Episode → Cluster → Image)
    images = relationship("Image", back_populates="episode")


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))
    episode_id = Column(
        UUID(), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False
    )
    cluster_name = Column(String(100), nullable=False)
    image_paths = Column(TextArray())
    is_single_person = Column(Boolean, nullable=True)
    person_name = Column(String(255), nullable=True)
    annotation_status = Column(String(50), server_default=text("'pending'"))
    initial_label = Column(String(255), nullable=True)
    cluster_number = Column(Integer, nullable=True)
    has_outliers = Column(Boolean, server_default=text("false"))
    outlier_count = Column(Integer, server_default=text("0"))

    episode = relationship("Episode", back_populates="clusters")
    split_annotations = relationship(
        "SplitAnnotation", back_populates="cluster", cascade="all, delete-orphan"
    )
    images = relationship(
        "Image", back_populates="cluster", cascade="all, delete-orphan"
    )


class SplitAnnotation(Base):
    __tablename__ = "split_annotations"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))
    cluster_id = Column(
        UUID(), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False
    )
    scene_track_pattern = Column(String(100), nullable=False)
    person_name = Column(String(255), nullable=False)
    image_paths = Column(TextArray())

    cluster = relationship("Cluster", back_populates="split_annotations")


class Annotator(Base):
    __tablename__ = "annotators"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))
    session_token = Column(String(255), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_tasks = Column(Integer, server_default=text("0"))


class Image(Base):
    """
    Individual face image with annotation tracking.

    Images belong to both a Cluster (for grouping) and Episode (for metadata).
    Tracks initial label (from folder name) and current label (user-assigned).
    Supports outlier workflow where images can be marked as 'outlier' status.
    """

    __tablename__ = "images"
    __table_args__ = (
        UniqueConstraint("cluster_id", "file_path", name="uix_cluster_filepath"),
    )

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))
    cluster_id = Column(
        UUID(), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False
    )
    # episode_id FK without CASCADE - deletion cascades through Cluster (single path)
    episode_id = Column(UUID(), ForeignKey("episodes.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    filename = Column(String(255), nullable=False)
    initial_label = Column(String(255), nullable=True)
    current_label = Column(String(255), nullable=True)
    annotation_status = Column(String(50), server_default=text("'pending'"))
    annotated_at = Column(DateTime(timezone=True), nullable=True)
    is_custom_label = Column(Boolean, nullable=False, server_default=text("false"))
    quality_attributes = Column(TextArray())  # ['@poor', '@blurry', '@dark', '@profile', '@back']

    cluster = relationship("Cluster", back_populates="images")
    episode = relationship("Episode", back_populates="images")


class EpisodeSpeaker(Base):
    """
    Reference data for speakers in Friends episodes.

    Loaded from backend/data/friends_speakers.tsv during setup.
    Used to populate episode-specific dropdown options during annotation.

    This is static reference data, not user-generated content.
    No relationship to Episode table (denormalized for query performance).
    """

    __tablename__ = "episode_speakers"
    __table_args__ = (
        UniqueConstraint(
            "season",
            "episode_number",
            "speaker_name",
            name="uix_season_episode_speaker",
        ),
    )

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))
    season = Column(Integer, nullable=False)
    episode_number = Column(Integer, nullable=False)
    speaker_name = Column(
        String(255), nullable=False
    )  # Title case (e.g., "Rachel", "Mrs. Geller")
    utterances = Column(Integer, nullable=False)  # For sorting by frequency
