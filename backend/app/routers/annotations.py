from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import models, schemas
from app.services.annotation_service import AnnotationService

router = APIRouter()

@router.post("/split", response_model=List[schemas.SplitAnnotation])
async def create_split_annotations(
    annotations: List[schemas.SplitAnnotationCreate],
    db: Session = Depends(get_db)
):
    service = AnnotationService(db)
    return await service.create_split_annotations(annotations)

@router.get("/tasks/next")
async def get_next_task(
    session_token: str,
    db: Session = Depends(get_db)
):
    service = AnnotationService(db)
    return await service.get_next_task(session_token)

@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    session_token: str,
    db: Session = Depends(get_db)
):
    service = AnnotationService(db)
    return await service.complete_task(task_id, session_token)