import os
from PIL import Image
import sys

def convert_image(image_path):
    """
    Converts a single image to WebP format (lossless, no alpha) and 
    replaces the original image with the converted version.

    Args:
        image_path: The path to the image file.
    """
    try:
        img = Image.open(image_path)
        has_alpha = img.mode in ('RGBA', 'LA', 'P')

        if has_alpha:
            img = img.convert("RGB")  # Convert to RGB if alpha channel exists

        # Save as WebP (lossless, no alpha)
        webp_path = os.path.splitext(image_path)[0] + ".webp"
        img.save(webp_path, "webp", lossless=True, exact=True)

        # Remove the original image file
        os.remove(image_path)

        print(f"Converted {image_path} to {webp_path}")

    except Exception as e:
        print(f"Error converting {image_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py image1.png image2.jpg ...")
        sys.exit(1)

    image_paths = sys.argv[1:]
    for image_path in image_paths:
        convert_image(image_path)