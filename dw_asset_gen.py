import pygame
import pygame.gfxdraw
import os

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
CARD_W, CARD_H = 142, 215
OUTPUT_DIR = os.path.join("images", "cards")

# IGT Authentic Palette
C_WHITE     = (255, 255, 255)
C_BLACK     = (0, 0, 0)
C_RED       = (230, 0, 0)      # High-vis Red
C_BLUE_BACK = (0, 0, 150)
C_GOLD      = (255, 215, 0)
C_PURPLE    = (128, 0, 128)
C_SHIELD_BG = (240, 240, 240)

pygame.init()
pygame.font.init()

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# --- FONTS ---
# We try to find a "Slab Serif" to match the IGT look (Courier/Rockwell)
try:
    FONT_RANK = pygame.font.SysFont("couriernew", 48, bold=True)
    FONT_WILD = pygame.font.SysFont("arial", 28, bold=True) 
except:
    FONT_RANK = pygame.font.SysFont("arial", 48, bold=True)
    FONT_WILD = pygame.font.SysFont("arial", 28, bold=True)

# ==========================================
# 🎨 VECTOR PRIMITIVES
# ==========================================
def draw_diamond(surf, cx, cy, w, color):
    pts = [(cx, cy-w*0.65), (cx+w*0.5, cy), (cx, cy+w*0.65), (cx-w*0.5, cy)]
    pygame.draw.polygon(surf, color, pts)
    pygame.gfxdraw.aapolygon(surf, pts, color)

def draw_heart(surf, cx, cy, w, color):
    r = w // 2
    pygame.draw.circle(surf, color, (int(cx-r/2), int(cy-r/2)), int(r/1.8))
    pygame.draw.circle(surf, color, (int(cx+r/2), int(cy-r/2)), int(r/1.8))
    pts = [(cx-w+2, cy-r/4), (cx+w-2, cy-r/4), (cx, cy+w)]
    pygame.draw.polygon(surf, color, pts)

def draw_spade(surf, cx, cy, w, color):
    r = w // 2
    pygame.draw.circle(surf, color, (int(cx-r/2), int(cy+r/4)), int(r/1.8))
    pygame.draw.circle(surf, color, (int(cx+r/2), int(cy+r/4)), int(r/1.8))
    pts = [(cx-w+2, cy+r/2), (cx+w-2, cy+r/2), (cx, cy-w+5)]
    pygame.draw.polygon(surf, color, pts)
    stem = [(cx, cy), (cx-5, cy+w), (cx+5, cy+w)]
    pygame.draw.polygon(surf, color, stem)

def draw_club(surf, cx, cy, w, color):
    r = w // 2
    pygame.draw.circle(surf, color, (int(cx), int(cy-r)), int(r/1.5))
    pygame.draw.circle(surf, color, (int(cx-r), int(cy+r/3)), int(r/1.5))
    pygame.draw.circle(surf, color, (int(cx+r), int(cy+r/3)), int(r/1.5))
    stem = [(cx, cy), (cx-6, cy+w), (cx+6, cy+w)]
    pygame.draw.polygon(surf, color, stem)

def draw_suit(surf, suit, cx, cy, sz):
    col = C_RED if suit in ['h', 'd'] else C_BLACK
    if suit == 'd': draw_diamond(surf, cx, cy, sz, col)
    elif suit == 'h': draw_heart(surf, cx, cy, sz, col)
    elif suit == 's': draw_spade(surf, cx, cy, sz, col)
    elif suit == 'c': draw_club(surf, cx, cy, sz, col)

