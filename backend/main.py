import asyncio
import io
import os
import random
import time
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional, List, Dict, Any

import httpx
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from ultralytics import YOLO

# Load environment variables
load_dotenv()

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ESP32_CAM_URL = os.getenv("ESP32_CAM_URL")
MOCK_SENSORS = os.getenv("MOCK_SENSORS", "true").lower() == "true"
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Initialize YOLO model (will download yolov8n.pt on first run)
yolo_model = None
try:
    yolo_model = YOLO('yolov8n.pt')
except Exception as e:
    print(f"Warning: Could not load YOLO model: {e}")

app = FastAPI(title="Museum Anomaly Dashboard API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_ORIGIN, 
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:5174", 
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SensorData(BaseModel):
    temperature_c: float
    humidity_pct: float
    vibration: float
    vibration_triggered: bool
    timestamp: str


class ChatRequest(BaseModel):
    question: str  # Changed from message to question to match requirement
    context: Optional[dict] = None


class AnomalyRequest(BaseModel):
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None  
    vibration: Optional[float] = None
    sensors: Optional[SensorData] = None


class VisionDetection(BaseModel):
    label: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]


class VisionResponse(BaseModel):
    detections: List[VisionDetection]
    anomaly_detected: bool
    status: str


# --- Utils ---

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_mock_sensors() -> SensorData:
    # Simulate fairly normal museum environment with occasional spikes
    base_temp = random.uniform(18.5, 23.5)
    base_humidity = random.uniform(35.0, 55.0)
    vib = max(0.0, random.gauss(0.02, 0.02))

    # Random anomaly spikes
    if random.random() < 0.07:
        base_temp += random.uniform(4, 8)  # sudden heat
    if random.random() < 0.06:
        base_humidity += random.uniform(15, 30)  # humidity spike
    if random.random() < 0.05:
        vib += random.uniform(0.3, 0.8)  # vibration spike

    return SensorData(
        temperature_c=round(base_temp, 2),
        humidity_pct=round(base_humidity, 2),
        vibration=round(vib, 3),
        vibration_triggered=vib > 0.25,
        timestamp=now_iso(),
    )


def basic_anomaly_rules(s: SensorData) -> dict:
    issues = []
    if s.temperature_c < 16 or s.temperature_c > 26:
        issues.append(
            {
                "type": "temperature",
                "severity": "high" if s.temperature_c > 30 or s.temperature_c < 12 else "medium",
                "message": f"Temperature out of range: {s.temperature_c}C (ideal 18-22C)",
            }
        )
    if s.humidity_pct < 35 or s.humidity_pct > 60:
        issues.append(
            {
                "type": "humidity",
                "severity": "high" if s.humidity_pct > 70 or s.humidity_pct < 25 else "medium",
                "message": f"Humidity out of range: {s.humidity_pct}% (ideal 40-55%)",
            }
        )
    if s.vibration_triggered or s.vibration > 0.25:
        issues.append(
            {
                "type": "vibration",
                "severity": "medium" if s.vibration < 0.6 else "high",
                "message": f"Vibration spike detected: {s.vibration}",
            }
        )
    return {
        "has_anomaly": len(issues) > 0,
        "issues": issues,
    }


# --- AI Helper Functions ---

async def call_openrouter_llama(messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
    """Call OpenRouter API with LLaMA 3 8B Instruct model"""
    if not OPENROUTER_API_KEY:
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"OpenRouter API error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return None


async def call_openai(messages, temperature=0.2) -> Optional[str]:
    """Legacy OpenAI function (kept for backward compatibility)"""
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}")
        return None


def process_yolo_detections(results) -> List[VisionDetection]:
    """Process YOLO results into VisionDetection objects"""
    detections = []
    
    if results and len(results) > 0:
        result = results[0]  # First result
        if result.boxes is not None:
            boxes = result.boxes
            for i in range(len(boxes)):
                # Get bounding box coordinates
                box = boxes.xyxy[i].cpu().numpy()  # x1, y1, x2, y2
                confidence = float(boxes.conf[i].cpu().numpy())
                class_id = int(boxes.cls[i].cpu().numpy())
                
                # Get class name
                class_name = result.names[class_id] if result.names else f"class_{class_id}"
                
                detection = VisionDetection(
                    label=class_name,
                    confidence=confidence,
                    bbox=box.tolist()
                )
                detections.append(detection)
    
    return detections


