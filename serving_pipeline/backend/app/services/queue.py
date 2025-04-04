import json
import uuid
import logging
from typing import Dict, Any, Optional
import redis.asyncio as redis
import base64
from io import BytesIO
from app.core.config import settings

logger = logging.getLogger("queue-service")

class QueueService:
    _redis = None
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QueueService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    async def _initialize(self):
        if not self._initialized:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
            self._initialized = True
    

    async def enqueue_yolo_task(self, image_data: BytesIO, confidence: float) -> str:
        await self._initialize()
        
        task_id = str(uuid.uuid4())
        
        # Convert image to base64 for storage
        base64_image = base64.b64encode(image_data.getvalue()).decode("utf-8")
        
        task = {
            "id": task_id,
            "type": "yolo",
            "image": base64_image,
            "confidence": confidence,
            "status": "pending"
        }
        
        # Store task in Redis
        await self._redis.set(f"task:{task_id}", json.dumps(task))
        await self._redis.expire(f"task:{task_id}", 3600)  # Expire after 1 hour
        
        # Add to processing queue
        await self._redis.lpush("queue:yolo", task_id)
        
        logger.info(f"Enqueued YOLO task: {task_id}")
        return task_id


    async def enqueue_diffusion_task(
        self, 
        prompt: str, 
        negative_prompt: Optional[str] = None,
        guidance_scale: float = 7.5,
        steps: int = 50,
        seed: Optional[int] = None
    ) -> str:
        await self._initialize()
        
        task_id = str(uuid.uuid4())
        
        task = {
            "id": task_id,
            "type": "diffusion",
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "guidance_scale": guidance_scale,
            "steps": steps,
            "seed": seed,
            "status": "pending"
        }
        
        # Store task in Redis
        await self._redis.set(f"task:{task_id}", json.dumps(task))
        await self._redis.expire(f"task:{task_id}", 3600)  # Expire after 1 hour
        
        # Add to processing queue
        await self._redis.lpush("queue:diffusion", task_id)
        
        logger.info(f"Enqueued diffusion task: {task_id}")
        return task_id
    

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        await self._initialize()
        
        task_json = await self._redis.get(f"task:{task_id}")
        if not task_json:
            return None
        
        return json.loads(task_json)
    

    async def set_task_result(self, task_id: str, result: Any) -> None:
        await self._initialize()
        
        # Convert result to dict if it's a Pydantic model
        if hasattr(result, "dict"):
            result_dict = result.dict()
        else:
            result_dict = result
        
        # Update the result
        result_dict["status"] = "success"
        
        # Save to Redis
        await self._redis.set(f"result:{task_id}", json.dumps(result_dict))
        await self._redis.expire(f"result:{task_id}", 3600)  # Expire after 1 hour
        
        # Update task status
        task = await self.get_task(task_id)
        if task:
            task["status"] = "success"
            await self._redis.set(f"task:{task_id}", json.dumps(task))
        
        logger.info(f"Task {task_id} completed")
    

    async def set_task_error(self, task_id: str, error_message: str) -> None:
        await self._initialize()
        
        error_result = {
            "status": "error",
            "message": error_message
        }
        
        # Save to Redis
        await self._redis.set(f"result:{task_id}", json.dumps(error_result))
        await self._redis.expire(f"result:{task_id}", 3600)  # Expire after 1 hour
        
        # Update task status
        task = await self.get_task(task_id)
        if task:
            task["status"] = "error"
            await self._redis.set(f"task:{task_id}", json.dumps(task))
        
        logger.error(f"Task {task_id} failed: {error_message}")
    
    
    async def get_task_result(self, task_id: str) -> Optional[Any]:
        await self._initialize()
        
        result_json = await self._redis.get(f"result:{task_id}")
        if not result_json:
            # Check if the task exists but hasn't completed
            task = await self.get_task(task_id)
            if task:
                return None  # Task exists but still processing
            return None  # Task doesn't exist
        
        return json.loads(result_json)
    