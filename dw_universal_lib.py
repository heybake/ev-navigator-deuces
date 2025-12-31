import pygame
import os
import math
import platform

# ==============================================================================
# 📐 UNIVERSAL SCALING & CONFIG ENGINE
# ==============================================================================
# The game logic is built around this "Virtual Resolution".
VIRTUAL_W = 1600
VIRTUAL_H = 850

# CONFIG FLAGS
IS_MOBILE = "ANDROID_ARGUMENT" in os.environ

# DETECT PHYSICAL SCREEN
pygame.init()
info = pygame.display.Info()

if IS_MOBILE:
    # 📱 MOBILE: Grab the actual hardware dimensions to fill the screen
    PHYSICAL_W = info.current_w
    PHYSICAL_H = info.current_h
    
    # FORCE LANDSCAPE ON MOBILE
    if PHYSICAL_H > PHYSICAL_W:
        PHYSICAL_W, PHYSICAL_H = info.current_h, info.current_w
else:
    # 💻 PC: Force a civilized window size (1:1 Scale)
    PHYSICAL_W = VIRTUAL_W
    PHYSICAL_H = VIRTUAL_H

# CALCULATE SCALE FACTOR
scale_x = PHYSICAL_W / VIRTUAL_W
scale_y = PHYSICAL_H / VIRTUAL_H
SCALE = min(scale_x, scale_y) # Fit within the bounds

# CENTERING OFFSETS
ACTUAL_GAME_W = int(VIRTUAL_W * SCALE)
ACTUAL_GAME_H = int(VIRTUAL_H * SCALE)
X_OFFSET = (PHYSICAL_W - ACTUAL_GAME_W) // 2
Y_OFFSET = (PHYSICAL_H - ACTUAL_GAME_H) // 2

# FRAME RATE TARGETS
FPS_LIMIT = 30 if IS_MOBILE else 60
FPS_ACTIVE = FPS_LIMIT
FPS_IDLE = 15 if IS_MOBILE else 30
FULLSCREEN_FLAG = pygame.FULLSCREEN if IS_MOBILE else pygame.RESIZABLE

# --- SCALING HELPERS ---
def s(val):
    """Scales a single integer value."""
    return int(val * SCALE)

def s_rect(x, y, w, h):
    """Creates a Scaled Rect, centered on the physical screen."""
    return pygame.Rect(s(x) + X_OFFSET, s(y) + Y_OFFSET, s(w), s(h))

def s_font(size):
    """Scales font size."""
    return max(10, int(size * SCALE))

# COLORS
C_BG_BLUE     = (0, 0, 150)
C_FELT_GREEN  = (0, 80, 40)
C_BLACK       = (0, 0, 0)
C_WHITE       = (255, 255, 255)
C_YEL_TEXT    = (255, 255, 0)
C_RED_ACTIVE  = (180, 0, 0)
C_DIGITAL_RED = (255, 50, 50)
C_DIGITAL_YEL = (255, 255, 50)
C_DIGITAL_GRN = (50, 205, 50)
C_CYAN_MSG    = (0, 255, 255)
C_BTN_FACE    = (230, 230, 230)
C_BTN_SHADOW  = (100, 100, 100)
C_HELD_BORDER = (255, 255, 0)
C_SILVER      = (192, 192, 192) 
C_GOLD_HELD   = (255, 215, 0)
C_PUSH_GREY   = (120, 120, 120) # Added for Hand History (Push/Break Even)

# --- PANEL THEMES ---
C_PANEL_BG    = (40, 45, 50)
C_NB_BG       = (255, 255, 255)
C_NB_TEXT     = (20, 20, 20)
C_NB_RED      = (200, 0, 0)
C_NB_BLACK    = (0, 0, 0)
C_NB_HIGHLIGHT= (255, 230, 80)
C_NB_LINES    = (200, 200, 200)
C_GRAPH_BG    = (20, 25, 30)
C_GRAPH_GRID  = (50, 60, 70)
C_GRAPH_LINE_G= (0, 255, 100)
C_GRAPH_LINE_R= (255, 80, 80)
C_GRAPH_BASE  = (100, 100, 255)
C_GRAPH_CEIL  = (0, 200, 0)
C_GRAPH_FLOOR = (200, 0, 0)

# --- IGT MENU THEME ---
C_IGT_BG      = (0, 0, 130)
C_IGT_GOLD    = (218, 165, 32)
C_IGT_RED     = (200, 0, 0)
C_IGT_TXT_BG  = (0, 0, 80)
C_IGT_TXT     = (0, 255, 255)
C_IGT_TXT_SEL = (255, 255, 0)

