from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import models, schemas
from app.services.cluster_service import ClusterService

router = APIRouter()

@router.get("/{cluster_id}", response_model=schemas.Cluster)
async def get_cluster(cluster_id: str, db: Session = Depends(get_db)):
    cluster = db.query(models.Cluster).filter(models.Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster

@router.post("/{cluster_id}/annotate")
async def annotate_cluster(
    cluster_id: str,
    annotation: schemas.ClusterAnnotate,
    db: Session = Depends(get_db)
):
    service = ClusterService(db)
    return await service.annotate_cluster(cluster_id, annotation)

@router.get("/{cluster_id}/images")
async def get_cluster_images(cluster_id: str, db: Session = Depends(get_db)):
    service = ClusterService(db)
    return await service.get_cluster_images(cluster_id)