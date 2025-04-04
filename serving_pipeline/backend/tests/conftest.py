import pytest
import asyncio
import base64
from io import BytesIO
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
import numpy as np

from app.main import app
from app.models.manager import ModelManager
from app.services.queue import QueueService


@pytest.fixture
def test_client():
    # Patch the model manager to avoid loading actual models during tests
    with patch.object(ModelManager, 'are_models_ready', return_value=True), \
         patch.object(ModelManager, 'initialize', AsyncMock()):
        with TestClient(app) as client:
            yield client


@pytest.fixture
def mock_queue_service():
    with patch('app.services.queue.QueueService') as MockQueueService:
        instance = MockQueueService.return_value
        instance._initialize = AsyncMock()
        instance.enqueue_yolo_task = AsyncMock(return_value="test-task-id")
        instance.enqueue_diffusion_task = AsyncMock(return_value="test-task-id")
        instance.get_task = AsyncMock()
        instance.get_task_result = AsyncMock()
        instance.set_task_result = AsyncMock()
        instance.set_task_error = AsyncMock()
        yield instance


@pytest.fixture
def mock_yolo_inference():
    with patch('app.models.inference.YoloInference') as MockYoloInference:
        MockYoloInference.detect = AsyncMock()
        yield MockYoloInference


@pytest.fixture
def mock_diffusion_inference():
    with patch('app.models.inference.DiffusionInference') as MockDiffusionInference:
        MockDiffusionInference.generate = AsyncMock()
        yield MockDiffusionInference


@pytest.fixture
def test_image():
    # Create a simple test image (100x100 white image with a black rectangle)
    img = Image.new('RGB', (100, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (80, 80)], fill='black')
    
    # Convert to bytes
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr


@pytest.fixture
def base64_image():
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (80, 80)], fill='black')
    
    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
