# ClusterMark - Production Deployment Guide

This guide covers deploying ClusterMark to production environments.

## Prerequisites

- Linux server (Ubuntu 20.04+ or similar)
- Docker & Docker Compose installed
- Domain name (optional, for HTTPS)
- SSL certificate (optional, for HTTPS)

**Note:** PostgreSQL is included in Docker Compose - no separate installation needed.

## Deployment Options

### Option 1: Docker Compose (Recommended)

**1. Clone repository on server:**
```bash
git clone https://github.com/yibeichan/clustermark.git
cd clustermark
```

**2. Change default database password (IMPORTANT for production):**

Edit `docker-compose.yml` and change the password:
```yaml
db:
  environment:
    POSTGRES_PASSWORD: your_secure_password_here  # Change from default "password"
```

**3. Deploy:**
```bash
docker-compose up -d --build
```

**4. Check status:**
```bash
docker-compose ps
docker-compose logs -f
```

The app will be available at:
- Frontend: http://your-server:3000
- Backend API: http://your-server:8000

**That's it!** PostgreSQL, backend, and frontend all start automatically. Database migrations run automatically on backend startup.

---

### Option 2: Manual Production Setup

**Prerequisites for this option:**
- PostgreSQL 15+ installed and running
- Database created: `createdb clustermark`

**1. Backend Setup:**
```bash
cd backend

# Create production virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
# Replace with your PostgreSQL username and password
export DATABASE_URL="postgresql://your_pg_user:your_pg_password@localhost:5432/clustermark"
export DEBUG="false"

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

### Using Docker Compose (Recommended)

All configuration is in `docker-compose.yml`. For production, only change:
```yaml
db:
  environment:
    POSTGRES_PASSWORD: your_secure_password_here  # Change this!
```

The backend automatically uses the database password from the `db` service.

### Using .env file (Optional)

You can override settings with a `.env` file:
```bash
POSTGRES_PASSWORD=your_secure_password_here
```

**Authentication:** This application has no authentication system. All endpoints are open. For production with sensitive data, restrict access via firewall/VPN or add authentication middleware.

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
