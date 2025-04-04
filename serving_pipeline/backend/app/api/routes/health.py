from fastapi import APIRouter
from app.api.controllers import HealthController
from app.schemas.models import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return await HealthController.check_health()
