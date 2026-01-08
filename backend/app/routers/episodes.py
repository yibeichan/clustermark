from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import models, schemas
from app.services.episode_service import EpisodeService

router = APIRouter()


@router.post("/upload", response_model=schemas.Episode)
async def upload_episode(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
    clusters = (
        db.query(models.Cluster).filter(models.Cluster.episode_id == episode_id).all()
    )
    return clusters


@router.get("/{episode_id}/export")
async def export_annotations(episode_id: str, db: Session = Depends(get_db)):
    service = EpisodeService(db)
    return await service.export_annotations(episode_id)


@router.get("/{episode_id}/speakers", response_model=schemas.EpisodeSpeakersResponse)
async def get_episode_speakers(episode_id: str, db: Session = Depends(get_db)):
    """
    Get list of speakers for this episode.

    Returns speakers sorted by utterance frequency (descending).
    Used to populate dropdown options during annotation.

    Speakers are loaded from reference data (friends_speakers.tsv).
    If no speaker data exists for this episode, returns empty list
    (allows graceful fallback to custom input).

    Args:
        episode_id: UUID of the episode

    Returns:
        EpisodeSpeakersResponse with episode metadata and speaker list
    """
    service = EpisodeService(db)
    return await service.get_episode_speakers(episode_id)


@router.delete("/{episode_id}", status_code=204)
async def delete_episode(episode_id: str, db: Session = Depends(get_db)):
    """
    Delete an episode and all associated data.

    This permanently removes:
    - The episode record
    - All cluster records
    - All image records
    - All uploaded files
    """
    service = EpisodeService(db)
    await service.delete_episode(episode_id)
    return None


@router.post("/{episode_id}/replace", response_model=schemas.Episode)
async def replace_episode(
    episode_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """
    Replace an existing episode with a new upload.

    Deletes all existing data for this episode, then uploads the new ZIP.
    """
    service = EpisodeService(db)
    return await service.replace_episode(episode_id, file)

