from kafka import KafkaConsumer
from PIL import Image
from io import BytesIO
import numpy as np
import psycopg2
import logging
import json
import os
import time
import base64
from concurrent.futures import ThreadPoolExecutor
import threading
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

# Database configuration
DB_CONFIG = {
    'dbname': 'image_db',         
    'user': 'postgres',         
    'password': 'aivn2025',        
    'host': 'localhost',         
    'port': 5454              
}

# Processing configuration
TARGET_SIZE = (224, 224)  # Updated to 224x224 as requested
MIN_IMAGE_SIZE = (50, 50)  # Minimum image size to process
MAX_WORKERS = 4  # Number of worker threads for parallel processing
BATCH_SIZE = 10  # Process messages in batches for efficiency

# Database connection pool
db_connection_lock = threading.Lock()
db_connections = []

def get_db_connection():
    """Get a database connection from the pool or create a new one."""
    with db_connection_lock:
        if db_connections:
            return db_connections.pop()
        else:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                return conn
            except Exception as e:
                logger.error(f"Failed to create database connection: {e}")
                raise

def return_db_connection(conn):
    """Return a connection to the pool."""
    with db_connection_lock:
        db_connections.append(conn)

class ImageProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        
    def decode_image_data(self, image_data_str):
        """
        Try multiple methods to decode the image data.
        """
        try:
            # Ensure the string contains only valid hex characters
            if all(c in '0123456789abcdefABCDEF' for c in image_data_str.strip()):
                try:
                    return bytes.fromhex(image_data_str.strip())
                except ValueError:
                    pass  # Not a valid hex string
            
            # Try base64 decoding
            try:
                return base64.b64decode(image_data_str)
            except Exception:
                pass  # Not valid base64
            
            # Try evaluating byte string representation
            if image_data_str.startswith("b'") or image_data_str.startswith('b"'):
                try:
                    evaluated = eval(image_data_str)
                    if isinstance(evaluated, bytes):
                        return evaluated
                except:
                    pass

            # Return as UTF-8 encoded string if nothing else works
            return image_data_str.encode('utf-8')

        except Exception as e:
            logger.error(f"All decoding methods failed: {e}")
            return None

    
    def preprocess_image(self, image_data_str):
        """
        Preprocess an image: validate format, check size, resize, and ensure it's a 3-channel color image.
        Returns both the processed original image and its grayscale version, or None if invalid.
        """
        try:
            # First, try to decode the image data
            image_data = self.decode_image_data(image_data_str)
            if not image_data:
                logger.error("Failed to decode image data")
                return None, None
                
            logger.info(f"Image data length: {len(image_data)} bytes")
            
            # For debugging: save a copy of the raw image data
            debug_path = "debug_image_raw.bin"
            with open(debug_path, 'wb') as f:
                f.write(image_data)
            logger.info(f"Raw image data saved to {debug_path}")
            
            # Load image from bytes
            try:
                img = Image.open(BytesIO(image_data))
            except Exception as e:
                logger.error(f"Failed to open image: {e}")
                return None, None
                
            # Basic validation
            width, height = img.size
            logger.info(f"Image loaded successfully. Size: {width}x{height}, Format: {img.format}, Mode: {img.mode}")
            
            # Skip if image is too small
            if width < MIN_IMAGE_SIZE[0] or height < MIN_IMAGE_SIZE[1]:
                logger.warning(f"Image too small: {width}x{height}, skipping")
                return None, None
                
            # Check if it's a valid image format
            if img.format not in ['JPEG', 'PNG', 'WEBP', None]:
                logger.warning(f"Unsupported image format: {img.format}, skipping")
                return None, None
            
            # Convert to RGB if not already (handles RGBA, grayscale, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Resize image
            processed_img = img.resize(TARGET_SIZE)
            
            # Create grayscale version
            grayscale_img = processed_img.convert('L')
            
            # Convert to numpy arrays for verification and storage
            img_array = np.asarray(processed_img)
            grayscale_array = np.asarray(grayscale_img)
            
            # Verify dimensions
            if img_array.shape != (TARGET_SIZE[1], TARGET_SIZE[0], 3):
                logger.warning(f"Image has unexpected shape after processing: {img_array.shape}, skipping")
                return None, None
                
            # Save processed image for debugging
            debug_path = "debug_image_processed.jpg"
            processed_img.save(debug_path)
            logger.info(f"Processed image saved to {debug_path}")
            
            return processed_img, grayscale_img
            
        except Exception as e:
            logger.error(f"Failed to preprocess image: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None

    def save_to_database(self, metadata, grayscale_img, original_img):
        """Save grayscale image (input) and preprocessed original image (label) to the database."""
        conn = None
        try:
            # Get a connection from the pool
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Convert PIL images to numpy arrays and then to bytes
            grayscale_data = np.asarray(grayscale_img).tobytes()
            original_data = np.asarray(original_img).tobytes()

            # Insert data into the database
            cur.execute("""
                INSERT INTO crawl_images (name, image_url, color_image, grey_image)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (
                metadata['image_id'],
                metadata.get('image_url', metadata['image_id']),
                original_data,
                grayscale_data,
            ))

            # Commit the transaction
            conn.commit()
            cur.close()
            
            logger.info(f"Saved image {metadata['image_id']} to database")
            return True
        except Exception as e:
            logger.error(f"Failed to save image {metadata['image_id']} to database: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                return_db_connection(conn)


    def process_message(self, message):
        """Process a single message from Kafka."""
        try:
            # Extract data from message
            message_value = message.value
            logger.info(f"Message keys: {message_value.keys()}")
            
            # Extract metadata and image data
            # Handle different possible message structures
            if isinstance(message_value, dict):
                if 'metadata' in message_value and 'image_data' in message_value:
                    metadata = message_value['metadata']
                    image_data_str = message_value['image_data']
                elif 'image_path' in message_value:
                    # Alternative structure
                    image_path = message_value['image_path']
                    metadata = {
                        'image_id': os.path.basename(image_path),
                        'image_url': image_path
                    }
                    # Maybe the image data is directly in the message
                    image_data_str = message_value.get('image_data', message_value.get('data', ''))
                else:
                    # Try to find image data in any field
                    image_data_str = None
                    metadata = {'image_id': f"unknown_{time.time()}"}
                    
                    for key, value in message_value.items():
                        if isinstance(value, str) and len(value) > 1000:  # Likely image data
                            image_data_str = value
                            break
                    
                    if not image_data_str:
                        logger.error(f"Could not find image data in message: {message_value.keys()}")
                        return False
            else:
                logger.error(f"Unexpected message format: {type(message_value)}")
                return False

            # Generate a unique ID if not present
            if 'image_id' not in metadata:
                metadata['image_id'] = f"image_{time.time()}"

            logger.info(f"Processing image: {metadata['image_id']}")
            
            # Preprocess the image
            original_img, grayscale_img = self.preprocess_image(image_data_str)
            if original_img is None or grayscale_img is None:
                return False
                
            # Save to database
            return self.save_to_database(metadata, grayscale_img, original_img)
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def process_batch(self, message_batch):
        """Process a batch of messages in parallel."""
        # Submit all tasks to the thread pool
        futures = [self.executor.submit(self.process_message, message) for message in message_batch]
        
        # Wait for all tasks to complete
        results = [future.result() for future in futures]
        
        # Log statistics
        success_count = sum(1 for result in results if result)
        logger.info(f"Batch processing complete: {success_count}/{len(results)} successful")



class KafkaImageConsumer:
    def __init__(self):
        self.processor = ImageProcessor()
        self.consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda x: self._safe_json_deserialize(x),
            group_id='image-consumer-group',
            auto_offset_reset='earliest',
            max_poll_records=BATCH_SIZE,
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000
        )
    
    def _safe_json_deserialize(self, msg_value):
        """Safely deserialize JSON, handling potential errors."""
        try:
            return json.loads(msg_value.decode('utf-8'))
        except Exception as e:
            logger.warning(f"Failed to decode JSON, treating as raw data: {e}")
            # Return a dict with the raw data for processing
            return {
                'metadata': {'image_id': f"raw_{time.time()}"},
                'image_data': msg_value.decode('utf-8', errors='ignore')
            }


    def consume_and_process(self):
        """Consume messages from Kafka, process images, and store in the database."""
        logger.info(f"Starting Kafka consumer on topic: {KAFKA_TOPIC}")
        
        # Initialize database
        # self.initialize_database()
        
        # Track processing metrics
        start_time = time.time()
        message_count = 0
        success_count = 0
        
        try:
            while True:
                # Poll for messages with timeout
                message_batch = []
                messages = self.consumer.poll(timeout_ms=1000)
                
                if not messages:
                    elapsed = time.time() - start_time
                    if elapsed > 60:  # Log stats every minute
                        if message_count > 0:
                            logger.info(f"Processing stats: {success_count}/{message_count} successful "
                                    f"({success_count/message_count*100:.1f}%), "
                                    f"{message_count/elapsed:.1f} messages/sec")
                        start_time = time.time()
                        message_count = 0
                        success_count = 0
                    continue
                
                # Collect messages into a batch
                for topic_partition, partition_messages in messages.items():
                    message_batch.extend(partition_messages)
                    
                # Update metrics
                batch_size = len(message_batch)
                message_count += batch_size
                logger.info(f"Received batch of {batch_size} messages")
                
                # Process the batch
                self.processor.process_batch(message_batch)
                
                # Commit offsets
                self.consumer.commit()
                
        except KeyboardInterrupt:
            logger.info("Shutting down consumer")
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self.processor.executor.shutdown()
            self.consumer.close()

if __name__ == "__main__":
    consumer = KafkaImageConsumer()
    consumer.consume_and_process()