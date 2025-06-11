import os
from pathlib import Path
from typing import List, Dict
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import models, schemas

class ClusterService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("uploads")

    async def annotate_cluster(self, cluster_id: str, annotation: schemas.ClusterAnnotate) -> Dict:
        cluster = self.db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        cluster.is_single_person = annotation.is_single_person
        cluster.person_name = annotation.person_name
        cluster.annotation_status = "completed"
        
        episode = self.db.query(models.Episode).filter(models.Episode.id == cluster.episode_id).first()
        if episode:
            episode.annotated_clusters += 1
            if episode.annotated_clusters >= episode.total_clusters:
                episode.status = "completed"
        
        self.db.commit()
        
        return {
            "cluster_id": str(cluster.id),
            "status": "completed",
            "is_single_person": cluster.is_single_person,
            "person_name": cluster.person_name
        }

    async def get_cluster_images(self, cluster_id: str) -> Dict:
        cluster = self.db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        images_by_track = {}
        for image_path in cluster.image_paths:
            filename = Path(image_path).name
            if 'scene_' in filename and 'track_' in filename:
                parts = filename.split('_')
                scene_idx = next(i for i, part in enumerate(parts) if part == 'scene') + 1
                track_idx = next(i for i, part in enumerate(parts) if part == 'track') + 1
                
                if scene_idx < len(parts) and track_idx < len(parts):
                    scene_track = f"scene_{parts[scene_idx]}_track_{parts[track_idx]}"
                    if scene_track not in images_by_track:
                        images_by_track[scene_track] = []
                    images_by_track[scene_track].append(image_path)
        
        return {
            "cluster_id": str(cluster.id),
            "cluster_name": cluster.cluster_name,
            "all_images": cluster.image_paths,
            "grouped_by_track": images_by_track
        }