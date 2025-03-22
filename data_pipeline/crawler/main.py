import schedule
import time
from datetime import datetime
import os
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import json
from crawler.url_crawler import urls_to_txts
from crawler.image_crawler import get_image_from_txts
from PIL import Image
import logging
import io
import base64
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

# Maximum recommended message size (Kafka default is 1MB)
MAX_MESSAGE_SIZE = 900000  # Slightly under 1MB to be safe

def create_kafka_producer():
    """Create and return a Kafka producer with retry logic."""
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                max_request_size=MAX_MESSAGE_SIZE,  # Set maximum request size
                retries=3,  # Automatically retry sending on failure
                acks='all'  # Wait for all replicas to acknowledge the message
            )
            logger.info("Successfully connected to Kafka broker")
            return producer
        except NoBrokersAvailable:
            retry_count += 1
            wait_time = 5 * retry_count
            logger.warning(f"Could not connect to Kafka broker. Retry {retry_count}/{max_retries} in {wait_time} seconds...")
            time.sleep(wait_time)
    
    logger.error("Failed to connect to Kafka broker after multiple attempts. Ensure Kafka is running.")
    return None

# Initialize producer
producer = create_kafka_producer()
if not producer:
    logger.error("Could not initialize Kafka producer. Exiting.")
    exit(1)

def prepare_image_for_kafka(image, max_size=(1024, 1024), quality=85):
    """
    Prepare an image for Kafka by resizing if necessary and converting to bytes.
    Returns the image bytes and dimensions.
    """
    # Make a copy to prevent modifying the original
    img = image.copy()
    
    # Convert to RGB if not already
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize if the image is too large
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.LANCZOS)
        logger.info(f"Resized image to {img.width}x{img.height}")
    
    # Convert to JPEG bytes with specified quality
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    img_bytes = buffer.getvalue()
    
    # If still too large, reduce quality until it fits
    current_quality = quality
    while len(img_bytes) > MAX_MESSAGE_SIZE and current_quality > 50:
        current_quality -= 10
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=current_quality)
        img_bytes = buffer.getvalue()
        logger.info(f"Reduced image quality to {current_quality} to fit size limit")
    
    return img_bytes, (img.width, img.height)

def send_to_kafka(image_url, image_path, image):
    """Send image and metadata to Kafka."""
    if not producer:
        logger.error("Kafka producer not available")
        return False
    
    try:
        # Prepare image
        img_bytes, img_size = prepare_image_for_kafka(image)
        
        # Check if the image is still too large
        if len(img_bytes) > MAX_MESSAGE_SIZE:
            logger.warning(f"Image {image_path} is too large ({len(img_bytes)} bytes), skipping")
            return False
            
        # Base64 encode the bytes (more reliable than hex for binary data)
        img_b64 = base64.b64encode(img_bytes).decode('ascii')
        
        # Prepare metadata
        metadata = {
            'image_url': image_url,
            'image_id': os.path.basename(image_path),
            'size': {
                'width': img_size[0],
                'height': img_size[1]
            },
            'format': 'JPEG',
            'processed_at': datetime.now().isoformat()
        }

        # Create the message
        message = {
            'metadata': metadata,
            'image_data': img_b64
        }
        
        # Log data size
        msg_size = len(json.dumps(message).encode('utf-8'))
        logger.info(f"Sending image {metadata['image_id']} (size: {msg_size} bytes)")

        # Send to Kafka
        future = producer.send(KAFKA_TOPIC, value=message)
        
        # Wait for the send to complete or time out
        record_metadata = future.get(timeout=10)
        
        # Log successful send
        logger.info(f"Sent to Kafka: {metadata['image_id']} - "
                   f"Topic: {record_metadata.topic}, "
                   f"Partition: {record_metadata.partition}, "
                   f"Offset: {record_metadata.offset}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to send {image_path} to Kafka: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def daily_task():
    # Versioning: Use timestamp as version
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting daily download for version: {version}")

    # Define your crawling parameters
    animal = ["cat"]
    # plant = ["apple", "carrot"]
    topic_names = ["animal"]
    topics = [animal]
    
    urltopic = {
        "freeimages": "https://www.freeimages.com/search/{name}/"
    }
    n_page = 2
    n_threads = 4

    try:
        # Step 1: Crawl URLs
        logger.info("Step 1: Crawling image URLs...")
        urls_to_txts(topic_names, topics, urltopic, n_page, n_threads)
        logger.info("URL crawling completed")

        # Step 2: Download images
        logger.info("Step 2: Downloading images from URLs...")
        get_image_from_txts(topic_names, topics)
        logger.info("Image downloading completed")

        # Step 3: Send images to Kafka
        logger.info("Step 3: Sending images to Kafka...")
        image_folder = "images"
        
        # Count variables for statistics
        total_images = 0
        successful_sends = 0
        
        for root, _, files in os.walk(image_folder):
            image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
            total_images += len(image_files)
            
            for file in image_files:
                image_path = os.path.join(root, file)
                try:
                    # Open the image
                    with Image.open(image_path) as image:
                        # Send the image to Kafka
                        if send_to_kafka(image_path, image_path, image):
                            successful_sends += 1
                except Exception as e:
                    logger.error(f'Failed to process {image_path}: {e}')
        
        # Log statistics
        logger.info(f"Image processing complete. Processed {total_images} images, "
                   f"successfully sent {successful_sends} to Kafka "
                   f"({successful_sends/total_images*100:.1f}% success rate)")

    except Exception as e:
        logger.error(f"Error during daily task: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info(f"Daily task completed for version: {version}")
    
    # Flush any remaining messages
    producer.flush()

def run_now():
    """Run the task immediately without scheduling."""
    logger.info("Running task immediately")
    daily_task()

def schedule_task():
    """Schedule the task to run daily."""
    # Schedule the task to run daily at a specific time
    schedule_time = "00:00"
    schedule.every().day.at(schedule_time).do(daily_task)
    logger.info(f"Task scheduled to run daily at {schedule_time}")
    
    # Keep the script running
    logger.info("Scheduler is running. Press Ctrl+C to exit.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        producer.flush()
        producer.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        run_now()
    else:
        schedule_task()
