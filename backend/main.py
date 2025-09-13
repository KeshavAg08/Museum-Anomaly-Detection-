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
    # Add some sample exhibits if none exist
    with get_db() as conn:
        cursor = conn.execute("SELECT COUNT(*) as count FROM exhibits")
        count = cursor.fetchone()['count']
        if count == 0:
            sample_exhibits = [
                ("Ancient Vase", "2000-year-old ceramic vase from Roman period", "Gallery A", 20.0, 22.0, 45.0, 55.0, 0.3),
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

# Database functions
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
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mock_mode": MOCK_SENSORS,
        "database": "connected"
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
    if MOCK_SENSORS:
        data = generate_mock_sensor_data()
    else:
        # TODO: Implement real sensor data collection
        data = generate_mock_sensor_data()
    
    return data

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
    async def generate_stream():
        placeholder_img = create_placeholder_image()
        
        while True:
            # Create MJPEG frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   placeholder_img + b'\r\n')
            await asyncio.sleep(0.1)  # 10 FPS
    
    return StreamingResponse(
        generate_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )