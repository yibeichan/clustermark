from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Episode(Base):
    __tablename__ = "episodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default="pending")
    total_clusters = Column(Integer)
    annotated_clusters = Column(Integer, default=0)
    
    clusters = relationship("Cluster", back_populates="episode")

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False)
    cluster_name = Column(String(100), nullable=False)
    image_paths = Column(ARRAY(Text))
    is_single_person = Column(Boolean)
    person_name = Column(String(255))
    annotation_status = Column(String(20), default="pending")

    # NEW: Label tracking
    initial_label = Column(String(255))  # Folder name as initial label

    episode = relationship("Episode", back_populates="clusters")
    split_annotations = relationship("SplitAnnotation", back_populates="cluster")

class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"), nullable=False)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False)

    # File info
    file_path = Column(Text, nullable=False)
    filename = Column(String(255), nullable=False)

    # Labels
    initial_label = Column(String(255))  # From folder name
    current_label = Column(String(255))  # Annotator's assigned label

    # Metadata
    annotation_status = Column(String(20), default="pending")  # pending/completed
    annotated_at = Column(DateTime(timezone=True))

    # Relationships
    cluster = relationship("Cluster")
    episode = relationship("Episode")

class SplitAnnotation(Base):
    __tablename__ = "split_annotations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id"), nullable=False)
    scene_track_pattern = Column(String(100), nullable=False)
    person_name = Column(String(255), nullable=False)
    image_paths = Column(ARRAY(Text))
    
    cluster = relationship("Cluster", back_populates="split_annotations")

class Annotator(Base):
    __tablename__ = "annotators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(255), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_tasks = Column(Integer, default=0)