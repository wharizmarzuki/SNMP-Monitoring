# SNMP Monitoring System - Deployment Guide

This guide covers running the SNMP monitoring system for both local development and production deployment.

## System Architecture

- **Backend**: FastAPI (Python) on port 8000
- **Frontend**: Next.js (React/TypeScript) on port 3000
- **Database**: SQLite (file-based, no external DB needed)

---

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm

### Quick Start

The easiest way to run both services:

```bash
# Make scripts executable (first time only)
chmod +x start-dev.sh stop-dev.sh

# Start both services
./start-dev.sh

# Stop both services
./stop-dev.sh
```

### Access Points

- Frontend UI: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### View Logs

```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs
tail -f logs/frontend.log
```

### Manual Start (Alternative)

If you prefer to run services in separate terminals:

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

---

## Production Deployment with PM2

PM2 is a production-ready process manager that handles automatic restarts, monitoring, and logging.

### 1. Install PM2

```bash
# Install PM2 globally
npm install -g pm2
```

### 2. Prepare Frontend for Production

```bash
cd frontend
npm run build
cd ..
```

### 3. Start Services with PM2

```bash
# Start both backend and frontend
pm2 start ecosystem.config.js

# Save PM2 configuration (survives reboots)
pm2 save

# Setup PM2 to start on system boot
pm2 startup
```

### 4. PM2 Management Commands

```bash
# View status of all services
pm2 status

# Monitor services in real-time
pm2 monit

# View logs
pm2 logs                    # All logs
pm2 logs snmp-backend       # Backend only
pm2 logs snmp-frontend      # Frontend only

# Restart services
pm2 restart ecosystem.config.js
pm2 restart snmp-backend    # Restart backend only
pm2 restart snmp-frontend   # Restart frontend only

# Stop services
pm2 stop ecosystem.config.js
pm2 stop snmp-backend       # Stop backend only
pm2 stop snmp-frontend      # Stop frontend only

# Delete services from PM2
pm2 delete ecosystem.config.js
```

### 5. View PM2 Dashboard (Optional)

```bash
# Install PM2 web dashboard
pm2 install pm2-server-monit

# Access at http://localhost:9615
```

---

## Environment Configuration

### Backend (.env)

Located at `backend/.env`:

```bash
# SNMP Configuration
SNMP_COMMUNITY=fyp
SNMP_TIMEOUT=10
SNMP_RETRIES=3

# Database
DATABASE_URL=sqlite:///./monitoring.db

# Application Settings
POLLING_INTERVAL=60
DISCOVERY_CONCURRENCY=20
POLLING_CONCURRENCY=20

# Email Settings
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# Logging
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Frontend (.env.local)

Located at `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production with a different domain:
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## Reverse Proxy Setup (Optional)

For production, you may want to use Nginx as a reverse proxy:

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Backend Docs
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill process on port 8000
kill -9 $(lsof -t -i:8000)

# Check what's using port 3000
lsof -i :3000

# Kill process on port 3000
kill -9 $(lsof -t -i:3000)
```

### Services Won't Start

```bash
# Check logs
cat logs/backend.log
cat logs/frontend.log

# Or with PM2
pm2 logs snmp-backend
pm2 logs snmp-frontend
```

### Database Issues

```bash
# Reset database (WARNING: deletes all data)
rm backend/monitoring.db
# Backend will recreate it on next startup
```

### PM2 Not Starting on Boot

```bash
# Re-setup startup script
pm2 unstartup
pm2 startup
pm2 save
```

---

## Security Considerations

1. **Change default credentials** in `backend/.env`
2. **Use HTTPS** in production (with Let's Encrypt)
3. **Update SNMP community strings** to secure values
4. **Configure firewall** to restrict access to ports 8000 and 3000
5. **Use environment-specific .env files** (don't commit to git)

---

## Performance Tuning

### Backend

- Adjust `POLLING_INTERVAL` in `.env` (default: 60 seconds)
- Increase `POLLING_CONCURRENCY` for faster polling (default: 20)
- Monitor memory usage: `pm2 monit`

### Frontend

- Production build is optimized automatically
- Consider enabling Next.js ISR (Incremental Static Regeneration)
- Use CDN for static assets

---

## Monitoring & Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8000/docs

# Frontend health
curl http://localhost:3000

# With PM2
pm2 status
```

### Log Rotation

PM2 handles log rotation automatically. Configure in `ecosystem.config.js` if needed.

### Database Backup

```bash
# Backup SQLite database
cp backend/monitoring.db backend/monitoring.db.backup

# Automated backup (add to crontab)
0 2 * * * cp /path/to/backend/monitoring.db /path/to/backups/monitoring.db.$(date +\%Y\%m\%d)
```

---

## Support

For issues or questions:
- Check logs: `pm2 logs` or `tail -f logs/*.log`
- Review API docs: http://localhost:8000/docs
- Check PM2 status: `pm2 status`
