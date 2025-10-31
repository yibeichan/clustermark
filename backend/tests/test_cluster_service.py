"""
Test suite for ClusterService Phase 3 functionality.

Tests cover:
- Paginated image retrieval with various scenarios
- Outlier marking and cluster metadata updates
- Batch annotation excluding outliers
- Individual outlier annotation
- Episode progress tracking
- Edge cases (empty clusters, all outliers, etc.)
"""

import pytest
from fastapi import HTTPException
from app.services.cluster_service import ClusterService
from app.models import models, schemas
from sqlalchemy.sql import func


@pytest.fixture
def sample_episode_with_images(test_db):
    """
    Create a sample Episode with Cluster and Images for testing.

    Structure:
    - 1 Episode (Season 1, Episode 5)
    - 1 Cluster with 25 images (for pagination tests)
    - All images initially pending, label="cluster-23"
    """
    episode = models.Episode(
        name="Friends_S01E05",
        total_clusters=2,
        annotated_clusters=0,
        status="pending",
        season=1,
        episode_number=5
    )
    test_db.add(episode)
    test_db.flush()

    cluster = models.Cluster(
        episode_id=episode.id,
        cluster_name="S01E05_cluster-23",
        image_paths=None,  # Phase 3 uses Image table, not ARRAY field
        initial_label="cluster-23",
        cluster_number=23,
        has_outliers=False,
        outlier_count=0
    )
    test_db.add(cluster)
    test_db.flush()

    # Create 25 Image records
    for i in range(25):
        image = models.Image(
            cluster_id=cluster.id,
            episode_id=episode.id,
            file_path=f"uploads/test/scene_0_track_1_frame_{i:03d}.jpg",
            filename=f"scene_0_track_1_frame_{i:03d}.jpg",
            initial_label="cluster-23",
            annotation_status="pending"
        )
        test_db.add(image)

    test_db.commit()
    test_db.refresh(episode)
    test_db.refresh(cluster)

    return {"episode": episode, "cluster": cluster}


@pytest.fixture
def sample_cluster_with_outliers(test_db):
    """
    Create a cluster with some images marked as outliers.

    Structure:
    - 1 Episode
    - 1 Cluster with 10 images
    - 3 images marked as outliers
    - 7 images pending
    """
    episode = models.Episode(
        name="test_episode_outliers",
        total_clusters=1,
        annotated_clusters=0,
        status="pending"
    )
    test_db.add(episode)
    test_db.flush()

    cluster = models.Cluster(
        episode_id=episode.id,
        cluster_name="test_cluster_outliers",
        image_paths=None,  # Phase 3 uses Image table, not ARRAY field
        initial_label="test-label",
        has_outliers=True,
        outlier_count=3
    )
    test_db.add(cluster)
    test_db.flush()

    # Create 10 images: 3 outliers, 7 pending
    outlier_image_ids = []
    for i in range(10):
        status = "outlier" if i < 3 else "pending"
        image = models.Image(
            cluster_id=cluster.id,
            episode_id=episode.id,
            file_path=f"uploads/test/image_{i}.jpg",
            filename=f"image_{i}.jpg",
            initial_label="test-label",
            annotation_status=status
        )
        test_db.add(image)
        test_db.flush()
        if status == "outlier":
            outlier_image_ids.append(image.id)

    test_db.commit()
    test_db.refresh(episode)
    test_db.refresh(cluster)

    return {"episode": episode, "cluster": cluster, "outlier_ids": outlier_image_ids}


class TestGetClusterImagesPaginated:
    """Test paginated image retrieval."""

    def test_pagination_first_page(self, test_db, sample_episode_with_images):
        """Test retrieving first page of images."""
        service = ClusterService(test_db)
        cluster_id = str(sample_episode_with_images["cluster"].id)

        result = service.get_cluster_images_paginated(cluster_id, page=1, page_size=10)

        assert result["cluster_id"] == cluster_id
        assert result["cluster_name"] == "S01E05_cluster-23"
        assert result["initial_label"] == "cluster-23"
        assert len(result["images"]) == 10
        assert result["total_count"] == 25
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["has_next"] is True
        assert result["has_prev"] is False

    def test_pagination_middle_page(self, test_db, sample_episode_with_images):
        """Test retrieving middle page of images."""
        service = ClusterService(test_db)
        cluster_id = str(sample_episode_with_images["cluster"].id)

        result = service.get_cluster_images_paginated(cluster_id, page=2, page_size=10)

        assert len(result["images"]) == 10
        assert result["page"] == 2
        assert result["has_next"] is True
        assert result["has_prev"] is True

    def test_pagination_last_page(self, test_db, sample_episode_with_images):
        """Test retrieving last page with partial results."""
        service = ClusterService(test_db)
        cluster_id = str(sample_episode_with_images["cluster"].id)

        result = service.get_cluster_images_paginated(cluster_id, page=3, page_size=10)

        assert len(result["images"]) == 5  # 25 total, 10 per page, page 3 has 5
        assert result["page"] == 3
        assert result["has_next"] is False
        assert result["has_prev"] is True

    def test_pagination_excludes_outliers(self, test_db, sample_cluster_with_outliers):
        """Test that pagination excludes images marked as outliers."""
        service = ClusterService(test_db)
        cluster_id = str(sample_cluster_with_outliers["cluster"].id)

        result = service.get_cluster_images_paginated(cluster_id, page=1, page_size=20)

        # Should return 7 images (10 total - 3 outliers)
        assert len(result["images"]) == 7
        assert result["total_count"] == 7

        # Verify none are outliers
        for img in result["images"]:
            assert img.annotation_status != "outlier"

    def test_pagination_empty_cluster(self, test_db, sample_episode_with_images):
        """Test pagination on empty cluster (all marked as outliers)."""
        service = ClusterService(test_db)
        cluster = sample_episode_with_images["cluster"]

        # Mark all images as outliers
        test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id
        ).update({"annotation_status": "outlier"})
        test_db.commit()

        result = service.get_cluster_images_paginated(str(cluster.id), page=1, page_size=10)

        assert len(result["images"]) == 0
        assert result["total_count"] == 0
        assert result["has_next"] is False
        assert result["has_prev"] is False

    def test_pagination_invalid_cluster(self, test_db):
        """Test that invalid cluster_id raises HTTPException."""
        service = ClusterService(test_db)

        with pytest.raises(HTTPException) as exc_info:
            service.get_cluster_images_paginated("00000000-0000-0000-0000-000000000000", page=1, page_size=10)

        assert exc_info.value.status_code == 404

    def test_pagination_different_page_sizes(self, test_db, sample_episode_with_images):
        """Test pagination with different page sizes (10, 20, 50)."""
        service = ClusterService(test_db)
        cluster_id = str(sample_episode_with_images["cluster"].id)

        # Page size 20
        result_20 = service.get_cluster_images_paginated(cluster_id, page=1, page_size=20)
        assert len(result_20["images"]) == 20
        assert result_20["has_next"] is True

        # Page size 50
        result_50 = service.get_cluster_images_paginated(cluster_id, page=1, page_size=50)
        assert len(result_50["images"]) == 25  # All images fit on one page
        assert result_50["has_next"] is False


class TestMarkOutliers:
    """Test outlier marking functionality."""

    def test_mark_outliers_updates_image_status(self, test_db, sample_episode_with_images):
        """Test that marking outliers updates Image.annotation_status."""
        service = ClusterService(test_db)
        cluster = sample_episode_with_images["cluster"]

        # Get first 3 image IDs
        images = test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id
        ).limit(3).all()
        outlier_ids = [img.id for img in images]

        request = schemas.OutlierSelectionRequest(
            cluster_id=cluster.id,
            outlier_image_ids=outlier_ids
        )

        result = service.mark_outliers(request)

        assert result["status"] == "outliers_marked"
        assert result["count"] == 3

        # Verify images are marked as outliers
        for img_id in outlier_ids:
            img = test_db.query(models.Image).filter(models.Image.id == img_id).first()
            assert img.annotation_status == "outlier"

    def test_mark_outliers_updates_cluster_metadata(self, test_db, sample_episode_with_images):
        """Test that marking outliers updates Cluster.has_outliers and outlier_count."""
        service = ClusterService(test_db)
        cluster = sample_episode_with_images["cluster"]

        # Get first 5 image IDs
        images = test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id
        ).limit(5).all()
        outlier_ids = [img.id for img in images]

        request = schemas.OutlierSelectionRequest(
            cluster_id=cluster.id,
            outlier_image_ids=outlier_ids
        )

        service.mark_outliers(request)

        # Refresh cluster and verify metadata
        test_db.refresh(cluster)
        assert cluster.has_outliers is True
        assert cluster.outlier_count == 5

    def test_mark_outliers_idempotency(self, test_db, sample_episode_with_images):
        """Test that marking outliers twice is idempotent (safe to run multiple times)."""
        service = ClusterService(test_db)
        cluster = sample_episode_with_images["cluster"]

        images = test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id
        ).limit(3).all()
        outlier_ids = [img.id for img in images]

        request = schemas.OutlierSelectionRequest(
            cluster_id=cluster.id,
            outlier_image_ids=outlier_ids
        )

        # Mark outliers twice
        service.mark_outliers(request)
        service.mark_outliers(request)

        # Should still have 3 outliers, not 6
        test_db.refresh(cluster)
        assert cluster.outlier_count == 3

        # Verify images are still marked correctly
        for img_id in outlier_ids:
            img = test_db.query(models.Image).filter(models.Image.id == img_id).first()
            assert img.annotation_status == "outlier"

    def test_mark_outliers_empty_list(self, test_db, sample_episode_with_images):
        """Test marking outliers with empty list (edge case)."""
        service = ClusterService(test_db)
        cluster = sample_episode_with_images["cluster"]

        request = schemas.OutlierSelectionRequest(
            cluster_id=cluster.id,
            outlier_image_ids=[]
        )

        result = service.mark_outliers(request)

        assert result["count"] == 0
        test_db.refresh(cluster)
        # Cluster metadata should reflect no outliers
        assert cluster.outlier_count == 0


class TestAnnotateClusterBatch:
    """Test batch annotation functionality."""

    def test_batch_annotation_all_images(self, test_db, sample_episode_with_images):
        """Test batch annotation when no outliers exist (Path A workflow)."""
        service = ClusterService(test_db)
        cluster = sample_episode_with_images["cluster"]
        episode = sample_episode_with_images["episode"]

        annotation = schemas.ClusterAnnotateBatch(
            person_name="Rachel",
            is_custom_label=False
        )

        result = service.annotate_cluster_batch(str(cluster.id), annotation)

        assert result["status"] == "completed"

        # Verify all 25 images are annotated
        images = test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id
        ).all()
        assert len(images) == 25
        for img in images:
            assert img.current_label == "Rachel"
            assert img.annotation_status == "annotated"
            assert img.annotated_at is not None

        # Verify cluster status
        test_db.refresh(cluster)
        assert cluster.person_name == "Rachel"
        assert cluster.is_single_person is True
        assert cluster.annotation_status == "completed"

        # Verify episode progress
        test_db.refresh(episode)
        assert episode.annotated_clusters == 1

    def test_batch_annotation_excludes_outliers(self, test_db, sample_cluster_with_outliers):
        """Test batch annotation only affects non-outlier images (Path B workflow)."""
        service = ClusterService(test_db)
        cluster = sample_cluster_with_outliers["cluster"]

        annotation = schemas.ClusterAnnotateBatch(
            person_name="Monica",
            is_custom_label=False
        )

        result = service.annotate_cluster_batch(str(cluster.id), annotation)

        assert result["status"] == "completed"

        # Verify only 7 non-outlier images are annotated
        annotated_images = test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id,
            models.Image.annotation_status == "annotated"
        ).all()
        assert len(annotated_images) == 7
        for img in annotated_images:
            assert img.current_label == "Monica"

        # Verify 3 outliers are untouched
        outlier_images = test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id,
            models.Image.annotation_status == "outlier"
        ).all()
        assert len(outlier_images) == 3
        for img in outlier_images:
            assert img.current_label is None  # Outliers should not be labeled yet

    def test_batch_annotation_custom_label(self, test_db, sample_episode_with_images):
        """Test batch annotation with custom label (not in Friends characters)."""
        service = ClusterService(test_db)
        cluster = sample_episode_with_images["cluster"]

        annotation = schemas.ClusterAnnotateBatch(
            person_name="Gunther",
            is_custom_label=True
        )

        result = service.annotate_cluster_batch(str(cluster.id), annotation)

        assert result["status"] == "completed"

        # Verify all images have custom label
        images = test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id
        ).all()
        for img in images:
            assert img.current_label == "Gunther"

    def test_batch_annotation_updates_episode_status(self, test_db, sample_episode_with_images):
        """Test that episode status becomes 'completed' when all clusters annotated."""
        service = ClusterService(test_db)
        cluster = sample_episode_with_images["cluster"]
        episode = sample_episode_with_images["episode"]

        # Episode has total_clusters=2, annotated_clusters=0
        # After annotating 1 cluster, should be 1/2 (still pending)
        annotation = schemas.ClusterAnnotateBatch(person_name="Joey", is_custom_label=False)
        service.annotate_cluster_batch(str(cluster.id), annotation)

        test_db.refresh(episode)
        assert episode.annotated_clusters == 1
        assert episode.status == "pending"  # Not completed yet

    def test_batch_annotation_invalid_cluster(self, test_db):
        """Test that invalid cluster_id raises exception."""
        service = ClusterService(test_db)

        annotation = schemas.ClusterAnnotateBatch(person_name="Test", is_custom_label=False)

        # Should handle invalid cluster ID gracefully
        result = service.annotate_cluster_batch("00000000-0000-0000-0000-000000000000", annotation)
        # Implementation should either raise HTTPException or return error status
        # We'll verify behavior after implementation


