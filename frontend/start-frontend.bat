@echo off
echo Starting Museum Anomaly Dashboard Frontend...
echo Frontend will run on http://localhost:5173 (or another port if busy)
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
npm run dev
pause
