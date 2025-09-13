# Museum Anomaly Detection System

A real-time monitoring system for museum exhibits with AI-powered anomaly detection, intelligent chat assistance, and vision-based monitoring.

## Features

- 🤖 **AI Chat Assistant**: Intelligent assistant for museum staff queries
- 📊 **Smart Anomaly Detection**: AI analysis of sensor readings with rule-based and ML approaches
- 👁️ **Vision Detection**: YOLOv8n object detection for security monitoring
- 📱 **Real-time Dashboard**: Live monitoring interface with sensor data visualization
- 🔧 **IoT Integration**: ESP32-CAM, DHT11, SW-420 sensors support
- 📈 **Historical Data**: Trend analysis and pattern recognition

## Tech Stack

**Frontend**: React, Vite, Tailwind CSS  
**Backend**: FastAPI, Python, Uvicorn  
**AI/ML**: YOLOv8n, scikit-learn, custom anomaly detection  
**Hardware**: ESP32-CAM, DHT11, SW-420 sensors

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+

### Backend Setup

1. Clone the repository and navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy environment configuration:
```bash
cp .env.example .env
```

5. Run the backend server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /sensors/data` - Get current sensor readings
- `GET /camera/stream` - Camera stream (MJPEG)
- `POST /anomaly/check` - Anomaly detection analysis
- `POST /chat` - AI chat assistant
- `POST /vision/check` - YOLOv8n object detection

### Example API Usage

#### Check for Anomalies
```bash
curl -X POST "http://localhost:8000/anomaly/check" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_data": {
      "temperature": 26.5,
      "humidity": 75.0,
      "vibration": 0.8
    }
  }'
```

#### Chat with AI Assistant
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the ideal temperature range for artifacts?",
    "context": "museum_monitoring"
  }'
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Core Configuration
FRONTEND_ORIGIN=http://localhost:5173
MOCK_SENSORS=true
ESP32_CAM_URL=http://192.168.1.25:81/stream

# Anomaly Detection Thresholds
TEMP_MIN=18.0
TEMP_MAX=24.0
HUMIDITY_MIN=40.0
HUMIDITY_MAX=60.0
VIBRATION_MAX=0.5
```

### Hardware Integration

To connect real ESP32 sensors:
1. Set `MOCK_SENSORS=false` in your `.env` file
2. Configure `ESP32_CAM_URL` with your camera's IP address
3. Implement sensor data collection endpoint in your ESP32 code

## Architecture

```
ESP32 Sensors → Backend API → Frontend Dashboard
     ↓              ↓              ↓
  DHT11/SW-420 → FastAPI → React UI
     ↓              ↓              ↓
  ESP32-CAM → Anomaly ML → Real-time Updates
```

### Data Flow
1. ESP32 sensors collect environmental data
2. Backend evaluates data against thresholds
3. ML models analyze patterns for anomalies
4. Frontend displays real-time status and alerts
5. Chat assistant provides contextual help

## Anomaly Detection

The system uses a multi-layered approach:

1. **Rule-based Detection**: Threshold checking for immediate alerts
2. **Statistical Analysis**: Z-score and trend analysis
3. **Machine Learning**: Pattern recognition for complex anomalies
4. **Computer Vision**: Object detection for security monitoring

### Default Thresholds
- **Temperature**: 18-24°C (64-75°F)
- **Humidity**: 40-60% RH
- **Vibration**: 0-0.5 units

## Development

### Adding New Sensor Types
1. Update the `SensorData` model in `main.py`
2. Add threshold configuration in `.env`
3. Implement detection logic in `detect_anomaly_rule_based()`
4. Update frontend components to display new sensor data

### Custom AI Integration
Replace the simple chat responses in `generate_chat_response()` with your preferred AI service:

```python
async def generate_chat_response(message: str, context: str = None) -> str:
    # Integration with your AI service
    # Example: Hugging Face, local LLM, etc.
    pass
```

### Adding Machine Learning Models
```python
# Example: Scikit-learn integration
from sklearn.ensemble import IsolationForest

def ml_anomaly_detection(sensor_data):
    model = IsolationForest(contamination=0.1)
    # Training and prediction logic
    return anomaly_score
```

## Production Deployment

### Security Considerations
- Set up proper CORS origins
- Implement authentication/authorization
- Use HTTPS in production
- Secure API keys and secrets

### Performance Optimization
- Enable caching for sensor data
- Implement WebSocket connections for real-time updates
- Use connection pooling for database operations
- Add monitoring and logging

### Docker Deployment
```dockerfile
# Example Dockerfile structure
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Future Enhancements

- [ ] Historical data persistence and analytics
- [ ] WebSocket real-time notifications
- [ ] Multi-camera support and snapshot capture
- [ ] Role-based authentication system
- [ ] Mobile app for remote monitoring
- [ ] Integration with building management systems
- [ ] Advanced ML models for predictive maintenance
- [ ] Custom threshold calibration UI
- [ ] Automated report generation
- [ ] Multi-language support

## Support

For questions and support, please open an issue on GitHub or contact the development team.