# ==========================================
# 🛡️ SPECIAL GRAPHICS
# ==========================================
def draw_ace_crest(surf, cx, cy):
    """ Draws the IGT-style Shield found on Aces """
    # Shield Body
    w, h = 60, 70
    rect = pygame.Rect(cx - w//2, cy - h//2, w, h)
    
    # Gold Outline
    pygame.draw.rect(surf, C_GOLD, rect.inflate(6,6), border_radius=5)
    pygame.draw.rect(surf, C_BLACK, rect.inflate(6,6), 2, border_radius=5)
    
    # Quarters (Red/Purple)
    pygame.draw.rect(surf, C_RED, (rect.left, rect.top, w//2, h//2))
    pygame.draw.rect(surf, C_PURPLE, (rect.left + w//2, rect.top, w//2, h//2))
    pygame.draw.rect(surf, C_PURPLE, (rect.left, rect.top + h//2, w//2, h//2))
    pygame.draw.rect(surf, C_RED, (rect.left + w//2, rect.top + h//2, w//2, h//2))
    
    # Banner
    banner_rect = pygame.Rect(cx - w//2 - 10, cy + h//2 - 10, w + 20, 20)
    pygame.draw.rect(surf, C_WHITE, banner_rect, border_radius=5)
    pygame.draw.rect(surf, C_BLACK, banner_rect, 1, border_radius=5)

def draw_face_graphic(surf, rank, cx, cy):
    """ stylized crown/hat for J/Q/K """
    col = C_GOLD
    if rank == 'K': # Crown
        pts = [(cx-30, cy+20), (cx-30, cy-10), (cx-15, cy+10), (cx, cy-20), (cx+15, cy+10), (cx+30, cy-10), (cx+30, cy+20)]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, C_BLACK, pts, 2)
    elif rank == 'Q': # Tiara
        pygame.draw.arc(surf, col, (cx-30, cy-10, 60, 40), 3.14, 6.28, 5)
    elif rank == 'J': # Helmet
        pygame.draw.rect(surf, col, (cx-25, cy-20, 50, 40), border_radius=10)

# ==========================================
# 📐 CARD LOGIC
# ==========================================
def create_card(rank, suit):
    surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    
    # 1. Body
    rect = pygame.Rect(0, 0, CARD_W, CARD_H)
    pygame.draw.rect(surf, C_WHITE, rect, border_radius=8)
    pygame.draw.rect(surf, C_BLACK, rect, 2, border_radius=8)
    
    # 2. Top-Left Index ONLY (IGT Style)
    col = C_RED if suit in ['h', 'd'] else C_BLACK
    rank_txt = FONT_RANK.render(rank, True, col)
    surf.blit(rank_txt, (8, 4))
    draw_suit(surf, suit, 22, 55, 18)
    
    # 3. Center Content
    cx, cy = CARD_W//2, CARD_H//2
    
    # ACES
    if rank == 'A':
        draw_ace_crest(surf, cx, cy)
        return surf
        
    # DEUCES (WILD)
    if rank == '2':
        # Draw "WILD" text vertically
        txt = FONT_WILD.render("WILD", True, C_RED)
        txt = pygame.transform.rotate(txt, -90)
        tr = txt.get_rect(center=(cx, cy))
        surf.blit(txt, tr)
        
        # 4 Corner Pips
        draw_suit(surf, suit, 45, 55, 24)
        draw_suit(surf, suit, CARD_W-45, 55, 24)
        draw_suit(surf, suit, 45, CARD_H-55, 24)
        draw_suit(surf, suit, CARD_W-45, CARD_H-55, 24)
        return surf

    # FACE CARDS
    if rank in ['J', 'Q', 'K']:
        # Draw a portrait frame
        box = pygame.Rect(40, 50, CARD_W-80, CARD_H-90)
        pygame.draw.rect(surf, (250, 240, 230), box) # Cream bg
        pygame.draw.rect(surf, C_BLACK, box, 2)
        
        # Draw Graphic
        draw_face_graphic(surf, rank, cx, cy)
        
        # Big Letter
        lrg = pygame.font.SysFont("timesnewroman", 60, bold=True).render(rank, True, C_BLACK)
        lr = lrg.get_rect(center=(cx, cy + 30))
        # surf.blit(lrg, lr) # Optional: overlay letter
        return surf

    # NUMBER CARDS (Pips)
    pip_locs = []
    pip_sz = 24
    
    # Standard Grid
    if rank in ['3', '4', '5', '6', '7', '8', '9', '10', 'T']:
        col_l, col_r = 45, CARD_W-45
        row_t, row_b = 55, CARD_H-55
        mid_y = CARD_H//2
        mid_x = CARD_W//2
        
        # Columns
        if rank not in ['3']:
            pip_locs += [(col_l, row_t), (col_r, row_t), (col_l, row_b), (col_r, row_b)]
        
        # Mids
        if rank in ['6', '7', '8']: pip_locs += [(col_l, mid_y), (col_r, mid_y)]
        if rank in ['9', '10', 'T']: 
            pip_locs += [(col_l, 90), (col_r, 90), (col_l, CARD_H-90), (col_r, CARD_H-90)]
        
        # Centers
        if rank in ['3', '5', '9']: pip_locs.append((mid_x, mid_y))
        if rank in ['7', '8']: pip_locs.append((mid_x, 80))
        if rank == '8': pip_locs.append((mid_x, CARD_H-80))
        if rank in ['10', 'T']: 
            pip_locs.append((mid_x, 70))
            pip_locs.append((mid_x, CARD_H-70))
            
    for x, y in pip_locs:
        draw_suit(surf, suit, x, y, pip_sz)

    return surf

def create_back():
    surf = pygame.Surface((CARD_W, CARD_H))
    surf.fill(C_BLUE_BACK)
    pygame.draw.rect(surf, C_WHITE, (0,0, CARD_W, CARD_H), 6, border_radius=8)
    # Diamond Pattern
    for x in range(0, CARD_W, 20):
        for y in range(0, CARD_H, 20):
             pygame.draw.circle(surf, (20, 20, 180), (x, y), 2)
    return surf

if __name__ == "__main__":
    ensure_dir(OUTPUT_DIR)
    print("🏭 Minting IGT Vector Deck v3.0...")
    
    ranks = "23456789TJQKA"
    suits = "shdc"
    for s in suits:
        for r in ranks:
            r_key = "10" if r == 'T' else r
            img = create_card(r_key, s)
            # Save as key format (e.g. Th.png or 10h.png depending on engine preference)
            # Engine uses T, J, Q... so save as 'Th.png'
            fname = f"{r}{s}.png"
            pygame.image.save(img, os.path.join(OUTPUT_DIR, fname))
            
    pygame.image.save(create_back(), os.path.join(OUTPUT_DIR, "back.png"))
    print("✅ Done.")