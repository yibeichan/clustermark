# ClusterMark - Friends Face Annotation Tool

Efficiently label face clusters from Friends TV show episodes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18+](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)

---

## Quick Start

### Prerequisites

- **macOS/Linux**: [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Windows**: See [Windows Setup Guide](docs/WINDOWS-SETUP.md) for Docker Desktop, Podman, or WSL2 options

### Start the App

```bash
git clone https://github.com/yibeichan/clustermark.git
cd clustermark
docker-compose up --build
```

Wait ~1 minute, then open **http://localhost:3000**

---

## How to Use

### 1. Upload Episode

Upload a ZIP file with this structure:
```
Friends_S01E05.zip
└── Friends_S01E05/
    ├── S01E05_cluster-01/
    │   ├── scene_0_track_1_frame_001.jpg
    │   └── scene_0_track_1_frame_015.jpg
    ├── S01E05_cluster-02/
    │   └── ...
    └── S01E05_Rachel/  (optional: pre-labeled)
```

### 2. Annotate Clusters

```
Review Images → Mark Outliers (if any) → Select Character → Save
```

**Clean cluster (95% of cases):** See same person → Select name → Done in 3 clicks

**Mixed cluster:** Click wrong faces (red border) → Label outliers separately → Label remaining

### 3. Harmonize & Export

- **Harmonize**: Merge duplicate labels (e.g., "Rachel" + "Rach" → "Rachel")
- **Export**: Download JSON with all annotations (can re-import later)

---

## Features

- **Fast batch labeling**: Label 10-50 images in 3 clicks
- **Outlier handling**: Mark and label misplaced faces separately
- **Friends characters**: Dropdown with main cast + episode-specific speakers
- **Harmonization**: Consolidate labels across clusters
- **Round-trip workflow**: Export → Re-import to resume work
- **Quality attributes**: Mark images as `@blurry`, `@dark`, etc.

---

## Troubleshooting

**App won't start:**
```bash
docker-compose down
docker-compose up --build
docker-compose logs -f backend  # Check logs
```

**Database issues (reset all data):**
```bash
docker-compose down -v
docker-compose up --build
```

**Port conflicts:**
Edit `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Change frontend port
  - "8001:8000"  # Change backend port
```

**Windows users:** See [Windows Setup Guide](docs/WINDOWS-SETUP.md)

---

## Production Deployment

```bash
# On your server
git clone https://github.com/yibeichan/clustermark.git
cd clustermark

# Change default password in docker-compose.yml
# POSTGRES_PASSWORD: your_secure_password_here

docker-compose up -d --build
```

Access at `http://your-server-ip:3000`

For HTTPS, use nginx reverse proxy + Let's Encrypt.

---

## For Developers

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Project architecture
- API documentation
- Testing guidelines

**API Docs**: http://localhost:8000/docs (when running)

---

## License

MIT License - see [LICENSE](LICENSE)

---

**Questions?** [GitHub Issues](https://github.com/yibeichan/clustermark/issues)
