import os
from pathlib import Path
from typing import List, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models import models, schemas
import uuid as uuid_pkg

class ClusterService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("uploads")

    async def annotate_cluster(self, cluster_id: str, annotation: schemas.ClusterAnnotate) -> Dict:
        cluster = self.db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        cluster.is_single_person = annotation.is_single_person
        cluster.person_name = annotation.person_name
        cluster.annotation_status = "completed"
        
        episode = self.db.query(models.Episode).filter(models.Episode.id == cluster.episode_id).first()
        if episode:
            episode.annotated_clusters += 1
            if episode.annotated_clusters >= episode.total_clusters:
                episode.status = "completed"
        
        self.db.commit()
        
        return {
            "cluster_id": str(cluster.id),
            "status": "completed",
            "is_single_person": cluster.is_single_person,
            "person_name": cluster.person_name
        }

    async def get_cluster_images(self, cluster_id: str) -> Dict:
        cluster = self.db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        images_by_track = {}
        for image_path in cluster.image_paths:
            filename = Path(image_path).name
            if 'scene_' in filename and 'track_' in filename:
                parts = filename.split('_')
                scene_idx = next(i for i, part in enumerate(parts) if part == 'scene') + 1
                track_idx = next(i for i, part in enumerate(parts) if part == 'track') + 1
                
                if scene_idx < len(parts) and track_idx < len(parts):
                    scene_track = f"scene_{parts[scene_idx]}_track_{parts[track_idx]}"
                    if scene_track not in images_by_track:
                        images_by_track[scene_track] = []
                    images_by_track[scene_track].append(image_path)
        
        return {
            "cluster_id": str(cluster.id),
            "cluster_name": cluster.cluster_name,
            "all_images": cluster.image_paths,
            "grouped_by_track": images_by_track
        }

    def get_cluster_images_paginated(
        self,
        cluster_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        Get paginated images for cluster review.

        Returns images excluding those marked as outliers, with pagination metadata.
        Uses idx_images_cluster_status index for efficient filtering.

        Args:
            cluster_id: UUID of the cluster
            page: Page number (1-indexed)
            page_size: Number of images per page

        Returns:
            Dict with cluster info, images, pagination metadata

        Raises:
            HTTPException: If cluster not found (404)
        """
        # Validate cluster exists
        cluster = self.db.query(models.Cluster).filter(
            models.Cluster.id == cluster_id
        ).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        # Query non-outlier images (uses idx_images_cluster_status index)
        query = self.db.query(models.Image).filter(
            models.Image.cluster_id == cluster_id,
            models.Image.annotation_status != "outlier"
        ).order_by(models.Image.id)  # Stable ordering for pagination

        total_count = query.count()
        offset = (page - 1) * page_size
        images = query.offset(offset).limit(page_size).all()

        return {
            "cluster_id": str(cluster.id),
            "cluster_name": cluster.cluster_name,
            "initial_label": cluster.initial_label,
            "images": images,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_next": offset + page_size < total_count,
            "has_prev": page > 1
        }

    def mark_outliers(self, request: schemas.OutlierSelectionRequest) -> Dict:
        """
        Mark selected images as outliers.

        Updates Image.annotation_status to 'outlier' and updates Cluster metadata.
        Operation is idempotent - safe to run multiple times.

        Args:
            request: Contains cluster_id and list of outlier image IDs

        Returns:
            Dict with status and count of marked outliers

        Raises:
            HTTPException: If cluster not found (404)
        """
        # Validate cluster exists first (Gemini CRITICAL: fail fast)
        cluster = self.db.query(models.Cluster).filter(
            models.Cluster.id == request.cluster_id
        ).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        # Update Image status in bulk (avoid N+1 queries)
        # Add cluster_id filter to prevent cross-cluster modifications (Gemini CRITICAL)
        if request.outlier_image_ids:
            self.db.query(models.Image).filter(
                models.Image.id.in_(request.outlier_image_ids),
                models.Image.cluster_id == request.cluster_id  # Security: verify ownership
            ).update(
                {"annotation_status": "outlier"},
                synchronize_session=False
            )

        # Recount total outliers from database (Gemini CRITICAL: ensure accuracy)
        # This makes the operation truly idempotent and handles retries correctly
        outlier_count = self.db.query(models.Image).filter(
            models.Image.cluster_id == request.cluster_id,
            models.Image.annotation_status == "outlier"
        ).count()

        cluster.has_outliers = outlier_count > 0
        cluster.outlier_count = outlier_count

        self.db.commit()
        return {
            "status": "outliers_marked",
            "count": outlier_count  # Return actual count from DB, not request length
        }

    def annotate_cluster_batch(
        self,
        cluster_id: str,
        annotation: schemas.ClusterAnnotateBatch
    ) -> Dict:
        """
        Batch annotate all non-outlier images in a cluster.

        This is the fast path (Path A) when no outliers exist, or the final step
        in Path B after outliers have been annotated individually.

        Updates:
        - Image.current_label and annotation_status for pending images
        - Cluster.person_name, is_single_person, annotation_status
        - Episode.annotated_clusters counter (only if not already completed)

        Args:
            cluster_id: UUID of the cluster
            annotation: Person name and whether it's a custom label

        Returns:
            Dict with completion status

        Raises:
            HTTPException: If cluster not found (404)
        """
        # Convert string UUID to UUID object if needed
        if isinstance(cluster_id, str):
            cluster_id = uuid_pkg.UUID(cluster_id)

        # Validate cluster exists first (Gemini HIGH: fail fast)
        cluster = self.db.query(models.Cluster).filter(
            models.Cluster.id == cluster_id
        ).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        # Check if cluster is already completed (Codex P1: prevent double-counting)
        cluster_was_already_completed = cluster.annotation_status == "completed"

        # Update only pending images (don't overwrite already-annotated outliers)
        self.db.query(models.Image).filter(
            models.Image.cluster_id == cluster_id,
            models.Image.annotation_status == "pending"
        ).update({
            "current_label": annotation.person_name,
            "annotation_status": "annotated",
            "annotated_at": func.now()
        }, synchronize_session=False)

        # Update cluster status
        cluster.person_name = annotation.person_name
        cluster.is_single_person = True
        cluster.annotation_status = "completed"

        # Update episode progress counter only if cluster wasn't already completed
        # This prevents double-counting on retries (Codex P1)
        if not cluster_was_already_completed:
            # Use with_for_update() to lock row and prevent race conditions (Gemini MEDIUM)
            episode = self.db.query(models.Episode).filter(
                models.Episode.id == cluster.episode_id
            ).with_for_update().first()

            if episode:
                episode.annotated_clusters += 1
                # Update episode status if all clusters annotated
                if episode.annotated_clusters >= episode.total_clusters:
                    episode.status = "completed"

        self.db.commit()
        return {"status": "completed"}

    def annotate_outliers(self, annotations: List[schemas.OutlierAnnotation]) -> Dict:
        """
        Annotate individual outlier images.

        Used in Path B workflow where user assigns different labels to
        each outlier image (or same label if they're all the same person).

        Args:
            annotations: List of image_id -> person_name mappings

        Returns:
            Dict with status and count of annotated outliers
        """
        # Handle empty list edge case
        if not annotations:
            return {"status": "outliers_annotated", "count": 0}

        # Fetch all images in single query to avoid N+1 (Gemini MEDIUM)
        image_ids = [annotation.image_id for annotation in annotations]
        images = self.db.query(models.Image).filter(
            models.Image.id.in_(image_ids)
        ).all()

        # Create map for O(1) lookup
        image_map = {image.id: image for image in images}

        # Update images in memory (single commit at end)
        for annotation in annotations:
            image = image_map.get(annotation.image_id)
            if image:
                image.current_label = annotation.person_name
                image.annotation_status = "annotated"
                image.annotated_at = func.now()

        self.db.commit()
        return {
            "status": "outliers_annotated",
            "count": len([a for a in annotations if a.image_id in image_map])
        }