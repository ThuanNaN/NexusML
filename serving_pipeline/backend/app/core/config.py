from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "ML Model Server"
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Model paths
    MODELS_DIR: Path = Path("model_ckpts")
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    DIFFUSION_MODEL_NAME: str = "segmind/SSD-1B"
    
    # Redis for queue
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # Performance
    WORKERS_PER_MODEL: int = 2
    BATCH_SIZE: int = 4
    MODEL_TIMEOUT: int = 30  # seconds
    
    # Security
    API_KEY_HEADER: str = "X-API-Key"
    API_KEYS: List[str] = ["AIO2024"]
    
    class Config:
        env_file = ".env"

settings = Settings()