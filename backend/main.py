from fastapi import FastAPI, HTTPException, Depends
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
from PIL import Image
import sqlite3
import logging
from contextlib import contextmanager
import cv2
import threading

app = FastAPI(title="Museum Anomaly Detection API", version="1.0.0")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MOCK_SENSORS = os.getenv("MOCK_SENSORS", "true").lower() == "true"
ESP32_CAM_URL = os.getenv("ESP32_CAM_URL")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
DATABASE_URL = os.getenv("DATABASE_URL", "museum.db")

# NEW: ESP32 Real Sensor Configuration
ESP32_IP = os.getenv("ESP32_IP", "10.174.95.69")
ESP32_PORT = int(os.getenv("ESP32_PORT", "80"))
REAL_DATA_EXHIBIT_ID = int(os.getenv("REAL_DATA_EXHIBIT_ID", "1"))

# NEW: USB Camera Configuration
USB_CAMERA_INDEX = int(os.getenv("USB_CAMERA_INDEX", "0"))
CAMERA_QUALITY = int(os.getenv("CAMERA_QUALITY", "70"))
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "10"))

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

class AnomalyCheck(BaseModel):
    sensor_data: SensorData
    exhibit_id: Optional[int] = None
    threshold_config: Optional[Dict[str, float]] = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str

class AnomalyResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    explanation: str
    affected_sensors: list
    timestamp: str

# NEW: ESP32 Sensor Manager
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
                # Try the recommended /api/sensors endpoint first
                response = await client.get(f"{self.base_url}/api/sensors")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"ESP32 sensor data: {data}")
                    
                    # Map the ESP32 data structure to our SensorData model
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
            
            if self.connection_errors >= self.max_connection_errors:
                logger.error(f"Max connection errors reached for ESP32. Falling back to mock data.")
        
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
    
    def is_connected(self) -> bool:
        """Check if ESP32 connection is healthy"""
        if self.last_successful_read is None:
            return False
        
        # Consider connection stale if no successful read in last 30 seconds
        time_since_last_read = datetime.now() - self.last_successful_read
        return time_since_last_read.total_seconds() < 30

