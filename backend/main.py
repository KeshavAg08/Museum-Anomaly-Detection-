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

# Try to import OpenCV, but make it optional
try:
    import cv2
    import threading
    from queue import Queue
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Camera features will use placeholders only.")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using default environment variables.")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Museum Anomaly Detection API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MOCK_SENSORS = os.getenv("MOCK_SENSORS", "true").lower() == "true"
ESP32_IP = os.getenv("ESP32_IP", "10.174.95.69")
ESP32_PORT = int(os.getenv("ESP32_PORT", "80"))
REAL_DATA_EXHIBIT_ID = int(os.getenv("REAL_DATA_EXHIBIT_ID", "1"))
USB_CAMERA_INDEX = int(os.getenv("USB_CAMERA_INDEX", "0"))
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

# Global ESP32 manager instance
esp32_sensor_manager = ESP32SensorManager(ESP32_IP, ESP32_PORT)

# Camera Manager (only if OpenCV is available)
class CameraManager:
    def __init__(self):
        self.camera = None
        self.is_camera_available = False
        self.latest_frame = None
        self.frame_lock = None
        self.capture_thread = None
        
        if CV2_AVAILABLE:
            self.frame_lock = threading.Lock()
            self.initialize_camera()
        else:
            logger.warning("OpenCV not available, camera features disabled")
        
    def initialize_camera(self):
        """Initialize USB camera"""
        if not CV2_AVAILABLE:
            return
            
        try:
            self.camera = cv2.VideoCapture(USB_CAMERA_INDEX)
            if self.camera.isOpened():
                # Set camera properties for better performance
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                self.is_camera_available = True
                logger.info(f"USB Camera initialized successfully on index {USB_CAMERA_INDEX}")
                
                # Start background thread to continuously capture frames
                self.capture_thread = threading.Thread(target=self._capture_frames, daemon=True)
                self.capture_thread.start()
            else:
                logger.warning("USB Camera not available")
                self.is_camera_available = False
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            self.is_camera_available = False
    
    def _capture_frames(self):
        """Background thread to capture frames continuously"""
        if not CV2_AVAILABLE:
            return
            
        while self.is_camera_available and self.camera.isOpened():
            try:
                ret, frame = self.camera.read()
                if ret:
                    with self.frame_lock:
                        self.latest_frame = frame
                time.sleep(1/30)  # 30 FPS
            except Exception as e:
                logger.error(f"Error capturing frame: {e}")
                break
    
    def get_latest_frame(self):
        """Get the latest captured frame"""
        if not CV2_AVAILABLE or not self.frame_lock:
            return None
            
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def release(self):
        """Release camera resources"""
        self.is_camera_available = False
        if self.camera and CV2_AVAILABLE:
            self.camera.release()

# Initialize camera manager
camera_manager = CameraManager()

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
    
    # Occasionally generate anomalous data
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
def create_placeholder_image_with_message(message: str):
    """Create placeholder image with custom message"""
    img = Image.new('RGB', (640, 480), color='lightgray')
    draw = ImageDraw.Draw(img)
    
    # Draw message in center
    lines = message.split('\n')
    y_offset = 240 - (len(lines) * 10)
    
    for line in lines:
        # Calculate text width to center it
        try:
            bbox = draw.textbbox((0, 0), line)
            text_width = bbox[2] - bbox[0]
        except AttributeError:
            # Fallback for older PIL versions
            text_width = len(line) * 6
        x_position = (640 - text_width) // 2
        draw.text((x_position, y_offset), line, fill='black')
        y_offset += 25
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((10, 450), f"Time: {timestamp}", fill='gray')
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=70)
    return img_bytes.getvalue()

def save_sensor_reading(exhibit_id: int, sensor_data: SensorData):
    """Save sensor reading to database"""
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO sensor_readings (exhibit_id, temperature, humidity, vibration)
                VALUES (?, ?, ?, ?)
            ''', (exhibit_id, sensor_data.temperature, sensor_data.humidity, sensor_data.vibration))
            conn.commit()
    except Exception as e:
        logger.error(f"Error saving sensor reading: {e}")

async def get_exhibit_thresholds(exhibit_id: int) -> Optional[Dict]:
    """Get custom thresholds for an exhibit from database"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT temperature_min, temperature_max, humidity_min, humidity_max, vibration_max
                FROM exhibits WHERE id = ?
            ''', (exhibit_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "temperature": {"min": row["temperature_min"], "max": row["temperature_max"]},
                    "humidity": {"min": row["humidity_min"], "max": row["humidity_max"]},
                    "vibration": {"min": 0.0, "max": row["vibration_max"]}
                }
    except Exception as e:
        logger.error(f"Error fetching exhibit thresholds: {e}")
    
    return None