# --- TEXT MAPPING ---
# Translates internal engine codes to clean Human Readable text
RANK_DISPLAY_MAP = {
    "NATURAL_ROYAL":    "Royal Flush",
    "ROYAL_FLUSH":      "Royal Flush",
    "FOUR_DEUCES":      "Four Deuces",
    "FOUR_DEUCES_ACE":  "4 Deuces + Ace",
    "WILD_ROYAL":       "Wild Royal",
    "FIVE_OF_A_KIND":   "Five of a Kind",
    "FIVE_OAK":         "Five of a Kind",
    "FIVE_ACES":        "Five Aces",
    "FIVE_3_4_5":       "Five 3s 4s 5s",
    "FIVE_6_TO_K":      "Five 6s thru Ks",
    "STRAIGHT_FLUSH":   "Straight Flush",
    "FOUR_OF_A_KIND":   "Four of a Kind",
    "FOUR_OAK":         "Four of a Kind",
    "FULL_HOUSE":       "Full House",
    "FLUSH":            "Flush",
    "STRAIGHT":         "Straight",
    "THREE_OF_A_KIND":  "Three of a Kind",
    "THREE_OAK":        "Three of a Kind",
    "TWO_PAIR":         "Two Pair",
    "JACKS_OR_BETTER":  "Jacks or Better",
    "NOTHING":          "Loss",
    "LOSER":            "Loss",
    "ERROR":            "Error"
}

# ASSETS
ASSET_DIR = os.path.join("images", "cards")
SOUND_DIR = "sounds"
CARD_SIZE = (s(142), s(215))

# ==============================================================================
# 🔊 SOUND MANAGER (Updated for Duration Control)
# ==============================================================================
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self.volume = 0.5 
        if os.path.exists(SOUND_DIR):
            self._load("bet", "bet.wav")
            self._load("deal", "deal.wav")
            self._load("win", "win.wav")
            self._load("rollup", "rollup.wav")
            self._load("voucher", "voucher.wav")
        self.set_volume(self.volume)

    def _load(self, name, filename):
        try:
            path = os.path.join(SOUND_DIR, filename)
            self.sounds[name] = pygame.mixer.Sound(path)
        except: pass

    def set_volume(self, vol):
        self.volume = vol
        for s in self.sounds.values():
            s.set_volume(vol)

    def play(self, name, maxtime=0):
        # maxtime: milliseconds to play (0 = play full length)
        if self.enabled and self.volume > 0 and name in self.sounds:
            self.sounds[name].play(maxtime=maxtime)

# ==============================================================================
# 🖼️ ASSET MANAGER (SCALED FONTS & SYMBOLS)
# ==============================================================================
class AssetManager:
    def __init__(self):
        self.cards = {}
        self.back = None
        # Fonts scaled by SCALE factor
        self.font_ui = pygame.font.SysFont("Arial", s_font(16), bold=True)
        self.font_grid = pygame.font.SysFont("Arial", s_font(18), bold=True)
        self.font_vfd = pygame.font.SysFont("Impact", s_font(32))
        self.font_lbl = pygame.font.SysFont("Arial", s_font(14), bold=True)
        self.font_msg = pygame.font.SysFont("Arial", s_font(24), bold=True)
        
        # LOG FONT
        self.font_log_bold = pygame.font.SysFont("Arial", s_font(16), bold=True)
        self.font_log = pygame.font.SysFont("Arial", s_font(16))
            
        self.font_tiny = pygame.font.SysFont("Arial", s_font(13))
        self.font_micro = pygame.font.SysFont("Arial", s_font(11), bold=True)
        self.font_menu_title = pygame.font.SysFont("Arial Black", s_font(24))
        self.font_menu_item = pygame.font.SysFont("Arial", s_font(22), bold=True)
        
        self._init_symbols()
        self._load_textures()

    def _init_symbols(self):
        # 🛡️ TEXT TAG PROTOCOL (No Unicode boxes)
        if IS_MOBILE:
            self.symbols = {'s': 'S', 'c': 'C', 'h': 'H', 'd': 'D'}
        else:
            self.symbols = {'s': '♠', 'c': '♣', 'h': '♥', 'd': '♦'}

    def get_symbol(self, key):
        return self.symbols.get(key, '?')

    def _load_textures(self):
        print(f"Loading assets from: {os.path.abspath(ASSET_DIR)}")
        ranks = "23456789TJQKA"; suits = "shdc"
        for s_char in suits:
            for r in ranks:
                key = r + s_char
                path = os.path.join(ASSET_DIR, f"{key}.png")
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        self.cards[key] = pygame.transform.smoothscale(img, CARD_SIZE)
                    except: pass
        
        joker_path = os.path.join(ASSET_DIR, "joker.png")
        if os.path.exists(joker_path):
            try:
                img = pygame.image.load(joker_path).convert_alpha()
                self.cards['JOKER'] = pygame.transform.smoothscale(img, CARD_SIZE)
            except: pass

        back_path = os.path.join(ASSET_DIR, "back.png")
        if os.path.exists(back_path):
            try:
                img = pygame.image.load(back_path).convert_alpha()
                self.back = pygame.transform.smoothscale(img, CARD_SIZE)
            except: pass
        else:
            surf = pygame.Surface(CARD_SIZE)
            surf.fill((0, 50, 200))
            pygame.draw.rect(surf, C_WHITE, (5,5,CARD_SIZE[0]-10,CARD_SIZE[1]-10), 2)
            self.back = surf

