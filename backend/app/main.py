from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.routers import episodes, clusters, annotations

app = FastAPI(
    title="ClusterMark API",
    description="Face cluster annotation system",
    version="1.0.0",
)

# Serve uploaded images as static files
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(episodes.router, prefix="/episodes", tags=["episodes"])
app.include_router(clusters.router, prefix="/clusters", tags=["clusters"])
app.include_router(annotations.router, prefix="/annotations", tags=["annotations"])


@app.get("/")
async def root():
    return {"message": "ClusterMark API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
