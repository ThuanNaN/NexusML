# NexusML Gradio Frontend

This is a Gradio-based web interface for the NexusML Serving Pipeline. It provides user-friendly interfaces for using YOLOv8 object detection and Stable Diffusion image generation models.

## Features

- YOLOv8 object detection interface with confidence control
- Stable Diffusion image generation with prompt, negative prompt, and parameter settings
- Real-time feedback on model inference status
- Responsive UI that works on desktop and mobile

## Setup

1. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

2. Configure environment variables:

    ```bash
    cp .env.example .env
    ```

    Edit the `.env` file to set your backend API URL and API key.

3. Run the application:

    ```bash
    python run.py
    ```

The interface will be available at `http://localhost:7860`

## Usage

### Object Detection

1. Upload an image using the file uploader or drag-and-drop
2. Adjust the confidence threshold slider if needed
3. Click "Detect Objects"
4. View the results with bounding boxes around detected objects

### Image Generation

1. Enter a text prompt describing the image you want to generate
2. Optionally enter a negative prompt to specify what to avoid
3. Adjust generation parameters if needed
4. Click "Generate Image"
5. Wait for the generation process to complete

## Connection to Backend

This frontend connects to the NexusML backend API. Make sure the backend is running and properly configured in the `.env` file.
