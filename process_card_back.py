import os
from PIL import Image, ImageDraw, ImageFilter

# === Configuration ===
# Where the raw art source is located
SOURCE_IMAGE_PATH = os.path.join("assets", "card_back_source.png")

# Where the final game asset should go
OUTPUT_DIR = "final_cards_53_set"
OUTPUT_FILENAME = "back.png"

# Target dimensions to match the front of the cards
TARGET_WIDTH = 500
TARGET_HEIGHT = 726
CORNER_RADIUS = 60

# === Helper Function: Aspect-Fill Resize ===
def resize_aspect_fill(image, target_width, target_height):
    """
    Resizes an image to fill target dimensions while maintaining aspect ratio,
    and center-crops any excess.
    """
    target_ratio = target_height / target_width
    img_ratio = image.height / image.width

    if img_ratio > target_ratio:
        # Image is taller than target: resize based on width
        new_width = target_width
        new_height = int(image.height * (target_width / image.width))
    else:
        # Image is wider than target: resize based on height
        new_height = target_height
        new_width = int(image.width * (target_height / image.height))

    # 1. High-quality resize
    resized_img = image.resize((new_width, new_height), Image.LANCZOS)

    # 2. Center Crop
    left = (new_width - target_width) / 2
    top = (new_height - target_height) / 2
    right = (new_width + target_width) / 2
    bottom = (new_height + target_height) / 2
    
    return resized_img.crop((left, top, right, bottom))

# === Helper Function: Rounded Corners ===
def add_rounded_corners(image, radius):
    """
    Applies a rounded corner mask to an image.
    """
    # Create a mask image with the same size, filled with 0 (transparent)
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    
    # Draw a filled white rounded rectangle onto the mask
    # The white areas will be kept, black areas will become transparent
    draw.rounded_rectangle(
        [(0, 0), (image.width, image.height)], 
        radius=radius, 
        fill=255,
        outline=255, # Ensure edge is filled
        width=2
    )
    
    # Put the mask into the alpha channel of the image
    result = image.copy()
    result.putalpha(mask)
    return result

# === Main Processing Loop ===
def process_back():
    # 1. Checks
    if not os.path.exists(SOURCE_IMAGE_PATH):
        print(f"ERROR: Source image not found at {SOURCE_IMAGE_PATH}")
        print("Please save the card back design image into the 'assets' folder with that name.")
        return
        
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    print(f"Processing card back image...")

    try:
        # 2. Load Source
        source_img = Image.open(SOURCE_IMAGE_PATH).convert("RGBA")

        # 3. Resize to fill 500x726 perfectly
        resized_img = resize_aspect_fill(source_img, TARGET_WIDTH, TARGET_HEIGHT)

        # 4. Apply rounded corners so it matches the front cards
        final_img = add_rounded_corners(resized_img, CORNER_RADIUS)

        # 5. Save
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
        final_img.save(output_path, "PNG")
        print(f"Success! Final card back saved to: {output_path}")
        print(f"Dimensions: {final_img.size}, Corners rounded.")

    except Exception as e:
        print(f"An error occurred processing the image: {e}")

if __name__ == "__main__":
    process_back()