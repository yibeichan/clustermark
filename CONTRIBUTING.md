# Contributing to ClusterMark

Thank you for your interest in contributing to ClusterMark! This guide will help you get started with development.

## Quick Start for Developers

### Prerequisites
- Docker Desktop (recommended) OR
- Python 3.11+ + Node.js 18+ + PostgreSQL 15+

### Setup with Docker (Easiest)

```bash
git clone https://github.com/yibeichan/clustermark.git
cd clustermark
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Setup without Docker

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows (PowerShell or CMD)
pip install -r requirements.txt
export DATABASE_URL="postgresql://user:password@localhost:5432/clustermark"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Terminal 3 - Tests:**
```bash
# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && pytest -v
```

---

## Tech Stack

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy + Alembic
- **Frontend**: React 18 + TypeScript + Vite
- **Testing**: Vitest + React Testing Library (frontend), pytest (backend)
- **Deployment**: Docker Compose

---

## Project Structure

```
clustermark/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── models/            # SQLAlchemy models + Pydantic schemas
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── database.py        # DB connection
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   ├── tests/                # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client
│   │   ├── types/           # TypeScript types
│   │   └── __tests__/       # Tests
│   ├── package.json
│   └── vitest.config.ts
├── docker-compose.yml
├── README.md                 # User documentation
├── CONTRIBUTING.md          # This file
└── DEPLOYMENT.md            # Production deployment
```

---

## API Documentation

### Episodes
- `POST /episodes/upload` - Upload ZIP file with face clusters
- `GET /episodes` - List all episodes
- `GET /episodes/{id}` - Get episode details
- `GET /episodes/{id}/export` - Export annotations as JSON

### Clusters
- `GET /clusters/{id}` - Get cluster details
- `GET /clusters/{id}/images/paginated?page=1&page_size=20` - Get paginated images
- `POST /clusters/{id}/outliers` - Mark outlier images
- `GET /clusters/{id}/outliers` - Get currently marked outliers
- `POST /clusters/{id}/annotate-batch` - Batch label non-outlier images
- `POST /clusters/annotate-outliers` - Label individual outliers

**Interactive API docs:** http://localhost:8000/docs (when running)

---

## Database Schema

### Main Tables

**episodes**
- Tracks uploaded episodes with season/episode metadata
- Fields: id, name, path, status, progress, season, episode, created_at

**clusters**
- Face clusters from episodes
- Fields: id, episode_id, name, initial_label, annotation_status, image_paths (array)

**images**
- Individual images within clusters
- Fields: id, cluster_id, file_path, initial_label, current_label, annotation_status, is_outlier

**split_annotations** (legacy)
- For multi-person clusters
- Fields: id, cluster_id, scene_track_pattern, label

**annotators**
- Session management for crowdsourcing (future)
- Fields: id, session_token, created_at

### Relationships
- Episode 1:N Clusters
- Cluster 1:N Images
- Cluster 1:N SplitAnnotations

---

## Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current
```

---

## Testing

### Frontend Tests

```bash
cd frontend

# Run tests once
npm test

# Watch mode (auto-rerun on changes)
npx vitest

# UI mode (interactive)
npx vitest --ui

# View coverage
npm test
open coverage/index.html
```

**Coverage targets:**
- Frontend: >70% (currently ~34%)
- Backend: >80% (currently ~80%)

### Backend Tests

```bash
cd backend

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_episode_service.py -v
```

---

## Contributing Workflow

1. **Fork the repository**

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add tests for new features
   - Update documentation if needed

4. **Code style**
   - **Python**: Use Black for formatting, flake8 for linting
     ```bash
     cd backend
     black app/
     flake8 app/
     ```
   - **TypeScript**: Use ESLint
     ```bash
     cd frontend
     npm run lint
     ```

5. **Run tests**
   ```bash
   # Frontend
   cd frontend && npm test
   
   # Backend
   cd backend && pytest -v
   ```

6. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
   
   Use conventional commit format:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test changes
   - `refactor:` Code refactoring
   - `chore:` Maintenance tasks

7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request**
   - Describe what your PR does
   - Reference any related issues
   - Include screenshots if UI changes

---

## Development Best Practices

### Backend

- Use dependency injection for database sessions (`Depends(get_db)`)
- Write Pydantic schemas for request/response validation
- Keep business logic in services, not routers
- Name all database constraints explicitly
- Test database operations with transactions
- Use type hints everywhere

### Frontend

- Use TypeScript strict mode
- Follow React hooks best practices
- Keep components small and focused
- Use React Testing Library for tests
- Use `userEvent` instead of `fireEvent` in tests
- Handle loading and error states

### General

- Write tests for new features (required)
- Update documentation for user-facing changes
- Keep PRs focused and small (<500 lines)
- Respond to all code review feedback
- Test your changes with Docker before submitting

---

## Helpful Resources

- **API Documentation**: http://localhost:8000/docs
- **React Testing Library**: https://testing-library.com/docs/react-testing-library/intro
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Vitest**: https://vitest.dev/
- **SQLAlchemy**: https://docs.sqlalchemy.org/

---

## Getting Help

- **Issues**: https://github.com/yibeichan/clustermark/issues
- **Discussions**: https://github.com/yibeichan/clustermark/discussions

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
