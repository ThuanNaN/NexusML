import numpy as np
import os
import io
from PIL import Image
import logging
from database.connect import SessionLocal, engine
from database.models import Base, SourceImage, TARGET_SIZE
Base.metadata.create_all(engine)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

    
def convert_image_to_binary(pil_image):
    return np.asarray(pil_image).tobytes()

def convert_image_to_grey(pil_image):
    image = pil_image.convert("L")
    return np.asarray(image).tobytes()

# Function to save image to database
def save_image_to_db(image_path):
    pil_image = Image.open(image_path).convert("RGB").resize(TARGET_SIZE)
    color_img = convert_image_to_binary(pil_image)
    grey_img = convert_image_to_grey(pil_image)
    image = SourceImage(
        name=os.path.basename(image_path),
        image_path=image_path,
        color_image=color_img,
        grey_image=grey_img,
    )
    logger.info(f"Saving image: {image_path}")
    session = SessionLocal()
    try:
        session.add(image)
        session.commit()
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        session.rollback()
        raise
    finally:
        session.close()


# Save all images in a folder
def save_folder_images(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(folder_path, filename)
            save_image_to_db(image_path)

if __name__ == "__main__":
    import sys
    image_folder = sys.argv[1]
    save_folder_images(image_folder)
