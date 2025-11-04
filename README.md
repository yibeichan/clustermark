# ClusterMark - Friends Face Annotation Tool

Efficiently label face clusters from Friends TV show episodes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18+](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

<!-- TODO: Add demo GIF here - placeholder for visual demonstration -->

---

## Quick Start

### Prerequisites
- Docker Desktop installed ([download here](https://www.docker.com/products/docker-desktop))

### Step 1: Clone & Start

```bash
git clone https://github.com/yibeichan/clustermark.git
cd clustermark
docker-compose up --build
```

Wait ~1 minute for containers to start. You'll see:
```
✔ Container clustermark-db-1        Started
✔ Container clustermark-backend-1   Started  
✔ Container clustermark-frontend-1  Started
```

### Step 2: Open the App

Go to **http://localhost:3000** in your browser.

### Step 3: Upload Your First Episode

ClusterMark expects a ZIP file with this structure:

```
Friends_S01E05.zip
└── Friends_S01E05/
    ├── S01E05_cluster-01/
    │   ├── scene_0_track_1_frame_001.jpg
    │   ├── scene_0_track_1_frame_015.jpg
    │   └── scene_2_track_5_frame_108.jpg
    ├── S01E05_cluster-02/
    │   └── ...
    └── S01E05_Rachel/  (optional: pre-labeled clusters)
        └── ...
```

**Folder naming:**
- `S01E05_cluster-01` → Season 1, Episode 5, Cluster 1 (unlabeled)
- `S01E05_Rachel` → Season 1, Episode 5, pre-labeled as "Rachel"
- Case insensitive: `s01e05_joey` works too

**Upload:**
1. Drag & drop your ZIP onto the upload area (or click to browse)
2. Wait for processing (a few seconds)
3. Click on your episode name to start annotating

### Step 4: Annotate Clusters

The workflow:

```
1. Review All Images (paginated)
   ├─ View 10/20/50 images per page
   ├─ Click images to mark as outliers (red border)
   └─ Click "Continue"

2. Choose Your Path
   ├─ No outliers? → Select character from dropdown → Save
   └─ Has outliers? → Label outliers individually → Label remaining images

3. Next Cluster
```

**Example: Clean cluster (no outliers)**
1. See 20 images of Rachel
2. Click "Continue" (no outliers selected)
3. Select "Rachel" from dropdown
4. Click "Save Annotation"
5. All 20 images labeled as Rachel

**Example: Mixed cluster (has outliers)**
1. See 18 images of Monica + 2 images of Chandler
2. Click the 2 Chandler images (they get red borders)
3. Click "Continue"
4. Label first outlier: "Chandler"
5. Label second outlier: "Chandler"
6. Label remaining 18 images: "Monica"

### Step 5: Export Results

1. Go back to episode page
2. Click "Export Annotations"
3. Download JSON file with all your labels

**JSON format:**
```json
{
  "episode_name": "Friends_S01E05",
  "season": 1,
  "episode": 5,
  "annotations": {
    "cluster-01": {
      "label": "Rachel",
      "image_count": 20,
      "outliers": []
    },
    "cluster-02": {
      "label": "Monica",
      "image_count": 18,
      "outliers": [
        {"image": "scene_0_track_1_frame_001.jpg", "label": "Chandler"},
        {"image": "scene_0_track_1_frame_015.jpg", "label": "Chandler"}
      ]
    }
  }
}
```

---

## Usage Tips

### Efficient Annotation

**Batch label clean clusters (fastest):**
- Most clusters are correct (95%+)
- If all faces look like the same person, just select name and save
- The outlier workflow is there if needed

**When to use outliers:**
- You see 2+ different people in the cluster
- A few images are clearly wrong (different face)
- Mixed clusters (e.g., group scenes with multiple characters)

### Data Preparation

**Folder naming conventions:**
- **Recommended**: `SxxEyy_cluster-zz` format (e.g., `S01E05_cluster-01`)
  - Captures season/episode metadata automatically
  - Case insensitive: `s01e05` or `S01E05` both work
  
- **Pre-labeled clusters**: `SxxEyy_CharacterName` (e.g., `S01E05_Rachel`)
  - App will suggest "Rachel" as initial label
  - You can still change it if needed

- **Legacy format**: `cluster_01`, `cluster_02`, etc.
  - Still works, just doesn't capture season/episode info

**Image naming requirements:**
- Must follow pattern: `scene_X_track_Y_frame_Z.jpg`
- Example: `scene_0_track_1_frame_001.jpg`
- Required for splitting clusters by scene/track

---

## Features

- Fast annotation: Label entire clusters in 3 clicks (10-20 images at once)
- Friends characters: Dropdown menu with main cast (Chandler, Joey, Monica, Rachel, Ross, Phoebe)
- Paginated review: Browse through 10/20/50 images per page
- Outlier handling: Click to mark images that don't belong, then label them separately
- Progress tracking: See how many clusters you've labeled
- Export results: Download annotations as JSON

**Current Status:**
- Core annotation workflow complete (Phases 1-6)
- Testing infrastructure complete (Phase 7)
- All features listed above are working

**Known limitations:**
- No keyboard shortcuts yet
- Single user mode (no concurrent annotations)
- No undo/redo functionality (save is final)

---

## For Developers

### Tech Stack

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy + Alembic
- **Frontend**: React 18 + TypeScript + Vite + React Testing Library
- **Deployment**: Docker Compose (local-first, no external services)
- **Testing**: Vitest + React Testing Library (frontend), pytest (backend)

### Development Setup

**Requirements:**
- Docker Desktop (easiest) OR
- Python 3.11+ + Node.js 18+ + PostgreSQL 15+

**Option 1: Docker (Recommended)**
```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

**Option 2: Local Development**
```bash
# Terminal 1: Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://user:password@localhost:5432/clustermark"
alembic upgrade head
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev

# Terminal 3: Tests
cd frontend && npm test    # Frontend tests
cd backend && pytest      # Backend tests
```

### Project Structure

```
clustermark/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── models/            # SQLAlchemy models + Pydantic schemas
│   │   ├── routers/           # API endpoints (episodes, clusters, annotations)
│   │   ├── services/          # Business logic (episode, cluster, annotation services)
│   │   ├── database.py        # DB connection & session management
│   │   └── main.py           # FastAPI app entry point
│   ├── alembic/              # Database migrations
│   ├── tests/                # Backend tests
│   └── requirements.txt      # Python dependencies
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # Reusable components (LabelDropdown, etc.)
│   │   ├── pages/           # Page components (HomePage, AnnotationPage)
│   │   ├── services/        # API client (api.ts)
│   │   ├── types/           # TypeScript types
│   │   └── __tests__/       # Frontend tests
│   ├── package.json
│   └── vitest.config.ts     # Test configuration
├── docs/                     # Documentation & internal guides
├── docker-compose.yml        # Development environment
└── README.md                # This file
```

### API Endpoints

**Episodes:**
- `POST /episodes/upload` - Upload ZIP file
- `GET /episodes` - List all episodes
- `GET /episodes/{id}` - Get episode details
- `GET /episodes/{id}/export` - Export annotations

**Clusters:**
- `GET /clusters/{id}` - Get cluster details
- `GET /clusters/{id}/images/paginated?page=1&page_size=20` - Get paginated images
- `POST /clusters/{id}/outliers` - Mark outlier images
- `GET /clusters/{id}/outliers` - Get current outliers
- `POST /clusters/{id}/annotate-batch` - Batch label non-outlier images
- `POST /clusters/annotate-outliers` - Label individual outlier images

**Interactive API docs:** http://localhost:8000/docs

### Database Schema

The system uses PostgreSQL with these main tables:

- **episodes**: Video episodes with clustering results
  - Fields: id, name, path, status, progress, season, episode, created_at
  - Tracks upload status and metadata
  
- **clusters**: Individual face clusters from episodes
  - Fields: id, episode_id, name, initial_label, annotation_status, image_paths
  - Contains array of image paths and annotation status
  
- **images**: Individual images within clusters
  - Fields: id, cluster_id, file_path, initial_label, current_label, annotation_status, is_outlier
  - Tracks per-image labels and outlier status
  
- **split_annotations**: Annotations for multi-person clusters (legacy)
  - Fields: id, cluster_id, scene_track_pattern, label
  - Links scene/track patterns to person names
  
- **annotators**: Session management for crowdsourcing
  - Fields: id, session_token, created_at
  - Tracks annotator sessions

**Relationships:**
- Episode 1:N Clusters
- Cluster 1:N Images
- Cluster 1:N SplitAnnotations

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Frontend tests (Vitest + React Testing Library)
cd frontend
npm test                    # Run once
npx vitest                 # Watch mode
npx vitest --ui            # UI mode
open coverage/index.html   # View coverage

# Backend tests (pytest)
cd backend
pytest tests/ -v
pytest --cov=app tests/    # With coverage
```

**Current coverage:**
- Backend: ~80%
- Frontend: ~34%

### Contributing

We welcome contributions:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow existing code style (Black for Python, ESLint for TypeScript)
4. Add tests for new features
5. Run tests before committing: `npm test` (frontend), `pytest` (backend)
6. Write clear commit messages
7. Open a PR with description of changes

**See also:**
- `docs/internal/BEST-PRACTICES.md` - Development guidelines
- `docs/internal/LESSONS-LEARNED-*.md` - Lessons from previous PRs
- `CLAUDE.md` - Project overview for Claude Code

---

## Troubleshooting

**App won't start:**
```bash
# Check Docker is running
docker ps

# Restart containers
docker-compose down
docker-compose up --build

# Check logs (follow in real-time)
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Upload fails:**
```bash
# Check uploads volume has space
docker-compose exec backend df -h

# Check backend logs
docker-compose logs -f backend
```

**Database issues:**
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up --build
```

**Port conflicts (3000 or 8000 already in use):**
```bash
# Edit docker-compose.yml and change ports:
ports:
  - "3001:3000"  # Frontend
  - "8001:8000"  # Backend
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built for validating face clustering results from the Friends TV show dataset. Designed for efficient human-in-the-loop annotation workflows.

---

## Additional Resources

- **Production Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup, security, scaling, and monitoring
- **API Documentation**: http://localhost:8000/docs (when running)
- **Project Implementation Plan**: `docs/internal/implementation-plan-friends-annotation.md`
- **Lessons Learned**: `docs/internal/LESSONS-LEARNED-*.md`
- **Development Guide**: `docs/internal/BEST-PRACTICES.md`

**Questions or Issues?**
- GitHub Issues: https://github.com/yibeichan/clustermark/issues
- Discussions: https://github.com/yibeichan/clustermark/discussions
