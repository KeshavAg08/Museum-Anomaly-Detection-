@echo off
echo Starting Museum Anomaly Dashboard Backend...
echo Backend will run on http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
