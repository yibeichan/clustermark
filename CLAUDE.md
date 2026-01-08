# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL: DO NOT COMMIT THIS FILE 🚨

**This file (CLAUDE.md) and docs/internal/* are in .gitignore and MUST NEVER be committed.**

See `docs/internal/DEV-RULES.md` for complete git workflow rules.

## Project Overview

ClusterMark is a web-based face cluster annotation tool for validating automated face clustering results. It's a full-stack application with a FastAPI backend and React frontend, designed for human-in-the-loop annotation workflows.

**Tech Stack:**
- Backend: FastAPI (Python) + PostgreSQL + SQLAlchemy + Alembic
- Frontend: React 18 + TypeScript + Vite
- Deployment: Docker Compose (local-first, no external services)

## Active Development Plans

**✅ Current State (Main Branch):**
- Cluster-based validation workflow
- "Same person?" question → single name OR split by scene/track
- Basic folder parsing (`cluster_*` format)
- Image model migration exists (`001_add_image_annotations.py`)

**🎯 Target State: Friends Character Annotation System**

**See detailed plan:** `docs/internal/implementation-plan-friends-annotation.md`
**See best practices:** `docs/internal/BEST-PRACTICES.md`
**See lessons learned:** `docs/internal/LESSONS-LEARNED-PR2.md` ⭐ **READ THIS!**

### Key Goals
1. **Parse episode metadata**: Support `SxxEyy_cluster-zz` folder naming (Season/Episode/Cluster)
2. **Paginated cluster review**: Show 10/20/50 images per page, click-to-select outliers
3. **Predefined labels**: Dropdown with Friends characters (Chandler, Joey, Monica, Rachel, Ross, Phoebe, Others)
4. **Two-path workflow**:
   - **Path A (no outliers)**: Batch label entire cluster → done in 3 clicks
   - **Path B (has outliers)**: Annotate outliers individually → batch label remaining

### Why This Design?
- **Optimizes common case**: 95% of clusters are correct, batch labeling is fastest
- **Handles edge cases**: Outlier workflow for mixed/incorrect clusters
- **Reduces typing**: Predefined dropdown faster than text input
- **Maintains local-first**: No external services, runs in Docker Compose

### Previous Refactoring (Closed)

**PR: feature/folder-based-labels (CLOSED 2025-10-28)**
- Attempted image-by-image annotation (too slow for clean clusters)
- Introduced API routing bugs and serialization issues
- Codex/Gemini reviews identified critical flaws
- **Decision**: Reverted to main, redesigned as cluster-based with outlier handling

**Issues found:**
- `/api/api/` prefix duplication in frontend
- Missing response serialization for Image endpoints
- Broken legacy routes
- Inconsistent workflow (cluster list + image-by-image confusion)

**See:** `docs/internal/refactor-plan-folder-labels.md` (archived reference)

### Recent Changes

**2025-12-01:** Completed Phase 7: Episode-Specific Speakers (PR #9)
- Added dynamic speaker dropdowns from `friends_speakers.tsv` (1,565 speaker-episode records)
- Backend: `EpisodeSpeaker` model, migration, import script, `GET /episodes/{id}/speakers` endpoint
- Frontend: Dynamic `LabelDropdown` component fetches episode-specific speakers
- Fixed apostrophe normalization bug (`str.title()` → `word.capitalize()`)
- Fixed empty speaker array handling (was falling back to default characters incorrectly)
- All tests passing: 87 backend + 18 frontend = 105 total
- See: `docs/internal/implementation-plan-episode-speakers.md`, `docs/internal/LESSONS-LEARNED-PHASE7.md`

**2025-10-28:** Closed feature/folder-based-labels PR, created new implementation plan
- Analyzed Codex/Gemini review feedback
- Decided on cluster-based approach with outlier selection
- Verified local-first architecture maintained (no external services)

**2025-10-27:** Fixed Copilot code review issues
- Changed `_normalize_label()` to return "unlabeled" string instead of None
- Fixed inconsistent API response structure in images router
- Added state reset for unlabeled images to prevent annotation errors

## Development Commands

### Docker Compose (Recommended)
```bash
# Start all services (database, backend, frontend)
docker-compose up --build

# Stop services
docker-compose down

# Apply migrations (after updates)
docker-compose exec backend alembic upgrade head

# Optional: Backfill existing data (if upgrading)
docker-compose exec backend python scripts/backfill_images.py
```

### Backend Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run backend server (requires PostgreSQL running)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Testing
python -m pytest tests/ -v

# Code quality
black app/
flake8 app/
mypy app/
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Testing and linting
npm test
npm run lint
npm run type-check
```

## Architecture

### Backend Structure
- **`app/main.py`**: FastAPI application entry point with CORS middleware and router registration
- **`app/database.py`**: Database engine, session management, and dependency injection
- **`app/models/models.py`**: SQLAlchemy ORM models (Episode, Cluster, SplitAnnotation, Annotator, Image)
- **`app/models/schemas.py`**: Pydantic schemas for request/response validation
- **`app/routers/`**: API endpoints organized by resource (episodes, clusters, annotations)
- **`app/services/`**: Business logic layer handling episode upload, cluster processing, and annotation logic
- **`alembic/`**: Database migration files

### Frontend Structure
- **`src/App.tsx`**: Main application component with React Router setup
- **`src/pages/`**: Page-level components:
  - `HomePage.tsx`: Episode list and upload interface
  - `EpisodePage.tsx`: Episode details with cluster list
  - `AnnotationPage.tsx`: Cluster annotation interface (review → batch/outlier workflow)
- **`src/services/api.ts`**: Axios-based API client for backend communication
- **`src/types/index.ts`**: TypeScript type definitions matching backend schemas
- **`src/components/`**: Reusable React components (LabelDropdown, LazyImage, etc.)

### Data Flow
1. **Upload**: ZIP file → Backend extracts clusters → Store metadata in PostgreSQL → Store images in uploads volume
2. **Annotation**:
   - Frontend displays paginated cluster images
   - User selects outliers (if any)
   - Path A: Batch label all → done
   - Path B: Annotate outliers individually → batch label remaining
3. **Export**: Backend queries annotations → Generates JSON mapping images to person names

### Database Schema
- **episodes**: Video episodes with upload status, progress tracking, season/episode metadata
- **clusters**: Face clusters with image paths, annotation status, initial labels, outlier tracking
- **images**: Individual images with file paths, labels (initial/current), annotation status
- **split_annotations**: Multi-person cluster annotations with scene/track patterns (legacy)
- **annotators**: Session management for crowdsourcing workflows

### Key Concepts
- **Scene/Track Pattern**: Images follow naming `scene_{X}_track_{Y}_frame_{Z}.jpg` to enable splitting clusters by scene and track
- **Initial Label**: Parsed from folder name (e.g., `S01E05_cluster-23` → "cluster-23", `S01E05_Rachel` → "Rachel")
- **Outlier Status**: Images can be marked as outliers (don't belong in cluster), annotated separately
- **Batch Annotation**: Assign one label to all non-outlier images in a cluster (fast path)
- **Annotation Status**: Images progress "pending" → "outlier" → "annotated"

### Local-First Architecture ✅
- **No external services required**: Everything runs in Docker Compose
- **PostgreSQL**: Containerized, data in `postgres_data` volume
- **File storage**: Local `uploads_data` volume
- **No cloud dependencies**: S3, Redis, Elasticsearch, etc. NOT needed
- **Save-as-you-go**: Database commits after each action
- **Browser persistence**: localStorage for UI state (outlier selections)

## Environment Variables

**Backend** (`backend/.env` or docker-compose):
```
DATABASE_URL=postgresql://user:password@db:5432/clustermark
DEBUG=true
```

**Frontend**: Vite automatically proxies `/api` requests to backend at http://localhost:8000

## API Structure

Base URL: http://localhost:8000

- **Episodes**: `/episodes/*` - Upload, list, and export episodes
- **Clusters**: `/clusters/{id}/*` - Get cluster details, paginated images, annotate
- **Annotations**: `/annotations/*` - Submit annotations, crowdsourcing tasks

**Phase 3-6 Endpoints (Implemented):**
- `GET /clusters/{id}/images/paginated?page=1&page_size=20` - Paginated image review (includes outliers)
- `POST /clusters/{id}/outliers` - Mark outlier images (syncs: marks selected, resets deselected)
- `GET /clusters/{id}/outliers` - Get currently marked outliers (enables resume workflow)
- `POST /clusters/{id}/annotate-batch` - Batch label non-outlier images
- `POST /clusters/annotate-outliers` - Annotate individual outlier images

Interactive API docs available at: http://localhost:8000/docs

## Development Notes

- Frontend uses Vite for fast HMR and build tooling
- Backend uses dependency injection pattern with `Depends(get_db)` for database sessions
- All IDs use UUIDs (not integers)
- File uploads are handled via multipart/form-data and stored in `backend/uploads/`
- CORS is configured to allow localhost:3000 in development
- Database migrations should be auto-generated but reviewed before applying
- Image paths are stored as PostgreSQL ARRAY(Text) columns (clusters) and Text (images)
- Image model migration exists: `alembic/versions/001_add_image_annotations.py`

## Best Practices & Development Workflow

**ALWAYS follow:** `docs/internal/BEST-PRACTICES.md`

**Key Guidelines:**
- **Incremental PRs**: Use phase-based branches (`feature/phase1-database`, `feature/phase2-episode-parsing`)
- **PR Size**: Target <500 lines per PR
- **Testing**: >80% backend coverage, >70% frontend coverage
- **Migrations**: Always test upgrade + downgrade, write idempotent backfill scripts
- **Performance**: <2s batch annotation, <500ms API response
- **Documentation**: Update README with each user-facing change
- **One-command setup**: `docker-compose up --build` must always work
- **No external services**: Keep local-first architecture (no S3, Redis, cloud APIs)

## Common Tasks

### Adding a New Feature
1. Check `docs/internal/implementation-plan-friends-annotation.md` for planned work
2. Backend: Update models → schemas → services → routers → tests
3. Frontend: Update types → API client → components → pages
4. Create migration: `alembic revision --autogenerate -m "description"`
5. Test locally with `docker-compose up --build`

### Applying Database Changes
```bash
# Check current migration state
docker-compose exec backend alembic current

# Apply pending migrations
docker-compose exec backend alembic upgrade head

# Rollback if needed
docker-compose exec backend alembic downgrade -1
```

### Debugging Issues
1. Check container logs: `docker-compose logs backend` or `docker-compose logs frontend`
2. Access backend shell: `docker-compose exec backend bash`
3. Access database: `docker-compose exec db psql -U user -d clustermark`
4. Check API docs: http://localhost:8000/docs
5. Check browser console for frontend errors

## Implementation Status

### Completed ✅
- **Phase 1**: Database Foundation (PR #2) - Episode/Cluster/Image models, migrations, backfill script
- **Phase 2**: Episode Folder Parsing (PR #3) - SxxEyy format, security, bulk operations, TDD tests
- **Phase 3**: Cluster Service & Endpoints (PR #4) - Pagination, outlier workflow, batch annotation, 26 tests
- **Phase 4**: Frontend Foundation (PR #5) - TypeScript types, API client, LabelDropdown component, 11 tests
- **Phase 5**: AnnotationPage Integration (PR #6) - Paginated two-path workflow, 6 review rounds, 20+ issues fixed
- **Phase 6**: Polish & Edge Cases (PR #7) - GET /outliers endpoint, resume workflow, 7 code review rounds, test failures fixed
- **Phase 7**: Episode-Specific Speakers (PR #9) - Dynamic speaker dropdowns from Friends metadata, 1,565 speaker records
- Basic cluster-based annotation workflow
- Episode upload and management
- Split annotation for multi-person clusters
- Export functionality
- Docker Compose setup
- Micromamba environment for reproducible dev setup

### In Progress 🚧
- None (Friends annotation system complete!)

### Planned 📋
- ✅ ~~Phase 1: Database & Backend Foundation~~ (Merged PR #2)
- ✅ ~~Phase 2: Episode Service Updates (SxxEyy parsing)~~ (Merged PR #3)
- ✅ ~~Phase 3: Cluster Service & Endpoints (pagination, outliers)~~ (Merged PR #4)
- ✅ ~~Phase 4: Frontend Foundation (types, API client, LabelDropdown)~~ (Merged PR #5)
- ✅ ~~Phase 5: AnnotationPage Refactor (two-path workflow)~~ (Merged PR #6)
- ✅ ~~Phase 6: Polish & Edge Cases (outlier resume workflow)~~ (Merged PR #7)
- ✅ ~~Phase 7: Episode-Specific Speakers (dynamic dropdowns)~~ (Merged PR #9)

## 🎓 Critical Lessons Learned

### Phase 1 (PR #2): Database Foundation
**⭐ MUST READ:** `docs/internal/LESSONS-LEARNED-PR2.md`

Critical lessons from extensive multi-round AI code review. Key takeaways:

### For AI Code Reviews:
- ✅ **Test AI claims** before accepting (Codex P1 was proven wrong)
- ✅ **Watch for contradictions** (same reviewer suggested undoing their own fix)
- ✅ **Reject invalid suggestions** with evidence (testing is proof)
- ❌ **Never blindly accept** AI suggestions without understanding why

### For Performance:
- ✅ **Watch for N+1 queries** (queries in loops = performance killer)
- ✅ **Batch operations** (reduced 101 queries → 2 queries = 50x improvement)
- ✅ **Understand memory tradeoffs** (UUIDs are 16 bytes, not "heavy")
- ❌ **Don't optimize theoretically** without measuring actual cost

### For Database Design:
- ✅ **Name all constraints** explicitly (prevents migration hell)
- ✅ **Single cascade paths** (clearer semantics, avoids trigger issues)
- ✅ **Test migrations both ways** (upgrade + downgrade)
- ❌ **Never rely on auto-generated names** (varies by environment)

### For Scripts:
- ✅ **Make scripts idempotent** (safe to run multiple times)
- ✅ **Test idempotency** (run 2-3 times to verify)
- ✅ **Commit in batches** for resumability
- ❌ **Never assume** scripts run exactly once

**Full details, examples, and red flags:** See `docs/internal/LESSONS-LEARNED-PR2.md`

---

### Phase 2 (PR #3): Episode Folder Parsing
**⭐ MUST READ:** `docs/internal/LESSONS-LEARNED-PHASE2.md`

Critical security, data integrity, and code quality lessons. Key takeaways:

### For Security:
- ✅ **Think like an attacker** (multi-pass bypasses: `....` → `..`)
- ✅ **Order matters in sanitization** (remove separators FIRST)
- ✅ **Use loops for recursive patterns** (`while '..' in ...`)
- ✅ **Test explicit attack vectors** (`../../etc/passwd`, `..//..\\...`)

### For Data Integrity:
- ✅ **One transaction = one unit of work** (atomic operations)
- ✅ **Use flush() for IDs, commit() for completion** (maintain atomicity)
- ✅ **Fail atomically** (all or nothing, no orphaned records)
- ❌ **Never commit() in the middle** of multi-step operations

### For Code Quality:
- ✅ **Pre-compile regex used in loops** (module-level constants)
- ✅ **Filter system files** (`__MACOSX`, `.DS_Store`)
- ✅ **Never assume filesystem order** (`iterdir()` is non-deterministic)
- ✅ **One directory scan > multiple scans** (Pythonic iterdir + suffix check)
- ✅ **Specific exceptions > broad catches** (let real errors surface)

### For Process:
- ✅ **Address ALL feedback** (100% response rate, not just CRITICAL)
- ✅ **Test after every fix** (caught 0 regressions across 3 review rounds)
- ✅ **Incremental commits** (one theme per commit)
- ✅ **Concise commit messages** (respect reviewer time)

**Full details, 11 issues addressed, metrics:** See `docs/internal/LESSONS-LEARNED-PHASE2.md`

---

### Phase 3 (PR #4): Cluster Service & Endpoints
**⭐ MUST READ:** `docs/internal/LESSONS-LEARNED-PHASE3.md`

Critical security vulnerabilities and performance issues found. Key takeaways:

### For Security (MOST IMPORTANT):
- ✅ **NEVER trust client-provided IDs** - always validate ownership and state
- ✅ **Defense in depth**: Pre-validate inputs AND add explicit filters in queries
- ✅ **Think like an attacker**: What if I send wrong IDs? Mixed clusters? Wrong statuses?
- ❌ **Found CRITICAL vulnerability**: Cross-cluster attack allowing User A to corrupt User B's data

### For Performance:
- ✅ **Avoid N+1 queries in loops** (group by value, use bulk operations: 3.3x faster)
- ✅ **Lock BEFORE checking state** (prevent race conditions with `with_for_update()`)
- ✅ **Use positive filters** (`status == "pending"` clearer than `status != "outlier"`)

### For Code Quality:
- ✅ **Framework-level validation**: Use FastAPI `Query` for auto-validation + OpenAPI docs
- ✅ **PEP 8 compliance**: Imports at top, not inline
- ✅ **Test edge cases**: Empty lists, invalid IDs, cross-cluster attacks, race conditions

### Review Results:
- **Issues found**: 7 total (2 CRITICAL security, 2 HIGH performance, 3 MEDIUM code quality)
- **Security vulnerabilities blocked**: 2 (cross-cluster attack, accidental state updates)
- **Performance improvement**: 3.3x on outlier annotation (N queries → M queries where M = unique labels)
- **Regressions**: 0 (all 39 tests passing)

**Full details, attack vectors, metrics:** See `docs/internal/LESSONS-LEARNED-PHASE3.md`

---

### Phase 4 (PR #5): Frontend Foundation
**⭐ MUST READ:** `docs/internal/LESSONS-LEARNED-PHASE4.md`

React component lifecycle and type safety lessons. Key takeaways:

### For React Components:
- ✅ **Handle full lifecycle**: init, update, AND reset (not just initialization)
- ✅ **Think about edge cases**: Empty string, null, undefined are different values
- ✅ **Controlled components**: Must notify parent of ALL changes (including clear)
- ❌ **Found bug**: useEffect ignored empty value, state never reset

### For Type Safety:
- ✅ **String literal unions** for enums (not plain `string`)
- ✅ **Export types** for reuse across files
- ✅ **Compile-time > runtime** checking

### For Code Quality:
- ✅ **Extract helpers** for business logic (DRY principle)
- ✅ **Comment strategic decisions** (why, not what)
- ✅ **Write tests to document** behavior (even without infrastructure)

### Review Results:
- **Issues found**: 4 total (2 P1/HIGH, 2 MEDIUM)
- **Workflow bugs fixed**: 2 (state reset, placeholder selection)
- **Code quality**: DRY principle applied, type safety improved
- **Regressions**: 0 (build passing)

**Full details, edge cases, examples:** See `docs/internal/LESSONS-LEARNED-PHASE4.md`

---

### Phase 5 (PR #6): AnnotationPage Integration
**⭐ MUST READ:** `docs/internal/LESSONS-LEARNED-PHASE5.md`

Most intensive review process with 6 rounds catching critical bugs. Key takeaways:

### For API Integration:
- ✅ **Verify API contracts FIRST**: Check backend filters/limits before implementing
- ✅ **Don't assume endpoints exist**: Backend may not support what you need
- ❌ **Found CRITICAL bug**: Attempted to fetch outliers but API filters them out (dead code)
- ❌ **Found DATA LOSS bug**: Users can skip pre-existing outliers, leaving them unlabeled forever

### For State Management:
- ✅ **Single source of truth**: Don't duplicate state (Set + Map → just Map)
- ✅ **Apply patterns consistently**: Fixed race condition in one useEffect, missed the other
- ✅ **Defensive programming**: Guards should mirror UI constraints

### For Race Conditions:
- ✅ **All async effects need cleanup**: Use isCancelled flag pattern
- ✅ **Disable ALL interactions during submission**: Not just buttons, also image grids
- ❌ **Found 3 race conditions**: Pagination, metadata loading, outlier selection

### For Code Quality:
- ✅ **DRY applies everywhere**: Constants, logic, AND error handling
- ✅ **Type safety > convenience**: Use axios.isAxiosError() not (err as any)
- ✅ **Accessibility from start**: Use semantic HTML (button > div for actions)

### Review Results:
- **Review rounds**: 6 (most intensive PR so far)
- **Issues found**: 20+ (3 CRITICAL, multiple P1/HIGH, many MEDIUM)
- **Repeat mistakes caught**: 4 (dead code, race conditions, DRY violations, type safety)
- **Lines changed**: +490/-141 (net +349)
- **Reviewers**: Gemini, Codex, Copilot (all 3 provided valuable feedback)

**Full details, all 6 rounds, metrics:** See `docs/internal/LESSONS-LEARNED-PHASE5.md`

---

### Phase 6 (PR #7): Polish & Edge Cases - Outlier Resume Workflow
**⭐ MUST READ:** `docs/internal/LESSONS-LEARNED-PHASE6.md`

The "why we keep having P1 problem?" phase. Key takeaways:

### For Testing (MOST IMPORTANT):
- ✅ **ALWAYS run tests BEFORE committing** - Non-negotiable best practice
- ✅ **Use Docker to run tests** - No excuses, we have the infrastructure
- ✅ **Catch regressions early** - Tests exist to prevent P1 issues
- ❌ **Found META-ISSUE**: 7 rounds of changes without running tests = recurring P1 problems

### For Code Review Process:
- ✅ **Verify AI suggestions** - Gemini was WRONG about /uploads/ prefix duplication
- ✅ **Trace through logic completely** - AI missed null guard in line 332
- ✅ **Test claims with evidence** - Code analysis proved race condition didn't exist
- ❌ **Don't blindly trust AI** - Even when marked "high" priority

### For Backend Testing:
- ✅ **Fixture dependencies matter** - HTTP client tests need proper test_db initialization
- ✅ **SQLite :memory: isolation** - Each connection gets separate database
- ✅ **Add missing dependencies** - httpx required by FastAPI TestClient but not in requirements.txt

### For Workflow Design:
- ✅ **Resume workflows need state sync** - Fetch backend outliers on mount
- ✅ **Clear deselected items** - POST empty array to reset backend state
- ✅ **Always sync on continue** - Prevents data loss when user deselects all

### Review Results:
- **Review rounds**: 7 (addressed 15+ issues across Rounds 1-7)
- **Critical lesson**: "why we keep having P1 problem?" → NOT RUNNING TESTS
- **Test failures caught**: 3 (missing httpx, 2 fixture issues)
- **Invalid AI suggestions rejected**: 2 (Gemini race condition, /uploads/ prefix)
- **Backend tests**: All 45 passing
- **New endpoint**: GET /clusters/{id}/outliers for resume workflow

**Full details, test debugging, AI review evaluation:** See `docs/internal/LESSONS-LEARNED-PHASE6.md`

---

### Phase 7 (PR #9): Episode-Specific Speakers
**⭐ MUST READ:** `docs/internal/LESSONS-LEARNED-PHASE7.md`

Dynamic speaker dropdowns from Friends metadata. Key takeaways:

### For Component Props (MOST IMPORTANT):
- ✅ **Pass exact values, not conditional undefined** - Empty array !== undefined in React
- ✅ **Understand fallback behavior** - Components may have defaults you don't want
- ❌ **Found BUG**: `speakers={speakers.length > 0 ? speakers : undefined}` caused empty episodes to show default characters

### For String Normalization:
- ✅ **`str.title()` has apostrophe bug** - "three's" → "Three'S" (WRONG)
- ✅ **Use `word.capitalize()` instead** - "three's" → "Three's" (CORRECT)
- ✅ **Apply pattern consistently** - Fixed in both `normalize_label()` and `normalize_speaker_name()`

### For Code Reviews:
- ✅ **AI caught real bugs** - Gemini found 4 valid issues (2 HIGH, 2 MEDIUM)
- ✅ **Test expectations matter** - Test was expecting OLD buggy behavior
- ✅ **Update tests when fixing bugs** - Don't just make tests pass, make them test the RIGHT thing

### For Data Import:
- ✅ **TSV parsing with normalization** - 1,565 speaker records imported successfully
- ✅ **UPSERT for idempotency** - Safe to run import script multiple times
- ✅ **Database indexes matter** - Composite index on (season, episode_number) for fast lookups

### Review Results:
- **Issues found**: 4 (2 HIGH priority prop logic, 2 MEDIUM apostrophe bugs)
- **Lines changed**: +3,638/-3,066 (net +572)
- **Tests**: 87 backend + 18 frontend = 105 total (all passing)
- **Files changed**: 27 files across backend/frontend/docs

**Full details, implementation plan, PR description:** See `docs/internal/LESSONS-LEARNED-PHASE7.md`

---

## Important Reminders

- **DO NOT commit CLAUDE.md or docs/internal/*** (in .gitignore)
- **Always test with Docker Compose** (ensures local-first works)
- **Review migrations before applying** (especially with existing data)
- **Keep backward compatibility** (don't break existing annotations)
- **Optimize for common case** (batch labeling) while handling edge cases (outliers)
- **No external services** (keep local-first architecture)
- **READ LESSONS LEARNED** before major PRs (avoid repeating mistakes)
