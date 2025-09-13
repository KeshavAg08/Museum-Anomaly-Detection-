from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import asyncio
import json
import random
import time
import os
from datetime import datetime
import httpx
import io
from PIL import Image, ImageDraw
import sqlite3
import logging
from contextlib import contextmanager

app = FastAPI(title="Museum Anomaly Detection API", version="1.0.0")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
MOCK_SENSORS = os.getenv("MOCK_SENSORS", "true").lower() == "true"
ESP32_IP = os.getenv("ESP32_IP", "10.174.95.69")
ESP32_PORT = int(os.getenv("ESP32_PORT", "80"))
REAL_DATA_EXHIBIT_ID = int(os.getenv("REAL_DATA_EXHIBIT_ID", "1"))
DATABASE_URL = os.getenv("DATABASE_URL", "museum.db")

# Data models
class SensorData(BaseModel):
    temperature: float
    humidity: float
    vibration: float
    timestamp: Optional[str] = None

class Exhibit(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    location: str
    temperature_min: Optional[float] = 18.0
    temperature_max: Optional[float] = 24.0
    humidity_min: Optional[float] = 40.0
    humidity_max: Optional[float] = 60.0
    vibration_max: Optional[float] = 0.5
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ExhibitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    humidity_min: Optional[float] = None
    humidity_max: Optional[float] = None
    vibration_max: Optional[float] = None

class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str

class AnomalyCheck(BaseModel):
    sensor_data: SensorData
    exhibit_id: Optional[int] = None
    threshold_config: Optional[Dict[str, float]] = None

class AnomalyResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    explanation: str
    affected_sensors: list
    timestamp: str

# ESP32 Sensor Manager
class ESP32SensorManager:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self.base_url = f"http://{ip}:{port}"
        self.last_successful_read = None
        self.connection_errors = 0
        self.max_connection_errors = 5
        
    async def get_sensor_data(self) -> Optional[SensorData]:
        """Get real sensor data from ESP32"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/sensors")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"ESP32 sensor data: {data}")
                    
                    sensor_data = SensorData(
                        temperature=float(data.get('temperature', 0.0)),
                        humidity=float(data.get('humidity', 0.0)),
                        vibration=float(data.get('vibration_value', 0.0)),
                        timestamp=datetime.now().isoformat()
                    )
                    
                    self.connection_errors = 0
                    self.last_successful_read = datetime.now()
                    return sensor_data
                else:
                    logger.warning(f"ESP32 responded with status {response.status_code}")
                    
        except Exception as e:
            self.connection_errors += 1
            logger.error(f"Error reading ESP32 data (attempt {self.connection_errors}): {e}")
        
        return None
    
    async def get_full_esp32_data(self) -> Optional[Dict]:
        """Get comprehensive data from ESP32 /json endpoint"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/json")
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Error reading ESP32 full data: {e}")
        
        return None

# Global instance
esp32_sensor_manager = ESP32SensorManager(ESP32_IP, ESP32_PORT)

