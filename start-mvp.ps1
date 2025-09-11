# Museum Anomaly Dashboard MVP Startup Script
Write-Host "🏛️ Starting Museum Anomaly Dashboard MVP..." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Start Backend
Write-Host "🔧 Starting FastAPI Backend..." -ForegroundColor Yellow
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .venv\Scripts\uvicorn.exe backend.main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep -Seconds 3

# Start Frontend  
Write-Host "🎨 Starting React Frontend..." -ForegroundColor Yellow
Start-Process PowerShell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

Start-Sleep -Seconds 2

Write-Host "🎉 MVP Starting! Opening in browser..." -ForegroundColor Green
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend Dashboard: http://localhost:5173" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan

# Wait a moment then open browser
Start-Sleep -Seconds 5
Start-Process "http://localhost:5173"
