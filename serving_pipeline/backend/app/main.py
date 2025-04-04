import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import api_router
from app.models.manager import ModelManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ml-server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading ML models...")
    await ModelManager.initialize()
    logger.info("ML models loaded successfully!")
    yield
    logger.info("Shutting down, releasing resources...")
    await ModelManager.cleanup()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for serving YOLO and Stable Diffusion models",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
