import gradio as gr
import requests
import time
import os
from PIL import Image
import io
import base64
from dotenv import load_dotenv
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
API_KEY = os.getenv("API_KEY", "AIO2024")

HEADERS = {
    "X-API-Key": API_KEY
}

def run_yolo_detection(image, confidence=0.5):
    """Send image to YOLOv8 detection API and return results"""
    if image is None:
        return None, "No image provided"
    
    # Convert to bytes for sending
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # Send to detection API
    files = {
        'file': ('image.jpg', img_byte_arr, 'image/jpeg')
    }
    params = {
        'confidence': confidence
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/yolo/detect",
            headers=HEADERS,
            files=files,
            params=params
        )
        response.raise_for_status()
        result = response.json()

        # If task is still processing, poll for results
        if result.get("status") == "processing":
            task_id = result.get("task_id")
            for _ in range(30):  # Poll for up to 30 seconds
                time.sleep(1)
                result_response = requests.get(
                    f"{API_BASE_URL}/yolo/result/{task_id}",
                    headers=HEADERS
                )
                result = result_response.json()
                if result.get("status") != "processing":
                    break

        # Process results to display them on the image
        if result.get("status") == "success":
            base64_image = result.get("base64_image")
            if base64_image is None:
                return image, "No detections found"
            img_data = base64.b64decode(base64_image)
            result_image = Image.open(io.BytesIO(img_data))
            return result_image, f"Found {len(result.get('detections', []))} objects"
        else:
            return image, f"Error: {result.get('message', 'Unknown error')}"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return image, f"Error: {str(e)}"


def generate_image(prompt, negative_prompt="", guidance_scale=7.5, steps=50, seed=None):
    """Send text prompt to Stable Diffusion API and return generated image"""
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "guidance_scale": float(guidance_scale),
        "steps": int(steps)
    }
    
    if seed is not None and seed != "":
        payload["seed"] = int(seed)
    
    try:
        # Call the generation API
        response = requests.post(
            f"{API_BASE_URL}/diffusion/generate",
            headers={**HEADERS, "Content-Type": "application/json"},
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        
        # If task is still processing, poll for results
        if result.get("status") == "processing":
            task_id = result.get("task_id")
            for _ in range(60):  # Poll for up to 60 seconds (diffusion can take longer)
                time.sleep(1)
                result_response = requests.get(
                    f"{API_BASE_URL}/diffusion/result/{task_id}",
                    headers=HEADERS
                )
                result = result_response.json()
                if result.get("status") != "processing":
                    break
        
        # Process the results
        if result.get("status") == "success":
            base64_image = result.get("base64_image")
            img_data = base64.b64decode(base64_image)
            generated_image = Image.open(io.BytesIO(img_data))
            return generated_image, ""
        else:
            return None, f"Error: {result.get('message', 'Unknown error')}"
    
    except Exception as e:
        return None, f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="NexusML Model Serving") as demo:
    gr.Markdown("# NexusML Model Serving")
    
    with gr.Tab("YOLOv8 Object Detection"):
        with gr.Row():
            with gr.Column():
                yolo_input = gr.Image(type="pil", label="Upload Image")
                yolo_confidence = gr.Slider(
                    minimum=0.1, maximum=1.0, value=0.5, step=0.05,
                    label="Confidence Threshold"
                )
                yolo_button = gr.Button("Detect Objects")
            
            with gr.Column():
                yolo_output = gr.Image(type="pil", label="Detection Results")
                yolo_message = gr.Textbox(label="Status", interactive=False)
    
    with gr.Tab("Stable Diffusion Image Generation"):
        with gr.Row():
            with gr.Column():
                sd_prompt = gr.Textbox(label="Prompt", lines=3, value="A fantasy landscape with mountains and rivers")
                sd_negative_prompt = gr.Textbox(label="Negative Prompt", lines=2, value="ugly, blurry, poor quality")
                
                with gr.Row():
                    sd_guidance = gr.Slider(
                        minimum=1.0, maximum=20.0, value=7.5, step=0.5,
                        label="Guidance Scale"
                    )
                    sd_steps = gr.Slider(
                        minimum=20, maximum=150, value=50, step=1,
                        label="Steps"
                    )
                
                sd_seed = gr.Textbox(label="Seed (optional)", placeholder="Random if empty")
                sd_button = gr.Button("Generate Image")
            
            with gr.Column():
                sd_output = gr.Image(type="pil", label="Generated Image")
                sd_message = gr.Textbox(label="Status", interactive=False)
    
    # Connect buttons to functions
    yolo_button.click(
        run_yolo_detection,
        inputs=[yolo_input, yolo_confidence],
        outputs=[yolo_output, yolo_message]
    )
    
    sd_button.click(
        generate_image,
        inputs=[sd_prompt, sd_negative_prompt, sd_guidance, sd_steps, sd_seed],
        outputs=[sd_output, sd_message]
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=7860)
