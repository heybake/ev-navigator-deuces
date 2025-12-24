import os
from PIL import Image, ImageDraw, ImageColor, ImageFont
import math

# === Configuration ===
OUTPUT_FILENAME = "procedural_back_fitted.png"
CARD_WIDTH = 500
CARD_HEIGHT = 726
CORNER_RADIUS = 60

# Colors
COLOR_BLUE_DARK = ImageColor.getrgb("#001840") # Deep Royal Blue
COLOR_GOLD = ImageColor.getrgb("#D4AF37")      # Metallic Gold

# === Helper: Rounded Corners ===
def add_rounded_corners(image, radius):
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (image.width, image.height)], radius=radius, fill=255)
    result = image.copy()
    result.putalpha(mask)
    return result

# === Component 1: The Background Pattern ===
def draw_pattern(draw, width, height):
    grid_spacing = 56
    line_width = 6
    
    # Diagonal lines /
    for offset in range(-height, width + height, grid_spacing):
        draw.line([(offset, -10), (offset + height + 10, height + 10)], fill=COLOR_GOLD, width=line_width)
    # Diagonal lines \
    for offset in range(-width, width + height, grid_spacing):
        draw.line([(offset, -10), (offset - height - 10, height + 10)], fill=COLOR_GOLD, width=line_width)

    # Blue squares at intersections
    half_grid = grid_spacing / 2
    square_size = 14
    for x in range(int(-half_grid), width + int(half_grid), int(half_grid)):
        for y in range(int(-half_grid), height + int(half_grid), int(half_grid)):
            grid_x = round(x / half_grid)
            grid_y = round(y / half_grid)
            if (grid_x + grid_y) % 2 == 0:
                draw.rectangle([x - square_size/2, y - square_size/2, x + square_size/2, y + square_size/2], fill=COLOR_BLUE_DARK)

# === Component 2: The Borders ===
def draw_borders(draw, width, height):
    draw.rectangle([(0,0), (width, height)], outline=COLOR_GOLD, width=12)
    margin1 = 12
    draw.rectangle([(margin1, margin1), (width-margin1, height-margin1)], outline=COLOR_BLUE_DARK, width=8)
    margin2 = 20
    draw.rectangle([(margin2, margin2), (width-margin2, height-margin2)], outline=COLOR_GOLD, width=4)

# === Component 3: The Central Monogram (Dynamic Fitting) ===
def draw_monogram_fitted(draw, center_x, center_y):
    radius_outer = 130
    radius_inner = 120
    text = "DW"
    
    # 1. Draw framing circles
    draw.ellipse((center_x - radius_outer, center_y - radius_outer, center_x + radius_outer, center_y + radius_outer), fill=COLOR_BLUE_DARK, outline=COLOR_GOLD, width=6)
    draw.ellipse((center_x - radius_inner, center_y - radius_inner, center_x + radius_inner, center_y + radius_inner), outline=COLOR_GOLD, width=3)

    # 2. Find Font Path
    font_candidates = ["C:/Windows/Fonts/georgiab.ttf", "/Library/Fonts/Georgia Bold.ttf", "C:/Windows/Fonts/timesbd.ttf", "/Library/Fonts/Times Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]
    font_path = None
    for path in font_candidates:
        if os.path.exists(path): font_path = path; break
            
    # 3. Dynamic Font Sizing Loop
    # We define a target box slightly smaller than the inner diameter to leave padding.
    # Diameter is 240. Let's target a box of about 190px wide/tall.
    target_dim = radius_inner * 1.6 
    font_size = 250 # Start too big
    font = ImageFont.load_default()

    if font_path:
        # Loop downwards until the text bounding box fits within target dimensions
        while font_size > 20:
            try:
                temp_font = ImageFont.truetype(font_path, font_size)
                bbox = draw.textbbox((0, 0), text, font=temp_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Check if both width and height fit comfortably
                if text_width < target_dim and text_height < target_dim:
                    font = temp_font # Found the right size!
                    break
            except: pass
            font_size -= 5 # Reduce size and try again

    # 4. Calculate Centering with final font
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    # Center X
    text_x = center_x - (text_width / 2)
    # Center Y (compensating for font baseline offset bbox[1])
    text_y = center_y - (text_height / 2) - bbox[1] 

    # 5. Draw
    draw.text((text_x, text_y), text, font=font, fill=COLOR_GOLD)


# === Main Execution ===
def generate_card_back():
    print("Generating procedural card back with fitted font...")
    img = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), COLOR_BLUE_DARK)
    draw = ImageDraw.Draw(img)
    
    draw_pattern(draw, CARD_WIDTH, CARD_HEIGHT)
    draw_borders(draw, CARD_WIDTH, CARD_HEIGHT)
    # Use the new dynamic fitting function
    draw_monogram_fitted(draw, CARD_WIDTH / 2, CARD_HEIGHT / 2)
    
    final_img = add_rounded_corners(img, CORNER_RADIUS)
    final_img.save(OUTPUT_FILENAME)
    print(f"Success! Generated {OUTPUT_FILENAME}")

if __name__ == "__main__":
    generate_card_back()