import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


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
    season: Optional[int] = None
    episode_number: Optional[int] = None

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
    cluster_number: Optional[int] = None
    has_outliers: bool = False
    outlier_count: int = 0

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


# Image schemas
class ImageBase(BaseModel):
    file_path: str
    filename: str


class ImageCreate(ImageBase):
    cluster_id: uuid.UUID
    episode_id: uuid.UUID
    initial_label: Optional[str] = None


class Image(ImageBase):
    id: uuid.UUID
    cluster_id: uuid.UUID
    episode_id: uuid.UUID
    initial_label: Optional[str] = None
    current_label: Optional[str] = None
    annotation_status: str
    annotated_at: Optional[datetime] = None
    is_custom_label: bool = False
    quality_attributes: List[str] = []

    class Config:
        from_attributes = True


# Paginated response schemas (for Phase 3)
class PaginatedImagesResponse(BaseModel):
    cluster_id: uuid.UUID
    cluster_name: str
    initial_label: Optional[str] = None
    images: List[Image]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# Outlier and batch annotation schemas (for Phase 3)
class OutlierSelectionRequest(BaseModel):
    cluster_id: uuid.UUID
    outlier_image_ids: List[uuid.UUID]


class ClusterAnnotateBatch(BaseModel):
    person_name: str
    is_custom_label: bool = False


class OutlierAnnotation(BaseModel):
    image_id: uuid.UUID
    person_name: str
    is_custom_label: bool = False
    quality_attributes: List[str] = []


# Phase 6b: Outlier fetch response schema
class OutlierImagesResponse(BaseModel):
    cluster_id: uuid.UUID
    outliers: List[Image]
    count: int


# Phase 7: Episode speakers response schema
class EpisodeSpeakersResponse(BaseModel):
    """
    Response for GET /episodes/{episode_id}/speakers endpoint.

    Returns speakers for a specific episode, sorted by utterance frequency.
    Used to populate episode-specific dropdown options during annotation.
    """

    episode_id: uuid.UUID
    season: Optional[int] = None
    episode_number: Optional[int] = None
    speakers: List[str]  # Speaker names in title case, sorted by frequency (desc)
