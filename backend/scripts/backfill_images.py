"""
Backfill script to convert existing Cluster.image_paths to Image records.

This script is idempotent and safe to run multiple times.
It will only create Image records for clusters that don't already have them.

Usage:
    docker-compose exec backend python scripts/backfill_images.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.models import Cluster, Image, Episode
from sqlalchemy import exists


def backfill_images():
    """Convert existing Cluster.image_paths to Image records"""
    db = SessionLocal()
    try:
        print("Starting backfill process...")

        # Get all clusters (use streaming query to avoid loading all into memory)
        clusters_query = db.query(Cluster)
        print(f"Found {clusters_query.count()} clusters to process")

        total_images_created = 0
        clusters_processed = 0

        for idx, cluster in enumerate(clusters_query):
            # Skip clusters with no image_paths
            if not cluster.image_paths:
                continue

            # Check if this cluster already has Image records using EXISTS (faster)
            image_exists = db.query(exists().where(Image.cluster_id == cluster.id)).scalar()

            if image_exists:
                print(f"  Cluster {cluster.cluster_name}: Already has images, skipping")
                continue

            # Create Image records for this cluster (batch for performance)
            images_to_create = []
            for img_path in cluster.image_paths:
                # Extract filename from path
                filename = Path(img_path).name

                # Create Image record
                image = Image(
                    cluster_id=cluster.id,
                    episode_id=cluster.episode_id,
                    file_path=img_path,
                    filename=filename,
                    initial_label=cluster.initial_label or "unlabeled",  # Use consistent default
                    annotation_status="pending"
                )
                images_to_create.append(image)

            # Bulk insert for performance
            db.bulk_save_objects(images_to_create)

            # Commit every 10 clusters for safety
            if (idx + 1) % 10 == 0:
                db.commit()
                print(f"  Committed batch at cluster {idx + 1}")

            images_created = len(images_to_create)
            total_images_created += images_created
            clusters_processed += 1
            print(f"  Cluster {cluster.cluster_name}: Created {images_created} image records")

        # Final commit for remaining clusters
        db.commit()

        print(f"\nBackfill complete!")
        print(f"  Clusters processed: {clusters_processed}")
        print(f"  Total images created: {total_images_created}")

    except Exception as e:
        print(f"Error during backfill: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    backfill_images()
