from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import episodes, clusters, annotations, images

app = FastAPI(
    title="ClusterMark API",
    description="Face cluster annotation system",
    version="1.0.0"
)

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
app.include_router(images.router, prefix="/api", tags=["images"])

@app.get("/")
async def root():
    return {"message": "ClusterMark API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}