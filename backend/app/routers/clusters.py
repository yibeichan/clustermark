from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import models, schemas
from app.services.cluster_service import ClusterService

router = APIRouter()


@router.get("/{cluster_id}", response_model=schemas.Cluster)
async def get_cluster(cluster_id: str, db: Session = Depends(get_db)):
    cluster = db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster


@router.post("/{cluster_id}/annotate")
async def annotate_cluster(
    cluster_id: str, annotation: schemas.ClusterAnnotate, db: Session = Depends(get_db)
):
    service = ClusterService(db)
    return await service.annotate_cluster(cluster_id, annotation)


@router.get("/{cluster_id}/images")
async def get_cluster_images(cluster_id: str, db: Session = Depends(get_db)):
    service = ClusterService(db)
    return await service.get_cluster_images(cluster_id)


# Phase 3: New endpoints for paginated cluster review and outlier workflow


@router.get(
    "/{cluster_id}/images/paginated", response_model=schemas.PaginatedImagesResponse
)
async def get_cluster_images_paginated(
    cluster_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        20, ge=1, le=100, description="Images per page (recommended: 10, 20, or 50)"
    ),
    db: Session = Depends(get_db),
):
    """
    Get paginated images for cluster review.

    Returns images excluding outliers, with pagination metadata.
    Used in Step 1 of the annotation workflow (review all images).

    Args:
        cluster_id: UUID of the cluster
        page: Page number (1-indexed, default 1)
        page_size: Images per page (default 20, options: 10/20/50)
        db: Database session (injected)

    Returns:
        PaginatedImagesResponse with images and pagination metadata
    """
    service = ClusterService(db)
    return service.get_cluster_images_paginated(cluster_id, page, page_size)


@router.get("/{cluster_id}/outliers")
async def get_cluster_outliers(
    cluster_id: str,
    db: Session = Depends(get_db),
):
    """
    Get images marked as outliers for this cluster.

    Enables resume workflow: when user returns to a cluster with pre-existing
    outliers, this endpoint fetches them so they can be displayed/edited.

    Fixes data loss bug discovered in Phase 5 Round 6 code review.

    Args:
        cluster_id: UUID of the cluster
        db: Database session (injected)

    Returns:
        Dict with cluster_id, outliers list, and count
    """
    # Verify cluster exists
    cluster = db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    # Fetch outlier images
    outliers = (
        db.query(models.Image)
        .filter(
            models.Image.cluster_id == cluster_id,
            models.Image.annotation_status == "outlier",
        )
        .all()
    )

    return {"cluster_id": cluster_id, "outliers": outliers, "count": len(outliers)}


@router.post("/{cluster_id}/outliers")
async def mark_outliers(
    cluster_id: str,
    request: schemas.OutlierSelectionRequest,
    db: Session = Depends(get_db),
):
    """
    Mark selected images as outliers.

    Updates Image.annotation_status to 'outlier' and Cluster metadata.
    Used when user selects outlier images during review phase.

    Args:
        cluster_id: UUID of the cluster (must match request.cluster_id)
        request: Contains cluster_id and list of outlier image IDs
        db: Database session (injected)

    Returns:
        Dict with status and count of marked outliers
    """
    # Ensure cluster_id in path matches request body
    if str(cluster_id) != str(request.cluster_id):
        raise HTTPException(
            status_code=400,
            detail="cluster_id in path must match cluster_id in request body",
        )

    service = ClusterService(db)
    return service.mark_outliers(request)


@router.post("/{cluster_id}/annotate-batch")
async def annotate_batch(
    cluster_id: str,
    annotation: schemas.ClusterAnnotateBatch,
    db: Session = Depends(get_db),
):
    """
    Batch annotate all non-outlier images in cluster.

    This is the fast path (Path A) when no outliers exist, or the final step
    in Path B after outliers have been annotated individually.

    Updates all non-outlier images with the same label and marks cluster as completed.

    Args:
        cluster_id: UUID of the cluster
        annotation: Person name and whether it's a custom label
        db: Database session (injected)

    Returns:
        Dict with completion status
    """
    service = ClusterService(db)
    return service.annotate_cluster_batch(cluster_id, annotation)


@router.post("/annotate-outliers")
async def annotate_outliers(
    annotations: List[schemas.OutlierAnnotation], db: Session = Depends(get_db)
):
    """
    Annotate individual outlier images.

    Used in Path B workflow where user assigns different labels to
    each outlier image (or same label if they're all the same person).

    Args:
        annotations: List of image_id -> person_name mappings
        db: Database session (injected)

    Returns:
        Dict with status and count of annotated outliers
    """
    service = ClusterService(db)
    return service.annotate_outliers(annotations)