def detect_vision_anomaly(detections: List[VisionDetection]) -> bool:
    """Determine if vision detections indicate an anomaly"""
    # Define expected objects in a museum setting
    normal_objects = {
        'person', 'chair', 'book', 'vase', 'bottle', 'cup', 'bowl',
        'dining table', 'potted plant', 'couch', 'tv', 'laptop',
        'mouse', 'remote', 'keyboard', 'cell phone', 'clock',
        'scissors', 'teddy bear', 'hair drier', 'toothbrush'
    }
    
    # Check for unexpected objects or no objects at all
    if not detections:
        return False  # No detections might be normal for some exhibits
    
    # Check for anomalous objects
    for detection in detections:
        if detection.confidence > 0.5:  # Only consider confident detections
            if detection.label not in normal_objects:
                return True  # Unexpected object detected
    
    return False


# --- Routes ---
@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": now_iso()}


@app.get("/sensors/data", response_model=SensorData)
async def get_sensors_data():
    if MOCK_SENSORS:
        return generate_mock_sensors()
    # In real mode, you'd collect from actual sensors or a DB
    return generate_mock_sensors()


async def proxy_mjpeg_stream() -> AsyncGenerator[bytes, None]:
    # Proxy ESP32-CAM MJPEG stream if available
    if ESP32_CAM_URL:
        timeout = httpx.Timeout(10.0, read=None)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", ESP32_CAM_URL) as r:
                async for chunk in r.aiter_bytes():
                    yield chunk
    else:
        # Serve a simple repeating multipart stream from a placeholder image
        # This keeps the frontend <img> tag happy for the MVP
        boundary = "frame"
        placeholder_path = os.path.join(os.path.dirname(__file__), "static", "placeholder.jpg")
        if not os.path.exists(placeholder_path):
            # Generate a tiny blank image in-memory if file is missing
            jpeg_bytes = (
                b"\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c !$.'\x1c!\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xff\xd9"
            )
        else:
            with open(placeholder_path, "rb") as f:
                jpeg_bytes = f.read()

        while True:
            yield (
                b"--" + boundary.encode() + b"\r\n" +
                b"Content-Type: image/jpeg\r\n" +
                b"Content-Length: " + str(len(jpeg_bytes)).encode() + b"\r\n\r\n" +
                jpeg_bytes + b"\r\n"
            )
            await asyncio.sleep(0.5)


@app.get("/camera/stream")
async def camera_stream():
    if ESP32_CAM_URL:
        media_type = "multipart/x-mixed-replace; boundary=--"
    else:
        media_type = "multipart/x-mixed-replace; boundary=frame"
    return StreamingResponse(proxy_mjpeg_stream(), media_type=media_type)



# === NEW ROUTES WITH OPENROUTER LLAMA & YOLOV8N ===

@app.post("/chat")
async def chat_with_llama(req: ChatRequest):
    """Chat endpoint using OpenRouter LLaMA 3 8B Instruct"""
    user_question = req.question.strip()
    if not user_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a question."
        )
    
    # Try OpenRouter LLaMA first
    if OPENROUTER_API_KEY:
        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a helpful AI assistant for museum operations and preventive conservation. "
                    "Answer questions concisely and professionally. When applicable, reference environmental "
                    "tolerances for artifacts (temperature 18-22C, humidity 40-55%, minimal vibration)."
                )
            },
            {"role": "user", "content": user_question}
        ]
        
        reply = await call_openrouter_llama(messages, temperature=0.3)
        if reply:
            return {"reply": reply}
    
    # Fallback to OpenAI if OpenRouter fails
    if OPENAI_API_KEY:
        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a helpful AI assistant for museum operations and preventive conservation. "
                    "Answer questions concisely and professionally."
                )
            },
            {"role": "user", "content": user_question}
        ]
        reply = await call_openai(messages, temperature=0.3)
        if reply:
            return {"reply": reply}
    
    # Final fallback
    return {
        "reply": "I'm currently in demo mode. For museum operations, maintain temperature 18-22°C, "
                "humidity 40-55%, and minimize vibrations. How else can I assist you?"
    }


@app.post("/anomaly/check")
async def check_anomaly_with_llama(req: AnomalyRequest):
    """Anomaly detection using sensor data and LLaMA analysis"""
    
    # Get sensor data from request or generate mock data
    if req.sensors:
        sensors = req.sensors
    elif req.temperature_c is not None or req.humidity_pct is not None or req.vibration is not None:
        sensors = SensorData(
            temperature_c=req.temperature_c or 20.0,
            humidity_pct=req.humidity_pct or 45.0,
            vibration=req.vibration or 0.01,
            vibration_triggered=req.vibration > 0.25 if req.vibration else False,
            timestamp=now_iso()
        )
    else:
        sensors = generate_mock_sensors()
    
    # Run basic rule-based analysis
    rule_eval = basic_anomaly_rules(sensors)
    
    # Get AI analysis using OpenRouter LLaMA
    ai_explanation = None
    if OPENROUTER_API_KEY:
        prompt = (
            f"Analyze these museum environmental sensor readings and determine if there are any anomalies:\n"
            f"Temperature: {sensors.temperature_c}°C (ideal: 18-22°C)\n"
            f"Humidity: {sensors.humidity_pct}% (ideal: 40-55%)\n"
            f"Vibration: {sensors.vibration} (threshold: 0.25)\n\n"
            f"Rule-based issues found: {rule_eval['issues']}\n\n"
            f"Given these sensor readings, is there any anomaly? Explain briefly what actions museum staff should take."
        )
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert in preventive conservation for museums. Analyze environmental "
                    "sensor data and provide concise, actionable advice for museum staff."
                )
            },
            {"role": "user", "content": prompt}
        ]
        
        ai_explanation = await call_openrouter_llama(messages, temperature=0.2)
    
    # Fallback to OpenAI if OpenRouter fails
    if not ai_explanation and OPENAI_API_KEY:
        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a preventive conservation assistant for a museum. "
                    "Given environmental and vibration data, assess risk to artifacts and explain succinctly."
                )
            },
            {
                "role": "user", 
                "content": f"Sensor snapshot: temp={sensors.temperature_c}C, humidity={sensors.humidity_pct}%, vibration={sensors.vibration}. Issues: {rule_eval['issues']}"
            }
        ]
        ai_explanation = await call_openai(messages)
    
    # Prepare response
    result = {
        "sensors": sensors.model_dump(),
        "rule_based": rule_eval,
        "ai_explanation": ai_explanation or (
            "Based on thresholds: " + 
            ("no anomalies detected." if not rule_eval["has_anomaly"] 
             else "one or more anomalies detected. Consider checking HVAC and exhibit stability.")
        ),
        "timestamp": now_iso()
    }
    
    return JSONResponse(result)


@app.post("/vision/check", response_model=VisionResponse)
async def check_vision_anomaly(file: UploadFile = File(...)):
    """Vision anomaly detection using YOLOv8n"""
    
    if not yolo_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YOLO model not available. Please check server logs."
        )
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a valid image file."
        )
    
    try:
        # Read image data
        contents = await file.read()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Run YOLO detection
        results = yolo_model(image)
        
        # Process results
        detections = process_yolo_detections(results)
        
        # Determine if anomaly detected
        anomaly_detected = detect_vision_anomaly(detections)
        
        # Determine status
        if anomaly_detected:
            status_msg = "⚠️ Anomaly Detected"
        elif detections:
            status_msg = "✅ Normal"
        else:
            status_msg = "✅ Normal - No objects detected"
        
        return VisionResponse(
            detections=detections,
            anomaly_detected=anomaly_detected,
            status=status_msg
        )
        
    except Exception as e:
        print(f"Vision processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {str(e)}"
        )
    
    finally:
        # Clean up
        await file.close()

