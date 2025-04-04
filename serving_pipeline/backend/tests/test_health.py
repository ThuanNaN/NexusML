import pytest
from unittest.mock import patch
from app.models.manager import ModelManager


def test_health_check_endpoint(test_client):
    # Test when models are ready
    with patch.object(ModelManager, 'are_models_ready', return_value=True):
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["models_ready"] == True
        assert "timestamp" in data

    # Test when models are not ready
    with patch.object(ModelManager, 'are_models_ready', return_value=False):
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "starting"
        assert data["models_ready"] == False
