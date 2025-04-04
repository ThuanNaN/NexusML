from fastapi import APIRouter, BackgroundTasks, File, UploadFile, Form, Depends
from app.api.controllers import YoloController
from app.core.security import verify_api_key
from app.schemas.models import YoloDetectionResponse

router = APIRouter()

@router.post("/detect", response_model=YoloDetectionResponse)
async def detect_objects(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    confidence: float = Form(0.5),
    _: bool = Depends(verify_api_key)
):
    return await YoloController.detect(background_tasks, file, confidence)

@router.get("/result/{task_id}", response_model=YoloDetectionResponse)
async def get_detection_result(
    task_id: str,
    _: bool = Depends(verify_api_key)
):
    return await YoloController.get_result(task_id)
