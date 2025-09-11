# Museum Anomaly Dashboard

A real-time monitoring system for museum exhibits with AI-powered anomaly detection, intelligent chat assistance, and vision-based monitoring.

## Features

- 🤖 **LLaMA AI Chat**: Intelligent assistant powered by OpenRouter
- 📊 **Smart Anomaly Detection**: AI analysis of sensor readings
- 👁️ **Vision Detection**: YOLOv8n object detection for security monitoring
- 📱 **Real-time Dashboard**: Live monitoring interface
- 🔧 **IoT Integration**: ESP32-CAM, DHT11, SW-420 sensors

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `POST /chat` - AI chat with LLaMA 3 8B
- `POST /anomaly/check` - Anomaly detection with AI analysis
- `POST /vision/check` - YOLOv8n object detection
- `GET /health` - Health check

## Configuration

Set up your `.env` files with the required API keys:
- OpenRouter API key (for LLaMA)
- OpenAI API key (optional fallback)

## Tech Stack

**Frontend**: React, Vite, Tailwind CSS  
**Backend**: FastAPI, Python, OpenRouter, YOLOv8n

# Museum Anomaly Dashboard with AI Agent (MVP)

A full-stack MVP for monitoring museum artifact conditions with real-time dashboard, ESP32-CAM stream, sensor data, anomaly detection, and AI assistant.

## Features
- Live feed from ESP32-CAM (or placeholder stream)
- Sensor data cards (Temperature, Humidity, Vibration) with green/red status
- Anomaly alerts using rule-based thresholds + AI explanation via OpenAI
- AI Agent chat for staff queries
- Mock sensor data so it runs without hardware

## Tech Stack
- Frontend: React + Vite + TailwindCSS
- Backend: FastAPI (Python), Uvicorn, httpx, OpenAI API

## Prerequisites
- Node.js 18+
- Python 3.10+

## Setup

1) Clone or open this folder, then create a .env file

Copy .env.example to .env and set values as needed.

Required variables:
- OPENAI_API_KEY (optional for offline demo)
- ESP32_CAM_URL (optional, e.g. http://<esp-ip>:81/stream)
- MOCK_SENSORS=true
- FRONTEND_ORIGIN=http://localhost:5173

2) Backend install & run

Windows PowerShell:

```
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
$env:UVICORN_NO_ACCESS_LOG="1"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload --no-access-log
```

Endpoints:
- GET /health
- GET /sensors/data
- GET /camera/stream (proxies MJPEG or serves placeholder frames)
- POST /anomaly/check
- POST /chat

3) Frontend install & run

```
cd frontend
npm install
npm run dev
```

By default, the frontend expects the backend at http://localhost:8000. To change, set VITE_API_BASE in a frontend .env file.

Example: frontend/.env
```
VITE_API_BASE=http://127.0.0.1:8000
```

## Data Flow
- ESP32 + sensors -> Backend (/sensors/data)
- Backend evaluates rules and optionally calls OpenAI for explanations
- Frontend polls API every few seconds and updates the dashboard

## Notes on ESP32-CAM
- Set ESP32_CAM_URL in .env, e.g. http://192.168.1.25:81/stream for MJPEG
- If not set, backend streams a repeating placeholder JPEG to keep the UI functional

## Security
- Do not commit real API keys. Use .env locally.
- This MVP logs minimal info and is for demo only. Harden before production.

## Next Steps / Enhancements
- Persist sensor history and chart trends
- WebSocket push for real-time updates
- Role-based auth for staff
- Multi-camera support and snapshot capture
- Calibration UI for thresholds per gallery/artifact

