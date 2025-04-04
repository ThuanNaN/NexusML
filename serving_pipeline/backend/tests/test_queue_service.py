import pytest
import json
import base64
from io import BytesIO
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.queue import QueueService


class MockRedis:
    """Mock Redis for testing"""
    def __init__(self):
        self.data = {}
        self.expire_times = {}
        self.lists = {}
    
    async def set(self, key, value):
        self.data[key] = value
        return True
    
    async def get(self, key):
        return self.data.get(key)
    
    async def expire(self, key, seconds):
        self.expire_times[key] = seconds
        return True
    
    async def lpush(self, list_name, value):
        if list_name not in self.lists:
            self.lists[list_name] = []
        self.lists[list_name].append(value)
        return len(self.lists[list_name])


@pytest.fixture
def mock_redis():
    return MockRedis()


@pytest.fixture
async def queue_service(mock_redis):
    with patch('redis.asyncio.Redis', return_value=mock_redis):
        service = QueueService()
        await service._initialize()
        yield service


@pytest.mark.asyncio
async def test_enqueue_yolo_task(queue_service, mock_redis, test_image):
    """Test enqueueing a YOLO task"""
    task_id = await queue_service.enqueue_yolo_task(test_image, 0.5)
    
    # Check that task was stored in Redis
    task_key = f"task:{task_id}"
    assert task_key in mock_redis.data
    
    # Parse the JSON task data
    task_data = json.loads(mock_redis.data[task_key])
    assert task_data["type"] == "yolo"
    assert task_data["confidence"] == 0.5
    assert task_data["status"] == "pending"
    assert "image" in task_data  # Base64 image should be in the task
    
    # Check that task was added to the queue
    assert "queue:yolo" in mock_redis.lists
    assert task_id in mock_redis.lists["queue:yolo"]
    
    # Check expiration
    assert mock_redis.expire_times[task_key] == 3600  # 1 hour expiration


@pytest.mark.asyncio
async def test_enqueue_diffusion_task(queue_service, mock_redis):
    """Test enqueueing a diffusion task"""
    task_id = await queue_service.enqueue_diffusion_task(
        prompt="test prompt",
        negative_prompt="test negative",
        guidance_scale=7.5,
        steps=50,
        seed=42
    )
    
    # Check that task was stored in Redis
    task_key = f"task:{task_id}"
    assert task_key in mock_redis.data
    
    # Parse the JSON task data
    task_data = json.loads(mock_redis.data[task_key])
    assert task_data["type"] == "diffusion"
    assert task_data["prompt"] == "test prompt"
    assert task_data["negative_prompt"] == "test negative"
    assert task_data["guidance_scale"] == 7.5
    assert task_data["steps"] == 50
    assert task_data["seed"] == 42
    assert task_data["status"] == "pending"
    
    # Check that task was added to the queue
    assert "queue:diffusion" in mock_redis.lists
    assert task_id in mock_redis.lists["queue:diffusion"]


@pytest.mark.asyncio
async def test_get_task(queue_service, mock_redis):
    """Test retrieving a task"""
    # Set up a dummy task in Redis
    task_data = {
        "id": "test-id",
        "type": "yolo",
        "status": "pending"
    }
    await mock_redis.set("task:test-id", json.dumps(task_data))
    
    # Get the task
    task = await queue_service.get_task("test-id")
    
    assert task["id"] == "test-id"
    assert task["type"] == "yolo"
    assert task["status"] == "pending"
    
    # Test non-existent task
    task = await queue_service.get_task("nonexistent")
    assert task is None


@pytest.mark.asyncio
async def test_set_task_result(queue_service, mock_redis):
    """Test setting task results"""
    # Set up a dummy task in Redis
    task_data = {
        "id": "test-id",
        "type": "yolo",
        "status": "pending"
    }
    await mock_redis.set("task:test-id", json.dumps(task_data))
    
    # Set result
    result = {
        "detections": [{"class_id": 0, "class_name": "person", "confidence": 0.95}]
    }
    await queue_service.set_task_result("test-id", result)
    
    # Check that result was stored
    result_key = "result:test-id"
    assert result_key in mock_redis.data
    
    # Check that status was updated in the result
    stored_result = json.loads(mock_redis.data[result_key])
    assert stored_result["status"] == "success"
    assert "detections" in stored_result
    
    # Check that task status was updated
    updated_task = json.loads(mock_redis.data["task:test-id"])
    assert updated_task["status"] == "success"


@pytest.mark.asyncio
async def test_set_task_error(queue_service, mock_redis):
    """Test setting task errors"""
    # Set up a dummy task in Redis
    task_data = {
        "id": "test-id",
        "type": "yolo",
        "status": "pending"
    }
    await mock_redis.set("task:test-id", json.dumps(task_data))
    
    # Set error
    await queue_service.set_task_error("test-id", "Test error message")
    
    # Check that error was stored
    error_key = "result:test-id"
    assert error_key in mock_redis.data
    
    # Check error contents
    stored_error = json.loads(mock_redis.data[error_key])
    assert stored_error["status"] == "error"
    assert stored_error["message"] == "Test error message"
    
    # Check that task status was updated
    updated_task = json.loads(mock_redis.data["task:test-id"])
    assert updated_task["status"] == "error"
