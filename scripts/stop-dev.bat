@echo off
echo ========================================
echo  SkinCare AI - Stopping Services
echo ========================================
echo.

echo Stopping Backend Services...
docker-compose down

REM Kill any running uvicorn processes
taskkill /F /IM uvicorn.exe 2>nul
taskkill /F /IM node.exe 2>nul

echo.
echo All services stopped successfully!
echo.
pause
