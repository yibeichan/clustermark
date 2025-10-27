from sqlalchemy.orm import Session
from app.models import models
from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException

class ImageService:
    def __init__(self, db: Session):
        self.db = db

    async def get_next_pending_image(self, episode_id: str) -> Optional[models.Image]:
        """Get next unannotated image for an episode"""
        return self.db.query(models.Image)\
            .filter(models.Image.episode_id == episode_id)\
            .filter(models.Image.annotation_status == "pending")\
            .order_by(models.Image.cluster_id, models.Image.filename)\
            .first()

    async def annotate_image(self, image_id: str, label: str) -> models.Image:
        """Save annotation for an image"""
        image = self.db.query(models.Image).filter(models.Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        image.current_label = label
        image.annotation_status = "completed"
        image.annotated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(image)

        # Update episode progress
        await self._update_episode_progress(image.episode_id)

        return image

    async def _update_episode_progress(self, episode_id: str):
        """Recalculate episode annotation progress"""
        total = self.db.query(models.Image).filter(models.Image.episode_id == episode_id).count()
        completed = self.db.query(models.Image)\
            .filter(models.Image.episode_id == episode_id)\
            .filter(models.Image.annotation_status == "completed")\
            .count()

        episode = self.db.query(models.Episode).filter(models.Episode.id == episode_id).first()
        if episode:
            episode.total_clusters = total  # Rename to total_images?
            episode.annotated_clusters = completed  # Rename to annotated_images?
            if total > 0 and completed == total:
                episode.status = "completed"
            elif completed > 0:
                episode.status = "in_progress"
            self.db.commit()

    async def get_all_labels(self, episode_id: str) -> List[str]:
        """Get list of all unique labels in episode for dropdown"""
        labels = self.db.query(models.Image.initial_label)\
            .filter(models.Image.episode_id == episode_id)\
            .filter(models.Image.initial_label.isnot(None))\
            .distinct()\
            .all()
        return sorted([label[0] for label in labels])
