import asyncio
import io
import os
import random
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional, List, Dict

import httpx
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

# Initialize YOLO model
yolo_model = None
try:
    yolo_model = YOLO('yolov8n.pt')
except Exception as e:
    print(f"Warning: Could not load YOLO model: {e}")

# FastAPI app
app = FastAPI(title="Museum Anomaly Dashboard API", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_ORIGIN,
        "https://museum-anomaly-detection.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------- MODELS ----------------------
class SensorData(BaseModel):
    temperature_c: float
    humidity_pct: float
    vibration: float
    vibration_triggered: bool
    timestamp: str

class ChatRequest(BaseModel):
    question: str
    context: Optional[dict] = None

class AnomalyRequest(BaseModel):
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    vibration: Optional[float] = None
    sensors: Optional[SensorData] = None

class VisionDetection(BaseModel):
    label: str
    confidence: float
    bbox: List[float]

class VisionResponse(BaseModel):
    detections: List[VisionDetection]
    anomaly_detected: bool
    status: str

# ---------------------- UTILS ----------------------
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def generate_mock_sensors() -> SensorData:
    base_temp = random.uniform(18.5, 23.5)
    base_humidity = random.uniform(35.0, 55.0)
    vib = max(0.0, random.gauss(0.02, 0.02))
    if random.random() < 0.07: base_temp += random.uniform(4, 8)
    if random.random() < 0.06: base_humidity += random.uniform(15, 30)
    if random.random() < 0.05: vib += random.uniform(0.3, 0.8)
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
        issues.append({"type": "temperature", "message": f"Temperature: {s.temperature_c}C"})
    if s.humidity_pct < 35 or s.humidity_pct > 60:
        issues.append({"type": "humidity", "message": f"Humidity: {s.humidity_pct}%"})
    if s.vibration_triggered or s.vibration > 0.25:
        issues.append({"type": "vibration", "message": f"Vibration spike: {s.vibration}"})
    return {"has_anomaly": len(issues) > 0, "issues": issues}

# ---------------------- AI HELPERS ----------------------
async def call_openrouter_llama(messages: List[Dict[str, str]], temperature: float = 0.2) -> Optional[str]:
    if not OPENROUTER_API_KEY:
        return None
    try:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "meta-llama/llama-3-8b-instruct",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=payload
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"OpenRouter error {response.status_code}: {response.text}")
                return None
    except Exception as e:
        print(f"OpenRouter exception: {e}")
        return None

async def call_openai(messages, temperature=0.2) -> Optional[str]:
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {e}")
        return None

# ---------------------- YOLO HELPERS ----------------------
def process_yolo_detections(results) -> List[VisionDetection]:
    detections = []
    if results and len(results) > 0:
        result = results[0]
        if result.boxes is not None:
            for i in range(len(result.boxes)):
                box = result.boxes.xyxy[i].cpu().numpy()
                confidence = float(result.boxes.conf[i].cpu().numpy())
                class_id = int(result.boxes.cls[i].cpu().numpy())
                class_name = result.names[class_id] if result.names else f"class_{class_id}"
                detections.append(VisionDetection(
                    label=class_name, confidence=confidence, bbox=box.tolist()
                ))
    return detections

def detect_vision_anomaly(detections: List[VisionDetection]) -> bool:
    normal_objects = {'person','chair','book','vase','bottle','cup','bowl',
        'dining table','potted plant','couch','tv','laptop','mouse','remote',
        'keyboard','cell phone','clock','scissors','teddy bear'}
    if not detections:
        return False
    for d in detections:
        if d.confidence > 0.5 and d.label not in normal_objects:
            return True
    return False

# ---------------------- CAMERA STREAM ----------------------
async def proxy_mjpeg_stream() -> AsyncGenerator[bytes, None]:
    if ESP32_CAM_URL:
        timeout = httpx.Timeout(10.0, read=None)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", ESP32_CAM_URL) as r:
                async for chunk in r.aiter_bytes():
                    yield chunk
    else:
        boundary = "frame"
        jpeg_bytes = b"\xff\xd8\xff\xd9"
        while True:
            yield (
                b"--" + boundary.encode() + b"\r\n" +
                b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
            )
            await asyncio.sleep(0.5)

# ---------------------- ROUTES ----------------------
@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"status": "Backend is running", "message": "Welcome to the Museum Anomaly Dashboard API"}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": now_iso()}

@app.get("/sensors/data", response_model=SensorData)
async def get_sensors_data():
    return generate_mock_sensors()

@app.get("/camera/stream")
async def camera_stream():
    media_type = "multipart/x-mixed-replace; boundary=frame"
    return StreamingResponse(proxy_mjpeg_stream(), media_type=media_type)

@app.post("/chat")
async def chat_with_llama(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Please provide a question.")

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant for museum operations."},
        {"role": "user", "content": req.question}
    ]

    try:
        reply = await call_openrouter_llama(messages)
        if reply:
            return {"reply": reply}
        else:
            print("OpenRouter returned None")
            return {"reply": "AI temporarily unavailable"}
    except Exception as e:
        print(f"OpenRouter exception: {e}")
        return {"reply": "AI temporarily unavailable"}


@app.post("/anomaly/check")
async def check_anomaly_with_llama(req: AnomalyRequest):
    sensors = req.sensors or generate_mock_sensors()
    rule_eval = basic_anomaly_rules(sensors)
    return {"sensors": sensors.model_dump(), "rule_based": rule_eval, "timestamp": now_iso()}

@app.post("/vision/check", response_model=VisionResponse)
async def check_vision_anomaly(file: UploadFile = File(...)):
    if not yolo_model:
        raise HTTPException(status_code=503, detail="YOLO model not loaded")
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert('RGB')
    results = yolo_model(image)
    detections = process_yolo_detections(results)
    anomaly = detect_vision_anomaly(detections)
    status_msg = "⚠️ Anomaly Detected" if anomaly else "✅ Normal"
    return VisionResponse(detections=detections, anomaly_detected=anomaly, status=status_msg)

# ---------------------- ENTRY POINT ----------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