# API ENDPOINTS

@app.on_event("startup")
async def startup_event():
    init_database()
    
    # Add sample exhibits if none exist
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM exhibits")
        count = cursor.fetchone()['count']
        if count == 0:
            # Add multiple sample exhibits
            sample_exhibits = [
                ("ESP32 Real Sensors", "Live data from ESP32 device", "Gallery A", 20.0, 30.0, 40.0, 65.0, 100.0),
                ("Ancient Egyptian Artifacts", "Collection of ancient Egyptian pottery and tools", "Gallery B", 18.0, 22.0, 45.0, 55.0, 0.3),
                ("Modern Art Collection", "Contemporary paintings and sculptures", "Gallery C", 19.0, 23.0, 40.0, 60.0, 0.4),
                ("Natural History Display", "Fossils and geological specimens", "Gallery D", 18.0, 24.0, 42.0, 58.0, 0.5)
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
    """Cleanup resources on shutdown"""
    if camera_manager:
        camera_manager.release()
    logger.info("Application shutdown complete")

@app.get("/health")
async def health_check():
    esp32_connected = esp32_sensor_manager.last_successful_read is not None
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mock_mode": MOCK_SENSORS,
        "database": "connected",
        "esp32_connected": esp32_connected,
        "camera_available": camera_manager.is_camera_available,
        "opencv_available": CV2_AVAILABLE,
        "esp32_ip": ESP32_IP if not MOCK_SENSORS else None
    }

