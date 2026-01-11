"""
Tests for export_annotations functionality.

Test-Driven Development approach:
1. Write tests first (defining expected behavior)
2. Tests will fail initially
3. Implement code to make tests pass
4. Refactor and optimize
"""

import uuid

import pytest
from app.models import models
from app.services.episode_service import EpisodeService
from fastapi import HTTPException
from sqlalchemy.orm import Session

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


class TestExportAnnotationsFormat:
    """Test the structure and format of exported annotations."""

    @pytest.fixture
    def sample_episode(self, test_db: Session):
        """Create a sample episode with annotated clusters and outliers."""
        episode = models.Episode(
            name="Friends_S01E05",
            season=1,
            episode_number=5,
            total_clusters=3,
            annotated_clusters=3,
            status="completed",
        )
        test_db.add(episode)
        test_db.flush()

        # Cluster 1: Clean cluster with all Rachel images
        cluster1 = models.Cluster(
            episode_id=episode.id,
            cluster_name="cluster-01",
            person_name="Rachel",
            is_single_person=True,
            annotation_status="completed",
        )
        test_db.add(cluster1)
        test_db.flush()

        # Add images to cluster 1 (all annotated as Rachel)
        for i in range(5):
            img = models.Image(
                cluster_id=cluster1.id,
                episode_id=episode.id,
                file_path=f"uploads/Friends_S01E05/S01E05_cluster-01/scene_0_track_1_frame_{i:03d}.jpg",
                filename=f"scene_0_track_1_frame_{i:03d}.jpg",
                initial_label="cluster-01",
                current_label="Rachel",
                annotation_status="annotated",
            )
            test_db.add(img)

        # Cluster 2: Has outliers (2 Chandler images in Monica cluster)
        cluster2 = models.Cluster(
            episode_id=episode.id,
            cluster_name="cluster-02",
            person_name="Monica",
            is_single_person=True,
            annotation_status="completed",
            has_outliers=True,
            outlier_count=2,
        )
        test_db.add(cluster2)
        test_db.flush()

        # Add main images (Monica)
        for i in range(3):
            img = models.Image(
                cluster_id=cluster2.id,
                episode_id=episode.id,
                file_path=f"uploads/Friends_S01E05/S01E05_cluster-02/scene_1_track_2_frame_{i:03d}.jpg",
                filename=f"scene_1_track_2_frame_{i:03d}.jpg",
                initial_label="cluster-02",
                current_label="Monica",
                annotation_status="annotated",
            )
            test_db.add(img)

        # Add outliers (Chandler)
        for i in range(2):
            img = models.Image(
                cluster_id=cluster2.id,
                episode_id=episode.id,
                file_path=f"uploads/Friends_S01E05/S01E05_cluster-02/scene_2_track_3_frame_{i:03d}.jpg",
                filename=f"scene_2_track_3_frame_{i:03d}.jpg",
                initial_label="cluster-02",
                current_label="Chandler",
                annotation_status="outlier",  # Marked as outlier!
            )
            test_db.add(img)

        # Cluster 3: not_human cluster
        cluster3 = models.Cluster(
            episode_id=episode.id,
            cluster_name="cluster-03",
            person_name="not_human",
            is_single_person=True,
            annotation_status="completed",
        )
        test_db.add(cluster3)
        test_db.flush()

        for i in range(2):
            img = models.Image(
                cluster_id=cluster3.id,
                episode_id=episode.id,
                file_path=f"uploads/Friends_S01E05/S01E05_cluster-03/scene_5_track_1_frame_{i:03d}.jpg",
                filename=f"scene_5_track_1_frame_{i:03d}.jpg",
                initial_label="cluster-03",
                current_label="not_human",
                annotation_status="annotated",
            )
            test_db.add(img)

        test_db.commit()
        return episode

    async def test_export_has_correct_top_level_keys(
        self, test_db: Session, sample_episode
    ):
        """Export should have metadata, cluster_annotations, and statistics keys."""
        service = EpisodeService(test_db)
        result = await service.export_annotations(str(sample_episode.id))

        assert "metadata" in result
        assert "cluster_annotations" in result
        assert "split_annotations" in result
        assert "statistics" in result

    async def test_export_includes_is_custom_label(self, test_db: Session, sample_episode):
        """Test that the export JSON includes the is_custom_label flag for outliers."""
        service = EpisodeService(test_db)

        # Manually set an outlier image as custom label in the DB
        # Find one of the Chandler outliers from sample_episode
        outlier_img = test_db.query(models.Image).filter(
            models.Image.episode_id == sample_episode.id,
            models.Image.annotation_status == "outlier",
            models.Image.current_label == "Chandler"
        ).first()
        assert outlier_img is not None, "Pre-condition failed: No Chandler outlier found."

        outlier_img.is_custom_label = True
        outlier_img.current_label = "DK1" # Change label to a custom one
        test_db.commit()

        result = await service.export_annotations(str(sample_episode.id))

        # Verify the updated outlier (now DK1) has is_custom_label: True
        cluster_02_annotations = result["cluster_annotations"]["cluster-02"]
        outliers_list = cluster_02_annotations["outliers"]

        found_dk1_outlier = False
        for outlier in outliers_list:
            if outlier["label"] == "dk1": # Labels are lowercased in export
                assert outlier["is_custom_label"] is True
                found_dk1_outlier = True
                break
        assert found_dk1_outlier, "DK1 outlier with custom label not found in export."

        # Ensure other outliers (if any) don't have it set to True unless they are custom
        # In this setup, there should be one more Chandler outlier which is not custom
        found_chandler_outlier = False
        for outlier in outliers_list:
            if outlier["label"] == "chandler":
                assert outlier["is_custom_label"] is False
                found_chandler_outlier = True
                break
        assert found_chandler_outlier, "Chandler outlier (non-custom) not found in export."

    async def test_export_includes_quality_attributes(self, test_db: Session, sample_episode):
        """Test that the export JSON includes quality attributes for outliers."""
        service = EpisodeService(test_db)

        # Find one of the Chandler outliers and set quality attributes
        outlier_img = test_db.query(models.Image).filter(
            models.Image.episode_id == sample_episode.id,
            models.Image.annotation_status == "outlier",
            models.Image.current_label == "Chandler"
        ).first()
        assert outlier_img is not None, "Pre-condition failed: No Chandler outlier found."

        outlier_img.quality_attributes = ["@blurry", "@dark"]
        test_db.commit()

        result = await service.export_annotations(str(sample_episode.id))

        # Verify the outlier has quality field in export
        cluster_02_annotations = result["cluster_annotations"]["cluster-02"]
        outliers_list = cluster_02_annotations["outliers"]

        found_quality_outlier = False
        for outlier in outliers_list:
            if "quality" in outlier and len(outlier["quality"]) > 0:
                assert set(outlier["quality"]) == {"@blurry", "@dark"}
                found_quality_outlier = True
                break
        assert found_quality_outlier, "Outlier with quality attributes not found in export."

        # Verify other outliers have empty quality list
        for outlier in outliers_list:
            assert "quality" in outlier  # All outliers should have quality field

    async def test_metadata_structure(self, test_db: Session, sample_episode):
        """Metadata should contain required fields."""
        service = EpisodeService(test_db)
        result = await service.export_annotations(str(sample_episode.id))

        metadata = result["metadata"]
        assert "episode_id" in metadata
        assert "season" in metadata
        assert "episode" in metadata
        assert "clustering_file" in metadata
        assert "model_name" in metadata
        assert "annotation_date" in metadata
        assert "annotator_id" in metadata

        # Verify values
        assert metadata["season"] == 1
        assert metadata["episode"] == 5
        assert metadata["episode_id"].startswith("friends_")

    async def test_cluster_annotation_structure(self, test_db: Session, sample_episode):
        """Each cluster annotation should have correct fields."""
        service = EpisodeService(test_db)
        result = await service.export_annotations(str(sample_episode.id))

        cluster_annotations = result["cluster_annotations"]
        assert len(cluster_annotations) == 3  # We created 3 clusters

        # Check cluster-01 (clean cluster)
        cluster1 = cluster_annotations["cluster-01"]
        assert "label" in cluster1
        assert "confidence" in cluster1
        assert "image_count" in cluster1
        assert "image_paths" in cluster1
        assert "outliers" in cluster1
        assert "split_annotations" in cluster1

        assert cluster1["label"] == "rachel"
        assert cluster1["confidence"] == "high"  # No outliers
        assert cluster1["image_count"] == 5
        assert len(cluster1["image_paths"]) == 5
        assert len(cluster1["outliers"]) == 0
        assert cluster1["split_annotations"] == []

    async def test_outliers_exported_correctly(self, test_db: Session, sample_episode):
        """Outliers should be in separate list with their labels."""
        service = EpisodeService(test_db)
        result = await service.export_annotations(str(sample_episode.id))

        cluster2 = result["cluster_annotations"]["cluster-02"]

        # Main cluster should have 3 Monica images
        assert cluster2["label"] == "monica"
        assert cluster2["image_count"] == 3
        assert len(cluster2["image_paths"]) == 3

        # Should have 2 outliers labeled as Chandler
        assert len(cluster2["outliers"]) == 2
        for outlier in cluster2["outliers"]:
            assert "image_path" in outlier
            assert "label" in outlier
            assert outlier["label"] == "chandler"

    async def test_confidence_calculation(self, test_db: Session, sample_episode):
        """Confidence should be based on outlier ratio."""
        service = EpisodeService(test_db)
        result = await service.export_annotations(str(sample_episode.id))

        # cluster-01: 0 outliers / 5 total = 0% → high
        assert result["cluster_annotations"]["cluster-01"]["confidence"] == "high"

        # cluster-02: 2 outliers / 5 total = 40% → low (>= 20%)
        assert result["cluster_annotations"]["cluster-02"]["confidence"] == "low"

    async def test_statistics_aggregation(self, test_db: Session, sample_episode):
        """Statistics should correctly aggregate counts."""
        service = EpisodeService(test_db)
        result = await service.export_annotations(str(sample_episode.id))

        stats = result["statistics"]
        assert stats["total_clusters"] == 3
        assert stats["annotated_clusters"] == 3
        assert stats["total_faces"] == 12  # 5 + 5 + 2
        assert stats["outliers_found"] == 2
        assert stats["not_human_clusters"] == 1

        # Character distribution
        char_dist = stats["character_distribution"]
        assert char_dist["rachel"] == 5
        assert char_dist["monica"] == 3
        assert char_dist["chandler"] == 2
        assert char_dist["not_human"] == 2

    async def test_image_paths_relative_format(self, test_db: Session, sample_episode):
        """Image paths should be in relative format (lowercase)."""
        service = EpisodeService(test_db)
        result = await service.export_annotations(str(sample_episode.id))

        cluster1 = result["cluster_annotations"]["cluster-01"]
        first_path = cluster1["image_paths"][0]

        # Assert exact expected path for robust validation
        assert (
            first_path
            == "friends_s01e05/s01e05_cluster-01/scene_0_track_1_frame_000.jpg"
        )


