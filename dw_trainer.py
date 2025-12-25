import pygame
import os
import sys
import math
# Ensure dw_sim_engine.py is in the same directory or python path
import dw_sim_engine
# Import solvers
import dw_fast_solver
import dw_exact_solver 
from dw_pay_constants import PAYTABLES

# ==============================================================================
# ⚙️ CONFIGURATION & CONSTANTS
# ==============================================================================
SCREEN_W, SCREEN_H = 1400, 850 
FPS = 60

# COLORS
C_BG_BLUE     = (0, 0, 150)
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

# --- NOTEBOOK THEME ---
C_NB_BG       = (255, 255, 255)  # Paper White
C_NB_TEXT     = (20, 20, 20)     # Ink Black
C_NB_RED      = (200, 0, 0)      # Standard Red Ink
C_NB_BLACK    = (0, 0, 0)        # Standard Black Ink
C_NB_HIGHLIGHT= (255, 230, 80)   # High-vis Yellow
C_NB_LINES    = (200, 200, 200)  # Faint rule lines

# Path to card images relative to this script
ASSET_DIR = os.path.join("images", "cards")
SOUND_DIR = "sounds"
CARD_SIZE = (142, 215)

# ==============================================================================
# 🔊 SOUND MANAGER
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

    def play(self, name):
        if self.enabled and self.volume > 0 and name in self.sounds:
            self.sounds[name].play()

# ==============================================================================
# 🖼️ ASSET MANAGER
# ==============================================================================
class AssetManager:
    def __init__(self):
        self.cards = {}
        self.back = None
        # Fonts
        self.font_ui = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_grid = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_vfd = pygame.font.SysFont("Impact", 32)
        self.font_lbl = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_msg = pygame.font.SysFont("Arial", 24, bold=True)
        
        # Log Fonts
        self.font_log_bold = pygame.font.SysFont("Segoe UI Symbol", 16, bold=True)
        self.font_log = pygame.font.SysFont("Segoe UI Symbol", 16)
        
        self._load_textures()

    def _load_textures(self):
        print(f"Loading assets from: {os.path.abspath(ASSET_DIR)}")
        ranks = "23456789TJQKA"; suits = "shdc"
        count = 0
        for s in suits:
            for r in ranks:
                key = r + s
                path = os.path.join(ASSET_DIR, f"{key}.png")
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        self.cards[key] = pygame.transform.smoothscale(img, CARD_SIZE)
                        count += 1
                    except Exception as e: print(f"Error loading {key}: {e}")
        print(f"Loaded {count} standard card images.")

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
            s = pygame.Surface(CARD_SIZE)
            s.fill((0, 50, 200))
            pygame.draw.rect(s, C_WHITE, (5,5,130,200), 2)
            self.back = s

