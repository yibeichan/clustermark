import logging
import re
import zipfile
from pathlib import Path
from typing import Dict, List

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models import models, schemas

logger = logging.getLogger(__name__)

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

        episode_name = file.filename.replace(".zip", "")
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
        episode = (
            self.db.query(models.Episode)
            .filter(models.Episode.id == episode_id)
            .first()
        )
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        clusters = (
            self.db.query(models.Cluster)
            .filter(models.Cluster.episode_id == episode_id)
            .all()
        )

        # Build metadata
        episode_id_str = episode.name.lower().replace("_", "_").replace(" ", "_")
        if not episode_id_str.startswith("friends_"):
            episode_id_str = f"friends_{episode_id_str}"

        metadata = {
            "episode_id": episode_id_str,
            "season": episode.season if episode.season else None,
            "episode": episode.episode_number if episode.episode_number else None,
            "clustering_file": f"{episode_id_str}_matched_faces_with_clusters.json",
            "model_name": "vggface2",  # Default, could be made configurable
            "annotation_date": episode.upload_timestamp.isoformat() + "Z",
            "annotator_id": "user_01",  # Default, could be made configurable
        }

        # Build cluster annotations
        cluster_annotations = {}
        character_distribution = {}
        total_faces = 0
        outliers_found = 0
        annotated_clusters = 0
        not_human_clusters = 0

        for cluster in clusters:
            # Only include annotated clusters
            if cluster.annotation_status != "completed":
                continue

            annotated_clusters += 1

            # Get all images for this cluster
            images = (
                self.db.query(models.Image)
                .filter(models.Image.cluster_id == cluster.id)
                .filter(models.Image.annotation_status == "annotated")
                .all()
            )

            if not images:
                continue

            # Separate outliers from main cluster images
            outlier_images = [
                img
                for img in images
                if img.initial_label and img.current_label != cluster.person_name
            ]
            main_images = [img for img in images if img not in outlier_images]

            # Determine cluster label (from cluster.person_name or most common label)
            cluster_label = cluster.person_name if cluster.person_name else "unlabeled"
            cluster_label = cluster_label.lower()

            # Track not_human clusters
            if cluster_label == "not_human":
                not_human_clusters += 1

            # Calculate confidence based on outlier ratio
            total_images_in_cluster = len(main_images) + len(outlier_images)
            outlier_ratio = (
                len(outlier_images) / total_images_in_cluster
                if total_images_in_cluster > 0
                else 0
            )

            if outlier_ratio == 0:
                confidence = "high"
            elif outlier_ratio < 0.2:
                confidence = "medium"
            else:
                confidence = "low"

            # Build image paths (relative to episode folder)
            image_paths = []
            for img in main_images:
                # Convert file_path to relative format
                # uploads/Friends_S01E05/S01E05_cluster-01/scene_0_track_1_frame_001.jpg
                # -> friends_s01e05/friends_s01e05_cluster-01/scene_0_track_1_frame_001.jpg
                path_parts = img.file_path.replace("uploads/", "").split("/")
                if len(path_parts) >= 3:
                    relative_path = f"{path_parts[0].lower()}/{path_parts[1].lower()}/{path_parts[2]}"
                    image_paths.append(relative_path)

            # Build outliers list
            outliers = []
            for img in outlier_images:
                path_parts = img.file_path.replace("uploads/", "").split("/")
                if len(path_parts) >= 3:
                    relative_path = f"{path_parts[0].lower()}/{path_parts[1].lower()}/{path_parts[2]}"
                    outliers.append(
                        {
                            "image_path": relative_path,
                            "label": img.current_label.lower()
                            if img.current_label
                            else "unlabeled",
                        }
                    )
                    outliers_found += 1

            # Update character distribution
            if cluster_label not in character_distribution:
                character_distribution[cluster_label] = 0
            character_distribution[cluster_label] += len(main_images)

            for outlier in outliers:
                outlier_label = outlier["label"]
                if outlier_label not in character_distribution:
                    character_distribution[outlier_label] = 0
                character_distribution[outlier_label] += 1

            total_faces += total_images_in_cluster

            # Add to cluster_annotations
            cluster_annotations[cluster.cluster_name] = {
                "label": cluster_label,
                "confidence": confidence,
                "image_count": len(main_images),
                "image_paths": image_paths,
                "outliers": outliers,
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
            "statistics": statistics,
        }

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