# Database setup
@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize the database with required tables"""
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS exhibits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                location TEXT,
                temperature_min REAL DEFAULT 18.0,
                temperature_max REAL DEFAULT 24.0,
                humidity_min REAL DEFAULT 40.0,
                humidity_max REAL DEFAULT 60.0,
                vibration_max REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exhibit_id INTEGER,
                temperature REAL,
                humidity REAL,
                vibration REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exhibit_id) REFERENCES exhibits (id)
            )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")

# Mock sensor data generator
def generate_mock_sensor_data() -> SensorData:
    base_temp = 21.0 + random.uniform(-2, 3)
    base_humidity = 50.0 + random.uniform(-10, 15)
    base_vibration = random.uniform(0, 1.0)
    
    if random.random() < 0.1:
        if random.choice([True, False]):
            base_temp += random.uniform(5, 10)
        else:
            base_vibration += random.uniform(2, 5)
    
    return SensorData(
        temperature=round(base_temp, 1),
        humidity=round(base_humidity, 1),
        vibration=round(base_vibration, 2),
        timestamp=datetime.now().isoformat()
    )

# Default thresholds for anomaly detection
DEFAULT_THRESHOLDS = {
    "temperature": {"min": 18.0, "max": 24.0},
    "humidity": {"min": 40.0, "max": 60.0},
    "vibration": {"min": 0.0, "max": 0.5}
}

# Rule-based anomaly detection
def detect_anomaly_rule_based(data: SensorData, thresholds: Dict = None) -> Dict[str, Any]:
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS
    
    anomalies = []
    scores = []
    
    # Check temperature
    temp_threshold = thresholds.get("temperature", DEFAULT_THRESHOLDS["temperature"])
    if data.temperature < temp_threshold["min"]:
        anomalies.append("temperature_low")
        scores.append(abs(data.temperature - temp_threshold["min"]) / temp_threshold["min"])
    elif data.temperature > temp_threshold["max"]:
        anomalies.append("temperature_high")
        scores.append(abs(data.temperature - temp_threshold["max"]) / temp_threshold["max"])
    
    # Check humidity
    humidity_threshold = thresholds.get("humidity", DEFAULT_THRESHOLDS["humidity"])
    if data.humidity < humidity_threshold["min"]:
        anomalies.append("humidity_low")
        scores.append(abs(data.humidity - humidity_threshold["min"]) / humidity_threshold["min"])
    elif data.humidity > humidity_threshold["max"]:
        anomalies.append("humidity_high")
        scores.append(abs(data.humidity - humidity_threshold["max"]) / humidity_threshold["max"])
    
    # Check vibration
    vibration_threshold = thresholds.get("vibration", DEFAULT_THRESHOLDS["vibration"])
    if data.vibration > vibration_threshold["max"]:
        anomalies.append("vibration_high")
        scores.append(abs(data.vibration - vibration_threshold["max"]) / vibration_threshold["max"])
    
    is_anomaly = len(anomalies) > 0
    anomaly_score = max(scores) if scores else 0.0
    
    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": min(anomaly_score, 1.0),
        "anomalies": anomalies,
        "affected_sensors": [anomaly.split('_')[0] for anomaly in anomalies]
    }

# Generate explanation for anomalies
def generate_anomaly_explanation(anomalies: list, sensor_data: SensorData) -> str:
    if not anomalies:
        return "All sensor readings are within normal parameters."
    
    explanations = {
        "temperature_high": f"Temperature ({sensor_data.temperature}°C) is above safe levels.",
        "temperature_low": f"Temperature ({sensor_data.temperature}°C) is below recommended levels.",
        "humidity_high": f"Humidity ({sensor_data.humidity}%) is too high.",
        "humidity_low": f"Humidity ({sensor_data.humidity}%) is too low.",
        "vibration_high": f"Vibration levels ({sensor_data.vibration}) are excessive."
    }
    
    selected_explanations = [explanations.get(anomaly, f"Anomaly detected: {anomaly}") for anomaly in anomalies]
    
    if len(selected_explanations) == 1:
        return selected_explanations[0]
    else:
        return "Multiple issues detected: " + " | ".join(selected_explanations)

# Simple chat responses
def generate_chat_response(message: str, context: str = None) -> str:
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["temperature", "temp"]):
        return "The ideal temperature range for museum exhibits is 18-24°C (64-75°F)."
    elif any(word in message_lower for word in ["humidity", "moisture"]):
        return "Museum humidity should be maintained between 40-60% RH."
    elif any(word in message_lower for word in ["vibration", "shake"]):
        return "Vibrations can damage delicate artifacts over time. Monitor levels carefully."
    elif any(word in message_lower for word in ["help", "how", "what"]):
        return "I can help with museum environmental monitoring questions."
    else:
        return f"I understand you're asking about: '{message}'. For museum monitoring, check temperature, humidity, and vibration levels regularly."

# Create placeholder image for camera
def create_placeholder_image():
    img = Image.new('RGB', (640, 480), color='lightgray')
    draw = ImageDraw.Draw(img)
    draw.text((200, 220), "Camera Placeholder", fill='black')
    draw.text((180, 240), "(OpenCV not available)", fill='black')
    draw.text((160, 260), "Real ESP32 data is working!", fill='green')
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=70)
    return img_bytes.getvalue()

def save_sensor_reading(exhibit_id: int, sensor_data: SensorData):
    """Save sensor reading to database"""
    with get_db() as conn:
        conn.execute('''
            INSERT INTO sensor_readings (exhibit_id, temperature, humidity, vibration)
            VALUES (?, ?, ?, ?)
        ''', (exhibit_id, sensor_data.temperature, sensor_data.humidity, sensor_data.vibration))
        conn.commit()

@app.on_event("startup")
async def startup_event():
    init_database()
    
    # Add sample exhibit if none exist
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM exhibits")
        count = cursor.fetchone()['count']
        if count == 0:
            conn.execute('''
                INSERT INTO exhibits (name, description, location, temperature_min, temperature_max, 
                                    humidity_min, humidity_max, vibration_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ("ESP32 Real Sensors", "Live data from ESP32 device", "Gallery A", 20.0, 30.0, 40.0, 65.0, 100.0))
            conn.commit()
            logger.info("Sample exhibit added to database")

# API Endpoints
@app.get("/health")
async def health_check():
    esp32_connected = esp32_sensor_manager.last_successful_read is not None
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mock_mode": MOCK_SENSORS,
        "database": "connected",
        "esp32_connected": esp32_connected,
        "camera_status": "placeholder_mode",
        "esp32_ip": ESP32_IP if not MOCK_SENSORS else None
    }

@app.get("/sensors/data")
async def get_sensor_data():
    """Get sensor data - either from ESP32 or mock data"""
    if MOCK_SENSORS:
        data = generate_mock_sensor_data()
    else:
        real_data = await esp32_sensor_manager.get_sensor_data()
        if real_data:
            data = real_data
        else:
            logger.warning("ESP32 not available, falling back to mock data")
            data = generate_mock_sensor_data()
    
    return data

@app.get("/esp32/status")
async def esp32_status():
    """Get ESP32 connection status and device info"""
    if MOCK_SENSORS:
        return {"status": "mock_mode", "message": "ESP32 integration disabled (mock mode)"}
    
    full_data = await esp32_sensor_manager.get_full_esp32_data()
    if full_data:
        return {
            "status": "connected",
            "device_info": full_data.get("device_info", {}),
            "system_status": full_data.get("system_status", {}),
            "connection_errors": esp32_sensor_manager.connection_errors,
            "last_successful_read": esp32_sensor_manager.last_successful_read.isoformat() if esp32_sensor_manager.last_successful_read else None
        }
    else:
        return {
            "status": "disconnected",
            "connection_errors": esp32_sensor_manager.connection_errors,
            "message": "Unable to connect to ESP32"
        }

@app.post("/anomaly/check")
async def check_anomaly(request: AnomalyCheck):
    try:
        thresholds = request.threshold_config or DEFAULT_THRESHOLDS
        
        # Rule-based detection
        result = detect_anomaly_rule_based(request.sensor_data, thresholds)
        
        # Generate explanation
        explanation = generate_anomaly_explanation(result["anomalies"], request.sensor_data)
        
        # Save sensor reading if exhibit_id provided
        if request.exhibit_id:
            save_sensor_reading(request.exhibit_id, request.sensor_data)
        
        return AnomalyResponse(
            is_anomaly=result["is_anomaly"],
            anomaly_score=result["anomaly_score"],
            explanation=explanation,
            affected_sensors=result["affected_sensors"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in anomaly detection: {e}")
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

@app.post("/chat")
async def chat_endpoint(request: ChatMessage):
    try:
        response_text = generate_chat_response(request.message, request.context)
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in chat processing: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.get("/camera/stream")
async def camera_stream():
    """Placeholder camera stream"""
    async def generate_stream():
        placeholder_img = create_placeholder_image()
        while True:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   placeholder_img + b'\r\n')
            await asyncio.sleep(0.1)
    
    return StreamingResponse(
        generate_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/camera/snapshot")
async def camera_snapshot():
    """Take a placeholder snapshot"""
    placeholder_img = create_placeholder_image()
    return StreamingResponse(
        io.BytesIO(placeholder_img),
        media_type="image/jpeg"
    )

@app.get("/exhibits/{exhibit_id}/monitor")
async def monitor_exhibit_realtime(exhibit_id: int):
    """Get real-time monitoring data for a specific exhibit"""
    try:
        # Get sensor data based on whether this is the real sensor exhibit
        if not MOCK_SENSORS and exhibit_id == REAL_DATA_EXHIBIT_ID:
            sensor_data = await esp32_sensor_manager.get_sensor_data()
            data_source = "esp32"
            if not sensor_data:
                sensor_data = generate_mock_sensor_data()
                data_source = "mock_fallback"
                logger.warning(f"ESP32 unavailable for exhibit {exhibit_id}, using mock data")
        else:
            sensor_data = generate_mock_sensor_data()
            data_source = "mock"
        
        # Use default thresholds for anomaly detection
        anomaly_result = detect_anomaly_rule_based(sensor_data, DEFAULT_THRESHOLDS)
        explanation = generate_anomaly_explanation(anomaly_result["anomalies"], sensor_data)
        
        return {
            "exhibit_id": exhibit_id,
            "sensor_data": sensor_data,
            "anomaly_status": {
                "is_anomaly": anomaly_result["is_anomaly"],
                "anomaly_score": anomaly_result["anomaly_score"],
                "explanation": explanation,
                "affected_sensors": anomaly_result["affected_sensors"]
            },
            "thresholds": DEFAULT_THRESHOLDS,
            "data_source": data_source,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error monitoring exhibit {exhibit_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to monitor exhibit: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )