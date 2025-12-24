import os
from PIL import Image, ImageDraw, ImageFont, ImageColor

# === Configuration ===
OUTPUT_DIR = "final_cards_53_set"
ASSETS_DIR = "assets"

# Card Size
CARD_WIDTH = 500
CARD_HEIGHT = 726
CORNER_RADIUS = 60

# === Colors ===
COLOR_WHITE = ImageColor.getrgb("#FFFFFF")
COLOR_RED = ImageColor.getrgb("#E60000")
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY_END = (180, 180, 180)
COLOR_TRANSPARENT = (0, 0, 0, 0)

# === Ranks & Suits Definitions ===
# The standard ranks used for drawing patterns
DRAWING_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = {
    'Hearts': {'symbol': '♥', 'color': COLOR_RED, 'short': 'h'},
    'Diamonds': {'symbol': '♦', 'color': COLOR_RED, 'short': 'd'},
    'Clubs': {'symbol': '♣', 'color': COLOR_BLACK, 'short': 'c'},
    'Spades': {'symbol': '♠', 'color': COLOR_BLACK, 'short': 's'},
}

FACE_CARD_IMAGES = {
    'J': os.path.join(ASSETS_DIR, "jack.png"),
    'Q': os.path.join(ASSETS_DIR, "queen.png"),
    'K': os.path.join(ASSETS_DIR, "king.png")
}

# === Font Loading ===
font_candidates = ["C:/Windows/Fonts/arialbd.ttf", "/Library/Fonts/Arial Bold.ttf", "C:/Windows/Fonts/calibrib.ttf"]
GLOBAL_FONT_PATH = None
for path in font_candidates:
    if os.path.exists(path): GLOBAL_FONT_PATH = path; break
try:
    if GLOBAL_FONT_PATH:
        FONT_RANK = ImageFont.truetype(GLOBAL_FONT_PATH, 110)
        FONT_PIP_SMALL = ImageFont.truetype(GLOBAL_FONT_PATH, 120)
        FONT_PIP_LARGE = ImageFont.truetype(GLOBAL_FONT_PATH, 380)
        FONT_JOKER_TEXT = ImageFont.truetype(GLOBAL_FONT_PATH, 90)
        FONT_JOKER_ICON = ImageFont.truetype(GLOBAL_FONT_PATH, 250) 
    else: raise IOError
except: FONT_RANK = FONT_PIP_SMALL = FONT_PIP_LARGE = FONT_JOKER_TEXT = FONT_JOKER_ICON = ImageFont.load_default()

# === Helper Functions ===
def get_dynamic_font(size):
    if GLOBAL_FONT_PATH: return ImageFont.truetype(GLOBAL_FONT_PATH, int(size))
    else: return ImageFont.load_default()

def interpolate_color(start_rgb, end_rgb, t):
    r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
    g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
    b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
    return (r, g, b)

def draw_cascading_wild(draw_obj, center_x, start_y):
    text, steps, start_size, end_size = "WILD", 4, 105, 50
    current_y = start_y
    for i in range(steps):
        t = i / (steps - 1)
        current_size = start_size + (end_size - start_size) * t
        current_font = get_dynamic_font(current_size)
        current_color = interpolate_color(COLOR_BLACK, COLOR_GRAY_END, t)
        bbox = draw_obj.textbbox((0, 0), text, font=current_font)
        txt_width, txt_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw_obj.text((center_x - txt_width/2, current_y), text, font=current_font, fill=current_color)
        current_y += txt_height + 5

def draw_card_base():
    img = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), COLOR_TRANSPARENT)
    draw = ImageDraw.Draw(img)
    border_thickness = 25
    draw.rounded_rectangle([(0, 0), (CARD_WIDTH-1, CARD_HEIGHT-1)], radius=CORNER_RADIUS, fill=COLOR_BLACK)
    draw.rounded_rectangle([(border_thickness, border_thickness), (CARD_WIDTH-1-border_thickness, CARD_HEIGHT-1-border_thickness)], radius=CORNER_RADIUS-15, fill=COLOR_WHITE)
    return img, draw

