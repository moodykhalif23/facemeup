@echo off
echo ========================================
echo  SkinCare AI - Stopping Services
echo ========================================
echo.

echo Stopping Backend Services...
docker-compose down

echo.
echo All services stopped successfully!
echo.
pause
