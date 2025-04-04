from fastapi import BackgroundTasks
from app.models.manager import ModelManager
from app.services.queue import QueueService
from app.schemas.models import DiffusionRequest, DiffusionResponse

class DiffusionController:
    @classmethod
    async def generate(cls, background_tasks: BackgroundTasks, request: DiffusionRequest):
        queue_service = QueueService()
        task_id = await queue_service.enqueue_diffusion_task(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            guidance_scale=request.guidance_scale,
            steps=request.steps,
            seed=request.seed
        )
        
        background_tasks.add_task(ModelManager.process_diffusion_from_queue, task_id)
        
        return DiffusionResponse(
            task_id=task_id,
            status="processing",
            message="Image generation queued"
        )
    
    @classmethod
    async def get_result(cls, task_id: str):
        queue_service = QueueService()
        result = await queue_service.get_task_result(task_id)
        if result is None:
            return DiffusionResponse(
                task_id=task_id,
                status="processing",
                message="Still processing"
            )
        return result