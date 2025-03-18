import psycopg2
import numpy as np
import matplotlib.pyplot as plt

# Database connection parameters
db_params = {
    "host": "localhost",
    "database": "dataset",
    "user": "postgres",
    "password": "123456",
    "port": "5432"
}

try:
    # Connect to the database
    connection = psycopg2.connect(**db_params)
    print("Connected to the database successfully!")
    cursor = connection.cursor()

    # Fetch rows 3, 4, and 5 (OFFSET 2, LIMIT 3)
    cursor.execute("""
        SELECT image_id, original_data, grayscale_data, processed_shape
        FROM images
        OFFSET 2 LIMIT 3
    """)
    rows = cursor.fetchall()

    if rows:
        # Loop through the fetched rows (3rd, 4th, 5th)
        for idx, row in enumerate(rows, start=3):
            image_id, original_data, grayscale_data, processed_shape = row
            print(f"Row {idx} - Image ID: {image_id}")
            print(f"Processed Shape: {processed_shape}")

            # Extract shape info from processed_shape
            original_shape = processed_shape['original']  # [height, width, channels]
            grayscale_shape = processed_shape['grayscale']  # [height, width, 1]

            # Reconstruct NumPy arrays from raw bytes
            original_array = np.frombuffer(original_data, dtype=np.uint8).reshape(original_shape)
            grayscale_array = np.frombuffer(grayscale_data, dtype=np.uint8).reshape(grayscale_shape)

            # Plot the images
            plt.figure(figsize=(10, 5))

            # Original image (RGB)
            plt.subplot(1, 2, 1)
            plt.imshow(original_array)
            plt.title(f"Original Image (Row {idx})")
            plt.axis("off")

            # Grayscale image
            plt.subplot(1, 2, 2)
            plt.imshow(grayscale_array, cmap="gray")
            plt.title(f"Grayscale Image (Row {idx})")
            plt.axis("off")

            plt.show()

    else:
        print("No data found for rows 3, 4, and 5. Check if the table has at least 5 rows.")

    cursor.close()
    connection.close()
    print("Connection closed.")

except psycopg2.Error as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")