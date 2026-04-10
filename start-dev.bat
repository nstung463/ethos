@echo off
setlocal enabledelayedexpansion

echo Ethos Full Stack Startup
echo ========================

if not exist .env (
    echo .env not found. Creating from template...
    copy .env.example .env
    echo Edit .env with your API keys, then run again.
    pause
    exit /b 1
)

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker not found. Install Docker Desktop first.
    pause
    exit /b 1
)

echo Configuration OK
echo.

echo Starting Docker services...
docker-compose up -d

echo.
echo Waiting 15 seconds for services to be healthy...
timeout /t 15 /nobreak >nul

echo.
echo Health checks:

curl -s http://localhost:8080/v1/models >nul 2>&1
if errorlevel 1 (
    echo   FAIL Ethos API: NOT RESPONDING
) else (
    echo   OK Ethos API: http://localhost:8080
)

curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo   FAIL Open Terminal: NOT RESPONDING
) else (
    echo   OK Open Terminal: http://localhost:8000
)

curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo   FAIL Ethos Frontend: NOT RESPONDING
) else (
    echo   OK Ethos Frontend: http://localhost:3000
)

echo.
echo Full stack ready
echo.
echo Open http://localhost:3000 in your browser
echo.
echo Useful commands:
echo   docker-compose logs -f ethos-api
echo   docker-compose logs -f open-terminal
echo   docker-compose logs -f ethos-frontend
echo   docker-compose down
echo.
pause
