# 🚀 Quick Start Guide

## First Time Setup

### 1. Start Backend (Docker)
```bash
docker-compose up -d
docker-compose exec api alembic upgrade head
```

### 2. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Open Browser
http://localhost:3000

## Daily Development

### Start Everything
```bash
# Backend (if not running)
docker-compose up -d

# Frontend
cd frontend
npm run dev
```

### Stop Everything
```bash
# Stop frontend: Ctrl+C in terminal

# Stop backend
docker-compose down
```

## Common Commands

### Backend
```bash
# View logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head

# Access database
docker-compose exec db psql -U postgres -d skincare

# Restart backend
docker-compose restart api
```

### Frontend
```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

## URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## First User

1. Go to http://localhost:3000
2. Click "Sign up"
3. Enter:
   - Name: Test User
   - Email: test@example.com
   - Password: password123
4. Click "Sign Up"
5. Login with same credentials

## Troubleshooting

### "Relation users does not exist"
```bash
docker-compose exec api alembic upgrade head
```

### CORS Error
Backend must be running and configured for http://localhost:3000

### Port in Use
```bash
# Kill process on port 3000
npx kill-port 3000

# Or change port in frontend/vite.config.js
```

### Docker Issues
```bash
# Reset everything
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

## Mobile Development

### Android
```bash
cd frontend
npm run build
npx cap add android
npm run android
```

### iOS (Mac only)
```bash
cd frontend
npm run build
npx cap add ios
npm run ios
```

## Need Help?

1. Check [SETUP_NEW_FRONTEND.md](SETUP_NEW_FRONTEND.md)
2. Check [README.md](README.md)
3. View logs: `docker-compose logs -f`
4. Check browser console (F12)
