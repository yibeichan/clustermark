# ClusterMark - Face Cluster Annotation Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

A web-based annotation system for validating and correcting automated face clustering results from the facetracker pipeline. This tool enables human reviewers to efficiently validate face clusters and provide ground truth data for improving clustering algorithms.

![ClusterMark Demo](docs/demo.gif)

## 🚀 Features

- **📁 Episode Management**: Upload and organize face clustering results from video episodes
- **🖼️ Interactive Annotation**: Review face clusters with an intuitive grid-based interface
- **👥 Split Cluster Support**: Handle clusters containing multiple people with scene/track grouping
- **📊 Progress Tracking**: Monitor annotation progress across episodes and clusters
- **💾 Export Functionality**: Export annotations in JSON format for analysis and model training
- **🎨 Responsive UI**: Clean, modern interface optimized for annotation workflows
- **🔄 Crowdsourcing Ready**: Session management for distributed annotation tasks

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python) with PostgreSQL database
- **Frontend**: React with TypeScript and Vite
- **Authentication**: JWT tokens for session management
- **Deployment**: Docker and Docker Compose
- **Database**: PostgreSQL with Alembic migrations

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for local development)
- **PostgreSQL 15+** (if running without Docker)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone git@github.com:yibeichan/clustermark.git
   cd clustermark
   ```

2. **Start the application:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

### Option 2: Manual Setup

1. **Clone and setup:**
   ```bash
   git clone git@github.com:yibeichan/clustermark.git
   cd clustermark
   ```

2. **Backend setup:**
   ```bash
   cd backend
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up database (ensure PostgreSQL is running)
   export DATABASE_URL="postgresql://user:password@localhost:5432/clustermark"
   alembic upgrade head
   
   # Start backend server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Frontend setup (in another terminal):**
   ```bash
   cd frontend
   
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   ```

## 📖 Usage Guide

### Step 1: Prepare Your Data

ClusterMark expects ZIP files containing cluster folders from your facetracker pipeline:

```
your_episode.zip
└── episode_name/
    ├── cluster_01/
    │   ├── scene_0_track_1_frame_001.jpg
    │   ├── scene_0_track_1_frame_015.jpg
    │   ├── scene_0_track_1_frame_032.jpg
    │   └── scene_2_track_5_frame_108.jpg
    ├── cluster_02/
    │   ├── scene_1_track_3_frame_042.jpg
    │   ├── scene_1_track_3_frame_055.jpg
    │   └── scene_3_track_7_frame_201.jpg
    └── cluster_XX/
        └── ...
```

**Important**: Image filenames must follow the pattern `scene_X_track_Y_frame_Z.jpg` for proper grouping in split annotations.

### Step 2: Upload Episode