class TestAnnotateOutliers:
    """Test individual outlier annotation."""

    def test_annotate_outliers_updates_images(self, test_db, sample_cluster_with_outliers):
        """Test that annotating outliers updates each image individually."""
        service = ClusterService(test_db)
        outlier_ids = sample_cluster_with_outliers["outlier_ids"]

        # Create annotations for each outlier with different labels
        annotations = [
            schemas.OutlierAnnotation(image_id=outlier_ids[0], person_name="Joey", is_custom_label=False),
            schemas.OutlierAnnotation(image_id=outlier_ids[1], person_name="Chandler", is_custom_label=False),
            schemas.OutlierAnnotation(image_id=outlier_ids[2], person_name="Phoebe", is_custom_label=False)
        ]

        result = service.annotate_outliers(annotations)

        assert result["status"] == "outliers_annotated"
        assert result["count"] == 3

        # Verify each outlier has correct label
        outlier_1 = test_db.query(models.Image).filter(models.Image.id == outlier_ids[0]).first()
        assert outlier_1.current_label == "Joey"
        assert outlier_1.annotation_status == "annotated"
        assert outlier_1.annotated_at is not None

        outlier_2 = test_db.query(models.Image).filter(models.Image.id == outlier_ids[1]).first()
        assert outlier_2.current_label == "Chandler"

        outlier_3 = test_db.query(models.Image).filter(models.Image.id == outlier_ids[2]).first()
        assert outlier_3.current_label == "Phoebe"

    def test_annotate_outliers_same_label(self, test_db, sample_cluster_with_outliers):
        """Test annotating all outliers with the same label (they're all the same person)."""
        service = ClusterService(test_db)
        outlier_ids = sample_cluster_with_outliers["outlier_ids"]

        # All outliers are actually Ross
        annotations = [
            schemas.OutlierAnnotation(image_id=img_id, person_name="Ross", is_custom_label=False)
            for img_id in outlier_ids
        ]

        result = service.annotate_outliers(annotations)

        assert result["count"] == 3

        # Verify all have same label
        for img_id in outlier_ids:
            img = test_db.query(models.Image).filter(models.Image.id == img_id).first()
            assert img.current_label == "Ross"
            assert img.annotation_status == "annotated"

    def test_annotate_outliers_custom_labels(self, test_db, sample_cluster_with_outliers):
        """Test annotating outliers with custom labels (non-main characters)."""
        service = ClusterService(test_db)
        outlier_ids = sample_cluster_with_outliers["outlier_ids"]

        annotations = [
            schemas.OutlierAnnotation(image_id=outlier_ids[0], person_name="Gunther", is_custom_label=True),
            schemas.OutlierAnnotation(image_id=outlier_ids[1], person_name="Janice", is_custom_label=True)
        ]

        result = service.annotate_outliers(annotations)

        assert result["count"] == 2

        # Verify custom labels
        outlier_1 = test_db.query(models.Image).filter(models.Image.id == outlier_ids[0]).first()
        assert outlier_1.current_label == "Gunther"

        outlier_2 = test_db.query(models.Image).filter(models.Image.id == outlier_ids[1]).first()
        assert outlier_2.current_label == "Janice"

    def test_annotate_outliers_empty_list(self, test_db):
        """Test annotating with empty list (edge case)."""
        service = ClusterService(test_db)

        result = service.annotate_outliers([])

        assert result["count"] == 0
        assert result["status"] == "outliers_annotated"


