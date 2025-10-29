import os
import json
import zipfile
import re
import logging
from pathlib import Path
from typing import Dict, List
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.models import models, schemas

logger = logging.getLogger(__name__)

class EpisodeService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)

    def _sanitize_folder_name(self, name: str) -> str:
        """
        Prevent path traversal and injection attacks.

        Removes dangerous characters:
        - .. (parent directory reference)
        - / and \\ (path separators)
        - Null bytes (injection attacks)

        Args:
            name: Raw folder name from user input or ZIP file

        Returns:
            Sanitized folder name safe for processing
        """
        # Remove null bytes (injection attacks)
        sanitized = name.replace('\x00', '')

        # Remove path traversal attempts
        sanitized = sanitized.replace('..', '')

        # Remove path separators
        sanitized = sanitized.replace('/', '')
        sanitized = sanitized.replace('\\', '')

        logger.debug(f"Sanitized '{name}' → '{sanitized}'")
        return sanitized

    def _parse_folder_name(self, folder_name: str) -> Dict:
        """
        Parse folder name to extract episode metadata and labels.

        Supported formats (case-insensitive):
        - S01E05_cluster-23 → season=1, episode=5, cluster=23, label="cluster-23"
        - S01E05_Rachel → season=1, episode=5, label="Rachel"
        - cluster_123 → cluster=123, label="cluster_123"
        - AnyName → label="AnyName" (fallback)

        Args:
            folder_name: Folder name to parse (e.g., "S01E05_cluster-23")

        Returns:
            Dict with keys: season, episode, cluster_number, label (all optional except label)
            Example: {"season": 1, "episode": 5, "cluster_number": 23, "label": "cluster-23"}
        """
        logger.info(f"Parsing folder: {folder_name}")

        # Sanitize input first
        sanitized = self._sanitize_folder_name(folder_name).strip()

        # Pattern 1: SxxEyy_cluster-N (e.g., S01E05_cluster-23)
        # Captures: season, episode, cluster number
        pattern_sxxeyy_cluster = re.compile(
            r'^S(\d+)E(\d+)_cluster-?(\d+)$',
            re.IGNORECASE
        )
        match = pattern_sxxeyy_cluster.match(sanitized)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            cluster_num = int(match.group(3))
            result = {
                "season": season,
                "episode": episode,
                "cluster_number": cluster_num,
                "label": f"cluster-{cluster_num}"
            }
            logger.debug(f"Matched SxxEyy_cluster pattern: {result}")
            return result

        # Pattern 2: SxxEyy_CharacterName (e.g., S01E05_Rachel)
        # Captures: season, episode, character name
        pattern_sxxeyy_char = re.compile(
            r'^S(\d+)E(\d+)_(.+)$',
            re.IGNORECASE
        )
        match = pattern_sxxeyy_char.match(sanitized)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            char_name = match.group(3)
            result = {
                "season": season,
                "episode": episode,
                "label": char_name
            }
            logger.debug(f"Matched SxxEyy_character pattern: {result}")
            return result

        # Pattern 3: cluster_N (legacy format, e.g., cluster_123)
        # Captures: cluster number
        pattern_legacy_cluster = re.compile(
            r'^cluster_(\d+)$',
            re.IGNORECASE
        )
        match = pattern_legacy_cluster.match(sanitized)
        if match:
            cluster_num = int(match.group(1))
            result = {
                "cluster_number": cluster_num,
                "label": f"cluster_{cluster_num}"
            }
            logger.debug(f"Matched legacy cluster pattern: {result}")
            return result

        # Fallback: use folder name as-is
        result = {"label": sanitized}
        logger.warning(f"Unknown format: {folder_name}, using fallback: {result}")
        return result

    async def upload_episode(self, file: UploadFile) -> models.Episode:
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")

        episode_name = file.filename.replace('.zip', '')
        episode_path = self.upload_dir / episode_name
        episode_path.mkdir(exist_ok=True)

        logger.info(f"Uploading episode: {episode_name}")

        with zipfile.ZipFile(file.file, 'r') as zip_ref:
            zip_ref.extractall(episode_path)

        clusters = await self._parse_clusters(episode_path)
        logger.info(f"Found {len(clusters)} clusters in episode {episode_name}")

        # Extract episode-level metadata from first cluster (if available)
        episode_season = None
        episode_number = None
        if clusters:
            first_cluster_meta = self._parse_folder_name(clusters[0]["name"])
            episode_season = first_cluster_meta.get("season")
            episode_number = first_cluster_meta.get("episode")
            logger.info(f"Episode metadata: season={episode_season}, episode={episode_number}")

        # Create Episode record
        episode = models.Episode(
            name=episode_name,
            total_clusters=len(clusters),
            status="pending",
            season=episode_season,
            episode_number=episode_number
        )
        self.db.add(episode)
        self.db.commit()
        self.db.refresh(episode)
        logger.info(f"Created Episode record: id={episode.id}")

        # Accumulate all images for bulk insert (avoid N inserts)
        images_to_create = []

        for cluster_data in clusters:
            # Parse folder name to extract metadata
            parsed = self._parse_folder_name(cluster_data["name"])

            # Create Cluster record
            cluster = models.Cluster(
                episode_id=episode.id,
                cluster_name=cluster_data["name"],
                image_paths=cluster_data["images"],  # Keep for backward compatibility
                initial_label=parsed.get("label"),
                cluster_number=parsed.get("cluster_number")
            )
            self.db.add(cluster)
            self.db.flush()  # Get cluster.id for Image records

            logger.debug(f"Created Cluster: {cluster.cluster_name} (id={cluster.id}, label={parsed.get('label')})")

            # Prepare Image records for bulk insert
            for img_path in cluster_data["images"]:
                image = models.Image(
                    cluster_id=cluster.id,
                    episode_id=episode.id,
                    file_path=img_path,
                    filename=Path(img_path).name,
                    initial_label=parsed.get("label"),
                    annotation_status="pending"
                )
                images_to_create.append(image)

        # CRITICAL: Bulk insert all images at once (performance!)
        # This avoids N+1 query problem (one insert per image)
        if images_to_create:
            self.db.bulk_save_objects(images_to_create)
            logger.info(f"Bulk created {len(images_to_create)} Image records")

        self.db.commit()
        logger.info(f"Episode upload complete: {episode_name}")
        return episode

    async def _parse_clusters(self, episode_path: Path) -> List[Dict]:
        """
        Parse cluster directories and extract image paths.

        Supports any folder name format (not just cluster_* prefix).
        Searches for .jpg, .jpeg, .png image files (case-insensitive).

        Args:
            episode_path: Path to extracted episode directory

        Returns:
            List of dicts with "name" and "images" keys
        """
        clusters = []
        for cluster_dir in episode_path.iterdir():
            if cluster_dir.is_dir():
                # Collect images (case-insensitive extension matching)
                images = []
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                    for img_file in cluster_dir.glob(ext):
                        images.append(str(img_file.relative_to(self.upload_dir)))

                if images:
                    clusters.append({
                        "name": cluster_dir.name,
                        "images": images
                    })
                    logger.debug(f"Found cluster: {cluster_dir.name} with {len(images)} images")
                else:
                    logger.warning(f"Skipping empty cluster directory: {cluster_dir.name}")

        return clusters

    async def export_annotations(self, episode_id: str) -> Dict:
        episode = self.db.query(models.Episode).filter(models.Episode.id == episode_id).first()
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        
        clusters = self.db.query(models.Cluster).filter(models.Cluster.episode_id == episode_id).all()
        
        annotations = {}
        split_annotations = {}
        
        for cluster in clusters:
            if cluster.is_single_person and cluster.person_name:
                annotations[cluster.cluster_name] = cluster.person_name
            elif not cluster.is_single_person:
                splits = self.db.query(models.SplitAnnotation).filter(
                    models.SplitAnnotation.cluster_id == cluster.id
                ).all()
                for split in splits:
                    split_annotations[split.scene_track_pattern] = split.person_name
        
        return {
            "episode": episode.name,
            "single_person_clusters": annotations,
            "split_clusters": split_annotations,
            "export_timestamp": episode.upload_timestamp.isoformat()
        }