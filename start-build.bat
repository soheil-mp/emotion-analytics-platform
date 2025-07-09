@echo off
REM Development Build and Deploy Script
REM Builds Docker images and starts all services with monitoring

echo ==========================================
echo  EMOTION CLASSIFICATION - BUILD AND DEPLOY
echo ==========================================
echo.
echo Building Docker images and starting services...
echo This will take a few minutes on first run.
echo.

REM Stop any existing containers
echo Stopping existing containers...
docker-compose -f docker-compose.build.yml down

REM Build and start all services
echo Building and starting all services...
docker-compose -f docker-compose.build.yml up -d --build

REM Wait for services to be ready
echo.
echo Waiting for services to start...
timeout /t 30 /nobreak > nul

REM Check container status
echo.
echo ==========================================
echo  CONTAINER STATUS
echo ==========================================
docker-compose -f docker-compose.build.yml ps

echo.
echo ==========================================
echo  SERVICE ACCESS URLS
echo ==========================================
echo Frontend:   http://localhost:3121
echo Backend:    http://localhost:3120
echo Monitoring: Check /metrics endpoint and results/monitoring/ folder
echo.

REM Test backend health
echo Testing backend health...
curl -s http://localhost:3120/ > nul
if %errorlevel%==0 (
    echo ✅ Backend is responding
) else (
    echo ❌ Backend not responding - check logs
)

echo.
echo ==========================================
echo  MONITORING SETUP COMPLETE
echo ==========================================
echo All services are starting up...
echo Check /metrics endpoint and results/monitoring/ folder for monitoring data
echo Use 'docker-compose -f docker-compose.build.yml logs -f' to view logs
echo.
pause
