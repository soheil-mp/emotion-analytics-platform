@echo off
REM Production Deployment Script
REM Deploys pre-built Docker images with optimized configuration

echo ==========================================
echo  EMOTION CLASSIFICATION - PRODUCTION DEPLOY
echo ==========================================
echo.
echo Deploying production services with pre-built images...
echo.

REM Stop any existing containers
echo Stopping existing containers...
docker-compose down

REM Start production services
echo Starting production services...
docker-compose up -d

REM Wait for services to be ready
echo.
echo Waiting for services to start...
timeout /t 30 /nobreak > nul

REM Check container status
echo.
echo ==========================================
echo  CONTAINER STATUS
echo ==========================================
docker-compose ps

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
echo  PRODUCTION DEPLOYMENT COMPLETE
echo ==========================================
echo All services are running in production mode
echo Monitor performance via /metrics endpoint and local monitoring files
echo Use 'docker-compose logs -f' to view logs
echo.
pause
