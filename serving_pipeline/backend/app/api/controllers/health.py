from app.models.manager import ModelManager
from app.schemas.models import HealthResponse

class HealthController:
    @classmethod
    async def check_health(cls):
        models_ready = ModelManager.are_models_ready()
        return HealthResponse(
            status="healthy" if models_ready else "starting",
            models_ready=models_ready
        )