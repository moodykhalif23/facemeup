@echo off
echo ========================================
echo  SkinCare AI - Development Startup
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/5] Starting Database Services (Docker)...
echo.
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start database services!
    pause
    exit /b 1
)

echo.
echo [2/5] Waiting for database to be ready...
timeout /t 5 /nobreak >nul

echo.
echo [3/5] Starting Backend API (Local)...
start "SkinCare Backend" cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

echo.
echo [4/5] Installing Frontend Dependencies...
echo.
cd frontend
if not exist node_modules (
    echo Installing npm packages...
    call npm install --legacy-peer-deps
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install frontend dependencies!
        cd ..
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed, skipping...
)

echo.
echo [5/5] Starting Frontend Development Server...
echo.
echo ========================================
echo  Services Starting:
echo ========================================
echo  Backend API:  http://localhost:8000
echo  Frontend:     http://localhost:8081
echo  Docs:         http://localhost:8000/docs
echo ========================================
echo.
echo Press Ctrl+C to stop all services
echo.

REM Start frontend in the same window
call npm start

REM If npm start exits, stop backend
echo.
echo Stopping services...
cd ..
docker-compose down

pause