1. Open ClusterMark in your browser (http://localhost:3000)
2. Drag and drop your ZIP file onto the upload area, or click to select
3. Wait for processing - the system will extract and organize your clusters
4. Your episode will appear in the episodes list

### Step 3: Annotate Clusters

1. **Navigate to your episode** by clicking on its name
2. **Start annotation** by clicking "Annotate" on any pending cluster
3. **Review the cluster**: All faces in the cluster are displayed in a grid
4. **Answer the key question**: "Do all these faces belong to the same person?"

   **If YES (Single Person):**
   - Click "Yes - Same Person"
   - Enter the person's name in the text field
   - Click "Save Annotation"

   **If NO (Multiple People):**
   - Click "No - Multiple People"
   - The system groups images by scene/track combinations
   - For each group, enter the person's name
   - Click "Save Split Annotations"

### Step 4: Monitor Progress

- Track annotation progress on the episode page
- See completed vs. total clusters
- Episode status updates automatically when all clusters are annotated

### Step 5: Export Results

1. Go to your episode page
2. Click "Export Annotations" button
3. Download the JSON file containing all annotations
4. Use this data to improve your clustering algorithms

## 📁 Project Structure

```
clustermark/
├── backend/                    # FastAPI backend application
│   ├── app/
│   │   ├── models/            # SQLAlchemy models and Pydantic schemas
│   │   │   ├── models.py      # Database models
│   │   │   └── schemas.py     # API schemas
│   │   ├── routers/           # API route handlers
│   │   │   ├── episodes.py    # Episode endpoints
│   │   │   ├── clusters.py    # Cluster endpoints
│   │   │   └── annotations.py # Annotation endpoints
│   │   ├── services/          # Business logic services
│   │   │   ├── episode_service.py
│   │   │   ├── cluster_service.py
│   │   │   └── annotation_service.py
│   │   ├── utils/             # Helper utilities
│   │   ├── database.py        # Database configuration
│   │   └── main.py           # FastAPI application entry point
│   ├── alembic/              # Database migrations
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile           # Backend container configuration
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/       # Reusable React components
│   │   ├── pages/           # Page components
│   │   │   ├── HomePage.tsx      # Episode list and upload
│   │   │   ├── EpisodePage.tsx   # Episode details and cluster list
│   │   │   └── AnnotationPage.tsx # Cluster annotation interface
│   │   ├── services/        # API client and utilities
│   │   │   └── api.ts       # API service functions
│   │   ├── types/           # TypeScript type definitions
│   │   │   └── index.ts     # Core type definitions
│   │   ├── utils/           # Frontend utilities
│   │   ├── App.tsx          # Main application component
│   │   ├── main.tsx         # Application entry point
│   │   └── index.css        # Global styles
│   ├── package.json         # Node.js dependencies
│   ├── vite.config.ts       # Vite build configuration
│   └── Dockerfile          # Frontend container configuration
├── docker-compose.yml       # Development environment setup
├── .gitignore              # Git ignore patterns
└── README.md               # This file
```

## 📡 API Reference

### Episodes
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/episodes/upload` | Upload cluster folder as ZIP file |
| `GET` | `/episodes` | List all episodes |
| `GET` | `/episodes/{id}` | Get episode details |
| `GET` | `/episodes/{id}/clusters` | Get all clusters for an episode |
| `GET` | `/episodes/{id}/export` | Export episode annotations as JSON |

### Clusters
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/clusters/{id}` | Get cluster details |
| `GET` | `/clusters/{id}/images` | Get cluster images grouped by scene/track |
| `POST` | `/clusters/{id}/annotate` | Submit single-person cluster annotation |

### Annotations
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/annotations/split` | Save split cluster annotations for multiple people |
| `GET` | `/annotations/tasks/next` | Get next task for crowdsourcing (requires session token) |
| `POST` | `/annotations/tasks/{id}/complete` | Mark crowdsourcing task as complete |

### API Documentation
- Interactive API docs: http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/openapi.json

## 🗄️ Database Schema

The system uses PostgreSQL with these main tables:

- **`episodes`**: Video episodes with clustering results
  - Tracks upload status, progress, and metadata
- **`clusters`**: Individual face clusters from facetracker
  - Contains image paths and annotation status
- **`split_annotations`**: Annotations for multi-person clusters
  - Links scene/track patterns to person names
- **`annotators`**: Session management for crowdsourcing
  - Tracks annotator sessions and completed tasks

## 📥 Input Format

**Expected ZIP structure:**
```
your_episode.zip
└── episode_name/
    ├── cluster_01/
    │   ├── scene_0_track_1_frame_001.jpg
    │   ├── scene_0_track_1_frame_015.jpg
    │   └── scene_2_track_5_frame_108.jpg
    ├── cluster_02/
    │   ├── scene_1_track_3_frame_042.jpg
    │   └── scene_3_track_7_frame_201.jpg
    └── cluster_XX/
        └── ...
```

**File naming requirements:**
- Images must follow pattern: `scene_{X}_track_{Y}_frame_{Z}.jpg`
- Cluster folders should be named: `cluster_{XX}`
- Supported formats: `.jpg`, `.jpeg`, `.png`

## 📤 Output Format

**Exported annotation JSON:**
```json
{
  "episode": "episode_name",
  "single_person_clusters": {
    "cluster_01": "John Doe",
    "cluster_03": "Jane Smith"
  },
  "split_clusters": {
    "scene_0_track_1": "John Doe",
    "scene_0_track_2": "Jane Smith",
    "scene_1_track_3": "Alice Johnson"
  },
  "export_timestamp": "2024-01-01T00:00:00Z",
  "total_clusters": 15,
  "annotated_clusters": 15,
  "episode_status": "completed"
}
```

## 🔧 Development

### Environment Variables

**Backend:**
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/clustermark
DEBUG=true
```

**Frontend:**
- Vite automatically proxies `/api` requests to the backend

### Adding New Features

1. **Backend Changes:**
   ```bash
   cd backend
   # Add models to app/models/models.py
   # Add API endpoints to app/routers/
   # Add business logic to app/services/
   # Create migration: alembic revision --autogenerate -m "description"
   # Apply migration: alembic upgrade head
   ```

2. **Frontend Changes:**
   ```bash
   cd frontend
   # Add types to src/types/index.ts
   # Add API calls to src/services/api.ts
   # Create components in src/components/
   # Add pages to src/pages/
   ```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Testing

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test

# End-to-end tests
npm run test:e2e
```

### Code Quality

```bash
# Backend linting
cd backend
black app/
flake8 app/
mypy app/

# Frontend linting
cd frontend
npm run lint
npm run type-check
```

## 🚀 Deployment

### Production Deployment

1. **Environment Setup:**
   ```bash
   # Set production environment variables
   export DATABASE_URL="postgresql://user:password@prod-db:5432/clustermark"
   export DEBUG=false
   ```

2. **Docker Production:**
   ```bash
   # Build production images
   docker-compose -f docker-compose.prod.yml build
   
   # Deploy
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Manual Production:**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   alembic upgrade head
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   
   # Frontend
   cd frontend
   npm install
   npm run build
   # Serve dist/ with nginx or similar
   ```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes and add tests**
4. **Run quality checks:**
   ```bash
   # Backend
   cd backend && python -m pytest && black . && flake8 .
   
   # Frontend  
   cd frontend && npm test && npm run lint
   ```
5. **Commit your changes:**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to your branch:**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Development Guidelines

- Follow existing code style and conventions
- Add tests for new features
- Update documentation as needed
- Keep commits focused and atomic
- Write clear commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for integration with the facetracker pipeline
- Designed for efficient human-in-the-loop annotation workflows
- Optimized for crowdsourcing and distributed annotation tasks

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yibeichan/clustermark/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yibeichan/clustermark/discussions)
- **Email**: [your-email@domain.com](mailto:your-email@domain.com)

---

**Happy Annotating! 🎯**