# ==============================================================================
# 📜 LOG PANEL (NOTEBOOK EDITION - INTERACTIVE SCROLL)
# ==============================================================================
class LogPanel:
    def __init__(self, x, y, w, h, assets):
        self.rect = pygame.Rect(x, y, w, h)
        self.assets = assets
        self.logs = [] 
        self.scroll_y = 0 
        self.entry_height = 110
        self.content_height = 0
        self.header_h = 40
        
        # Scroll Interaction State
        self.is_dragging = False
        self.drag_start_y = 0
        self.scroll_start_y = 0
        self.thumb_rect = pygame.Rect(0,0,0,0) 

    def add_entry(self, hand_num, deal_cards, final_cards, held_indices, ev_data, result_data):
        entry = {
            'id': hand_num,
            'deal': deal_cards,
            'final': final_cards,
            'held_idx': held_indices,
            'ev': ev_data,
            'result': result_data
        }
        self.logs.insert(0, entry)
        self.content_height = len(self.logs) * self.entry_height

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        # 1. Mouse Wheel
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(mouse_pos):
                self.scroll_y -= event.y * 20
                self._clamp_scroll()

        # 2. Start Drag
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                if self.thumb_rect.collidepoint(mouse_pos):
                    self.is_dragging = True
                    self.drag_start_y = mouse_pos[1]
                    self.scroll_start_y = self.scroll_y

        # 3. Stop Drag
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False

        # 4. Dragging Motion
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                delta_y = mouse_pos[1] - self.drag_start_y
                view_h = self.rect.height - self.header_h
                track_h = view_h 
                if self.content_height > view_h and track_h > 0:
                    ratio = self.content_height / track_h
                    self.scroll_y = self.scroll_start_y + (delta_y * ratio)
                    self._clamp_scroll()

    def _clamp_scroll(self):
        view_h = self.rect.height - self.header_h
        max_scroll = max(0, self.content_height - view_h)
        if self.scroll_y < 0: self.scroll_y = 0
        if self.scroll_y > max_scroll: self.scroll_y = max_scroll

    def draw_cards_text(self, screen, cards, x, y, highlights=None):
        suit_map = {'s': '♠', 'c': '♣', 'h': '♥', 'd': '♦'}
        font = self.assets.font_log_bold
        char_w = 35 
        
        for i, card in enumerate(cards):
            current_x = x + (i * char_w)
            
            # 1. Draw Highlighter
            if highlights and i in highlights:
                bg_rect = pygame.Rect(current_x - 2, y, char_w - 2, 20)
                pygame.draw.rect(screen, C_NB_HIGHLIGHT, bg_rect)

            # 2. Determine Color
            rank = card[0]
            suit_char = card[1]
            symbol = suit_map.get(suit_char, suit_char)
            color = C_NB_RED if suit_char in 'hd' else C_NB_BLACK
            
            # 3. Draw Text
            txt = font.render(f"{rank}{symbol}", True, color)
            screen.blit(txt, (current_x, y))

    def draw(self, screen):
        # 1. Background
        pygame.draw.rect(screen, C_NB_BG, self.rect)
        pygame.draw.rect(screen, C_NB_TEXT, self.rect, 2)
        
        # 2. Header
        pygame.draw.rect(screen, (240, 240, 240), (self.rect.left, self.rect.top, self.rect.width, self.header_h))
        pygame.draw.line(screen, C_NB_TEXT, (self.rect.left, self.rect.top + self.header_h), (self.rect.right, self.rect.top + self.header_h), 2)
        
        title = self.assets.font_ui.render("LABORATORY NOTEBOOK", True, C_NB_TEXT)
        screen.blit(title, (self.rect.centerx - title.get_width()//2, self.rect.top + 10))
        
        # 3. Clipping Area
        clip_rect = pygame.Rect(self.rect.left, self.rect.top + self.header_h, self.rect.width, self.rect.height - self.header_h)
        original_clip = screen.get_clip()
        screen.set_clip(clip_rect)
        
        start_y = (self.rect.top + self.header_h + 10) - self.scroll_y
        
        for i, log in enumerate(self.logs):
            y = start_y + (i * self.entry_height)
            
            # Optimize drawing
            if y + self.entry_height < self.rect.top or y > self.rect.bottom:
                continue
            
            # Rule Line
            pygame.draw.line(screen, C_NB_LINES, (self.rect.left + 10, y + self.entry_height - 10), (self.rect.right - 20, y + self.entry_height - 10))
            
            # Line 1: ID + Result
            id_txt = self.assets.font_log_bold.render(f"#{log['id']}", True, (100, 100, 100))
            screen.blit(id_txt, (self.rect.left + 15, y))
            
            win_amt = log['result']['win']
            if win_amt > 0:
                win_str = f"WIN: ${win_amt:.2f} ({log['result']['rank']})"
                win_col = (0, 150, 0)
            else:
                win_str = "Result: Loss"
                win_col = (150, 150, 150)
            
            win_txt = self.assets.font_log_bold.render(win_str, True, win_col)
            screen.blit(win_txt, (self.rect.left + 70, y))
            
            # Line 2: Deal (Highlighted)
            lbl_deal = self.assets.font_log.render("Deal:", True, C_NB_TEXT)
            screen.blit(lbl_deal, (self.rect.left + 15, y + 25))
            self.draw_cards_text(screen, log['deal'], self.rect.left + 70, y + 25, highlights=log['held_idx'])
            
            # Line 3: Final (Highlighted!)
            lbl_fin = self.assets.font_log.render("Final:", True, C_NB_TEXT)
            screen.blit(lbl_fin, (self.rect.left + 15, y + 50))
            self.draw_cards_text(screen, log['final'], self.rect.left + 70, y + 50, highlights=log['held_idx'])
            
            # Line 4: EV Decision
            user_ev = log['ev']['user']
            max_ev = log['ev']['max']
            diff = max_ev - user_ev
            
            if diff < 0.025: # Slightly more tolerance for rounding (0.025 = 1/40th of a credit)
                dec_txt = self.assets.font_log_bold.render(f"✅ Optimal (EV: {max_ev:.4f})", True, (0, 120, 0))
            else:
                dec_txt = self.assets.font_log_bold.render(f"❌ Error: -{diff:.4f} EV (Max: {max_ev:.4f})", True, C_NB_RED)
                
            screen.blit(dec_txt, (self.rect.left + 15, y + 75))

        screen.set_clip(original_clip)
        
        # 4. Scrollbar Logic
        if self.content_height > clip_rect.height:
            bar_h = clip_rect.height
            thumb_h = max(30, (clip_rect.height / self.content_height) * bar_h)
            scroll_percent = self.scroll_y / (self.content_height - clip_rect.height) if (self.content_height - clip_rect.height) > 0 else 0
            available_track = bar_h - thumb_h
            thumb_y = clip_rect.top + (scroll_percent * available_track)
            
            self.thumb_rect = pygame.Rect(self.rect.right - 14, thumb_y, 12, thumb_h)
            
            pygame.draw.rect(screen, (230, 230, 230), (self.rect.right - 14, clip_rect.top, 12, bar_h))
            thumb_col = (150, 150, 150) if not self.is_dragging else (100, 100, 100)
            pygame.draw.rect(screen, thumb_col, self.thumb_rect, border_radius=4)
        else:
            self.thumb_rect = pygame.Rect(0,0,0,0)

# ==============================================================================
# 🧩 UI COMPONENTS (Existing)
# ==============================================================================
class PhysicalButton:
    def __init__(self, rect, text, callback, color=C_BTN_FACE):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover = False
        self.is_pressed = False

    def update(self, mouse_pos, mouse_down):
        self.hover = self.rect.collidepoint(mouse_pos)
        if self.hover and mouse_down:
            self.is_pressed = True
        else:
            if self.is_pressed and self.hover and not mouse_down:
                self.callback()
            self.is_pressed = False

    def draw(self, screen, font):
        draw_rect = self.rect.move(2, 2) if self.is_pressed else self.rect
        if not self.is_pressed:
            pygame.draw.rect(screen, C_BTN_SHADOW, self.rect.move(4, 4), border_radius=6)
        
        col = (255, 255, 200) if self.hover else self.color
        pygame.draw.rect(screen, col, draw_rect, border_radius=6)
        pygame.draw.rect(screen, C_BLACK, draw_rect, 2, border_radius=6)
        
        txt = font.render(self.text, True, C_BLACK)
        txt_rect = txt.get_rect(center=draw_rect.center)
        screen.blit(txt, txt_rect)

class ClickableMeter:
    def __init__(self, x_center, y_base, label, color, default_is_credits=True):
        self.x_center = x_center
        self.y_base = y_base
        self.label = label
        self.color = color
        self.show_credits = default_is_credits
        self.rect = pygame.Rect(x_center - 60, y_base, 120, 60)

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.show_credits = not self.show_credits
            return True
        return False

    def draw(self, screen, assets, dollar_value, denom):
        if self.show_credits:
            val_str = f"{int(dollar_value / denom)}"
        else:
            val_str = f"${dollar_value:.2f}"

        lbl_surf = assets.font_lbl.render(self.label, True, C_YEL_TEXT)
        val_surf = assets.font_vfd.render(val_str, True, self.color)

        screen.blit(lbl_surf, (self.x_center - lbl_surf.get_width()//2, self.y_base))
        screen.blit(val_surf, (self.x_center - val_surf.get_width()//2, self.y_base + 20))

class VolumeButton:
    def __init__(self, x, y, sound_manager):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.sm = sound_manager
        self.level = 2 
        self.levels = [0.0, 0.3, 0.6, 1.0]
        self.sm.set_volume(self.levels[self.level])

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.level = (self.level + 1) % 4
            self.sm.set_volume(self.levels[self.level])
            if self.level > 0:
                self.sm.play("bet") 
            return True
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, (50, 50, 50), self.rect, border_radius=5)
        pygame.draw.rect(screen, C_WHITE, self.rect, 2, border_radius=5)
        
        cx, cy = self.rect.centerx, self.rect.centery
        poly_color = C_WHITE if self.level > 0 else (150, 150, 150)
        p1 = (cx - 8, cy - 5); p2 = (cx - 8, cy + 5)
        p3 = (cx + 2, cy + 10); p4 = (cx + 2, cy - 10)
        pygame.draw.polygon(screen, poly_color, [p1, p2, p3, p4])
        
        if self.level >= 1: pygame.draw.arc(screen, poly_color, (cx-5, cy-6, 14, 12), -math.pi/2.5, math.pi/2.5, 2)
        if self.level >= 2: pygame.draw.arc(screen, poly_color, (cx-5, cy-10, 18, 20), -math.pi/2.5, math.pi/2.5, 2)
        if self.level >= 3: pygame.draw.arc(screen, poly_color, (cx-5, cy-14, 22, 28), -math.pi/2.5, math.pi/2.5, 2)
        if self.level == 0: pygame.draw.line(screen, C_DIGITAL_RED, (cx-10, cy-10), (cx+10, cy+10), 3)

class CardSlot:
    def __init__(self, x, y, assets):
        self.rect = pygame.Rect(x, y, CARD_SIZE[0], CARD_SIZE[1])
        self.assets = assets
        self.card_val = None
        self.is_face_up = False
        self.is_held = False

    def draw(self, screen):
        img = self.assets.back
        if self.is_face_up and self.card_val in self.assets.cards:
            img = self.assets.cards[self.card_val]
        
        screen.blit(img, self.rect)

        if self.is_held and self.is_face_up:
            stamp_rect = pygame.Rect(self.rect.centerx - 40, self.rect.top - 30, 80, 26)
            pygame.draw.rect(screen, C_DIGITAL_RED, stamp_rect)
            lbl = self.assets.font_ui.render("HELD", True, C_YEL_TEXT)
            screen.blit(lbl, lbl.get_rect(center=stamp_rect.center))

class PaytableDisplay:
    def __init__(self, assets, pay_data):
        self.rect = pygame.Rect(30, 20, 964, 360)
        self.assets = assets
        self.data = pay_data
        
        master_order = ["NATURAL_ROYAL", "FOUR_DEUCES_ACE", "FOUR_DEUCES", "FIVE_ACES", "FIVE_3_4_5", "FIVE_6_TO_K", "WILD_ROYAL", "FIVE_OAK", "STRAIGHT_FLUSH", "FOUR_OAK", "FULL_HOUSE", "FLUSH", "STRAIGHT", "THREE_OAK"]
        self.rows = [key for key in master_order if key in pay_data]
        self.labels = {
            "NATURAL_ROYAL": "ROYAL FLUSH", "FOUR_DEUCES_ACE": "4 DEUCES + A", "FOUR_DEUCES": "4 DEUCES", 
            "FIVE_ACES": "5 ACES", "FIVE_3_4_5": "5 3s 4s 5s", "FIVE_6_TO_K": "5 6s THRU Ks",
            "WILD_ROYAL": "WILD ROYAL", "FIVE_OAK": "5 OF A KIND", "STRAIGHT_FLUSH": "STR FLUSH", 
            "FOUR_OAK": "4 OF A KIND", "FULL_HOUSE": "FULL HOUSE", "FLUSH": "FLUSH", 
            "STRAIGHT": "STRAIGHT", "THREE_OAK": "3 OF A KIND"
        }

    def draw(self, screen, coins_bet, winning_rank=None):
        pygame.draw.rect(screen, C_BG_BLUE, self.rect)
        row_h = 25
        col_w = (self.rect.width - 160) // 5
        active_x = self.rect.left + 160 + ((coins_bet - 1) * col_w)
        
        pygame.draw.rect(screen, C_RED_ACTIVE, (active_x, self.rect.top, col_w, self.rect.height))
        
        for i in range(5):
            x = self.rect.left + 160 + (i * col_w)
            pygame.draw.line(screen, C_YEL_TEXT, (x, self.rect.top), (x, self.rect.bottom), 2)
        
        start_y = self.rect.top + 15
        for i, key in enumerate(self.rows):
            y = start_y + (i * row_h)
            text_color = C_WHITE if key == winning_rank else C_YEL_TEXT
            name = self.labels.get(key, key)
            screen.blit(self.assets.font_grid.render(name, True, text_color), (self.rect.left + 10, y))
            
            base = self.data.get(key, 0)
            for c in range(1, 6):
                val = base * c
                if key == "NATURAL_ROYAL" and c == 5: val = 4000
                x = self.rect.left + 160 + ((c-1) * col_w)
                val_surf = self.assets.font_grid.render(str(val), True, C_YEL_TEXT)
                screen.blit(val_surf, (x + col_w - val_surf.get_width() - 10, y))

        pygame.draw.rect(screen, C_YEL_TEXT, self.rect, 2)

# ==============================================================================
# 🎮 MAIN SYSTEM (TRAINER EDITION)
# ==============================================================================
class IGT_Machine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("EV Navigator - Deuces Wild Trainer (Extended)")
        self.clock = pygame.time.Clock()
        
        self.assets = AssetManager()
        self.sound = SoundManager()
        
        self.available_variants = list(PAYTABLES.keys())
        self.variant_idx = 0 
        self.sim = dw_sim_engine.DeucesWildSim(variant=self.available_variants[self.variant_idx])
        self.core = self.sim.core
        
        self.paytable = PaytableDisplay(self.assets, self.sim.paytable)
        
        # Initialize Log Panel (Right Side)
        self.log_panel = LogPanel(1034, 20, 350, 810, self.assets)
        
        self.cards = []
        for i in range(5):
            self.cards.append(CardSlot(132 + (i * 152), 410, self.assets))
            
        self.auto_hold_active = False 
        self.auto_play_active = False 
        self.last_action_time = 0     
        self.advice_msg = None        
        
        self.hands_played = 0
        self._init_buttons()
        self._init_meters()
        self.vol_btn = VolumeButton(965, 785, self.sound)

        self.state = "IDLE"
        self.bankroll = 100.00
        self.coins_bet = 5
        self.denom = 0.25
        self.win_display = 0.0
        self.win_target = 0.0
        self.last_win_rank = None
        self.hand = []
        self.stub = []
        self.held_indices = []
        # Store deal snapshot for log
        self.deal_snapshot = []

    def _init_buttons(self):
        y = 780; w, h = 90, 50
        self.buttons = [
            PhysicalButton((30, y, 120, h), "MORE GAMES", self.act_cycle_variant),
            PhysicalButton((160, y, w, h), "AUTO HOLD", self.act_toggle_auto_hold, color=C_DIGITAL_YEL),
            PhysicalButton((270, y, 110, h), "AUTO PLAY", self.act_toggle_auto_play, color=C_BTN_FACE),
            PhysicalButton((400, y, w, h), "BET ONE", self.act_bet_one),
            PhysicalButton((500, y, w, h), "BET MAX", self.act_bet_max),
            PhysicalButton((800, y, 150, h), "DEAL", self.act_deal_draw, color=(255, 215, 0))
        ]
        self.btn_auto_hold = self.buttons[1] 
        self.btn_auto_play = self.buttons[2]
        self.btn_deal = self.buttons[-1]

    def _init_meters(self):
        self.meter_win = ClickableMeter(100, 680, "WIN", C_DIGITAL_RED, default_is_credits=True)
        self.meter_bet = ClickableMeter(500, 680, "BET", C_DIGITAL_YEL, default_is_credits=True)
        self.meter_credit = ClickableMeter(900, 680, "CREDIT", C_DIGITAL_RED, default_is_credits=False)
        self.meters = [self.meter_win, self.meter_bet, self.meter_credit]

    def act_toggle_auto_hold(self):
        self.auto_hold_active = not self.auto_hold_active
        if self.auto_hold_active:
            self.btn_auto_hold.text = "AUTO: ON"
            self.btn_auto_hold.color = C_DIGITAL_GRN 
            if self.state == "DECISION":
                self.run_solver()
        else:
            self.btn_auto_hold.text = "AUTO HOLD"
            self.btn_auto_hold.color = C_DIGITAL_YEL 
            self.advice_msg = None

    def act_toggle_auto_play(self):
        self.auto_play_active = not self.auto_play_active
        if self.auto_play_active:
            self.btn_auto_play.text = "STOP"
            self.btn_auto_play.color = C_DIGITAL_RED
            self.last_action_time = pygame.time.get_ticks()
        else:
            self.btn_auto_play.text = "AUTO PLAY"
            self.btn_auto_play.color = C_BTN_FACE

    def run_solver(self):
        best_cards, _ = dw_fast_solver.solve_hand(self.hand, self.sim.paytable)
        self.held_indices = []
        for i, card in enumerate(self.hand):
            if card in best_cards:
                self.cards[i].is_held = True
                self.held_indices.append(i)
            else:
                self.cards[i].is_held = False
        
        if not best_cards:
            self.advice_msg = "ADVICE: DRAW ALL"
        else:
            self.advice_msg = None 
        self.sound.play("bet")

    def act_cycle_variant(self):
        if self.state != "IDLE": return 
        self.variant_idx = (self.variant_idx + 1) % len(self.available_variants)
        new_variant = self.available_variants[self.variant_idx]
        self.sim = dw_sim_engine.DeucesWildSim(variant=new_variant)
        self.core = self.sim.core
        self.paytable = PaytableDisplay(self.assets, self.sim.paytable)
        self.sound.play("bet")
        pygame.display.set_caption(f"IGT Game King Replica ({new_variant})")

    def act_bet_one(self):
        if self.state != "IDLE": return
        self.coins_bet = 1 if self.coins_bet >= 5 else self.coins_bet + 1
        self.sound.play("bet")

    def act_bet_max(self):
        if self.state != "IDLE": return
        self.coins_bet = 5
        self.sound.play("bet")
        self.act_deal_draw()

    def act_deal_draw(self):
        if self.state == "IDLE":
            cost = self.coins_bet * self.denom
            if self.bankroll < cost: return
            self.bankroll -= cost
            
            self.win_display = 0.0
            self.win_target = 0.0
            self.last_win_rank = None
            self.advice_msg = None 
            
            self.hand, self.stub = self.core.deal_hand()
            self.deal_snapshot = list(self.hand) # Keep copy for log
            self.hands_played += 1
            self.held_indices = []
            
            for i, c in enumerate(self.hand):
                self.cards[i].card_val = c
                self.cards[i].is_face_up = True
                self.cards[i].is_held = False
            
            rank, mult = self.sim.evaluate_hand_score(self.hand)
            if mult > 0: self.last_win_rank = rank
            else: self.last_win_rank = None
            
            self.sound.play("deal")
            self.state = "DECISION"
            self.btn_deal.text = "DRAW"
            
            if self.auto_hold_active or self.auto_play_active:
                self.run_solver()
            
        elif self.state == "DECISION":
            self.advice_msg = None
            
            # --- PERFORMANCE OPTIMIZATION: USE FAST SOLVER ---
            optimal_hold, max_ev = dw_fast_solver.solve_hand(self.hand, self.sim.paytable)
            
            user_hold_cards = [self.hand[i] for i in self.held_indices]
            
            if set(user_hold_cards) == set(optimal_hold):
                user_ev = max_ev # Perfect play!
            else:
                user_ev = dw_exact_solver.calculate_exact_ev(self.hand, self.held_indices, self.sim.paytable)
            
            # --- FIX: SCALE EV TO MAX BET ---
            max_ev_disp = max_ev * self.coins_bet
            user_ev_disp = user_ev * self.coins_bet
            
            # Record current held indices for the log BEFORE replacing cards
            logged_held_indices = list(self.held_indices)

            # 3. Process Draw
            self.core.shuffle(self.stub)
            for i in range(5):
                if i not in self.held_indices:
                    if self.stub:
                        new_card = self.stub.pop(0) 
                        self.hand[i] = new_card
            
            for i, c in enumerate(self.hand):
                self.cards[i].card_val = c
            
            self.sound.play("deal")
            
            rank, mult = self.sim.evaluate_hand_score(self.hand)
            win_val = (mult * self.coins_bet) * self.denom
            
            if win_val > 0:
                self.sound.play("win")
                self.last_win_rank = rank
                self.win_target = win_val 
                self.bankroll += win_val
            else:
                self.last_win_rank = None
                
            # --- LOG IT (With Scaled EV) ---
            self.log_panel.add_entry(
                self.hands_played,
                self.deal_snapshot,
                list(self.hand),
                logged_held_indices,
                {'user': user_ev_disp, 'max': max_ev_disp},
                {'win': win_val, 'rank': rank.replace('_',' ')}
            )
            
            self.state = "IDLE"
            self.btn_deal.text = "DEAL"

    def handle_click(self, pos):
        if self.vol_btn.check_click(pos):
            return

        for m in self.meters:
            if m.check_click(pos):
                self.sound.play("bet")
                return

        if self.state == "DECISION":
            for i, slot in enumerate(self.cards):
                if slot.rect.collidepoint(pos):
                    self.advice_msg = None
                    slot.is_held = not slot.is_held
                    if slot.is_held: self.held_indices.append(i)
                    else: self.held_indices.remove(i)

    def update_auto_play(self):
        if not self.auto_play_active: return
        now = pygame.time.get_ticks()
        if now - self.last_action_time > 400:
            self.last_action_time = now
            if self.state == "IDLE":
                self.act_deal_draw()
            elif self.state == "DECISION":
                self.act_deal_draw()

    def draw_variant_label(self):
        label_text = f"Deuces Wild ({self.sim.variant})"
        text_surf = self.assets.font_ui.render(label_text, True, C_WHITE)
        self.screen.blit(text_surf, (20, 835))

    def draw_denom_badge(self):
        cents = int(self.denom * 100)
        text = f"{cents}¢"
        center_x, center_y = 730, 805
        radius_x, radius_y = 40, 25
        rect = pygame.Rect(center_x - radius_x, center_y - radius_y, radius_x * 2, radius_y * 2)
        pygame.draw.ellipse(self.screen, (255, 215, 0), rect) 
        pygame.draw.ellipse(self.screen, C_BLACK, rect, 2)
        font = pygame.font.SysFont("timesnewroman", 28, bold=True)
        txt_surf = font.render(text, True, (200, 0, 0))
        txt_rect = txt_surf.get_rect(center=(center_x, center_y))
        self.screen.blit(txt_surf, txt_rect)

    def draw(self):
        self.screen.fill(C_BLACK)
        self.paytable.draw(self.screen, self.coins_bet, self.last_win_rank)
        self.log_panel.draw(self.screen) # Draw Log
        
        pygame.draw.rect(self.screen, C_BG_BLUE, (0, 380, 1024, 280)) # Adjusted width for blue area
        pygame.draw.line(self.screen, C_WHITE, (0, 380), (1024, 380), 2)
        pygame.draw.line(self.screen, C_WHITE, (0, 660), (1024, 660), 2)
        
        self.vol_btn.draw(self.screen)

        if self.advice_msg:
            msg_surf = self.assets.font_msg.render(self.advice_msg, True, C_CYAN_MSG)
            msg_rect = msg_surf.get_rect(center=(512, 395)) # Centered relative to game area
            bg_rect = msg_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, (0,0,50), bg_rect, border_radius=5)
            pygame.draw.rect(self.screen, C_CYAN_MSG, bg_rect, 2, border_radius=5)
            self.screen.blit(msg_surf, msg_rect)
            
        if self.auto_play_active:
            pilot_surf = self.assets.font_ui.render("PILOT ENGAGED", True, C_DIGITAL_GRN)
            self.screen.blit(pilot_surf, (300, 835))
            
        deals_surf = self.assets.font_lbl.render(f"DEALS: {self.hands_played}", True, C_YEL_TEXT)
        self.screen.blit(deals_surf, (30, 750)) 

        for c in self.cards: c.draw(self.screen)
        
        if self.win_display < self.win_target:
            self.win_display += self.denom 
            if self.win_display >= self.win_target: 
                self.win_display = self.win_target
            
        self.meter_win.draw(self.screen, self.assets, self.win_display, self.denom)
        self.meter_bet.draw(self.screen, self.assets, self.coins_bet * self.denom, self.denom)
        self.meter_credit.draw(self.screen, self.assets, self.bankroll, self.denom)
        
        self.draw_variant_label()
        self.draw_denom_badge()

        mouse_pos = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        for b in self.buttons:
            b.update(mouse_pos, mouse_down)
            b.draw(self.screen, self.assets.font_ui)
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.update_auto_play()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.MOUSEBUTTONUP: 
                    # Handle all mouse click interactions (buttons + scrollbar drag start)
                    self.handle_click(event.pos)
                    self.log_panel.handle_event(event)
                elif event.type in [pygame.MOUSEWHEEL, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                    # Pass other events to log panel for scrolling/dragging
                    self.log_panel.handle_event(event)
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_a: self.act_toggle_auto_hold()
                    elif event.key == pygame.K_p: self.act_toggle_auto_play()
                    elif event.key == pygame.K_SPACE: self.act_deal_draw()

            self.draw()
            self.clock.tick(FPS)
        pygame.quit(); sys.exit()

if __name__ == "__main__":
    app = IGT_Machine()
    app.run()