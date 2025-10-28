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
    """
    Convert existing Cluster.image_paths to Image records.

    Uses a safer batching approach:
    1. Fetch all cluster IDs first (lightweight query)
    2. Process IDs in chunks of 100
    3. Each chunk gets its own transaction (commit after each batch)
    4. Avoids yield_per cursor issues with flush/commit
    """
    db = SessionLocal()
    try:
        print("Starting backfill process...")

        # Step 1: Fetch all cluster IDs (lightweight, memory-efficient approach)
        # Note: UUIDs are only 16 bytes each. Loading all IDs into memory:
        #   - 1M clusters = ~16MB RAM (negligible)
        #   - 10M clusters = ~160MB RAM (acceptable)
        # Alternative LIMIT/OFFSET approach has severe performance degradation
        # at high offsets (O(n) for each batch), making this approach more efficient.
        cluster_ids = [row[0] for row in db.query(Cluster.id).all()]
        cluster_count = len(cluster_ids)
        print(f"Found {cluster_count} clusters to process")

        total_images_created = 0
        clusters_processed = 0

        # Step 2: Process IDs in batches of 100
        BATCH_SIZE = 100
        for batch_start in range(0, cluster_count, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, cluster_count)
            batch_ids = cluster_ids[batch_start:batch_end]

            # Fetch cluster objects for this batch
            clusters = db.query(Cluster).filter(Cluster.id.in_(batch_ids)).all()

            for cluster in clusters:
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
                        initial_label=cluster.initial_label or "unlabeled",
                        annotation_status="pending"
                    )
                    images_to_create.append(image)

                # Bulk insert for performance
                db.bulk_save_objects(images_to_create)

                images_created = len(images_to_create)
                total_images_created += images_created
                clusters_processed += 1
                print(f"  Cluster {cluster.cluster_name}: Created {images_created} image records")

            # Commit after each batch (safe, no cursor issues)
            db.commit()
            print(f"  Committed batch {batch_start//BATCH_SIZE + 1} (clusters {batch_start+1}-{batch_end})")

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
