# NexusML Serving Pipeline

A high-performance machine learning model serving platform designed to efficiently handle multiple AI models including YOLOv8 for object detection and various diffusion models (Stable Diffusion) for image generation.

## Requirements

- Python 3.12.9
- Redis server
- CUDA-compatible GPU for model inference

## Project Structure

The serving pipeline is organized as a FastAPI backend application with the following components:

- **API Routes**: RESTful endpoints for model inference
- **Worker Queue**: Redis-based queue for model inference tasks
- **Models**: Support for various ML models including YOLOv8 and diffusion models

## Configuration

The system is configured through environment variables and the `config.py` file. Key configurations include:

- Model paths and settings
- Redis connection details
- API security settings
- Performance parameters

## Setup

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Environment configuration**:
   Create a `.env` file in the project root with the following variables:

   ```env
   DEBUG=False
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

3. **Download models**:
   Place your models in the `models` directory as configured in `config.py`.

## Usage

### Starting the server

```bash
uvicorn app.main:app --reload
```

### API Endpoints

- `/api/detect` - YOLOv8 object detection
- `/api/generate` - Stable Diffusion image generation

### Example Requests

#### Object Detection

```bash
curl -X POST "http://localhost:8000/api/detect" \
  -H "X-API-Key: your_api_key" \
  -F "image=@path/to/your/image.jpg"
```

#### Image Generation

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a garden of coconut trees in the southeast of Vietnam", "negative_prompt": "ugly, blurry, poor quality"}'
```

## Performance Optimization

The system is optimized for batch processing with the following parameters in `config.py`:

- `WORKERS_PER_MODEL`: 2 workers per model
- `BATCH_SIZE`: 4 samples per batch
- `MODEL_TIMEOUT`: 30 seconds timeout for model inference

## Security

API access is secured using API keys. Configure your keys in the `.env` file or through the `config.py` settings.

## Supported Models

1. YOLOv8 for object detection
2. Stable Diffusion models:
   - Stable Diffusion XL (SSD-1B)

## Testing

Pytest is used for unit testing. Run the tests with:

```bash
pip install -r requirements-dev.txt

# Run the tests
pytest

# For coverage report
coverage run -m pytest
coverage report
coverage html  # Generates HTML report
```

Serve test coverage report with:

```bash
python -m http.server --directory htmlcov
```