@app.get("/exhibits")
async def get_all_exhibits():
    """Get all exhibits"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT id, name, description, location, 
                       temperature_min, temperature_max, 
                       humidity_min, humidity_max, vibration_max,
                       created_at, updated_at 
                FROM exhibits ORDER BY created_at DESC
            ''')
            exhibits = []
            for row in cursor.fetchall():
                exhibit = {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "location": row["location"],
                    "temperature_min": row["temperature_min"],
                    "temperature_max": row["temperature_max"],
                    "humidity_min": row["humidity_min"],
                    "humidity_max": row["humidity_max"],
                    "vibration_max": row["vibration_max"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                exhibits.append(exhibit)
            
            return {"exhibits": exhibits}
    except Exception as e:
        logger.error(f"Error fetching exhibits: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch exhibits: {str(e)}")

@app.get("/exhibits/{exhibit_id}")
async def get_exhibit(exhibit_id: int):
    """Get a specific exhibit"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT id, name, description, location, 
                       temperature_min, temperature_max, 
                       humidity_min, humidity_max, vibration_max,
                       created_at, updated_at 
                FROM exhibits WHERE id = ?
            ''', (exhibit_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Exhibit not found")
            
            exhibit = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "location": row["location"],
                "temperature_min": row["temperature_min"],
                "temperature_max": row["temperature_max"],
                "humidity_min": row["humidity_min"],
                "humidity_max": row["humidity_max"],
                "vibration_max": row["vibration_max"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            return exhibit
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exhibit {exhibit_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch exhibit: {str(e)}")

@app.get("/exhibits/{exhibit_id}/monitor")
async def monitor_exhibit_realtime(exhibit_id: int):
    """Get real-time monitoring data for a specific exhibit"""
    try:
        # Determine if this exhibit should use real ESP32 data
        use_real_data = (exhibit_id == REAL_DATA_EXHIBIT_ID and not MOCK_SENSORS)
        
        if use_real_data:
            # Try to get real ESP32 data for exhibit 1
            sensor_data = await esp32_sensor_manager.get_sensor_data()
            data_source = "esp32"
            
            if not sensor_data:
                # Fallback to mock if ESP32 is unavailable
                sensor_data = generate_mock_sensor_data()
                data_source = "mock_fallback"
                logger.warning(f"ESP32 unavailable for exhibit {exhibit_id}, using mock data")
        else:
            # Use mock data for all other exhibits
            sensor_data = generate_mock_sensor_data()
            data_source = "mock"
        
        # Get exhibit-specific thresholds from database
        exhibit_thresholds = await get_exhibit_thresholds(exhibit_id)
        
        # Use exhibit thresholds or default
        thresholds = exhibit_thresholds or DEFAULT_THRESHOLDS
        
        # Perform anomaly detection
        anomaly_result = detect_anomaly_rule_based(sensor_data, thresholds)
        explanation = generate_anomaly_explanation(anomaly_result["anomalies"], sensor_data)
        
        # Save sensor reading to database
        save_sensor_reading(exhibit_id, sensor_data)
        
        return {
            "exhibit_id": exhibit_id,
            "sensor_data": {
                **sensor_data.dict(),
                "data_source": data_source,
                "is_real_data": data_source == "esp32"
            },
            "anomaly_status": {
                "is_anomaly": anomaly_result["is_anomaly"],
                "anomaly_score": anomaly_result["anomaly_score"],
                "explanation": explanation,
                "affected_sensors": anomaly_result["affected_sensors"]
            },
            "thresholds": thresholds,
            "camera_available": camera_manager.is_camera_available if exhibit_id == REAL_DATA_EXHIBIT_ID else False,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error monitoring exhibit {exhibit_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to monitor exhibit: {str(e)}")

@app.get("/camera/stream/{exhibit_id}")
async def camera_stream_for_exhibit(exhibit_id: int):
    """Camera stream for specific exhibit - real camera for exhibit 1, placeholder for others"""
    
    async def generate_real_camera_stream():
        """Generate real USB camera stream"""
        while True:
            if camera_manager.is_camera_available and CV2_AVAILABLE:
                frame = camera_manager.get_latest_frame()
                if frame is not None:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               frame_bytes + b'\r\n')
                    else:
                        # Fallback to placeholder if encoding fails
                        placeholder_img = create_placeholder_image_with_message("Camera Error")
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + 
                               placeholder_img + b'\r\n')
                else:
                    # No frame available
                    placeholder_img = create_placeholder_image_with_message("No Signal")
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + 
                           placeholder_img + b'\r\n')
            else:
                # Camera not available
                placeholder_img = create_placeholder_image_with_message("Camera Offline")
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + 
                       placeholder_img + b'\r\n')
            
            await asyncio.sleep(1/15)  # 15 FPS for streaming
    
    async def generate_placeholder_stream(exhibit_name="Mock Exhibit"):
        """Generate placeholder stream for mock exhibits"""
        while True:
            placeholder_img = create_placeholder_image_with_message(f"{exhibit_name}\n(Mock Camera)")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   placeholder_img + b'\r\n')
            await asyncio.sleep(1/5)  # 5 FPS for placeholder
    
    # Use real camera for exhibit 1, placeholder for others
    if exhibit_id == REAL_DATA_EXHIBIT_ID:
        return StreamingResponse(
            generate_real_camera_stream(),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    else:
        # Get exhibit name for placeholder
        exhibit_name = f"Exhibit {exhibit_id}"
        try:
            with get_db() as conn:
                cursor = conn.execute("SELECT name FROM exhibits WHERE id = ?", (exhibit_id,))
                row = cursor.fetchone()
                if row:
                    exhibit_name = row["name"]
        except Exception:
            pass
            
        return StreamingResponse(
            generate_placeholder_stream(exhibit_name),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

@app.post("/exhibits")
async def create_exhibit(exhibit: Exhibit):
    """Create a new exhibit"""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                INSERT INTO exhibits (name, description, location, 
                                    temperature_min, temperature_max, 
                                    humidity_min, humidity_max, vibration_max)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                exhibit.name, exhibit.description, exhibit.location,
                exhibit.temperature_min, exhibit.temperature_max,
                exhibit.humidity_min, exhibit.humidity_max, exhibit.vibration_max
            ))
            conn.commit()
            
            # Get the created exhibit
            exhibit_id = cursor.lastrowid
            cursor = conn.execute('''
                SELECT id, name, description, location, 
                       temperature_min, temperature_max, 
                       humidity_min, humidity_max, vibration_max,
                       created_at, updated_at 
                FROM exhibits WHERE id = ?
            ''', (exhibit_id,))
            row = cursor.fetchone()
            
            created_exhibit = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "location": row["location"],
                "temperature_min": row["temperature_min"],
                "temperature_max": row["temperature_max"],
                "humidity_min": row["humidity_min"],
                "humidity_max": row["humidity_max"],
                "vibration_max": row["vibration_max"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
            
            logger.info(f"Created exhibit: {created_exhibit}")
            return created_exhibit
    except Exception as e:
        logger.error(f"Error creating exhibit: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create exhibit: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )