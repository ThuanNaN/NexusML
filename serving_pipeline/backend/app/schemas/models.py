from pydantic import BaseModel, Field
from typing import List, Optional
import datetime

class HealthResponse(BaseModel):
    status: str
    models_ready: bool
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)


class DetectionObject(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x, y, width, height] normalized

class YoloDetectionRequest(BaseModel):
    image: str  # base64 encoded image
    confidence: float = 0.5

class YoloDetectionResponse(BaseModel):
    task_id: Optional[str] = None
    status: str  # "success", "processing", "error"
    message: Optional[str] = None
    detections: Optional[List[DetectionObject]] = None
    processing_time: Optional[float] = None  # in seconds
    base64_image: Optional[str] = None  # processed image with bounding boxes


class DiffusionRequest(BaseModel):
    prompt: str = "An astronaut riding a green horse"
    negative_prompt: Optional[str] = "ugly, blurry, poor quality"
    guidance_scale: float = Field(7.5, ge=1.0, le=20.0)
    steps: int = Field(50, ge=10, le=150)
    seed: Optional[int] = None

class DiffusionResponse(BaseModel):
    task_id: Optional[str] = None
    status: str  # "success", "processing", "error"
    message: Optional[str] = None
    base64_image: Optional[str] = None
    processing_time: Optional[float] = None  # in seconds
    prompt: Optional[str] = None
    seed: Optional[int] = None
