import io
from PIL import Image
from fastapi import HTTPException, BackgroundTasks, UploadFile
from app.models.manager import ModelManager
from app.services.queue import QueueService
from app.models.inference import YoloInference
from app.schemas.models import YoloDetectionResponse

class YoloController:
    @classmethod
    async def detect(cls, background_tasks: BackgroundTasks, file: UploadFile, confidence: float):
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        contents = await file.read()
        image = io.BytesIO(contents)
        
        # Process immediately for small files
        if len(contents) < 1 * 1024 * 1024:  # Less than 1MB
            result = await YoloInference.detect(image, confidence)
            return result
        
        # Queue larger files
        queue_service = QueueService()
        task_id = await queue_service.enqueue_yolo_task(image, confidence)
        background_tasks.add_task(ModelManager.process_yolo_from_queue, task_id)
        
        return YoloDetectionResponse(
            task_id=task_id,
            status="processing",
            message="Image queued for processing"
        )
    
    @classmethod
    async def get_result(cls, task_id: str):
        queue_service = QueueService()
        result = await queue_service.get_task_result(task_id)
        if result is None:
            return YoloDetectionResponse(
                task_id=task_id,
                status="processing",
                message="Still processing"
            )
        return result
