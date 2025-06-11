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
                image_paths=cluster_data["images"]
            )
            self.db.add(cluster)
        
        self.db.commit()
        return episode

    async def _parse_clusters(self, episode_path: Path) -> List[Dict]:
        clusters = []
        for cluster_dir in episode_path.iterdir():
            if cluster_dir.is_dir() and cluster_dir.name.startswith('cluster_'):
                images = []
                for img_file in cluster_dir.glob('*.jpg'):
                    images.append(str(img_file.relative_to(self.upload_dir)))
                
                if images:
                    clusters.append({
                        "name": cluster_dir.name,
                        "images": images
                    })
        
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