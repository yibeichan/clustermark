# ClusterMark - Production Deployment Guide

This guide covers deploying ClusterMark to production environments.

## Prerequisites

- Linux server (Ubuntu 20.04+ or similar)
- Docker & Docker Compose installed
- PostgreSQL 15+ (can use dockerized version)
- Domain name (optional, for HTTPS)
- SSL certificate (optional, for HTTPS)

## Deployment Options

### Option 1: Docker Compose (Recommended)

**1. Clone repository on server:**
```bash
git clone https://github.com/yibeichan/clustermark.git
cd clustermark
```

**2. Create production environment file:**
```bash
# .env (in project root)
POSTGRES_USER=user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=clustermark
DEBUG=false
SECRET_KEY=your-secret-key-here-change-this
```

**3. Create docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    env_file: .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file: .env
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      DEBUG: ${DEBUG}
      SECRET_KEY: ${SECRET_KEY}
    volumes:
      - uploads_data:/app/uploads
    depends_on:
      - db
    restart: always
    ports:
      - "8000:8000"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    restart: always

volumes:
  postgres_data:
  uploads_data:
```

**4. Deploy:**
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

**5. Run migrations:**
```bash
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

**6. Check status:**
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

---

### Option 2: Manual Production Setup

**1. Backend Setup:**
```bash
cd backend

# Create production virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/clustermark"
export DEBUG="false"
export SECRET_KEY="your-secret-key"

# Run migrations
alembic upgrade head

# Start with Gunicorn (production server)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**2. Frontend Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx or similar
# The build output is in frontend/dist/
```

**3. Set up Nginx reverse proxy:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/clustermark/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Uploads
    location /uploads {
        proxy_pass http://localhost:8000/uploads;
        proxy_set_header Host $host;
    }
}
```

---

## Production Checklist

### Security
- [ ] Change default database password
- [ ] Set strong SECRET_KEY
- [ ] Disable DEBUG mode (DEBUG=false)
- [ ] Set up firewall (allow only 80/443)
- [ ] Enable HTTPS with SSL certificate
- [ ] Restrict database access to localhost
- [ ] Regular security updates

### Performance
- [ ] Configure PostgreSQL for production workload
- [ ] Set up database connection pooling
- [ ] Enable nginx gzip compression
- [ ] Configure proper worker count for Gunicorn
- [ ] Set up static file caching

### Monitoring
- [ ] Set up log rotation
- [ ] Monitor disk space (uploads can grow large)
- [ ] Set up health check endpoints
- [ ] Configure alerting for errors
- [ ] Monitor database performance

### Backup
- [ ] Set up automated database backups
- [ ] Back up uploads volume regularly
- [ ] Test restore procedures
- [ ] Document backup schedule

---

## Environment Variables

### Production .env file (project root)
```bash
# Database (used by both db and backend services)
POSTGRES_USER=user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=clustermark

# Backend
DEBUG=false
SECRET_KEY=your-secret-key-here-change-this

# Optional
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=500000000  # 500MB in bytes
```

**Note:** The `.env` file is shared by docker-compose services using `env_file: .env` and variables are interpolated with `${VARIABLE_NAME}` syntax. This ensures the database password is defined once and used consistently.

### Frontend
Build-time configuration in `frontend/vite.config.ts`:
```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://your-backend-url:8000'
    }
  }
})
```

---

## Scaling Considerations

### Horizontal Scaling
- Use external PostgreSQL (managed service)
- Use S3 or similar for uploads (instead of local volume)
- Load balance multiple backend instances
- Use Redis for session management (future)

### Database Optimization
```bash
# Increase connections
max_connections = 200

# Tune memory
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB

# Enable query logging for slow queries
log_min_duration_statement = 1000
```

### Monitoring
- Use Prometheus + Grafana for metrics
- Use Sentry for error tracking
- Set up uptime monitoring (Pingdom, UptimeRobot)

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check database connection
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.database import engine; engine.connect()"
```

### Database migration errors
```bash
# Check current version
docker-compose -f docker-compose.prod.yml exec backend alembic current

# Try downgrade and upgrade
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Out of disk space
```bash
# Check uploads volume
docker-compose -f docker-compose.prod.yml exec backend df -h

# Clean old uploads (manually or with script)
docker-compose -f docker-compose.prod.yml exec backend rm -rf /app/uploads/old-episode
```

---

## Updating Production

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Run new migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Check health
curl http://localhost:8000/health
```

---

## Support

For production deployment issues:
- Check logs first: `docker-compose logs -f`
- GitHub Issues: https://github.com/yibeichan/clustermark/issues
- Review this guide's troubleshooting section

---

**Production deployment requires careful planning. Test thoroughly in staging before production!**
