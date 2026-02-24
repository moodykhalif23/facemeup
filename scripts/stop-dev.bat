@echo off
echo ========================================
echo  SkinCare AI - Stopping Services
echo ========================================
echo.

echo Stopping Backend Services...
cd backend
docker-compose down
cd ..

echo.
echo All services stopped successfully!
echo.
pause
