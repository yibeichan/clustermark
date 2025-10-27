from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class EpisodeBase(BaseModel):
    name: str

class EpisodeCreate(EpisodeBase):
    pass

class Episode(EpisodeBase):
    id: uuid.UUID
    upload_timestamp: datetime
    status: str
    total_clusters: Optional[int] = None
    annotated_clusters: int = 0
    
    class Config:
        from_attributes = True

class ClusterBase(BaseModel):
    cluster_name: str
    image_paths: List[str]

class ClusterCreate(ClusterBase):
    episode_id: uuid.UUID

class ClusterAnnotate(BaseModel):
    is_single_person: bool
    person_name: Optional[str] = None

class Cluster(ClusterBase):
    id: uuid.UUID
    episode_id: uuid.UUID
    is_single_person: Optional[bool] = None
    person_name: Optional[str] = None
    annotation_status: str = "pending"
    initial_label: Optional[str] = None

    class Config:
        from_attributes = True

class SplitAnnotationBase(BaseModel):
    scene_track_pattern: str
    person_name: str
    image_paths: List[str]

class SplitAnnotationCreate(SplitAnnotationBase):
    cluster_id: uuid.UUID

class SplitAnnotation(SplitAnnotationBase):
    id: uuid.UUID
    cluster_id: uuid.UUID
    
    class Config:
        from_attributes = True

class AnnotatorBase(BaseModel):
    session_token: str

class AnnotatorCreate(AnnotatorBase):
    pass

class Annotator(AnnotatorBase):
    id: uuid.UUID
    created_at: datetime
    completed_tasks: int = 0

    class Config:
        from_attributes = True

# Image schemas for new annotation system
class ImageBase(BaseModel):
    file_path: str
    filename: str
    initial_label: Optional[str] = None
    current_label: Optional[str] = None
    annotation_status: str = "pending"

class Image(ImageBase):
    id: uuid.UUID
    cluster_id: uuid.UUID
    episode_id: uuid.UUID
    annotated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ImageAnnotate(BaseModel):
    label: str  # The assigned label