class TestFullWorkflow:
    """Integration tests for complete annotation workflows."""

    def test_workflow_path_a_no_outliers(self, test_db, sample_episode_with_images):
        """
        Test complete Path A workflow (no outliers).

        Steps:
        1. Get paginated images (review all)
        2. No outliers selected
        3. Batch annotate entire cluster
        4. Done!
        """
        service = ClusterService(test_db)
        cluster_id = str(sample_episode_with_images["cluster"].id)

        # Step 1: Review images (paginate through)
        page1 = service.get_cluster_images_paginated(cluster_id, page=1, page_size=10)
        assert len(page1["images"]) == 10

        page2 = service.get_cluster_images_paginated(cluster_id, page=2, page_size=10)
        assert len(page2["images"]) == 10

        page3 = service.get_cluster_images_paginated(cluster_id, page=3, page_size=10)
        assert len(page3["images"]) == 5

        # Step 2: No outliers selected (skip mark_outliers)

        # Step 3: Batch annotate all
        annotation = schemas.ClusterAnnotateBatch(person_name="Rachel", is_custom_label=False)
        result = service.annotate_cluster_batch(cluster_id, annotation)

        assert result["status"] == "completed"

        # Verify all 25 images labeled
        images = test_db.query(models.Image).filter(
            models.Image.cluster_id == sample_episode_with_images["cluster"].id
        ).all()
        assert len(images) == 25
        assert all(img.current_label == "Rachel" for img in images)

    def test_workflow_path_b_with_outliers(self, test_db, sample_episode_with_images):
        """
        Test complete Path B workflow (with outliers).

        Steps:
        1. Get paginated images (review all)
        2. Mark 3 images as outliers
        3. Annotate outliers individually
        4. Batch annotate remaining images
        5. Done!
        """
        service = ClusterService(test_db)
        cluster = sample_episode_with_images["cluster"]
        cluster_id = str(cluster.id)

        # Step 1: Review images
        page1 = service.get_cluster_images_paginated(cluster_id, page=1, page_size=20)
        assert len(page1["images"]) == 20

        # Step 2: Mark 3 outliers
        images = test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id
        ).limit(3).all()
        outlier_ids = [img.id for img in images]

        outlier_request = schemas.OutlierSelectionRequest(
            cluster_id=cluster.id,
            outlier_image_ids=outlier_ids
        )
        service.mark_outliers(outlier_request)

        # Verify pagination now excludes outliers
        page1_after = service.get_cluster_images_paginated(cluster_id, page=1, page_size=20)
        assert len(page1_after["images"]) == 20
        assert page1_after["total_count"] == 22  # 25 - 3 outliers

        # Step 3: Annotate outliers individually
        outlier_annotations = [
            schemas.OutlierAnnotation(image_id=outlier_ids[0], person_name="Joey", is_custom_label=False),
            schemas.OutlierAnnotation(image_id=outlier_ids[1], person_name="Chandler", is_custom_label=False),
            schemas.OutlierAnnotation(image_id=outlier_ids[2], person_name="Monica", is_custom_label=False)
        ]
        outlier_result = service.annotate_outliers(outlier_annotations)
        assert outlier_result["count"] == 3

        # Step 4: Batch annotate remaining 22 images
        batch_annotation = schemas.ClusterAnnotateBatch(person_name="Rachel", is_custom_label=False)
        batch_result = service.annotate_cluster_batch(cluster_id, batch_annotation)
        assert batch_result["status"] == "completed"

        # Verify final state: 22 Rachel + 3 others
        all_images = test_db.query(models.Image).filter(
            models.Image.cluster_id == cluster.id
        ).all()
        assert len(all_images) == 25
        assert all(img.annotation_status == "annotated" for img in all_images)

        rachel_count = sum(1 for img in all_images if img.current_label == "Rachel")
        assert rachel_count == 22

        outlier_labels = [img.current_label for img in all_images if img.id in outlier_ids]
        assert set(outlier_labels) == {"Joey", "Chandler", "Monica"}
