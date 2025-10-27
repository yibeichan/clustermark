from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import models, schemas
from app.services.image_service import ImageService

router = APIRouter()

@router.get("/episodes/{episode_id}/images/next")
async def get_next_image(episode_id: str, db: Session = Depends(get_db)):
    """Get next pending image to annotate"""
    service = ImageService(db)
    image = await service.get_next_pending_image(episode_id)
    if not image:
        return {"message": "No pending images", "image": None}
    return image

@router.post("/images/{image_id}/annotate")
async def annotate_image(
    image_id: str,
    annotation: schemas.ImageAnnotate,
    db: Session = Depends(get_db)
):
    """Save annotation for an image"""
    service = ImageService(db)
    return await service.annotate_image(image_id, annotation.label)

@router.get("/episodes/{episode_id}/labels")
async def get_episode_labels(episode_id: str, db: Session = Depends(get_db)):
    """Get all unique labels for dropdown"""
    service = ImageService(db)
    labels = await service.get_all_labels(episode_id)
    return {"labels": labels}

@router.get("/images/{image_id}")
async def get_image(image_id: str, db: Session = Depends(get_db)):
    """Get single image details"""
    image = db.query(models.Image).filter(models.Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image
