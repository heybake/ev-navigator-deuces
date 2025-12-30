import os
from PIL import Image, ImageDraw, ImageFont, ImageColor

# ==========================================
# ⚙️ TABLET CONFIGURATION
# ==========================================
# 1. Native "Master" Resolution (Preserves your exact art style)
MASTER_W = 500
MASTER_H = 726
CORNER_RADIUS = 60

# 2. Target Tablet Resolution (1.6x Scale of Desktop 142x215)
# This ensures they fit the 2560x1600 screen perfectly
TARGET_W = 227
TARGET_H = 344

OUTPUT_DIR = "tablet_cards"
ASSETS_DIR = "assets"

# ==========================================
# 🎨 ART DEFINITIONS (Identical to Original)
# ==========================================
COLOR_WHITE = ImageColor.getrgb("#FFFFFF")
COLOR_RED   = ImageColor.getrgb("#E60000")
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY_END = (180, 180, 180)
COLOR_TRANSPARENT = (0, 0, 0, 0)
COLOR_BLUE_DARK = ImageColor.getrgb("#001840") # For Back
COLOR_GOLD = ImageColor.getrgb("#D4AF37")      # For Back

DRAWING_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUITS = {
    'Hearts':   {'symbol': '♥', 'color': COLOR_RED,   'short': 'h'},
    'Diamonds': {'symbol': '♦', 'color': COLOR_RED,   'short': 'd'},
    'Clubs':    {'symbol': '♣', 'color': COLOR_BLACK, 'short': 'c'},
    'Spades':   {'symbol': '♠', 'color': COLOR_BLACK, 'short': 's'},
}

FACE_CARD_IMAGES = {
    'J': os.path.join(ASSETS_DIR, "jack.png"),
    'Q': os.path.join(ASSETS_DIR, "queen.png"),
    'K': os.path.join(ASSETS_DIR, "king.png"),
    'A': os.path.join(ASSETS_DIR, "ace.png")
}

# ==========================================
# 🅰️ FONT LOADER
# ==========================================
font_candidates = [
    "C:/Windows/Fonts/arialbd.ttf", 
    "/Library/Fonts/Arial Bold.ttf", 
    "C:/Windows/Fonts/calibrib.ttf",
    "/system/fonts/Roboto-Bold.ttf" # Android Fallback
]
GLOBAL_FONT_PATH = None
for path in font_candidates:
    if os.path.exists(path):
        GLOBAL_FONT_PATH = path
        break

try:
    if GLOBAL_FONT_PATH:
        FONT_RANK = ImageFont.truetype(GLOBAL_FONT_PATH, 110)
        FONT_PIP_SMALL = ImageFont.truetype(GLOBAL_FONT_PATH, 120)
        FONT_PIP_LARGE = ImageFont.truetype(GLOBAL_FONT_PATH, 380)
        FONT_JOKER_TEXT = ImageFont.truetype(GLOBAL_FONT_PATH, 90)
        FONT_JOKER_ICON = ImageFont.truetype(GLOBAL_FONT_PATH, 250)
    else:
        raise IOError
except:
    # Fallback if no fonts found
    FONT_RANK = FONT_PIP_SMALL = FONT_PIP_LARGE = FONT_JOKER_TEXT = FONT_JOKER_ICON = ImageFont.load_default()

# ==========================================
# 🖌️ DRAWING ENGINES
# ==========================================
def get_dynamic_font(size):
    if GLOBAL_FONT_PATH:
        return ImageFont.truetype(GLOBAL_FONT_PATH, int(size))
    return ImageFont.load_default()

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
        txt_width = bbox[2] - bbox[0]
        txt_height = bbox[3] - bbox[1]
        
        draw_obj.text((center_x - txt_width/2, current_y), text, font=current_font, fill=current_color)
        current_y += txt_height + 5

def draw_card_base():
    img = Image.new('RGBA', (MASTER_W, MASTER_H), COLOR_TRANSPARENT)
    draw = ImageDraw.Draw(img)
    # Background
    draw.rounded_rectangle([(0, 0), (MASTER_W-1, MASTER_H-1)], radius=CORNER_RADIUS, fill=COLOR_BLACK)
    # Inner White
    border = 10
    draw.rounded_rectangle([(border, border), (MASTER_W-border-1, MASTER_H-border-1)], radius=CORNER_RADIUS-5, fill=COLOR_WHITE)
    return img, draw

