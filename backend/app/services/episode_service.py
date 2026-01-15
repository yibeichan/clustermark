import json
import logging
import re
import shutil
import zipfile
from uuid import uuid4
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models import models, schemas

logger = logging.getLogger(__name__)

# Export format default values (configurable)
DEFAULT_MODEL_NAME = "vggface2"
DEFAULT_ANNOTATOR_ID = "user_01"

# Confidence thresholds for outlier ratio
MEDIUM_CONFIDENCE_OUTLIER_RATIO_THRESHOLD = 0.2

# Pre-compiled regex patterns for performance (Gemini HIGH priority)
# Compiling at module level prevents redundant compilation on every parse call

# Pattern: friends_s01e01a_cluster-XXX or friends_s01e01b_cluster-XXX
# Matches: optional prefix (friends_), season, episode, optional suffix (a/b), cluster number
# Groups: (season, episode, suffix, cluster_number)
PATTERN_FRIENDS_CLUSTER = re.compile(
    r"^(?:friends_)?[sS](\d+)[eE](\d+)([a-z])?_cluster-?(\d+)$", re.IGNORECASE
)

# Pattern: S01E05_cluster-23 (standard format)
PATTERN_SXXEYY_CLUSTER = re.compile(r"^S(\d+)E(\d+)_cluster-?(\d+)$", re.IGNORECASE)

# Pattern: S01E05_Rachel (standard format with character name)
PATTERN_SXXEYY_CHAR = re.compile(r"^S(\d+)E(\d+)_(.+)$", re.IGNORECASE)

