from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, ARRAY, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
from app.database import Base

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name = Column(String(255), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), server_default=text("'pending'"))
    total_clusters = Column(Integer, nullable=True)
    annotated_clusters = Column(Integer, server_default=text('0'))
    season = Column(Integer, nullable=True)
    episode_number = Column(Integer, nullable=True)

    clusters = relationship("Cluster", back_populates="episode", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="episode", cascade="all, delete-orphan")

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    cluster_name = Column(String(100), nullable=False)
    image_paths = Column(ARRAY(Text))
    is_single_person = Column(Boolean, nullable=True)
    person_name = Column(String(255), nullable=True)
    annotation_status = Column(String(20), server_default=text("'pending'"))
    initial_label = Column(String(255), nullable=True)
    cluster_number = Column(Integer, nullable=True)
    has_outliers = Column(Boolean, server_default=text('false'))
    outlier_count = Column(Integer, server_default=text('0'))

    episode = relationship("Episode", back_populates="clusters")
    split_annotations = relationship("SplitAnnotation", back_populates="cluster", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="cluster", cascade="all, delete-orphan")

class SplitAnnotation(Base):
    __tablename__ = "split_annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    scene_track_pattern = Column(String(100), nullable=False)
    person_name = Column(String(255), nullable=False)
    image_paths = Column(ARRAY(Text))

    cluster = relationship("Cluster", back_populates="split_annotations")

class Annotator(Base):
    __tablename__ = "annotators"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    session_token = Column(String(255), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_tasks = Column(Integer, server_default=text('0'))

class Image(Base):
    """
    Individual face image with annotation tracking.

    Images belong to both a Cluster (for grouping) and Episode (for metadata).
    Tracks initial label (from folder name) and current label (user-assigned).
    Supports outlier workflow where images can be marked as 'outlier' status.
    """
    __tablename__ = "images"
    __table_args__ = (
        UniqueConstraint('cluster_id', 'file_path', name='uix_cluster_filepath'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(Text, nullable=False)
    filename = Column(String(255), nullable=False)
    initial_label = Column(String(255), nullable=True)
    current_label = Column(String(255), nullable=True)
    annotation_status = Column(String(20), server_default=text("'pending'"))
    annotated_at = Column(DateTime(timezone=True), nullable=True)

    cluster = relationship("Cluster", back_populates="images")
    episode = relationship("Episode", back_populates="images")
