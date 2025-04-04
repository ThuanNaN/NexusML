from fastapi import APIRouter, BackgroundTasks, Depends
from app.api.controllers import DiffusionController
from app.core.security import verify_api_key
from app.schemas.models import DiffusionRequest, DiffusionResponse

router = APIRouter()

@router.post("/generate", response_model=DiffusionResponse)
async def generate_image(
    request: DiffusionRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_api_key)
):
    return await DiffusionController.generate(background_tasks, request)


@router.get("/result/{task_id}", response_model=DiffusionResponse)
async def get_generation_result(
    task_id: str,
    _: bool = Depends(verify_api_key)
):
    return await DiffusionController.get_result(task_id)