# Pattern: cluster_123 (legacy format)
PATTERN_LEGACY_CLUSTER = re.compile(r"^cluster_(\d+)$", re.IGNORECASE)


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
        sanitized = name.replace("\x00", "")

        # Remove path separators FIRST to prevent bypasses (Gemini CRITICAL)
        # Must happen before '..' removal to prevent attacks like '..//' → '..'
        sanitized = sanitized.replace("/", "").replace("\\", "")

        # Repeatedly remove '..' to handle bypasses like '....' → '..' (Gemini CRITICAL)
        # Simple replace('..', '') can be defeated with '....' which becomes '..' after one pass
        while ".." in sanitized:
            sanitized = sanitized.replace("..", "")

        logger.debug(f"Sanitized '{name}' → '{sanitized}'")
        return sanitized

    def _parse_folder_name(self, folder_name: str) -> Dict:
        """
        Parse folder name to extract episode metadata and labels.

        Supported formats (case-insensitive):
        - friends_s01e01a_cluster-23 → season=1, episode=1, cluster=23, label="cluster-23"
        - friends_s01e01b_cluster-23 → season=1, episode=1, cluster=23, label="cluster-23"
        - S01E05_cluster-23 → season=1, episode=5, cluster=23, label="cluster-23"
        - S01E05_Rachel → season=1, episode=5, label="Rachel"
        - cluster_123 → cluster=123, label="cluster_123"
        - AnyName → label="AnyName" (fallback)

        Note: The 'a' or 'b' suffix in friends_s01e01a is ignored - both map to same episode

        Args:
            folder_name: Folder name to parse (e.g., "friends_s01e01a_cluster-23")

        Returns:
            Dict with keys: season, episode, cluster_number, label (all optional except label)
            Example: {"season": 1, "episode": 1, "cluster_number": 23, "label": "cluster-23"}
        """
        logger.info(f"Parsing folder: {folder_name}")

        # Sanitize input first
        sanitized = self._sanitize_folder_name(folder_name).strip()

        # Pattern 1: friends_s01e01a_cluster-N or s01e01b_cluster-N
        # Captures: season, episode, optional suffix (a/b/etc), cluster number
        # Both 'a' and 'b' suffixes map to the same episode
        match = PATTERN_FRIENDS_CLUSTER.match(sanitized)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            # group(3) is the optional suffix (a/b) - we ignore it
            cluster_num = int(match.group(4))
            result = {
                "season": season,
                "episode": episode,
                "cluster_number": cluster_num,
                "label": f"cluster-{cluster_num}",
            }
            logger.debug(f"Matched friends_sXXeYY_cluster pattern: {result}")
            return result

        # Pattern 2: SxxEyy_cluster-N (e.g., S01E05_cluster-23)
        # Captures: season, episode, cluster number
        match = PATTERN_SXXEYY_CLUSTER.match(sanitized)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            cluster_num = int(match.group(3))
            result = {
                "season": season,
                "episode": episode,
                "cluster_number": cluster_num,
                "label": f"cluster-{cluster_num}",
            }
            logger.debug(f"Matched SxxEyy_cluster pattern: {result}")
            return result

        # Pattern 3: SxxEyy_CharacterName (e.g., S01E05_Rachel)
        # Captures: season, episode, character name
        match = PATTERN_SXXEYY_CHAR.match(sanitized)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            char_name = match.group(3)
            result = {"season": season, "episode": episode, "label": char_name}
            logger.debug(f"Matched SxxEyy_character pattern: {result}")
            return result

        # Pattern 4: cluster_N (legacy format, e.g., cluster_123)
        # Captures: cluster number
        match = PATTERN_LEGACY_CLUSTER.match(sanitized)
        if match:
            cluster_num = int(match.group(1))
            result = {"cluster_number": cluster_num, "label": f"cluster_{cluster_num}"}
            logger.debug(f"Matched legacy cluster pattern: {result}")
            return result

        # Fallback: use folder name as-is
        result = {"label": sanitized}
        logger.warning(f"Unknown format: {folder_name}, using fallback: {result}")
        return result

    async def upload_episode(self, file: UploadFile) -> models.Episode:
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")


        # CRITICAL FIX: Sanitize filename to prevent path traversal
        raw_filename = Path(file.filename).name
        episode_name = raw_filename.replace(".zip", "")
        # Further sanitize using existing helper
        episode_name = self._sanitize_folder_name(episode_name)

        if not episode_name or episode_name == ".":
            raise HTTPException(status_code=400, detail="Invalid episode name")

        # Check for duplicate episode (case-insensitive)
        existing = (
            self.db.query(models.Episode)
            .filter(models.Episode.name.ilike(episode_name))
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": f"Episode '{existing.name}' already exists",
                    "existing_id": str(existing.id),
                    "has_annotations": existing.annotated_clusters > 0,
                },
            )

        episode_path = self.upload_dir / episode_name
        episode_path.mkdir(exist_ok=True)

        logger.info(f"Uploading episode: {episode_name}")

        with zipfile.ZipFile(file.file, "r") as zip_ref:
            zip_ref.extractall(episode_path)

        clusters = await self._parse_clusters(episode_path)
        logger.info(f"Found {len(clusters)} clusters in episode {episode_name}")

        # Extract episode-level metadata from clusters (Codex P1 fix)
        # Scan all clusters for first valid SxxEyy metadata, not just clusters[0]
        # Path.iterdir() order is non-deterministic - first item might be legacy/empty
        episode_season = None
        episode_number = None
        for cluster_data in clusters:
            parsed = self._parse_folder_name(cluster_data["name"])
            if parsed.get("season") is not None and parsed.get("episode") is not None:
                episode_season = parsed.get("season")
                episode_number = parsed.get("episode")
                logger.info(
                    f"Episode metadata from cluster '{cluster_data['name']}': season={episode_season}, episode={episode_number}"
                )
                break  # Use first valid SxxEyy metadata found

        if episode_season is None and episode_number is None and clusters:
            logger.info(
                "No SxxEyy metadata found in clusters, episode will have season=None/episode_number=None"
            )

        # Create Episode record
        episode = models.Episode(
            name=episode_name,
            total_clusters=len(clusters),
            status="pending",
            season=episode_season,
            episode_number=episode_number,
        )
        self.db.add(episode)
        # Use flush() instead of commit() to maintain atomicity (Gemini HIGH)
        # If cluster/image processing fails, entire upload will rollback
        self.db.flush()
        self.db.refresh(episode)
        logger.info(f"Created Episode record: id={episode.id}")

        # Accumulate all images for bulk insert (avoid N inserts)
        images_to_create = []

        for cluster_data in clusters:
            # Parse folder name to extract metadata
            parsed = self._parse_folder_name(cluster_data["name"])

            # Validate episode metadata consistency (Gemini MEDIUM)
            # Warn if clusters from different episodes mixed in same upload
            if episode_season is not None and parsed.get("season") is not None:
                if parsed.get("season") != episode_season:
                    logger.warning(
                        f"Episode metadata mismatch: Cluster '{cluster_data['name']}' "
                        f"has season={parsed.get('season')} but episode has season={episode_season}. "
                        f"User may have packaged clusters from different episodes."
                    )
            if episode_number is not None and parsed.get("episode") is not None:
                if parsed.get("episode") != episode_number:
                    logger.warning(
                        f"Episode metadata mismatch: Cluster '{cluster_data['name']}' "
                        f"has episode={parsed.get('episode')} but episode has episode={episode_number}. "
                        f"User may have packaged clusters from different episodes."
                    )

            # Create Cluster record
            cluster = models.Cluster(
                episode_id=episode.id,
                cluster_name=cluster_data["name"],
                image_paths=cluster_data["images"],  # Keep for backward compatibility
                initial_label=parsed.get("label"),
                cluster_number=parsed.get("cluster_number"),
            )
            self.db.add(cluster)
            self.db.flush()  # Get cluster.id for Image records

            logger.debug(
                f"Created Cluster: {cluster.cluster_name} (id={cluster.id}, label={parsed.get('label')})"
            )

            # Prepare Image records for bulk insert
            for img_path in cluster_data["images"]:
                image = models.Image(
                    cluster_id=cluster.id,
                    episode_id=episode.id,
                    file_path=img_path,
                    filename=Path(img_path).name,
                    initial_label=parsed.get("label"),
                    annotation_status="pending",
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
        Filters out system/hidden directories like __MACOSX.

        Args:
            episode_path: Path to extracted episode directory

        Returns:
            List of dicts with "name" and "images" keys
        """
        clusters = []
        for cluster_dir in episode_path.iterdir():
            if not cluster_dir.is_dir():
                continue

            # Skip system/hidden directories (Codex P1)
            # ZIP archives from macOS contain __MACOSX with preview images (._*.jpg)
            # These would be imported as bogus clusters if not filtered
            if cluster_dir.name.startswith("__") or cluster_dir.name.startswith("."):
                logger.debug(f"Skipping system/hidden directory: {cluster_dir.name}")
                continue

            # Collect images (Pythonic case-insensitive matching - Gemini MEDIUM)
            # More efficient than multiple glob() calls for each extension
            images = []
            for item in cluster_dir.iterdir():
                if item.is_file() and item.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    images.append(str(item.relative_to(self.upload_dir)))

            if images:
                clusters.append({"name": cluster_dir.name, "images": images})
                logger.debug(
                    f"Found cluster: {cluster_dir.name} with {len(images)} images"
                )
            else:
                logger.warning(f"Skipping empty cluster directory: {cluster_dir.name}")

        return clusters

    async def export_annotations(self, episode_id: str) -> Dict:
        """
        Export annotations in detailed format with image-level labels.

        Returns format matching clustering pipeline expectations:
        - metadata: episode info, annotation metadata
        - cluster_annotations: per-cluster labels with image paths and outliers
        - statistics: aggregated counts and distribution
        """


        # Fetch episode
        episode = (
            self.db.query(models.Episode)
            .filter(models.Episode.id == episode_id)
            .first()
        )
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        # Fetch all clusters for this episode
        clusters = (
            self.db.query(models.Cluster)
            .filter(models.Cluster.episode_id == episode_id)
            .all()
        )

        # Prefetch split annotations (multi-person workflow)
        split_annotations = (
            self.db.query(models.SplitAnnotation)
            .join(
                models.Cluster,
                models.SplitAnnotation.cluster_id == models.Cluster.id,
            )
            .filter(models.Cluster.episode_id == episode_id)
            .all()
        )
        split_annotations_by_cluster = defaultdict(list)
        for split in split_annotations:
            split_annotations_by_cluster[split.cluster_id].append(split)

        # PERFORMANCE FIX: Fetch ALL images for episode in one query (avoid N+1)
        # Only fetch annotated images and outliers (not pending)
        all_images = (
            self.db.query(models.Image)
            .filter(models.Image.episode_id == episode_id)
            .filter(models.Image.annotation_status.in_(["annotated", "outlier"]))
            .all()
        )

        # Group images by cluster_id for fast lookup
        images_by_cluster = defaultdict(list)
        for img in all_images:
            images_by_cluster[img.cluster_id].append(img)

        # Build metadata
        episode_name_lower = episode.name.lower().replace(" ", "_")
        if not episode_name_lower.startswith("friends_"):
            episode_name_lower = f"friends_{episode_name_lower}"

        # Format annotation_date properly for timezone-aware timestamps
        annotation_date = episode.upload_timestamp.isoformat()
        if episode.upload_timestamp.tzinfo is None:
            # Only add Z if timestamp is naive (no timezone)
            annotation_date += "Z"

        metadata = {
            "episode_id": episode_name_lower,
            "season": episode.season if episode.season else None,
            "episode": episode.episode_number if episode.episode_number else None,
            "clustering_file": f"{episode_name_lower}_matched_faces_with_clusters.json",
            "model_name": DEFAULT_MODEL_NAME,
            "annotation_date": annotation_date,
            "annotator_id": DEFAULT_ANNOTATOR_ID,
        }

        # Build cluster annotations and statistics
        cluster_annotations = {}
        character_distribution = defaultdict(int)
        total_faces = 0
        outliers_found = 0
        annotated_clusters = 0
        not_human_clusters = 0
        split_annotations_export = {}

        for cluster in clusters:
            # Only include completed clusters
            if cluster.annotation_status != "completed":
                continue

            annotated_clusters += 1

            # Get images and split annotations for this cluster
            images = images_by_cluster.get(cluster.id, [])
            cluster_splits = split_annotations_by_cluster.get(cluster.id, [])

            if not images and not cluster_splits:
                continue

            # DYNAMIC RE-EVALUATION for Harmonization
            # Instead of relying on static cluster.person_name or old annotation_status,
            # we redetermine the cluster's identity based on the majority label of its images.
            # This ensures export matches the final harmonized state.
            
            valid_images = [
                img for img in images 
                if img.annotation_status in ["annotated", "outlier"]
            ]
            
            if not valid_images and not cluster_splits:
                continue

            # Determine dominant label
            label_counts = Counter(
                img.current_label for img in valid_images 
                if img.current_label
            )
            
            if label_counts:
                # Most frequent label becomes the cluster's exported label
                cluster_label = label_counts.most_common(1)[0][0]
            else:
                # Fallback to DB label if no images have labels (unlikely)
                cluster_label = cluster.person_name if cluster.person_name else "unlabeled"

            # Re-classify images based on the new dominant label
            main_images = [
                img for img in valid_images 
                if img.current_label == cluster_label
            ]
            outlier_images = [
                img for img in valid_images 
                if img.current_label != cluster_label
            ]
            
            # Ensure label is lowercase for export consistency
            cluster_label = cluster_label.lower()

            # Track not_human clusters
            if cluster_label == "not_human":
                not_human_clusters += 1

            # Calculate confidence based on outlier ratio
            total_images_in_cluster = len(main_images) + len(outlier_images)
            if total_images_in_cluster > 0:
                outlier_ratio = len(outlier_images) / total_images_in_cluster
            else:
                outlier_ratio = 0

            if outlier_ratio == 0:
                confidence = "high"
            elif outlier_ratio < MEDIUM_CONFIDENCE_OUTLIER_RATIO_THRESHOLD:
                confidence = "medium"
            else:
                confidence = "low"

            # Build image paths (relative format, lowercase)
            image_paths = []
            for img in main_images:
                relative_path = self._convert_to_relative_path(img.file_path)
                if relative_path:
                    image_paths.append(relative_path)

            # Build outliers list
            outliers = []
            for img in outlier_images:
                relative_path = self._convert_to_relative_path(img.file_path)
                if relative_path:
                    outlier_label = (
                        img.current_label.lower() if img.current_label else "unlabeled"
                    )
                    outliers.append(
                        {
                            "image_path": relative_path,
                            "label": outlier_label,
                            # Explicit True check handles None from pre-migration data
                            "is_custom_label": img.is_custom_label is True,
                            "quality": img.quality_attributes or [],
                        }
                    )
                    outliers_found += 1

            # Update character distribution (defaultdict simplifies this)
            character_distribution[cluster_label] += len(main_images)
            for outlier in outliers:
                character_distribution[outlier["label"]] += 1

            counted_paths = set(image_paths)
            counted_paths.update(outlier["image_path"] for outlier in outliers)

            # Include split annotations (multi-person clusters)
            split_entries = []
            split_face_count = 0
            for split in cluster_splits:
                normalized_paths = []
                if split.image_paths:
                    for raw_path in split.image_paths:
                        relative_path = self._convert_to_relative_path(raw_path)
                        if relative_path and relative_path not in counted_paths:
                            normalized_paths.append(relative_path)
                            counted_paths.add(relative_path)
                split_label = (
                    split.person_name.lower() if split.person_name else "unlabeled"
                )
                if normalized_paths:
                    character_distribution[split_label] += len(normalized_paths)
                    split_face_count += len(normalized_paths)
                split_entries.append(
                    {
                        "scene_track_pattern": split.scene_track_pattern,
                        "label": split_label,
                        "image_count": len(normalized_paths),
                        "image_paths": normalized_paths,
                    }
                )
                split_annotations_export[split.scene_track_pattern] = {
                    "cluster_name": cluster.cluster_name,
                    "label": split_label,
                    "image_paths": normalized_paths,
                }

            total_faces += total_images_in_cluster + split_face_count

            # Add to cluster_annotations
            # Note: is_custom_label checks if any main image was custom-labeled.
            # For batch annotations, all images get the same flag, so any() == all().
            # Handle potential None values from pre-migration data (treated as False).
            cluster_annotations[cluster.cluster_name] = {
                "label": cluster_label,
                "is_custom_label": any(
                    img.is_custom_label is True for img in main_images
                )
                if main_images
                else False,
                "confidence": confidence,
                "image_count": len(main_images),
                "image_paths": image_paths,
                "outliers": outliers,
                "split_annotations": split_entries,
            }

        # Build statistics
        statistics = {
            "total_clusters": len(clusters),
            "annotated_clusters": annotated_clusters,
            "total_faces": total_faces,
            "outliers_found": outliers_found,
            "not_human_clusters": not_human_clusters,
            "character_distribution": character_distribution,
        }

        return {
            "metadata": metadata,
            "cluster_annotations": cluster_annotations,
            "split_annotations": split_annotations_export,
            "statistics": statistics,
        }

    def _convert_to_relative_path(self, file_path: str) -> str:
        """
        Convert file path to relative format for export.

        Converts:
            uploads/Friends_S01E05/S01E05_cluster-01/scene_0_track_1_frame_001.jpg
        To:
            friends_s01e05/s01e05_cluster-01/scene_0_track_1_frame_001.jpg

        Handles paths of any depth by lowercasing the entire relative path.
        Returns empty string if path is invalid.
        """
        if not file_path:
            return ""

        # Remove 'uploads/' prefix (only first occurrence)
        path_without_uploads = file_path.replace("uploads/", "", 1)

        # Expect at least 3 parts: episode_folder/cluster_folder/filename
        if len(path_without_uploads.split("/")) < 3:
            return ""

        # Convert the whole relative path to lowercase to handle any depth
        return path_without_uploads.lower()

    async def get_episode_speakers(
        self, episode_id: str
    ) -> schemas.EpisodeSpeakersResponse:
        """
        Get speakers for an episode, sorted by utterance frequency.

        Process:
        1. Fetch episode metadata (season, episode_number)
        2. Query episode_speakers table for matching season/episode
        3. Sort by utterances DESC (most frequent speakers first)
        4. Return speaker names only (title case)

        Args:
            episode_id: UUID of the episode

        Returns:
            EpisodeSpeakersResponse with episode info and speaker list

        Raises:
            HTTPException 404: If episode not found
        """
        # Fetch episode to get season/episode_number
        episode = (
            self.db.query(models.Episode)
            .filter(models.Episode.id == episode_id)
            .first()
        )

        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        # If episode has no season/episode metadata, return empty list
        # (graceful degradation - user can still use custom input)
        if episode.season is None or episode.episode_number is None:
            logger.warning(
                f"Episode {episode_id} has no season/episode metadata, "
                "returning empty speaker list"
            )
            return schemas.EpisodeSpeakersResponse(
                episode_id=episode.id,
                season=episode.season,
                episode_number=episode.episode_number,
                speakers=[],
            )

        # Query speakers for this episode, sorted by frequency
        speakers = (
            self.db.query(models.EpisodeSpeaker)
            .filter(
                models.EpisodeSpeaker.season == episode.season,
                models.EpisodeSpeaker.episode_number == episode.episode_number,
            )
            .order_by(models.EpisodeSpeaker.utterances.desc())
            .all()
        )

        logger.info(
            f"Found {len(speakers)} speakers for S{episode.season:02d}E{episode.episode_number:02d}"
        )

        return schemas.EpisodeSpeakersResponse(
            episode_id=episode.id,
            season=episode.season,
            episode_number=episode.episode_number,
            speakers=[s.speaker_name for s in speakers],
        )

    async def delete_episode(self, episode_id: str) -> None:
        """
        Delete an episode and all associated data.

        Deletes the database record FIRST, then the associated files.
        SQLAlchemy cascade will handle Cluster -> Image deletion.

        If file deletion fails, the error is logged but the request does not fail.

        Args:
            episode_id: UUID of the episode to delete

        Raises:
            HTTPException 404: If episode not found
        """
        episode = (
            self.db.query(models.Episode)
            .filter(models.Episode.id == episode_id)
            .first()
        )

        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        episode_name = episode.name

        # CRITICAL FIX: Delete DB record first to prevent "zombie" state
        self.db.delete(episode)
        self.db.commit()
        logger.info(f"Deleted episode from database: {episode_name}")

        # Delete files second
        # If this fails, we have orphaned files but a clean UI/DB
        episode_path = self.upload_dir / episode_name
        if episode_path.exists():
            try:
                shutil.rmtree(episode_path)
                logger.info(f"Deleted files for episode: {episode.name}")
            except OSError as e:
                # Log error but don't fail the request (DB already clean)
                logger.error(f"Failed to delete files for episode {episode.name} after DB delete: {e}")

    async def replace_episode(self, episode_id: str, file: UploadFile) -> models.Episode:
        """
        Replace an existing episode with a new upload.

        Deletes the existing episode first, then uploads the new one.

        Args:
            episode_id: UUID of the episode to replace
            file: New ZIP file to upload

        Returns:
            The newly created Episode object
        """
        # Safety check: Verify new file is a valid ZIP *before* deleting the old one
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")

        # Check if actual content is a valid ZIP
        if not zipfile.is_zipfile(file.file):
            raise HTTPException(status_code=400, detail="Invalid ZIP file content")
        
        # Reset file pointer after check so upload_episode can read it
        file.file.seek(0)

        # Delete existing episode
        await self.delete_episode(episode_id)

        # Upload new episode (duplicate check will pass since we just deleted)
        return await self.upload_episode(file)

    async def import_annotations(self, episode_id: str, file: UploadFile):
        """
        Import annotations from a JSON file.

        Updates Cluster and Image records to reflect external annotations.
        """
        try:
            content = await file.read()
            data = json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON file")

        # Map cluster names to IDs
        clusters = (
            self.db.query(models.Cluster)
            .filter(models.Cluster.episode_id == episode_id)
            .all()
        )
        cluster_map = {c.cluster_name: c for c in clusters}

        # Process cluster annotations
        cluster_annotations = data.get("cluster_annotations", {})
        for cluster_name, info in cluster_annotations.items():
            cluster = cluster_map.get(cluster_name)
            if not cluster:
                logger.warning(f"Cluster {cluster_name} not found, skipping")
                continue

            # Update cluster status
            cluster.annotation_status = "annotated"
            cluster.person_name = info.get("label")
            cluster.is_single_person = True  # Assumption for simple import
            
            # Map outliers
            outlier_paths = {o["image_path"] for o in info.get("outliers", [])}
            
            # Update all images in this cluster
            images = (
                self.db.query(models.Image)
                .filter(models.Image.cluster_id == cluster.id)
                .all()
            )
            
            for img in images:
                # Get relative path key for matching
                rel_path = self._convert_to_relative_path(img.file_path)
                
                if rel_path in outlier_paths:
                    img.annotation_status = "outlier"
                    # Find specific outlier info
                    outlier_info = next(
                        (o for o in info.get("outliers", []) if o["image_path"] == rel_path), 
                        {}
                    )
                    label = outlier_info.get("label")
                    if label:
                        if label.upper().startswith("DK"):
                            # User request: DK labels stay cluster-specific (DK1_cluster-name)
                            img.current_label = f"{label}_{cluster.cluster_name}"
                        else:
                            # User request: Main characters (Rachel, Monica) auto-combine across clusters
                            img.current_label = label
                    else:
                        img.current_label = f"{cluster.cluster_name}_DK"
                    if outlier_info.get("is_custom_label"):
                        img.is_custom_label = True
                    if outlier_info.get("quality"):
                        img.quality_attributes = outlier_info.get("quality")
                else:
                    img.annotation_status = "annotated"
                    img.current_label = cluster.person_name
                    if info.get("is_custom_label"):
                        img.is_custom_label = True

            # Check if cluster has outliers
            cluster.has_outliers = bool(outlier_paths)
            cluster.outlier_count = len(outlier_paths)

        # Update episode status
        episode = self.db.query(models.Episode).get(episode_id)
        if episode:
            episode.annotated_clusters = len(cluster_annotations)
            episode.status = "ready_for_harmonization"

        self.db.commit()
        logger.info(f"Imported annotations for {len(cluster_annotations)} clusters")

    async def get_piles(self, episode_id: str) -> List[Dict]:
        """
        Get initial piles for harmonization.

        Group images by current_label to form piles.
        """
        # Fetch annotated and outlier images
        images = (
            self.db.query(models.Image)
            .join(models.Cluster)
            .filter(
                models.Image.episode_id == episode_id,
                models.Image.annotation_status.in_(["annotated", "outlier"]),
            )
            .all()
        )

        piles_map = defaultdict(list)
        
        for img in images:
            # Determine pile name
            # If annotated, use current_label (person name)
            # If outlier, use current_label if set, else construct default DK name
            pile_name = img.current_label
            if not pile_name:
                if img.annotation_status == "outlier":
                    pile_name = f"{img.cluster.cluster_name}_DK"
                else:
                    pile_name = "Unlabeled"

            piles_map[pile_name].append(img)

        # Convert to Pile objects
        piles = []
        for name, img_list in piles_map.items():
            is_outlier = "DK" in name or any(img.annotation_status == "outlier" for img in img_list)
            
            pile_images = []
            for img in img_list:
                pile_images.append({
                    "id": img.id,
                    "file_path": self._convert_to_relative_path(img.file_path),
                    "original_label": img.initial_label,
                    "source_cluster_id": img.cluster_id
                })

            piles.append({
                "id": str(uuid4()),
                "name": name,
                "isOutlier": is_outlier,
                "images": pile_images
            })
            
        # Sort piles by size (descending) then name
        piles.sort(key=lambda x: (-len(x["images"]), x["name"]))
        
        return piles

    async def save_harmonization(self, episode_id: str, piles: List[schemas.Pile]):
        """
        Save harmonized pile assignments.

        Updates Image.current_label for each image based on pile assignment.
        """
        # Create a map of image_id -> new_label
        image_updates = {}
        for pile in piles:
            for pile_img in pile.images:
                image_updates[pile_img.id] = pile.name

        if not image_updates:
            return {"status": "success", "updated_count": 0}

        # Fetch all affected images
        images = (
            self.db.query(models.Image)
            .filter(models.Image.id.in_(image_updates.keys()))
            .all()
        )
        
        count = 0
        for img in images:
            new_label = image_updates.get(img.id)
            if new_label and img.current_label != new_label:
                img.current_label = new_label
                count += 1
        
        self.db.commit()
        logger.info(f"Harmonization saved: updated {count} images")
        
        return {"status": "success", "updated_count": count}

