import pytest
import json
import base64
from unittest.mock import patch, AsyncMock
from app.schemas.models import YoloDetectionResponse, DetectionObject


def test_yolo_detect_endpoint_unauthorized(test_client):
    """Test that the endpoint requires authentication when API keys are enabled"""
    with patch('app.core.config.settings.API_KEYS', ["test_key"]):
        response = test_client.post("/api/yolo/detect", files={"file": ("test.jpg", b"test", "image/jpeg")})
        assert response.status_code == 401
        assert "Invalid API Key" in response.json()["detail"]


def test_yolo_detect_endpoint_small_file(test_client, test_image, mock_yolo_inference):
    """Test immediate processing for small files"""
    # Mock the YOLO inference response
    mock_result = YoloDetectionResponse(
        status="success",
        detections=[
            DetectionObject(class_id=0, class_name="person", confidence=0.95, bbox=[0.1, 0.2, 0.3, 0.4])
        ],
        processing_time=0.5,
        base64_image="test_base64"
    )
    mock_yolo_inference.detect.return_value = mock_result
    
    # Mock the file size to be small
    with patch('fastapi.UploadFile.read', return_value=b"small_content"), \
         patch('app.core.config.settings.API_KEYS', []):
        response = test_client.post(
            "/api/yolo/detect", 
            files={"file": ("test.jpg", test_image, "image/jpeg")},
            data={"confidence": 0.5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["detections"]) == 1
        assert data["detections"][0]["class_name"] == "person"


def test_yolo_detect_endpoint_large_file(test_client, test_image, mock_queue_service):
    """Test queuing for large files"""
    # Configure mock to return large content
    large_content = b"x" * (1024 * 1024 + 1)  # Just over 1MB
    
    with patch('fastapi.UploadFile.read', return_value=large_content), \
         patch('app.core.config.settings.API_KEYS', []):
        
        response = test_client.post(
            "/api/yolo/detect", 
            files={"file": ("test.jpg", test_image, "image/jpeg")},
            data={"confidence": 0.5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["task_id"] == "test-task-id"
        assert "queued for processing" in data["message"].lower()


def test_yolo_get_result_processing(test_client, mock_queue_service):
    """Test getting a result that's still processing"""
    mock_queue_service.get_task_result.return_value = None
    
    with patch('app.core.config.settings.API_KEYS', []):
        response = test_client.get("/api/yolo/result/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["task_id"] == "test-task-id"
        assert "still processing" in data["message"].lower()


def test_yolo_get_result_completed(test_client, mock_queue_service, base64_image):
    """Test getting a completed YOLO detection result"""
    # Create a mock completed result
    mock_result = {
        "status": "success",
        "detections": [
            {"class_id": 0, "class_name": "person", "confidence": 0.95, "bbox": [0.1, 0.2, 0.3, 0.4]}
        ],
        "processing_time": 0.5,
        "base64_image": base64_image
    }
    mock_queue_service.get_task_result.return_value = mock_result
    
    with patch('app.core.config.settings.API_KEYS', []):
        response = test_client.get("/api/yolo/result/test-task-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["detections"]) == 1
        assert data["detections"][0]["class_name"] == "person"
        assert data["base64_image"] == base64_image
