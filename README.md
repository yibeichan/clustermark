# ClusterMark - Friends Face Annotation Tool

Efficiently label face clusters from Friends TV show episodes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18+](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

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
  "metadata": {
    "episode_id": "friends_s01e05",
    "season": 1,
    "episode": 5,
    "clustering_file": "friends_s01e05_matched_faces_with_clusters.json",
    "model_name": "vggface2",
    "annotation_date": "2025-12-02T10:30:00Z",
    "annotator_id": "user_01"
  },
  "cluster_annotations": {
    "cluster-01": {
      "label": "rachel",
      "confidence": "high",
      "image_count": 20,
      "image_paths": [
        "friends_s01e05/friends_s01e05_cluster-01/scene_0_track_1_frame_001.jpg",
        "friends_s01e05/friends_s01e05_cluster-01/scene_0_track_1_frame_015.jpg",
        "...more image paths..."
      ],
      "outliers": []
    },
    "cluster-02": {
      "label": "monica",
      "confidence": "medium",
      "image_count": 16,
      "image_paths": [
        "friends_s01e05/friends_s01e05_cluster-02/scene_1_track_1_frame_020.jpg",
        "friends_s01e05/friends_s01e05_cluster-02/scene_1_track_1_frame_035.jpg",
        "...more image paths..."
      ],
      "outliers": [
        {
          "image_path": "friends_s01e05/friends_s01e05_cluster-02/scene_0_track_1_frame_001.jpg",
          "label": "chandler"
        },
        {
          "image_path": "friends_s01e05/friends_s01e05_cluster-02/scene_0_track_1_frame_015.jpg",
          "label": "chandler"
        }
      ]
    }
  },
  "statistics": {
    "total_clusters": 15,
    "annotated_clusters": 2,
    "total_faces": 38,
    "outliers_found": 2,
    "not_human_clusters": 0,
    "character_distribution": {
      "rachel": 20,
      "monica": 16,
      "chandler": 2
    }
  }
}
```

**Export includes:**
- **metadata**: Episode info, annotation date, model name
- **cluster_annotations**: Per-cluster labels with full image paths and outlier details
- **statistics**: Aggregated counts and character distribution
- **confidence**: Auto-calculated based on outlier ratio (high: 0%, medium: <20%, low: ≥20%)

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

## Production Deployment

To run ClusterMark on a server (instead of your local machine):

**1. Clone on your server:**
```bash
git clone https://github.com/yibeichan/clustermark.git
cd clustermark
```

**2. Change default password:**
Edit `docker-compose.yml` and change the database password:
```yaml
db:
  environment:
    POSTGRES_PASSWORD: your_secure_password_here  # Change from "password"
```

**3. Start in detached mode:**
```bash
docker-compose up -d --build
```

**4. Access the app:**
- Frontend: http://your-server-ip:3000
- Backend API: http://your-server-ip:8000

**Optional: Set up domain and HTTPS**

Use nginx as a reverse proxy:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

Then add SSL with Let's Encrypt: `certbot --nginx -d your-domain.com`

---

## For Developers

Want to contribute? See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup instructions
- Project structure and architecture
- API documentation
- Database schema
- Testing guidelines
- Code style and best practices

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

- **API Documentation**: http://localhost:8000/docs (when running)
- **Contributing Guide**: See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines

**Questions or Issues?**
- GitHub Issues: https://github.com/yibeichan/clustermark/issues
- Discussions: https://github.com/yibeichan/clustermark/discussions
