import logging
import time
import torch
import base64
from io import BytesIO
from typing import Optional
from PIL import Image
import asyncio
from pathlib import Path
from app.schemas.models import (
    YoloDetectionResponse, 
    DetectionObject,
    DiffusionResponse,
)

logger = logging.getLogger("inference")

class YoloInference:
    _model = None
    _lock = asyncio.Lock()
    
    @classmethod
    async def initialize(cls, model_path: Path):
        async with cls._lock:
            if cls._model is not None:
                return
            
            try:
                # Import here to avoid loading dependencies until needed
                from ultralytics import YOLO
                
                cls._model = YOLO(model_path)
                logger.info(f"YOLO model loaded from {model_path}")
            except Exception as e:
                logger.error(f"Error loading YOLO model: {e}")
                raise
    
    @classmethod
    async def cleanup(cls):
        async with cls._lock:
            if cls._model is not None:
                del cls._model
                cls._model = None
                
                # Force CUDA cache clear if available
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
                logger.info("YOLO model resources released")
    
    @classmethod
    async def detect(cls, image_data: BytesIO, confidence: float = 0.5):
        if cls._model is None:
            raise RuntimeError("YOLO model not initialized. Call initialize() first.")
        
        start_time = time.time()
        
        # Load image
        image = Image.open(image_data)
        image.save("input.jpg")
        
        # Run inference
        results = cls._model(image, conf=confidence)
        result = results[0]  # Get first image result
        
        # Extract detections
        detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
            # Convert to [x, y, width, height] normalized format
            img_width, img_height = image.size
            x = x1 / img_width
            y = y1 / img_height
            width = (x2 - x1) / img_width
            height = (y2 - y1) / img_height
            
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())
            class_name = result.names[class_id]
            
            detections.append(DetectionObject(
                class_id=class_id,
                class_name=class_name,
                confidence=confidence,
                bbox=[x, y, width, height]
            ))
        
        # Get image with bounding boxes
        result_image = result.plot()[..., ::-1] # Convert BGR to RGB
        buffered = BytesIO()
        Image.fromarray(result_image).save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        processing_time = time.time() - start_time

        return YoloDetectionResponse(
            status="success",
            detections=detections,
            processing_time=processing_time,
            base64_image=base64_image
        )


class DiffusionInference:
    _pipeline = None
    _lock = asyncio.Lock()
    
    @classmethod
    async def initialize(cls, 
                         model_name: str = "segmind/SSD-1B",
                         slicing_attn: bool = False,
                         low_resource: bool = False):
        async with cls._lock:
            if cls._pipeline is not None:
                return
            
            # Only load if CUDA is available
            if torch.cuda.is_available():
                try:
                    from diffusers import StableDiffusionXLPipeline
                    
                    cls._pipeline = StableDiffusionXLPipeline.from_pretrained(
                        "segmind/SSD-1B",
                        torch_dtype=torch.float16,
                        use_safetensors=True
                    )
                    cls._pipeline = cls._pipeline.to("cuda")
                    if slicing_attn:
                        # Enable attention slicing for lower memory
                        cls._pipeline.enable_attention_slicing()
                    if low_resource:
                        # Enable CPU offloading for lower resource usage
                        cls._pipeline.enable_model_cpu_offload()
                    logger.info(f"Diffusion model loaded: {model_name}")
                except Exception as e:
                    logger.error(f"Error loading Diffusion model: {e}")
                    raise
            else:
                logger.warning("CUDA not available, Diffusion model not loaded")
    
    @classmethod
    async def cleanup(cls):
        async with cls._lock:
            if cls._pipeline is not None:
                del cls._pipeline
                cls._pipeline = None
                
                # Force CUDA cache clear if available
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
                logger.info("Diffusion model resources released")
    
    @classmethod
    async def generate(cls, 
                        prompt: str, 
                        negative_prompt: Optional[str] = None,
                        guidance_scale: float = 7.5,
                        steps: int = 50,
                        seed: Optional[int] = None):
        if cls._pipeline is None:
            raise RuntimeError("Diffusion model not initialized or not available")
        
        start_time = time.time()
        
        # Set seed for reproducibility
        generator = None
        if seed is not None:
            generator = torch.Generator(device="cpu").manual_seed(seed)
        else:
            # Use random seed and record it
            seed = torch.randint(0, 2**32 - 1, (1,)).item()
            generator = torch.Generator(device="cpu").manual_seed(seed)

        # Generate image
        with torch.inference_mode():
            result = cls._pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                guidance_scale=guidance_scale,
                num_inference_steps=steps,
                generator=generator
            )
        
        # Convert to base64
        image = result.images[0]
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        processing_time = time.time() - start_time
        
        return DiffusionResponse(
            status="success",
            base64_image=base64_image,
            processing_time=processing_time,
            prompt=prompt,
            seed=seed
        )