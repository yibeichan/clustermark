from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import models, schemas
from app.services.episode_service import EpisodeService

router = APIRouter()

@router.post("/upload", response_model=schemas.Episode)
async def upload_episode(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    service = EpisodeService(db)
    return await service.upload_episode(file)

@router.get("/", response_model=List[schemas.Episode])
async def list_episodes(db: Session = Depends(get_db)):
    episodes = db.query(models.Episode).all()
    return episodes

@router.get("/{episode_id}", response_model=schemas.Episode)
async def get_episode(episode_id: str, db: Session = Depends(get_db)):
    episode = db.query(models.Episode).filter(models.Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode

@router.get("/{episode_id}/clusters", response_model=List[schemas.Cluster])
async def get_episode_clusters(episode_id: str, db: Session = Depends(get_db)):
    clusters = db.query(models.Cluster).filter(models.Cluster.episode_id == episode_id).all()
    return clusters

@router.get("/{episode_id}/export")
async def export_annotations(episode_id: str, db: Session = Depends(get_db)):
    service = EpisodeService(db)
    return await service.export_annotations(episode_id)