import pytest
import json
from unittest.mock import patch, AsyncMock
from app.schemas.models import DiffusionResponse


def test_diffusion_generate_endpoint_unauthorized(test_client):
    """Test that the endpoint requires authentication when API keys are enabled"""
    with patch('app.core.config.settings.API_KEYS', ["test_key"]):
        request_data = {
            "prompt": "test prompt",
            "negative_prompt": "test negative",
            "guidance_scale": 7.5,
            "steps": 50
        }
        response = test_client.post("/api/diffusion/generate", json=request_data)
        assert response.status_code == 401
        assert "Invalid API Key" in response.json()["detail"]


def test_diffusion_generate_endpoint(test_client, mock_queue_service):
    """Test the diffusion generation endpoint"""
    request_data = {
        "prompt": "test prompt",
        "negative_prompt": "test negative",
        "guidance_scale": 7.5,
        "steps": 50,
        "seed": 42
    }
    
    with patch('app.core.config.settings.API_KEYS', []):
        response = test_client.post("/api/diffusion/generate", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["task_id"] == "test-task-id"
        assert "queued" in data["message"].lower()
        
        # Verify the queue service was called with correct parameters
        mock_queue_service.enqueue_diffusion_task.assert_called_once_with(
            prompt="test prompt",
            negative_prompt="test negative",
            guidance_scale=7.5,
            steps=50,
            seed=42
        )


def test_diffusion_get_result_processing(test_client, mock_queue_service):
    """Test getting a result that's still processing"""
    mock_queue_service.get_task_result.return_value = None
    
    with patch('app.core.config.settings.API_KEYS', []):
        response = test_client.get("/api/diffusion/result/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["task_id"] == "test-task-id"
        assert "still processing" in data["message"].lower()


def test_diffusion_get_result_completed(test_client, mock_queue_service, base64_image):
    """Test getting a completed diffusion generation result"""
    # Create a mock completed result
    mock_result = {
        "status": "success",
        "prompt": "test prompt",
        "base64_image": base64_image,
        "processing_time": 2.5,
        "seed": 42
    }
    mock_queue_service.get_task_result.return_value = mock_result
    
    with patch('app.core.config.settings.API_KEYS', []):
        response = test_client.get("/api/diffusion/result/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["prompt"] == "test prompt"
        assert data["base64_image"] == base64_image
        assert data["seed"] == 42
