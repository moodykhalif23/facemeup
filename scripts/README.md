# SkinCare AI - Development Scripts

This folder contains scripts to easily start and stop the development environment.

## Scripts

### Start Development Environment

**Windows:**
```bash
scripts\start-dev.bat
```

**Mac/Linux:**
```bash
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh
```

This script will:
1. Start the backend services using Docker Compose
2. Wait for backend to be ready
3. Install frontend dependencies (if not already installed)
4. Start the Expo development server

### Stop Development Environment

**Windows:**
```bash
scripts\stop-dev.bat
```

**Mac/Linux:**
```bash
chmod +x scripts/stop-dev.sh
./scripts/stop-dev.sh
```

This script will:
1. Stop all Docker containers
2. Clean up resources

## Services

Once started, you can access:

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend (Expo)**: http://localhost:8081
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Requirements

### Backend
- Docker Desktop installed and running
- Docker Compose

### Frontend
- Node.js (v18 or higher)
- npm or yarn

## Troubleshooting

### Docker not running
If you see "Docker is not running", make sure Docker Desktop is started.

### Port already in use
If ports 8000, 8081, 5432, or 6379 are already in use:
1. Stop the conflicting service
2. Or modify the ports in `docker-compose.yml` and `frontend/src/api.js`

### Frontend dependencies fail to install
Try manually:
```bash
cd frontend
npm install
```

### Backend fails to start
Check Docker logs:
```bash
cd backend
docker-compose logs
```

## Manual Start (Alternative)

If you prefer to start services manually:

### Backend
```bash
cd backend
docker-compose up -d
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Development Workflow

1. Run `start-dev` script
2. Wait for services to start
3. Scan QR code with Expo Go app (mobile) or press 'w' for web
4. Make changes to code (hot reload enabled)
5. Press Ctrl+C to stop frontend
6. Run `stop-dev` script to stop backend

## Notes

- The frontend will automatically reload when you make changes
- Backend changes require rebuilding Docker containers
- Database data persists between restarts (stored in Docker volumes)
- To reset database: `cd backend && docker-compose down -v`