# ==============================================================================
# 🧩 UI COMPONENTS
# ==============================================================================
class PhysicalButton:
    def __init__(self, rect, text, callback, color=C_BTN_FACE):
        self.rect = rect; self.text = text; self.callback = callback; self.color = color; self.hover = False; self.is_pressed = False
    def update(self, mouse_pos, mouse_down):
        self.hover = self.rect.collidepoint(mouse_pos); self.is_pressed = self.hover and mouse_down
    def draw(self, screen, font):
        draw_rect = self.rect.move(s(2), s(2)) if self.is_pressed else self.rect
        if not self.is_pressed: pygame.draw.rect(screen, C_BTN_SHADOW, self.rect.move(s(4), s(4)), border_radius=s(6))
        pygame.draw.rect(screen, (255, 255, 200) if self.hover else self.color, draw_rect, border_radius=s(6))
        pygame.draw.rect(screen, C_BLACK, draw_rect, s(2), border_radius=s(6))
        txt = font.render(self.text, True, C_BLACK); screen.blit(txt, txt.get_rect(center=draw_rect.center))

class ClickableMeter:
    def __init__(self, x_center, y_base, label, color, default_is_credits=True):
        self.x_center = s(x_center) + X_OFFSET; self.y_base = s(y_base) + Y_OFFSET
        self.label = label; self.color = color; self.show_credits = default_is_credits
        self.rect = pygame.Rect(self.x_center - s(60), self.y_base, s(120), s(60))
    def check_click(self, pos):
        if self.rect.collidepoint(pos): self.show_credits = not self.show_credits; return True
        return False
    def draw(self, screen, assets, dollar_value, denom):
        val_str = f"{int(dollar_value / denom)}" if self.show_credits else f"${dollar_value:.2f}"
        lbl_surf = assets.font_lbl.render(self.label, True, C_YEL_TEXT)
        val_surf = assets.font_vfd.render(val_str, True, self.color)
        screen.blit(lbl_surf, (self.x_center - lbl_surf.get_width()//2, self.y_base))
        screen.blit(val_surf, (self.x_center - val_surf.get_width()//2, self.y_base + s(20)))

class VolumeButton:
    def __init__(self, x, y, sound_manager):
        self.rect = s_rect(x, y, 40, 40); self.sm = sound_manager; self.level = 1; self.levels = [0.0, 0.3, 0.6, 1.0]; self.sm.set_volume(self.levels[self.level])
    def check_click(self, pos):
        if self.rect.collidepoint(pos): self.level = (self.level + 1) % 4; self.sm.set_volume(self.levels[self.level]); self.level > 0 and self.sm.play("bet"); return True
        return False
    def draw(self, screen):
        pygame.draw.rect(screen, (50, 50, 50), self.rect, border_radius=s(5)); pygame.draw.rect(screen, C_WHITE, self.rect, s(2), border_radius=s(5))
        cx, cy = self.rect.centerx, self.rect.centery; poly_color = C_WHITE if self.level > 0 else (150, 150, 150)
        pygame.draw.polygon(screen, poly_color, [(cx-s(8), cy-s(5)), (cx-s(8), cy+s(5)), (cx+s(2), cy+s(10)), (cx+s(2), cy-s(10))])
        if self.level >= 1: pygame.draw.arc(screen, poly_color, (cx-s(5), cy-s(6), s(14), s(12)), -math.pi/2.5, math.pi/2.5, s(2))
        if self.level >= 2: pygame.draw.arc(screen, poly_color, (cx-s(5), cy-s(10), s(18), s(20)), -math.pi/2.5, math.pi/2.5, s(2))
        if self.level >= 3: pygame.draw.arc(screen, poly_color, (cx-s(5), cy-s(14), s(22), s(28)), -math.pi/2.5, math.pi/2.5, s(2))
        if self.level == 0: pygame.draw.line(screen, C_DIGITAL_RED, (cx-s(10), cy-s(10)), (cx+s(10), cy+s(10)), s(3))

class CardSlot:
    def __init__(self, x, y, assets):
        self.rect = s_rect(x, y, 142, 215) # Original size passed, scaler handles scaling
        self.assets = assets; self.card_val = None; self.is_face_up = False; self.is_held = False; self.is_runner_up = False

    def draw(self, screen):
        img = self.assets.cards[self.card_val] if (self.is_face_up and self.card_val in self.assets.cards) else self.assets.back
        screen.blit(img, self.rect)
        if self.is_held and self.is_face_up:
            center_x = self.rect.centerx; top_y = self.rect.top - s(15)
            pygame.draw.circle(screen, C_GOLD_HELD, (center_x - s(30), top_y), s(8))
            pygame.draw.circle(screen, C_BLACK, (center_x - s(30), top_y), s(8), 1)
            lbl = self.assets.font_ui.render("HELD", True, C_GOLD_HELD)
            screen.blit(lbl, (center_x - s(15), top_y - s(10)))
            
        if self.is_runner_up and self.is_face_up:
            center_x = self.rect.centerx; bottom_y = self.rect.bottom + s(15)
            pygame.draw.circle(screen, C_SILVER, (center_x, bottom_y), s(8))
            pygame.draw.circle(screen, C_BLACK, (center_x, bottom_y), s(8), 1)

class PaytableDisplay:
    def __init__(self, assets, pay_data):
        self.rect = s_rect(260, 10, 960, 360)
        self.assets = assets; self.data = pay_data
        master = ["NATURAL_ROYAL", "FOUR_DEUCES_ACE", "FOUR_DEUCES", "FIVE_ACES", "FIVE_3_4_5", "FIVE_6_TO_K", "WILD_ROYAL", "FIVE_OAK", "STRAIGHT_FLUSH", "FOUR_OAK", "FULL_HOUSE", "FLUSH", "STRAIGHT", "THREE_OAK"]
        self.rows = [k for k in master if k in pay_data]
        self.labels = {"NATURAL_ROYAL":"ROYAL FLUSH", "FOUR_DEUCES_ACE":"4 DEUCES + A", "FOUR_DEUCES":"4 DEUCES", "FIVE_ACES":"5 ACES", "FIVE_3_4_5":"5 3s 4s 5s", "FIVE_6_TO_K":"5 6s THRU Ks", "WILD_ROYAL":"WILD ROYAL", "FIVE_OAK":"5 OF A KIND", "STRAIGHT_FLUSH":"STR FLUSH", "FOUR_OAK":"4 OF A KIND", "FULL_HOUSE":"FULL HOUSE", "FLUSH":"FLUSH", "STRAIGHT":"STRAIGHT", "THREE_OAK":"3 OF A KIND"}

    def draw(self, screen, coins_bet, winning_rank=None):
        pygame.draw.rect(screen, C_BG_BLUE, self.rect)
        col_w = (self.rect.width - s(160)) // 5
        active_x = self.rect.left + s(160) + ((coins_bet - 1) * col_w)
        pygame.draw.rect(screen, C_RED_ACTIVE, (active_x, self.rect.top, col_w, self.rect.height))
        for i in range(5): pygame.draw.line(screen, C_YEL_TEXT, (self.rect.left + s(160) + (i*col_w), self.rect.top), (self.rect.left + s(160) + (i*col_w), self.rect.bottom), s(2))
        start_y = self.rect.top + s(15)
        for i, key in enumerate(self.rows):
            y = start_y + (i * s(25)); col = C_WHITE if key == winning_rank else C_YEL_TEXT
            screen.blit(self.assets.font_grid.render(self.labels.get(key, key), True, col), (self.rect.left + s(10), y))
            base = self.data.get(key, 0)
            for c in range(1, 6):
                val = 4000 if key == "NATURAL_ROYAL" and c == 5 else base * c
                val_surf = self.assets.font_grid.render(str(val), True, C_YEL_TEXT)
                screen.blit(val_surf, (self.rect.left + s(160) + ((c-1)*col_w) + col_w - val_surf.get_width() - s(10), y))
        pygame.draw.rect(screen, C_YEL_TEXT, self.rect, s(2))