class TestExportAnnotationsEdgeCases:
    """Test edge cases and error handling."""

    async def test_export_nonexistent_episode(self, test_db: Session):
        """Should raise 404 for non-existent episode."""
        service = EpisodeService(test_db)
        fake_id = str(uuid.uuid4())

        with pytest.raises(HTTPException) as exc_info:
            await service.export_annotations(fake_id)

        assert exc_info.value.status_code == 404

    async def test_export_episode_with_no_clusters(self, test_db: Session):
        """Should handle episode with no clusters gracefully."""
        episode = models.Episode(
            name="Empty_Episode",
            total_clusters=0,
            status="pending",
        )
        test_db.add(episode)
        test_db.commit()

        service = EpisodeService(test_db)
        result = await service.export_annotations(str(episode.id))

        assert result["cluster_annotations"] == {}
        assert result["statistics"]["total_clusters"] == 0
        assert result["statistics"]["annotated_clusters"] == 0

    async def test_export_skips_unannotated_clusters(self, test_db: Session):
        """Should only include completed clusters in export."""
        episode = models.Episode(
            name="Mixed_Episode",
            total_clusters=2,
            status="in_progress",
        )
        test_db.add(episode)
        test_db.flush()

        # Annotated cluster with images
        cluster1 = models.Cluster(
            episode_id=episode.id,
            cluster_name="cluster-01",
            person_name="Rachel",
            annotation_status="completed",
        )
        test_db.add(cluster1)
        test_db.flush()

        # Add images to cluster1 so it has data to export
        for i in range(2):
            img = models.Image(
                cluster_id=cluster1.id,
                episode_id=episode.id,
                file_path=f"uploads/Mixed_Episode/cluster-01/frame_{i:03d}.jpg",
                filename=f"frame_{i:03d}.jpg",
                initial_label="cluster-01",
                current_label="Rachel",
                annotation_status="annotated",
            )
            test_db.add(img)

        # Unannotated cluster (no images, should be skipped)
        cluster2 = models.Cluster(
            episode_id=episode.id,
            cluster_name="cluster-02",
            annotation_status="pending",
        )
        test_db.add(cluster2)
        test_db.commit()

        service = EpisodeService(test_db)
        result = await service.export_annotations(str(episode.id))

        # Should only export cluster-01
        assert "cluster-01" in result["cluster_annotations"]
        assert "cluster-02" not in result["cluster_annotations"]
        assert result["statistics"]["total_clusters"] == 2
        assert result["statistics"]["annotated_clusters"] == 1

    async def test_export_handles_split_annotated_clusters(self, test_db: Session):
        """Split-annotated clusters should be included with per-track labels."""
        episode = models.Episode(
            name="Split_Episode",
            total_clusters=1,
            status="completed",
        )
        test_db.add(episode)
        test_db.flush()

        cluster = models.Cluster(
            episode_id=episode.id,
            cluster_name="cluster-04",
            is_single_person=False,
            annotation_status="completed",
        )
        test_db.add(cluster)
        test_db.flush()

        image_paths = [
            "uploads/Split_Episode/cluster-04/scene_0_track_1_frame_000.jpg",
            "uploads/Split_Episode/cluster-04/scene_0_track_1_frame_001.jpg",
            "uploads/Split_Episode/cluster-04/scene_0_track_2_frame_000.jpg",
            "uploads/Split_Episode/cluster-04/scene_0_track_2_frame_001.jpg",
        ]
        for path in image_paths:
            img = models.Image(
                cluster_id=cluster.id,
                episode_id=episode.id,
                file_path=path,
                filename=path.split("/")[-1],
                initial_label="cluster-04",
                annotation_status="pending",
            )
            test_db.add(img)

        split_one = models.SplitAnnotation(
            cluster_id=cluster.id,
            scene_track_pattern="scene_0_track_1",
            person_name="Rachel",
            image_paths=image_paths[:2],
        )
        split_two = models.SplitAnnotation(
            cluster_id=cluster.id,
            scene_track_pattern="scene_0_track_2",
            person_name="Monica",
            image_paths=image_paths[2:],
        )
        test_db.add_all([split_one, split_two])
        test_db.commit()

        service = EpisodeService(test_db)
        result = await service.export_annotations(str(episode.id))

        assert "cluster-04" in result["cluster_annotations"]
        split_cluster = result["cluster_annotations"]["cluster-04"]
        assert split_cluster["image_count"] == 0
        assert len(split_cluster["split_annotations"]) == 2
        assert result["split_annotations"]["scene_0_track_1"]["label"] == "rachel"
        assert result["split_annotations"]["scene_0_track_2"]["label"] == "monica"

        total_split_images = sum(
            entry["image_count"] for entry in split_cluster["split_annotations"]
        )
        assert total_split_images == 4
        assert result["statistics"]["total_faces"] == 4
        char_dist = result["statistics"]["character_distribution"]
        assert char_dist["rachel"] == 2
        assert char_dist["monica"] == 2


