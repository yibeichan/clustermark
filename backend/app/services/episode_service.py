import os
import json
import zipfile
from pathlib import Path
from typing import Dict, List
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.models import models, schemas

class EpisodeService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)

    async def upload_episode(self, file: UploadFile) -> models.Episode:
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")
        
        episode_name = file.filename.replace('.zip', '')
        episode_path = self.upload_dir / episode_name
        episode_path.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(file.file, 'r') as zip_ref:
            zip_ref.extractall(episode_path)
        
        clusters = await self._parse_clusters(episode_path)
        
        episode = models.Episode(
            name=episode_name,
            total_clusters=len(clusters),
            status="pending"
        )
        self.db.add(episode)
        self.db.commit()
        self.db.refresh(episode)
        
        for cluster_data in clusters:
            cluster = models.Cluster(
                episode_id=episode.id,
                cluster_name=cluster_data["name"],
                initial_label=cluster_data["initial_label"],
                image_paths=cluster_data["images"]  # Keep for backward compat
            )
            self.db.add(cluster)
            self.db.flush()  # Get cluster ID

            # Create individual Image records
            for img_path in cluster_data["images"]:
                image = models.Image(
                    cluster_id=cluster.id,
                    episode_id=episode.id,
                    file_path=img_path,
                    filename=Path(img_path).name,
                    initial_label=cluster_data["initial_label"]
                )
                self.db.add(image)

        self.db.commit()
        return episode

    async def _parse_clusters(self, episode_path: Path) -> List[Dict]:
        """Parse uploaded folders as clusters with initial labels"""
        clusters = []

        # Find all subdirectories (ignore hidden folders)
        for cluster_dir in episode_path.iterdir():
            if not cluster_dir.is_dir() or cluster_dir.name.startswith('.'):
                continue

            # Collect images
            images = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                images.extend(cluster_dir.glob(ext))

            if not images:
                continue

            # Normalize label: replace underscores with spaces, handle special cases
            folder_name = cluster_dir.name
            initial_label = self._normalize_label(folder_name)

            clusters.append({
                "name": folder_name,  # Keep original folder name
                "initial_label": initial_label,  # Normalized label
                "images": [str(img.relative_to(self.upload_dir)) for img in images]
            })

        return clusters

    def _normalize_label(self, folder_name: str) -> str:
        """Convert folder name to label"""
        # Special cases: treat as unlabeled
        if folder_name.lower() in ['unknown', 'unlabeled', 'uncertain', 'unsure']:
            return None

        # Replace underscores with spaces
        label = folder_name.replace('_', ' ')

        return label

    async def export_annotations(self, episode_id: str) -> Dict:
        """Export all image annotations"""
        from datetime import datetime

        episode = self.db.query(models.Episode).filter(models.Episode.id == episode_id).first()
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")

        # Get all annotated images
        images = self.db.query(models.Image)\
            .filter(models.Image.episode_id == episode_id)\
            .filter(models.Image.annotation_status == "completed")\
            .all()

        # Group by label
        label_mapping = {}
        for image in images:
            label = image.current_label or "unlabeled"
            if label not in label_mapping:
                label_mapping[label] = []
            label_mapping[label].append(image.file_path)

        total_images = self.db.query(models.Image).filter(models.Image.episode_id == episode_id).count()

        return {
            "episode": episode.name,
            "total_images": total_images,
            "annotated_images": len(images),
            "label_mapping": label_mapping,
            "export_timestamp": datetime.utcnow().isoformat()
        }