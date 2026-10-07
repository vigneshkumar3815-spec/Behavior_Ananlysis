@echo off
echo ===================================================
echo Starting SentinelVision AI Engine (FastAPI) ...
echo ===================================================
cd /d "%~dp0"
start "SentinelVision Backend" cmd /c "python api.py"

echo.
echo ===================================================
echo Starting SentinelVision Dashboard (React) ...
echo ===================================================
cd /d "%~dp0\SentinelVision"
start "SentinelVision Frontend" cmd /c "npm run dev"

echo.
echo SentinelVision is starting up!
echo The React Dashboard will be available at: http://localhost:5174/
echo.
pause