class TestExportAnnotationsPerformance:
    """Test performance and query optimization."""

    async def test_no_n_plus_1_queries(self, test_db: Session):
        """Should not have N+1 query problem (one query per cluster)."""
        # Create episode with 10 clusters
        episode = models.Episode(
            name="Large_Episode",
            total_clusters=10,
            status="completed",
        )
        test_db.add(episode)
        test_db.flush()

        for i in range(10):
            cluster = models.Cluster(
                episode_id=episode.id,
                cluster_name=f"cluster-{i:02d}",
                person_name="Rachel",
                annotation_status="completed",
            )
            test_db.add(cluster)
            test_db.flush()

            # Add 5 images per cluster
            for j in range(5):
                img = models.Image(
                    cluster_id=cluster.id,
                    episode_id=episode.id,
                    file_path=f"uploads/test/cluster-{i:02d}/img_{j}.jpg",
                    filename=f"img_{j}.jpg",
                    current_label="Rachel",
                    annotation_status="annotated",
                )
                test_db.add(img)

        test_db.commit()

        service = EpisodeService(test_db)

        # TODO: Add query counting here once implemented
        # For now, this test documents the requirement
        result = await service.export_annotations(str(episode.id))

        # Should export all 10 clusters
        assert len(result["cluster_annotations"]) == 10
        assert result["statistics"]["total_faces"] == 50
