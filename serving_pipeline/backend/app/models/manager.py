import logging
import asyncio
from app.core.config import settings
from app.models.inference import YoloInference, DiffusionInference

logger = logging.getLogger("model-manager")

class ModelManager:
    _models_ready = False
    _lock = asyncio.Lock()

    @classmethod
    async def initialize(cls):
        async with cls._lock:
            if cls._models_ready:
                return
            
            try:
                await YoloInference.initialize(settings.MODELS_DIR / settings.YOLO_MODEL_PATH)
                await DiffusionInference.initialize(settings.DIFFUSION_MODEL_NAME)
                
                cls._models_ready = True
                logger.info("All models initialized successfully")
            except Exception as e:
                logger.error(f"Error loading models: {e}")
                raise

    @classmethod
    async def cleanup(cls):
        async with cls._lock:
            try:
                await YoloInference.cleanup()
                await DiffusionInference.cleanup()
                
                cls._models_ready = False
                logger.info("Model resources released")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

    @classmethod
    def are_models_ready(cls):
        return cls._models_ready


    @classmethod
    async def process_yolo_from_queue(cls, task_id: str):
        from app.services.queue import QueueService
        queue = QueueService()

        try:
            task = await queue.get_task(task_id)
            if task is None:
                logger.error(f"Task {task_id} not found in queue")
                return
            
            # Process based on task type
            if task.get("type") == "yolo":
                import base64
                from io import BytesIO
                
                image_data = BytesIO(base64.b64decode(task["image"]))
                confidence = task.get("confidence", 0.5)
                
                result = await YoloInference.detect(image_data, confidence)
                await queue.set_task_result(task_id, result)
            else:
                logger.error(f"Unknown task type: {task.get('type')}")
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            await queue.set_task_error(task_id, str(e))


    @classmethod
    async def process_diffusion_from_queue(cls, task_id: str):
        from app.services.queue import QueueService
        queue = QueueService()

        try:
            task = await queue.get_task(task_id)
            if task is None:
                logger.error(f"Task {task_id} not found in queue")
                return
            
            # Process diffusion task
            if task.get("type") == "diffusion":

                result = await DiffusionInference.generate(
                    prompt=task["prompt"],
                    negative_prompt=task.get("negative_prompt"),
                    guidance_scale=task.get("guidance_scale", 7.5),
                    steps=task.get("steps", 50),
                    seed=task.get("seed")
                )
                await queue.set_task_result(task_id, result)
            else:
                logger.error(f"Unknown task type: {task.get('type')}")
        except Exception as e:
            logger.error(f"Error processing diffusion task {task_id}: {e}")
            await queue.set_task_error(task_id, str(e))