def create_single_card(rank, suit_name=None, is_joker=False):
    img, draw = draw_card_base()
    margin_x, margin_y = 50, 50

    if is_joker:
        draw.text((margin_x, margin_y), "JOKER", font=FONT_JOKER_TEXT, fill=COLOR_BLACK)
        joker_char = "☻"
        bbox = draw.textbbox((0,0), joker_char, font=FONT_JOKER_ICON)
        w, h = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text(((MASTER_W-w)/2, (MASTER_H-h)/2 + 50), joker_char, font=FONT_JOKER_ICON, fill=COLOR_RED)
    else:
        suit_data = SUITS[suit_name]
        symbol, color = suit_data['symbol'], suit_data['color']
        is_wild = (rank == '2')

        # 1. Top-Left Rank
        draw.text((margin_x, margin_y), rank, font=FONT_RANK, fill=color)
        
        # Measure Rank for Pip placement
        r_bbox = draw.textbbox((margin_x, margin_y), rank, font=FONT_RANK)
        r_w = r_bbox[2] - r_bbox[0]
        r_h = r_bbox[3] - r_bbox[1]
        
        # 2. Small Pip
        p_bbox = draw.textbbox((0,0), symbol, font=FONT_PIP_SMALL)
        p_w = p_bbox[2] - p_bbox[0]
        draw.text((margin_x + (r_w - p_w)/2, margin_y + r_h + 10), symbol, font=FONT_PIP_SMALL, fill=color)

        # 3. Center Art
        art_drawn = False
        if rank in FACE_CARD_IMAGES:
            try:
                face = Image.open(FACE_CARD_IMAGES[rank]).convert("RGBA")
                face.thumbnail((180, 250), Image.Resampling.LANCZOS)
                img.paste(face, (MASTER_W - face.width - margin_x, margin_y), mask=face)
                art_drawn = True
            except: pass
            
        # 4. Large Bottom Pip
        l_bbox = draw.textbbox((0,0), symbol, font=FONT_PIP_LARGE)
        l_w, l_h = l_bbox[2]-l_bbox[0], l_bbox[3]-l_bbox[1]
        draw.text(((MASTER_W - l_w)/2, MASTER_H - l_h - 160), symbol, font=FONT_PIP_LARGE, fill=color)

        # 5. Wild Text
        if is_wild:
            draw_cascading_wild(draw, MASTER_W - 170, margin_y)

    return img

def create_back():
    img = Image.new('RGBA', (MASTER_W, MASTER_H), COLOR_BLUE_DARK)
    draw = ImageDraw.Draw(img)
    
    # Pattern
    spacing = 56
    for i in range(-MASTER_H, MASTER_W + MASTER_H, spacing):
        draw.line([(i, -10), (i+MASTER_H, MASTER_H+10)], fill=COLOR_GOLD, width=6)
        draw.line([(i, -10), (i-MASTER_H, MASTER_H+10)], fill=COLOR_GOLD, width=6)
        
    # Borders
    draw.rectangle([(0,0), (MASTER_W, MASTER_H)], outline=COLOR_GOLD, width=12)
    draw.rectangle([(20,20), (MASTER_W-20, MASTER_H-20)], outline=COLOR_GOLD, width=4)
    
    # Round Corners
    mask = Image.new('L', (MASTER_W, MASTER_H), 0)
    dmask = ImageDraw.Draw(mask)
    dmask.rounded_rectangle([(0,0), (MASTER_W, MASTER_H)], radius=CORNER_RADIUS, fill=255)
    img.putalpha(mask)
    return img

# ==========================================
# 🚀 MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"🏭 Minting TABLET Assets...")
    print(f"   Source Resolution: {MASTER_W}x{MASTER_H}")
    print(f"   Target Resolution: {TARGET_W}x{TARGET_H} (1.6x Scale)")

    count = 0
    
    # 1. Generate Faces
    for suit_name, data in SUITS.items():
        for rank in DRAWING_RANKS:
            # Create MASTER
            master_img = create_single_card(rank, suit_name)
            
            # Resize to TARGET
            tablet_img = master_img.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
            
            # Save
            r_char = 'T' if rank == '10' else rank
            fname = f"{r_char}{data['short']}.png"
            tablet_img.save(os.path.join(OUTPUT_DIR, fname), "PNG")
            count += 1
            print(f"   [Minified] {fname}", end='\r')

    # 2. Generate Joker
    j_master = create_single_card(None, None, is_joker=True)
    j_tablet = j_master.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
    j_tablet.save(os.path.join(OUTPUT_DIR, "joker.png"), "PNG")
    
    # 3. Generate Back
    b_master = create_back()
    b_tablet = b_master.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
    b_tablet.save(os.path.join(OUTPUT_DIR, "back.png"), "PNG")
    
    print(f"\n✅ Done. {count+2} assets saved to '{OUTPUT_DIR}/'.")