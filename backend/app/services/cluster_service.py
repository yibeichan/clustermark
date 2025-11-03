import os
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models import models, schemas
import uuid as uuid_pkg


class ClusterService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("uploads")

    async def annotate_cluster(
        self, cluster_id: str, annotation: schemas.ClusterAnnotate
    ) -> Dict:
        cluster = (
            self.db.query(models.Cluster)
            .filter(models.Cluster.id == cluster_id)
            .first()
        )
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        cluster.is_single_person = annotation.is_single_person
        cluster.person_name = annotation.person_name
        cluster.annotation_status = "completed"

        episode = (
            self.db.query(models.Episode)
            .filter(models.Episode.id == cluster.episode_id)
            .first()
        )
        if episode:
            episode.annotated_clusters += 1
            if episode.annotated_clusters >= episode.total_clusters:
                episode.status = "completed"

        self.db.commit()

        return {
            "cluster_id": str(cluster.id),
            "status": "completed",
            "is_single_person": cluster.is_single_person,
            "person_name": cluster.person_name,
        }

    async def get_cluster_images(self, cluster_id: str) -> Dict:
        cluster = (
            self.db.query(models.Cluster)
            .filter(models.Cluster.id == cluster_id)
            .first()
        )
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        images_by_track = {}
        for image_path in cluster.image_paths:
            filename = Path(image_path).name
            if "scene_" in filename and "track_" in filename:
                parts = filename.split("_")
                scene_idx = (
                    next(i for i, part in enumerate(parts) if part == "scene") + 1
                )
                track_idx = (
                    next(i for i, part in enumerate(parts) if part == "track") + 1
                )

                if scene_idx < len(parts) and track_idx < len(parts):
                    scene_track = f"scene_{parts[scene_idx]}_track_{parts[track_idx]}"
                    if scene_track not in images_by_track:
                        images_by_track[scene_track] = []
                    images_by_track[scene_track].append(image_path)

        return {
            "cluster_id": str(cluster.id),
            "cluster_name": cluster.cluster_name,
            "all_images": cluster.image_paths,
            "grouped_by_track": images_by_track,
        }

    def get_cluster_images_paginated(
        self, cluster_id: str, page: int = 1, page_size: int = 20
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
        cluster = (
            self.db.query(models.Cluster)
            .filter(models.Cluster.id == cluster_id)
            .first()
        )
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        # Phase 6 Round 5 Fix (Codex P1): Include both pending AND outlier images
        # This allows users to deselect pre-existing outliers in the review workflow
        # Previously only showed "pending", making outliers invisible and immutable
        query = (
            self.db.query(models.Image)
            .filter(
                models.Image.cluster_id == cluster_id,
                models.Image.annotation_status.in_(["pending", "outlier"]),
            )
            .order_by(models.Image.id)
        )  # Stable ordering for pagination

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
            "has_prev": page > 1,
        }

    def mark_outliers(self, request: schemas.OutlierSelectionRequest) -> Dict:
        """
        Mark selected images as outliers (sync operation).

        Updates Image.annotation_status to 'outlier' for selected images.
        Resets previously-marked outliers that are NOT in the selection back to 'pending'.
        This enables the resume workflow where users can deselect outliers.

        Operation is idempotent - safe to run multiple times.

        Args:
            request: Contains cluster_id and list of outlier image IDs

        Returns:
            Dict with status and count of marked outliers

        Raises:
            HTTPException: If cluster not found (404)
        """
        # Validate cluster exists first (Gemini CRITICAL: fail fast)
        cluster = (
            self.db.query(models.Cluster)
            .filter(models.Cluster.id == request.cluster_id)
            .first()
        )
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        # Phase 6 Round 4 Fix (Codex P1): Reset deselected outliers
        # Unmark images that were outliers but are NOT in the new selection
        # This allows users to deselect outliers in the resume workflow
        if request.outlier_image_ids:
            # Mark selected images as outliers
            self.db.query(models.Image).filter(
                models.Image.id.in_(request.outlier_image_ids),
                models.Image.cluster_id
                == request.cluster_id,  # Security: verify ownership
            ).update({"annotation_status": "outlier"}, synchronize_session=False)

            # Reset images that are marked as outliers but NOT in the new selection
            self.db.query(models.Image).filter(
                models.Image.cluster_id == request.cluster_id,
                models.Image.annotation_status == "outlier",
                ~models.Image.id.in_(request.outlier_image_ids),  # NOT in selection
            ).update({"annotation_status": "pending"}, synchronize_session=False)
        else:
            # No outliers selected - reset ALL outliers to pending
            self.db.query(models.Image).filter(
                models.Image.cluster_id == request.cluster_id,
                models.Image.annotation_status == "outlier",
            ).update({"annotation_status": "pending"}, synchronize_session=False)

        # Recount total outliers from database (Gemini CRITICAL: ensure accuracy)
        # This makes the operation truly idempotent and handles retries correctly
        outlier_count = (
            self.db.query(models.Image)
            .filter(
                models.Image.cluster_id == request.cluster_id,
                models.Image.annotation_status == "outlier",
            )
            .count()
        )

        cluster.has_outliers = outlier_count > 0
        cluster.outlier_count = outlier_count

        self.db.commit()
        return {
            "status": "outliers_marked",
            "count": outlier_count,  # Return actual count from DB, not request length
        }

    def annotate_cluster_batch(
        self, cluster_id: str, annotation: schemas.ClusterAnnotateBatch
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

        # Codex P1: Lock cluster row FIRST to prevent race conditions
        # Two concurrent requests could both read "pending" status and double-increment
        cluster = (
            self.db.query(models.Cluster)
            .filter(models.Cluster.id == cluster_id)
            .with_for_update()
            .first()
        )
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        # Check if cluster is already completed (Codex P1: prevent double-counting)
        # Now this check happens AFTER acquiring lock, preventing race conditions
        cluster_was_already_completed = cluster.annotation_status == "completed"

        # Update only pending images (don't overwrite already-annotated outliers)
        self.db.query(models.Image).filter(
            models.Image.cluster_id == cluster_id,
            models.Image.annotation_status == "pending",
        ).update(
            {
                "current_label": annotation.person_name,
                "annotation_status": "annotated",
                "annotated_at": func.now(),
            },
            synchronize_session=False,
        )

        # Update cluster status
        cluster.person_name = annotation.person_name
        cluster.is_single_person = True
        cluster.annotation_status = "completed"

        # Update episode progress counter only if cluster wasn't already completed
        # This prevents double-counting on retries (Codex P1)
        if not cluster_was_already_completed:
            # Use with_for_update() to lock row and prevent race conditions (Gemini MEDIUM)
            episode = (
                self.db.query(models.Episode)
                .filter(models.Episode.id == cluster.episode_id)
                .with_for_update()
                .first()
            )

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

        Raises:
            HTTPException: If images don't exist, belong to different clusters,
                          or are not marked as outliers (400)
        """
        # Handle empty list edge case
        if not annotations:
            return {"status": "outliers_annotated", "count": 0}

        # Codex P1: Validate cluster ownership and outlier status to prevent
        # cross-cluster attacks and accidental updates to non-outlier images
        image_ids = [annotation.image_id for annotation in annotations]
        images = (
            self.db.query(models.Image).filter(models.Image.id.in_(image_ids)).all()
        )

        # Verify all requested images exist
        if len(images) != len(image_ids):
            found_ids = {img.id for img in images}
            missing_ids = set(image_ids) - found_ids
            raise HTTPException(
                status_code=400, detail=f"Images not found: {missing_ids}"
            )

        # Verify all images belong to the same cluster (prevent cross-cluster attacks)
        cluster_ids = {img.cluster_id for img in images}
        if len(cluster_ids) > 1:
            raise HTTPException(
                status_code=400, detail="All images must belong to the same cluster"
            )

        # Verify all images are marked as outliers (prevent accidental updates to pending images)
        non_outliers = [
            str(img.id) for img in images if img.annotation_status != "outlier"
        ]
        if non_outliers:
            raise HTTPException(
                status_code=400,
                detail=f"Images must have outlier status: {non_outliers}",
            )

        # Gemini HIGH: Group annotations by person_name to perform bulk updates
        # This avoids N+1 query problem (one UPDATE per annotation)
        updates_by_name = defaultdict(list)
        for annotation in annotations:
            updates_by_name[annotation.person_name].append(annotation.image_id)

        # Perform one bulk update per person_name (instead of N individual updates)
        # Gemini HIGH + Codex P1: Filter by both ID and outlier status for safety
        total_updated = 0
        for person_name, image_ids_to_update in updates_by_name.items():
            result = (
                self.db.query(models.Image)
                .filter(
                    models.Image.id.in_(image_ids_to_update),
                    models.Image.annotation_status
                    == "outlier",  # Gemini HIGH: explicit outlier check
                )
                .update(
                    {
                        "current_label": person_name,
                        "annotation_status": "annotated",
                        "annotated_at": func.now(),
                    },
                    synchronize_session=False,
                )
            )
            total_updated += result

        self.db.commit()
        return {"status": "outliers_annotated", "count": total_updated}

    def get_cluster_outliers(self, cluster_id: str) -> schemas.OutlierImagesResponse:
        """
        Get images marked as outliers for this cluster.

        Enables resume workflow: when user returns to a cluster with pre-existing
        outliers, this endpoint fetches them so they can be displayed/edited.

        Fixes data loss bug discovered in Phase 5 Round 6 code review.

        Args:
            cluster_id: UUID of the cluster

        Returns:
            OutlierImagesResponse schema object with cluster_id, outliers list, and count

        Raises:
            HTTPException: 404 if cluster not found or invalid UUID format
        """
        # Validate cluster_id format to prevent 500 errors on invalid UUIDs
        try:
            uuid_pkg.UUID(cluster_id)
        except ValueError:
            # Raise 404 for invalid UUID format (consistent with non-existent clusters)
            raise HTTPException(status_code=404, detail="Cluster not found")

        # Verify cluster exists
        cluster = (
            self.db.query(models.Cluster)
            .filter(models.Cluster.id == cluster_id)
            .first()
        )
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")

        # Fetch outlier images
        outliers = (
            self.db.query(models.Image)
            .filter(
                models.Image.cluster_id == cluster_id,
                models.Image.annotation_status == "outlier",
            )
            .all()
        )

        return schemas.OutlierImagesResponse(
            cluster_id=cluster.id, outliers=outliers, count=len(outliers)
        )