# === Drawing Logic ===
def create_single_card(rank, suit_name=None, is_joker=False):
    img, draw = draw_card_base()
    margin_x, margin_y = 50, 50

    if is_joker:
        draw.text((margin_x, margin_y), "JOKER", font=FONT_JOKER_TEXT, fill=COLOR_BLACK)
        joker_char = "☻" 
        icon_bbox = draw.textbbox((0,0), joker_char, font=FONT_JOKER_ICON)
        icon_w, icon_h = icon_bbox[2] - icon_bbox[0], icon_bbox[3] - icon_bbox[1]
        draw.text(((CARD_WIDTH-icon_w)/2, (CARD_HEIGHT-icon_h)/2 + 50), joker_char, font=FONT_JOKER_ICON, fill=COLOR_RED)
    else:
        suit_data = SUITS[suit_name]
        suit_symbol, main_color = suit_data['symbol'], suit_data['color']
        # All 2s are visually wild in this game design
        is_wild_visual = (rank == '2')

        # 1. Top-left Rank & Centered Pip
        draw.text((margin_x, margin_y), rank, font=FONT_RANK, fill=main_color)
        rank_bbox_abs = draw.textbbox((margin_x, margin_y), rank, font=FONT_RANK)
        rank_center_x = rank_bbox_abs[0] + (rank_bbox_abs[2] - rank_bbox_abs[0]) / 2
        rank_height = rank_bbox_abs[3] - rank_bbox_abs[1]
        pip_bbox = draw.textbbox((0, 0), suit_symbol, font=FONT_PIP_SMALL)
        pip_width = pip_bbox[2] - pip_bbox[0]
        pip_x = rank_center_x - (pip_width / 2)
        pip_y = margin_y + rank_height + 10
        draw.text((pip_x, pip_y), suit_symbol, font=FONT_PIP_SMALL, fill=main_color)

        # 2. Face Image
        if rank in FACE_CARD_IMAGES:
            try:
                img_path = FACE_CARD_IMAGES[rank]
                face_img = Image.open(img_path).convert("RGBA")
                face_img.thumbnail((180, 250), Image.LANCZOS)
                img_w, img_h = face_img.size
                x_pos = CARD_WIDTH - img_w - margin_x
                y_pos = margin_y
                img.paste(face_img, (x_pos, y_pos), mask=face_img)
            except FileNotFoundError: pass
        
        # 3. Large Bottom Pip
        pip_bbox = draw.textbbox((0,0), suit_symbol, font=FONT_PIP_LARGE)
        pip_w, pip_h = pip_bbox[2] - pip_bbox[0], pip_bbox[3] - pip_bbox[1]
        draw.text(((CARD_WIDTH - pip_w)/2, CARD_HEIGHT - pip_h - 160), suit_symbol, font=FONT_PIP_LARGE, fill=main_color)

        # 4. Wild Text (Drawn on all 2s)
        if is_wild_visual:
            draw_cascading_wild(draw, CARD_WIDTH - 170, margin_y)

    return img

# === Main Generation Loop (Correct Naming Convention) ===
def generate_all_cards():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    if not os.path.exists(ASSETS_DIR): print(f"WARNING: Ensure '{ASSETS_DIR}' folder exists.")

    print(f"Starting generation of 53 cards based on Spec...")
    count = 0

    # A. Generate Standard 52 Cards
    for suit_name, suit_data in SUITS.items():
        for rank in DRAWING_RANKS:
            # 1. Generate Image (Visuals remain the same, 2s look wild)
            card_img = create_single_card(rank, suit_name)
            
            # 2. Determine correct filename mapping
            # Map '10' to 'T'
            fname_rank = 'T' if rank == '10' else rank
            # Get short suit char (h, d, c, s)
            fname_suit = suit_data['short']
            
            filename = f"{fname_rank}{fname_suit}.png"
            
            # 3. Save
            filepath = os.path.join(OUTPUT_DIR, filename)
            card_img.save(filepath, "PNG")
            print(f"Saved: {filename}")
            count += 1

    # B. Generate 1 Joker
    joker_img = create_single_card(None, None, is_joker=True)
    joker_filename = "joker.png"
    joker_path = os.path.join(OUTPUT_DIR, joker_filename)
    joker_img.save(joker_path, "PNG")
    print(f"Saved: {joker_filename}")
    count += 1

    print(f"\nSuccess! {count} cards saved to '{OUTPUT_DIR}/' matching the naming convention.")

if __name__ == "__main__":
    generate_all_cards()