# Museum Anomaly Dashboard - Startup Guide

## 🚀 Quick Start Instructions

### 1. Start the Backend Server
1. Open a new Command Prompt or PowerShell window
2. Navigate to the backend directory:
   ```
   cd "C:\Users\Keshav.DESKTOP-HC4NPKV\museum-anomaly-dashboard\backend"
   ```
3. Run the backend server:
   ```
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```
   **OR** double-click `start-backend.bat`

### 2. Start the Frontend Server
1. Open another Command Prompt or PowerShell window
2. Navigate to the frontend directory:
   ```
   cd "C:\Users\Keshav.DESKTOP-HC4NPKV\museum-anomaly-dashboard\frontend"
   ```
3. Run the frontend server:
   ```
   npm run dev
   ```
   **OR** double-click `start-frontend.bat`

### 3. Access the Application
- **Frontend (Dashboard)**: http://localhost:5173 (or the port shown in terminal)
- **Backend API**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs

## 📋 Server Status Check

If you get "Site not reached" error:

1. **Check if servers are running**:
   ```
   netstat -an | findstr ":8000 :5173"
   ```

2. **Check for port conflicts**:
   - Frontend may use port 5174 if 5173 is busy
   - Backend should always use port 8000

3. **Restart servers if needed**:
   - Press Ctrl+C in the terminal windows to stop
   - Run the startup commands again

## 🔧 Troubleshooting

### Backend Issues
- **Missing dependencies**: Run `pip install -r requirements.txt` in backend folder
- **Port 8000 in use**: Change port in the uvicorn command (e.g., --port 8001)

### Frontend Issues  
- **Missing node_modules**: Run `npm install` in frontend folder
- **Port conflicts**: Vite will automatically try the next available port

### Connection Issues
- Make sure both frontend and backend are running
- Check that CORS is properly configured (already done)
- Verify the API_BASE URL in frontend/src/api.js points to backend

## 🌟 System Status

✅ **Frontend**: Fully functional React application
✅ **Backend**: FastAPI server with all endpoints
✅ **Button Fixes**: All View/Edit/Details buttons working
✅ **Mock Data**: Simulated sensor data and exhibits
✅ **Dependencies**: All required packages installed
