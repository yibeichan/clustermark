from typing import List, Dict, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import models, schemas

class AnnotationService:
    def __init__(self, db: Session):
        self.db = db

    async def create_split_annotations(self, annotations: List[schemas.SplitAnnotationCreate]) -> List[models.SplitAnnotation]:
        created_annotations = []
        
        for annotation_data in annotations:
            cluster = self.db.query(models.Cluster).filter(
                models.Cluster.id == annotation_data.cluster_id
            ).first()
            
            if not cluster:
                raise HTTPException(status_code=404, detail=f"Cluster {annotation_data.cluster_id} not found")
            
            annotation = models.SplitAnnotation(
                cluster_id=annotation_data.cluster_id,
                scene_track_pattern=annotation_data.scene_track_pattern,
                person_name=annotation_data.person_name,
                image_paths=annotation_data.image_paths
            )
            self.db.add(annotation)
            created_annotations.append(annotation)
        
        self.db.commit()
        
        if annotations:
            cluster = self.db.query(models.Cluster).filter(
                models.Cluster.id == annotations[0].cluster_id
            ).first()
            cluster.annotation_status = "completed"
            cluster.is_single_person = False
            
            episode = self.db.query(models.Episode).filter(models.Episode.id == cluster.episode_id).first()
            if episode:
                episode.annotated_clusters += 1
                if episode.annotated_clusters >= episode.total_clusters:
                    episode.status = "completed"
            
            self.db.commit()
        
        return created_annotations

    async def get_next_task(self, session_token: str) -> Optional[Dict]:
        annotator = self.db.query(models.Annotator).filter(
            models.Annotator.session_token == session_token
        ).first()
        
        if not annotator:
            raise HTTPException(status_code=404, detail="Invalid session token")
        
        cluster = self.db.query(models.Cluster).filter(
            models.Cluster.annotation_status == "pending"
        ).first()
        
        if not cluster:
            return {"message": "No more tasks available"}
        
        cluster.annotation_status = "in_progress"
        self.db.commit()
        
        return {
            "cluster_id": str(cluster.id),
            "cluster_name": cluster.cluster_name,
            "episode_name": cluster.episode.name,
            "image_paths": cluster.image_paths
        }

    async def complete_task(self, task_id: str, session_token: str) -> Dict:
        annotator = self.db.query(models.Annotator).filter(
            models.Annotator.session_token == session_token
        ).first()
        
        if not annotator:
            raise HTTPException(status_code=404, detail="Invalid session token")
        
        cluster = self.db.query(models.Cluster).filter(models.Cluster.id == task_id).first()
        if not cluster:
            raise HTTPException(status_code=404, detail="Task not found")
        
        annotator.completed_tasks += 1
        self.db.commit()
        
        return {
            "task_id": task_id,
            "status": "completed",
            "annotator_completed_tasks": annotator.completed_tasks
        }