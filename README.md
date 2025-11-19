# SNMP Monitoring System

A comprehensive network monitoring solution built with FastAPI and Next.js that provides real-time SNMP device monitoring, alerting, and reporting capabilities.

## Features

### Core Monitoring
- **Automatic Device Discovery**: Scans network ranges to detect SNMP-enabled devices
- **Real-time Polling**: Continuous monitoring of device health and metrics
- **Multi-Metric Support**: Monitors CPU, memory, uptime, bandwidth, and custom OIDs
- **Alert Management**: Configurable thresholds with email notifications
- **Device Status Tracking**: Real-time reachability and performance monitoring

### User Interface
- **Interactive Dashboard**: Visual overview of network health with KPI cards
- **Device Details**: Comprehensive per-device metrics and historical data
- **Alert Console**: View, acknowledge, and manage network alerts
- **rting**: Generate network performance rts
- **Settings Management**: Configure alert recipients and thresholds

### Technical Highlights
- **Async Architecture**: Built on FastAPI for high-performance concurrent operations
- **Type Safety**: Full TypeScript frontend with React 18
- **Modern UI**: Responsive design with Tailwind CSS and shadcn/ui components
- **Real-time Updates**: TanStack Query for efficient data fetching
- **Background Services**: Automated discovery and polling processes

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Database**: SQLite with SQLAlchemy ORM
- **Cache**: Redis (optional, for performance optimization)
- **SNMP Library**: pysnmp
- **Server**: Uvicorn (ASGI)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **UI Library**: React 18
- **Styling**: Tailwind CSS + shadcn/ui
- **Data Fetching**: TanStack Query (React Query)
- **Charts**: Recharts

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn
- Redis (optional but recommended for performance caching)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/wharizmarzuki/SNMP-Monitoring.git
cd snmp-monitoring
```

2. **Redis Setup (Optional but Recommended)**

For optimal performance with caching enabled, install and start Redis:

```bash
# Automated setup (detects your OS and installs/starts Redis)
./setup-redis.sh
```

Or install manually:
- **Ubuntu/Debian**: `sudo apt-get install redis-server && sudo systemctl start redis`
- **macOS**: `brew install redis && brew services start redis`
- **Docker**: `docker run -d -p 6379:6379 redis:7-alpine`

Verify installation: `redis-cli ping` (should return `PONG`)

> **Note**: The application will work without Redis but with reduced performance. See [DEPLOYMENT.md](DEPLOYMENT.md) for more details.

3. **Backend Setup**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (SNMP community, email credentials, etc.)
```

4. **Frontend Setup**
```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps

# Configure environment
cp .env.example .env.local
# Edit .env.local if needed (default: http://localhost:8000)
```

### Running the Application

#### Option 1: Simple Script (Recommended for Development)

```bash
# From project root
./start-dev.sh
```

This will start both backend and frontend services. Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

Stop services:
```bash
./stop-dev.sh
```

#### Option 2: Manual (Separate Terminals)

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

## Configuration

### Backend Environment Variables

Edit `backend/.env`:

```bash
# SNMP Settings
SNMP_COMMUNITY=public          # SNMP community string
SNMP_TIMEOUT=10                # Connection timeout
SNMP_RETRIES=3                 # Retry attempts

# Database
DATABASE_URL=sqlite:///./monitoring.db

# Monitoring
POLLING_INTERVAL=60            # Seconds between polls
DISCOVERY_CONCURRENCY=20       # Concurrent discovery threads
POLLING_CONCURRENCY=20         # Concurrent polling threads

# Email Alerts
SENDER_EMAIL=your@email.com
SENDER_PASSWORD=your-app-password

# Redis Cache (Optional)
CACHE_ENABLED=true               # Enable/disable caching
REDIS_HOST=localhost             # Redis server hostname
REDIS_PORT=6379                  # Redis server port
REDIS_DB=0                       # Redis database number (0-15)

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG=false
```

### Frontend Environment Variables

Edit `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

```
snmp-monitoring/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes and middleware
│   │   ├── config/            # Configuration and settings
│   │   └── core/              # Database models and schemas
│   ├── services/              # Business logic services
│   │   ├── snmp_service.py
│   │   ├── device_service.py
│   │   ├── discovery_service.py
│   │   ├── polling_service.py
│   │   ├── alert_service.py
│   │   └── email_service.py
│   ├── main.py                # Application entry point
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/        # React components
│   │   ├── lib/               # Utilities and API client
│   │   └── types/             # TypeScript type definitions
│   ├── public/
│   ├── package.json
│   └── .env.example
│
├── logs/                       # Application logs
├── start-dev.sh               # Development startup script
├── stop-dev.sh                # Stop services script
├── ecosystem.config.js        # PM2 deployment config
├── DEPLOYMENT.md              # Deployment guide
└── README.md
```

## Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on:
- PM2 process management
- Nginx reverse proxy setup
- SSL/HTTPS configuration
- Performance tuning
- Monitoring and maintenance

Quick production start with PM2:
```bash
# Install PM2
npm install -g pm2

# Build frontend
cd frontend && npm run build && cd ..

# Start services
pm2 start ecosystem.config.js

# Monitor
pm2 monit
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Features in Detail

### Device Discovery
- Automated network scanning on configurable CIDR ranges
- SNMP v2c protocol support
- Concurrent scanning for faster discovery
- Automatic database updates

### Monitoring & Alerts
- Configurable polling intervals
- Custom OID support
- Threshold-based alerting
- Email notifications
- Alert acknowledgment and maintenance mode

### Reporting
- Historical data tracking
- Performance metrics visualization
- Export capabilities

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn main:app --reload

# Run tests (if available)
pytest
```

### Frontend Development
```bash
cd frontend

# Development server
npm run dev

# Type checking
npm run build

# Linting
npm run lint
```

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process on port 8000
lsof -i :8000
kill -9 $(lsof -t -i:8000)

# Find and kill process on port 3000
lsof -i :3000
kill -9 $(lsof -t -i:3000)
```

### Database Issues
```bash
# Reset database (WARNING: deletes all data)
rm backend/monitoring.db
# Will be recreated on next backend startup
```

### SNMP Connection Issues
- Verify SNMP community string matches device configuration
- Ensure devices have SNMP enabled
- Check firewall rules allow UDP port 161
- Verify network connectivity to target devices

### Redis Cache Issues
```bash
# Check if Redis is running
redis-cli ping

# Start Redis (if installed but not running)
sudo systemctl start redis

# Check Redis logs
sudo journalctl -u redis -f

# Disable caching if Redis unavailable
# In backend/.env, set: CACHE_ENABLED=false
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Specify your license here]

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Acknowledgments

Built with modern web technologies:
- FastAPI for the backend API
- Next.js for the frontend framework
- shadcn/ui for beautiful UI components
- pysnmp for SNMP protocol implementation