# NEW: USB Camera Manager
class USBCameraManager:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
    def start_camera(self):
        """Initialize and start USB camera"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Failed to open USB camera at index {self.camera_index}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            
            self.is_running = True
            logger.info(f"USB camera initialized successfully at index {self.camera_index}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing USB camera: {e}")
            return False
    
    def capture_frame(self) -> Optional[bytes]:
        """Capture a single frame from USB camera"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        try:
            ret, frame = self.cap.read()
            if ret:
                # Encode frame to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, CAMERA_QUALITY])
                return buffer.tobytes()
            else:
                logger.warning("Failed to capture frame from USB camera")
                return None
                
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None
    
    def stop_camera(self):
        """Stop and release USB camera"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            logger.info("USB camera released")

# Global instances
esp32_sensor_manager = ESP32SensorManager(ESP32_IP, ESP32_PORT)
usb_camera_manager = USBCameraManager(USB_CAMERA_INDEX)

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
        # Create exhibits table
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
        
        # Create sensor_readings table
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
        
        # Create anomalies table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exhibit_id INTEGER,
                anomaly_type TEXT,
                severity REAL,
                description TEXT,
                sensor_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (exhibit_id) REFERENCES exhibits (id)
            )
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    
    # Initialize USB camera if not using mock sensors
    if not MOCK_SENSORS:
        usb_camera_manager.start_camera()
    
    # Add some sample exhibits if none exist
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM exhibits")
        count = cursor.fetchone()['count']
        if count == 0:
            sample_exhibits = [
                ("Ancient Vase (Real Sensors)", "2000-year-old ceramic vase with real ESP32 monitoring", "Gallery A", 20.0, 30.0, 40.0, 65.0, 100.0),
                ("Medieval Manuscript", "Illuminated manuscript from 13th century", "Gallery B", 18.0, 21.0, 40.0, 50.0, 0.2),
                ("Oil Painting", "Renaissance oil painting", "Gallery C", 19.0, 23.0, 45.0, 60.0, 0.4)
            ]
            for exhibit in sample_exhibits:
                conn.execute('''
                    INSERT INTO exhibits (name, description, location, temperature_min, temperature_max, 
                                        humidity_min, humidity_max, vibration_max)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', exhibit)
            conn.commit()
            logger.info("Sample exhibits added to database")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    usb_camera_manager.stop_camera()

# Database functions (keeping all existing functions)
def create_exhibit(exhibit: Exhibit) -> Exhibit:
    """Create a new exhibit in the database"""
    with get_db() as conn:
        cursor = conn.execute('''
            INSERT INTO exhibits (name, description, location, temperature_min, temperature_max,
                                humidity_min, humidity_max, vibration_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (exhibit.name, exhibit.description, exhibit.location, exhibit.temperature_min,
              exhibit.temperature_max, exhibit.humidity_min, exhibit.humidity_max, exhibit.vibration_max))
        
        exhibit_id = cursor.lastrowid
        conn.commit()
        
        # Fetch the created exhibit
        cursor = conn.execute('''
            SELECT * FROM exhibits WHERE id = ?
        ''', (exhibit_id,))
        row = cursor.fetchone()
        
        return Exhibit(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            location=row['location'],
            temperature_min=row['temperature_min'],
            temperature_max=row['temperature_max'],
            humidity_min=row['humidity_min'],
            humidity_max=row['humidity_max'],
            vibration_max=row['vibration_max'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

def get_all_exhibits() -> List[Exhibit]:
    """Get all exhibits from the database"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM exhibits ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        exhibits = []
        for row in rows:
            exhibits.append(Exhibit(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                location=row['location'],
                temperature_min=row['temperature_min'],
                temperature_max=row['temperature_max'],
                humidity_min=row['humidity_min'],
                humidity_max=row['humidity_max'],
                vibration_max=row['vibration_max'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))
        return exhibits

def get_exhibit_by_id(exhibit_id: int) -> Optional[Exhibit]:
    """Get a specific exhibit by ID"""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM exhibits WHERE id = ?", (exhibit_id,))
        row = cursor.fetchone()
        
        if row:
            return Exhibit(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                location=row['location'],
                temperature_min=row['temperature_min'],
                temperature_max=row['temperature_max'],
                humidity_min=row['humidity_min'],
                humidity_max=row['humidity_max'],
                vibration_max=row['vibration_max'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        return None

def update_exhibit(exhibit_id: int, updates: ExhibitUpdate) -> Optional[Exhibit]:
    """Update an existing exhibit"""
    with get_db() as conn:
        # Build dynamic update query
        update_fields = []
        values = []
        
        for field, value in updates.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if not update_fields:
            return get_exhibit_by_id(exhibit_id)
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(exhibit_id)
        
        query = f"UPDATE exhibits SET {', '.join(update_fields)} WHERE id = ?"
        cursor = conn.execute(query, values)
        
        if cursor.rowcount == 0:
            return None
            
        conn.commit()
        return get_exhibit_by_id(exhibit_id)

def delete_exhibit(exhibit_id: int) -> bool:
    """Delete an exhibit from the database"""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM exhibits WHERE id = ?", (exhibit_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted

def save_sensor_reading(exhibit_id: int, sensor_data: SensorData):
    """Save sensor reading to database"""
    with get_db() as conn:
        conn.execute('''
            INSERT INTO sensor_readings (exhibit_id, temperature, humidity, vibration)
            VALUES (?, ?, ?, ?)
        ''', (exhibit_id, sensor_data.temperature, sensor_data.humidity, sensor_data.vibration))
        conn.commit()

def save_anomaly(exhibit_id: int, anomaly_type: str, severity: float, description: str, sensor_data: str):
    """Save anomaly detection result to database"""
    with get_db() as conn:
        conn.execute('''
            INSERT INTO anomalies (exhibit_id, anomaly_type, severity, description, sensor_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (exhibit_id, anomaly_type, severity, description, sensor_data))
        conn.commit()

# Default thresholds for anomaly detection
DEFAULT_THRESHOLDS = {
    "temperature": {"min": 18.0, "max": 24.0},
    "humidity": {"min": 40.0, "max": 60.0},
    "vibration": {"min": 0.0, "max": 0.5}
}

# Mock sensor data generator
def generate_mock_sensor_data() -> SensorData:
    # Add some randomness to make it interesting
    base_temp = 21.0 + random.uniform(-2, 3)
    base_humidity = 50.0 + random.uniform(-10, 15)
    base_vibration = random.uniform(0, 1.0)
    
    # Occasionally generate anomalous readings
    if random.random() < 0.1:  # 10% chance of anomaly
        if random.choice([True, False]):
            base_temp += random.uniform(5, 10)  # High temperature
        else:
            base_vibration += random.uniform(2, 5)  # High vibration
    
    return SensorData(
        temperature=round(base_temp, 1),
        humidity=round(base_humidity, 1),
        vibration=round(base_vibration, 2),
        timestamp=datetime.now().isoformat()
    )

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
        "temperature_high": f"Temperature ({sensor_data.temperature}°C) is above safe levels. This could damage artifacts or promote mold growth.",
        "temperature_low": f"Temperature ({sensor_data.temperature}°C) is below recommended levels. This could cause condensation or material stress.",
        "humidity_high": f"Humidity ({sensor_data.humidity}%) is too high. This increases risk of mold, corrosion, and deterioration.",
        "humidity_low": f"Humidity ({sensor_data.humidity}%) is too low. This can cause cracking and brittleness in organic materials.",
        "vibration_high": f"Vibration levels ({sensor_data.vibration}) are excessive. This could indicate structural issues or nearby construction."
    }
    
    selected_explanations = [explanations.get(anomaly, f"Anomaly detected: {anomaly}") for anomaly in anomalies]
    
    if len(selected_explanations) == 1:
        return selected_explanations[0]
    else:
        return "Multiple issues detected: " + " | ".join(selected_explanations)

# Simple chat responses (replace with your preferred AI service)
def generate_chat_response(message: str, context: str = None) -> str:
    message_lower = message.lower()
    
    # Museum-specific responses
    if any(word in message_lower for word in ["temperature", "temp"]):
        return "The ideal temperature range for museum exhibits is 18-24°C (64-75°F). Sudden changes should be avoided as they can cause expansion and contraction damage to artifacts."
    
    elif any(word in message_lower for word in ["humidity", "moisture"]):
        return "Museum humidity should be maintained between 40-60% RH. High humidity promotes mold and corrosion, while low humidity can cause cracking in organic materials."
    
    elif any(word in message_lower for word in ["vibration", "shake", "movement"]):
        return "Vibrations from construction, traffic, or HVAC systems can damage delicate artifacts over time. Monitor levels and install dampening systems if needed."
    
    elif any(word in message_lower for word in ["anomaly", "alert", "problem"]):
        return "Anomalies indicate conditions outside normal parameters. Investigate immediately to prevent artifact damage. Check HVAC systems, sensors, and environmental controls."
    
    elif any(word in message_lower for word in ["artifact", "artwork", "collection"]):
        return "Proper environmental monitoring is crucial for artifact preservation. Different materials have specific requirements - metals, organics, and textiles each need different conditions."
    
    elif any(word in message_lower for word in ["exhibit"]):
        return "Each exhibit may have unique environmental requirements. You can configure custom thresholds for temperature, humidity, and vibration for each exhibit in the system."
    
    elif any(word in message_lower for word in ["help", "how", "what"]):
        return "I can help with museum environmental monitoring questions. Ask me about temperature, humidity, vibration thresholds, or artifact preservation best practices."
    
    else:
        return f"I understand you're asking about: '{message}'. For museum environmental monitoring, I recommend checking temperature (18-24°C), humidity (40-60% RH), and vibration levels regularly."

# Create placeholder image for camera stream
def create_placeholder_image():
    img = Image.new('RGB', (640, 480), color='lightgray')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=70)
    return img_bytes.getvalue()

# API Endpoints
@app.get("/health")
async def health_check():
    esp32_status = esp32_sensor_manager.is_connected() if not MOCK_SENSORS else "mock_mode"
    camera_status = usb_camera_manager.is_running if not MOCK_SENSORS else "mock_mode"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mock_mode": MOCK_SENSORS,
        "database": "connected",
        "esp32_connected": esp32_status,
        "camera_status": camera_status,
        "esp32_ip": ESP32_IP if not MOCK_SENSORS else None
    }

# Exhibit management endpoints
@app.post("/exhibits")
async def create_exhibit_endpoint(exhibit: Exhibit):
    """Create a new exhibit"""
    try:
        created_exhibit = create_exhibit(exhibit)
        return created_exhibit
    except Exception as e:
        logger.error(f"Error creating exhibit: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create exhibit: {str(e)}")

@app.get("/exhibits")
async def get_exhibits():
    """Get all exhibits"""
    try:
        exhibits = get_all_exhibits()
        return {"exhibits": exhibits}
    except Exception as e:
        logger.error(f"Error fetching exhibits: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch exhibits: {str(e)}")

@app.get("/exhibits/{exhibit_id}")
async def get_exhibit(exhibit_id: int):
    """Get a specific exhibit by ID"""
    try:
        exhibit = get_exhibit_by_id(exhibit_id)
        if not exhibit:
            raise HTTPException(status_code=404, detail="Exhibit not found")
        return exhibit
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exhibit {exhibit_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch exhibit: {str(e)}")

@app.put("/exhibits/{exhibit_id}")
async def update_exhibit_endpoint(exhibit_id: int, updates: ExhibitUpdate):
    """Update an existing exhibit"""
    try:
        updated_exhibit = update_exhibit(exhibit_id, updates)
        if not updated_exhibit:
            raise HTTPException(status_code=404, detail="Exhibit not found")
        return updated_exhibit
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating exhibit {exhibit_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update exhibit: {str(e)}")

@app.delete("/exhibits/{exhibit_id}")
async def delete_exhibit_endpoint(exhibit_id: int):
    """Delete an exhibit"""
    try:
        deleted = delete_exhibit(exhibit_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Exhibit not found")
        return {"message": "Exhibit deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting exhibit {exhibit_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete exhibit: {str(e)}")

@app.get("/sensors/data")
async def get_sensor_data():
    """Get sensor data - either from ESP32 or mock data"""
    if MOCK_SENSORS:
        data = generate_mock_sensor_data()
    else:
        # Try to get real data from ESP32
        real_data = await esp32_sensor_manager.get_sensor_data()
        if real_data:
            data = real_data
        else:
            # Fallback to mock data if ESP32 is not available
            logger.warning("ESP32 not available, falling back to mock data")
            data = generate_mock_sensor_data()
    
    return data

# NEW: ESP32 specific endpoints
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

@app.get("/esp32/full-data")
async def esp32_full_data():
    """Get comprehensive data from ESP32 including history"""
    if MOCK_SENSORS:
        raise HTTPException(status_code=400, detail="ESP32 integration disabled (mock mode)")
    
    full_data = await esp32_sensor_manager.get_full_esp32_data()
    if full_data:
        return full_data
    else:
        raise HTTPException(status_code=503, detail="Unable to connect to ESP32")

@app.post("/anomaly/check")
async def check_anomaly(request: AnomalyCheck):
    try:
        # Get exhibit-specific thresholds if exhibit_id is provided
        thresholds = None
        if request.exhibit_id:
            exhibit = get_exhibit_by_id(request.exhibit_id)
            if exhibit:
                thresholds = {
                    "temperature": {"min": exhibit.temperature_min, "max": exhibit.temperature_max},
                    "humidity": {"min": exhibit.humidity_min, "max": exhibit.humidity_max},
                    "vibration": {"min": 0.0, "max": exhibit.vibration_max}
                }
                # Save sensor reading
                save_sensor_reading(request.exhibit_id, request.sensor_data)
        
        if thresholds is None:
            thresholds = request.threshold_config or DEFAULT_THRESHOLDS
        
        # Rule-based detection
        result = detect_anomaly_rule_based(request.sensor_data, thresholds)
        
        # Generate explanation
        explanation = generate_anomaly_explanation(result["anomalies"], request.sensor_data)
        
        # Save anomaly if detected
        if result["is_anomaly"] and request.exhibit_id:
            save_anomaly(
                request.exhibit_id,
                ",".join(result["anomalies"]),
                result["anomaly_score"],
                explanation,
                json.dumps(request.sensor_data.dict())
            )
        
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
    """Stream video from USB camera or placeholder"""
    async def generate_stream():
        if MOCK_SENSORS:
            # Mock mode - return placeholder image
            placeholder_img = create_placeholder_image()
            while True:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + 
                       placeholder_img + b'\r\n')
                await asyncio.sleep(1.0 / CAMERA_FPS)
        else:
            # Real camera mode
            while True:
                frame = usb_camera_manager.capture_frame()
                if frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + 
                           frame + b'\r\n')
                else:
                    # Fallback to placeholder if camera fails
                    placeholder_img = create_placeholder_image()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + 
                           placeholder_img + b'\r\n')
                
                await asyncio.sleep(1.0 / CAMERA_FPS)
    
    return StreamingResponse(
        generate_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/camera/snapshot")
async def camera_snapshot():
    """Take a single snapshot from USB camera"""
    if MOCK_SENSORS:
        # Return placeholder image
        placeholder_img = create_placeholder_image()
        return StreamingResponse(
            io.BytesIO(placeholder_img),
            media_type="image/jpeg"
        )
    else:
        frame = usb_camera_manager.capture_frame()
        if frame:
            return StreamingResponse(
                io.BytesIO(frame),
                media_type="image/jpeg"
            )
        else:
            # Fallback to placeholder
            placeholder_img = create_placeholder_image()
            return StreamingResponse(
                io.BytesIO(placeholder_img),
                media_type="image/jpeg"
            )

@app.post("/vision/check")
async def vision_check():
    # Placeholder for YOLOv8 integration
    return {
        "objects_detected": [],
        "threat_level": "low",
        "message": "Vision detection not implemented yet",
        "timestamp": datetime.now().isoformat()
    }

# NEW: Real-time monitoring endpoint for specific exhibit
@app.get("/exhibits/{exhibit_id}/monitor")
async def monitor_exhibit_realtime(exhibit_id: int):
    """Get real-time monitoring data for a specific exhibit"""
    try:
        exhibit = get_exhibit_by_id(exhibit_id)
        if not exhibit:
            raise HTTPException(status_code=404, detail="Exhibit not found")
        
        # Get sensor data based on whether this is the real sensor exhibit
        if not MOCK_SENSORS and exhibit_id == REAL_DATA_EXHIBIT_ID:
            sensor_data = await esp32_sensor_manager.get_sensor_data()
            if not sensor_data:
                sensor_data = generate_mock_sensor_data()
                logger.warning(f"ESP32 unavailable for exhibit {exhibit_id}, using mock data")
        else:
            sensor_data = generate_mock_sensor_data()
        
        # Check for anomalies using exhibit-specific thresholds
        thresholds = {
            "temperature": {"min": exhibit.temperature_min, "max": exhibit.temperature_max},
            "humidity": {"min": exhibit.humidity_min, "max": exhibit.humidity_max},
            "vibration": {"min": 0.0, "max": exhibit.vibration_max}
        }
        
        anomaly_result = detect_anomaly_rule_based(sensor_data, thresholds)
        explanation = generate_anomaly_explanation(anomaly_result["anomalies"], sensor_data)
        
        # Save reading and anomaly if needed
        save_sensor_reading(exhibit_id, sensor_data)
        if anomaly_result["is_anomaly"]:
            save_anomaly(
                exhibit_id,
                ",".join(anomaly_result["anomalies"]),
                anomaly_result["anomaly_score"],
                explanation,
                json.dumps(sensor_data.dict())
            )
        
        return {
            "exhibit": exhibit,
            "sensor_data": sensor_data,
            "anomaly_status": {
                "is_anomaly": anomaly_result["is_anomaly"],
                "anomaly_score": anomaly_result["anomaly_score"],
                "explanation": explanation,
                "affected_sensors": anomaly_result["affected_sensors"]
            },
            "thresholds": thresholds,
            "data_source": "esp32" if (not MOCK_SENSORS and exhibit_id == REAL_DATA_EXHIBIT_ID) else "mock",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error monitoring exhibit {exhibit_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to monitor exhibit: {str(e)}")

# NEW: Historical data endpoint
@app.get("/exhibits/{exhibit_id}/history")
async def get_exhibit_history(exhibit_id: int, limit: int = 100):
    """Get historical sensor readings for an exhibit"""
    try:
        exhibit = get_exhibit_by_id(exhibit_id)
        if not exhibit:
            raise HTTPException(status_code=404, detail="Exhibit not found")
        
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT temperature, humidity, vibration, timestamp
                FROM sensor_readings 
                WHERE exhibit_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (exhibit_id, limit))
            
            readings = []
            for row in cursor.fetchall():
                readings.append({
                    "temperature": row['temperature'],
                    "humidity": row['humidity'],
                    "vibration": row['vibration'],
                    "timestamp": row['timestamp']
                })
        
        return {
            "exhibit_id": exhibit_id,
            "readings": readings,
            "count": len(readings)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history for exhibit {exhibit_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch exhibit history: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )