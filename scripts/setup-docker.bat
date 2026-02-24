@echo off
echo ========================================
echo SkinCare AI - Docker Setup
echo ========================================
echo.

echo Step 1: Starting Docker containers...
docker-compose up -d

echo.
echo Step 2: Waiting for services to be ready...
timeout /t 10 /nobreak > nul

echo.
echo Step 3: Running database migrations...
docker-compose exec api alembic upgrade head

echo.
echo Step 4: Checking service health...
curl http://localhost:8000/health

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Services running:
echo - Backend API: http://localhost:8000
echo - Database: localhost:5432
echo - Redis: localhost:6379
echo.
echo Next steps:
echo 1. cd frontend
echo 2. npm install (if not done)
echo 3. npm run dev
echo.
echo Or run: .\scripts\start-new-frontend.bat
echo.
pause
