from fastapi import APIRouter
from .health import router as health_routes
from .yolo import router as yolo_routes
from .diffusion import router as diffusion_routes

api_router = APIRouter()

api_router.include_router(health_routes, tags=["system"])
api_router.include_router(yolo_routes, prefix="/yolo", tags=["object-detection"])
api_router.include_router(diffusion_routes, prefix="/diffusion", tags=["image-generation"])
