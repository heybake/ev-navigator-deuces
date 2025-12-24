import pygame
import os
import sys
# Ensure dw_sim_engine.py is in the same directory or python path
import dw_sim_engine
from dw_pay_constants import PAYTABLES

# ==============================================================================
# ⚙️ CONFIGURATION & CONSTANTS
# ==============================================================================
SCREEN_W, SCREEN_H = 1024, 768
FPS = 60

# COLORS
C_BG_BLUE     = (0, 0, 150)
C_BLACK       = (0, 0, 0)
C_WHITE       = (255, 255, 255)
C_YEL_TEXT    = (255, 255, 0)
C_RED_ACTIVE  = (180, 0, 0)
C_DIGITAL_RED = (255, 50, 50)
C_DIGITAL_YEL = (255, 255, 50)
C_BTN_FACE    = (230, 230, 230)
C_BTN_SHADOW  = (100, 100, 100)
C_HELD_BORDER = (255, 255, 0)

# Path to card images relative to this script
ASSET_DIR = os.path.join("images", "cards")
SOUND_DIR = "sounds"
# Final display size for cards in the game window
CARD_SIZE = (142, 215)

# ==============================================================================
# 🔊 SOUND MANAGER
# ==============================================================================
class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        if os.path.exists(SOUND_DIR):
            self._load("bet", "bet.wav")
            self._load("deal", "deal.wav")
            self._load("win", "win.wav")
            self._load("rollup", "rollup.wav")

    def _load(self, name, filename):
        try:
            path = os.path.join(SOUND_DIR, filename)
            self.sounds[name] = pygame.mixer.Sound(path)
        except: pass

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

# ==============================================================================
# 🖼️ ASSET MANAGER
# ==============================================================================
class AssetManager:
    def __init__(self):
        self.cards = {}
        self.back = None
        # Initialize fonts needed for UI
        self.font_ui = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_grid = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_vfd = pygame.font.SysFont("Impact", 32)
        self.font_lbl = pygame.font.SysFont("Arial", 14, bold=True)
        # Start loading images
        self._load_textures()

    def _load_textures(self):
        print(f"Loading assets from: {os.path.abspath(ASSET_DIR)}")
        
        # 1. Load Standard 52 Cards
        ranks = "23456789TJQKA"; suits = "shdc"
        count = 0
        for s in suits:
            for r in ranks:
                key = r + s # e.g., "Th", "As", "2c"
                path = os.path.join(ASSET_DIR, f"{key}.png")
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        #Resize to game/display size
                        self.cards[key] = pygame.transform.smoothscale(img, CARD_SIZE)
                        count += 1
                    except Exception as e: print(f"Error loading {key}: {e}")
        print(f"Loaded {count} standard card images.")

        # 2. Load Joker (Optional, strictly IGT Deuces Wild uses 52 cards)
        joker_path = os.path.join(ASSET_DIR, "joker.png")
        if os.path.exists(joker_path):
            try:
                img = pygame.image.load(joker_path).convert_alpha()
                self.cards['JOKER'] = pygame.transform.smoothscale(img, CARD_SIZE)
                print("Loaded Joker image.")
            except Exception as e: print(f"Error loading Joker: {e}")

        # 3. Load Card Back
        back_path = os.path.join(ASSET_DIR, "back.png")
        if os.path.exists(back_path):
            try:
                img = pygame.image.load(back_path).convert_alpha()
                self.back = pygame.transform.smoothscale(img, CARD_SIZE)
                print("Loaded Card Back.")
            except Exception as e: print(f"Error loading back.png: {e}")
        else:
            # Fallback placeholder if back.png is missing
            print("Warning: back.png not found. Using placeholder.")
            s = pygame.Surface(CARD_SIZE)
            s.fill((0, 50, 200))
            pygame.draw.rect(s, C_WHITE, (5,5,130,200), 2)
            self.back = s

# ==============================================================================
# 🧩 UI COMPONENTS
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
    """ A VFD meter that toggles between Credits and Cash when clicked. """
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

class CardSlot:
    def __init__(self, x, y, assets):
        self.rect = pygame.Rect(x, y, CARD_SIZE[0], CARD_SIZE[1])
        self.assets = assets
        self.card_val = None
        self.is_face_up = False
        self.is_held = False

    def draw(self, screen):
        # Default to back image
        img = self.assets.back
        # If face up AND we have the loaded image for this card value
        if self.is_face_up and self.card_val in self.assets.cards:
            img = self.assets.cards[self.card_val]
        
        screen.blit(img, self.rect)

        if self.is_held and self.is_face_up:
            # 1. No Border (Clean look)
            # 2. Red Stamp FLOATING ABOVE CARD (y - 30)
            stamp_rect = pygame.Rect(self.rect.centerx - 40, self.rect.top - 30, 80, 26)
            pygame.draw.rect(screen, C_DIGITAL_RED, stamp_rect)
            
            # 3. Yellow Text
            lbl = self.assets.font_ui.render("HELD", True, C_YEL_TEXT)
            screen.blit(lbl, lbl.get_rect(center=stamp_rect.center))

class PaytableDisplay:
    def __init__(self, assets, pay_data):
        self.assets = assets
        self.data = pay_data
        self.rect = pygame.Rect(30, 20, 964, 280)
        
        # 1. Master List of all possible display rows in Rank Order
        master_order = [
            "NATURAL_ROYAL", 
            "FOUR_DEUCES_ACE", 
            "FOUR_DEUCES", 
            "FIVE_ACES", 
            "WILD_ROYAL", 
            "FIVE_OAK", 
            "STRAIGHT_FLUSH", 
            "FOUR_OAK", 
            "FULL_HOUSE", 
            "FLUSH", 
            "STRAIGHT", 
            "THREE_OAK"
        ]
        
        # 2. Dynamic Filter: Only include rows that exist in the current variant's data
        self.rows = [key for key in master_order if key in pay_data]
        
        # 3. Label Map (Human Readable)
        self.labels = {
            "NATURAL_ROYAL": "ROYAL FLUSH", 
            "FOUR_DEUCES_ACE": "4 DEUCES + A",
            "FOUR_DEUCES": "4 DEUCES", 
            "FIVE_ACES": "5 ACES",
            "WILD_ROYAL": "WILD ROYAL", 
            "FIVE_OAK": "5 OF A KIND", 
            "STRAIGHT_FLUSH": "STR FLUSH", 
            "FOUR_OAK": "4 OF A KIND", 
            "FULL_HOUSE": "FULL HOUSE", 
            "FLUSH": "FLUSH", 
            "STRAIGHT": "STRAIGHT", 
            "THREE_OAK": "3 OF A KIND"
        }

    def draw(self, screen, coins_bet, winning_rank=None):
        # 1. Background (Bottom Layer)
        pygame.draw.rect(screen, C_BG_BLUE, self.rect)
        
        # --- DYNAMIC ROW HEIGHT LOGIC ---
        # Standard games have ~10 rows (fits in 280px with 25px spacing)
        # Bonus Deuces has 12 rows. We must shrink spacing to 22px to fit.
        if len(self.rows) > 10:
            row_h = 22
        else:
            row_h = 25
        
        col_w = (self.rect.width - 160) // 5
        active_x = self.rect.left + 160 + ((coins_bet - 1) * col_w)
        
        # 2. Red Active Column (Draw BEFORE grid lines and border)
        pygame.draw.rect(screen, C_RED_ACTIVE, (active_x, self.rect.top, col_w, self.rect.height))
        
        # 3. Vertical Grid Lines
        for i in range(5):
            x = self.rect.left + 160 + (i * col_w)
            pygame.draw.line(screen, C_YEL_TEXT, (x, self.rect.top), (x, self.rect.bottom), 2)
        
        # 4. Text Content
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
                # Render numbers in YELLOW
                val_surf = self.assets.font_grid.render(str(val), True, C_YEL_TEXT)
                screen.blit(val_surf, (x + col_w - val_surf.get_width() - 10, y))

        # 5. Outer Border (Top Layer - Ensures clean frame)
        pygame.draw.rect(screen, C_YEL_TEXT, self.rect, 2)

# ==============================================================================
# 🎮 MAIN SYSTEM
# ==============================================================================
class IGT_Machine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        # center window
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("IGT Game King Replica (Deuces Wild)")
        self.clock = pygame.time.Clock()
        
        # Load assets first
        self.assets = AssetManager()
        self.sound = SoundManager()
        
        # Initialize Engine with variant cycling logic
        self.available_variants = list(PAYTABLES.keys())
        self.variant_idx = 0  # Default to NSUD (Index 0)
        self.sim = dw_sim_engine.DeucesWildSim(variant=self.available_variants[self.variant_idx])
        self.core = self.sim.core
        
        self.paytable = PaytableDisplay(self.assets, self.sim.paytable)
        self.cards = []
        # Create 5 card slots on screen
        for i in range(5):
            self.cards.append(CardSlot(132 + (i * 152), 340, self.assets))
            
        self._init_buttons()
        self._init_meters()
        
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

    def _init_buttons(self):
        y = 700; w, h = 90, 50
        self.buttons = [
            PhysicalButton((30, y, 120, h), "MORE GAMES", self.act_cycle_variant),
            PhysicalButton((160, y, w, h), "SPEED", lambda: None),
            PhysicalButton((400, y, w, h), "BET ONE", self.act_bet_one),
            PhysicalButton((500, y, w, h), "BET MAX", self.act_bet_max),
            PhysicalButton((800, y, 150, h), "DEAL", self.act_deal_draw, color=(255, 215, 0))
        ]
        self.btn_deal = self.buttons[-1]

    def _init_meters(self):
        self.meter_win = ClickableMeter(100, 630, "WIN", C_DIGITAL_RED, default_is_credits=True)
        self.meter_bet = ClickableMeter(500, 630, "BET", C_DIGITAL_YEL, default_is_credits=True)
        self.meter_credit = ClickableMeter(900, 630, "CREDIT", C_DIGITAL_RED, default_is_credits=False)
        self.meters = [self.meter_win, self.meter_bet, self.meter_credit]

    def act_cycle_variant(self):
        """Cycles through available game variants (NSUD -> Airport -> Bonus, etc.)"""
        if self.state != "IDLE": return # Lockout during play

        # 1. Increment Index
        self.variant_idx = (self.variant_idx + 1) % len(self.available_variants)
        new_variant = self.available_variants[self.variant_idx]

        # 2. Re-Initialize Engine
        print(f"Switching to {new_variant}...")
        self.sim = dw_sim_engine.DeucesWildSim(variant=new_variant)
        self.core = self.sim.core # Re-link core (physics remains same, but good practice)

        # 3. Update Paytable GUI
        # We must create a new display object because it caches the pay data
        self.paytable = PaytableDisplay(self.assets, self.sim.paytable)

        # Optional: Flash a message or sound to confirm switch
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
            # --- DEAL PHASE ---
            cost = self.coins_bet * self.denom
            if self.bankroll < cost: return
            self.bankroll -= cost
            
            self.win_display = 0.0
            self.win_target = 0.0
            self.last_win_rank = None
            
            # Deal 5 cards from fresh deck
            self.hand, self.stub = self.core.deal_hand()
            self.held_indices = []
            
            for i, c in enumerate(self.hand):
                self.cards[i].card_val = c
                self.cards[i].is_face_up = True
                self.cards[i].is_held = False
            
            # --- PRE-DRAW EVALUATION (Fixes Pat Hand Indicator) ---
            # Evaluate the dealt hand immediately to light up the paytable
            rank, mult = self.sim.evaluate_hand_score(self.hand)
            if mult > 0:
                self.last_win_rank = rank
            else:
                self.last_win_rank = None
            
            self.sound.play("deal")
            self.state = "DECISION"
            self.btn_deal.text = "DRAW"
            
        elif self.state == "DECISION":
            # --- DRAW PHASE (FIXED) ---
            # 1. Shuffle the remaining cards (Critical for RNG integrity)
            self.core.shuffle(self.stub)
            
            # 2. Iterate through all 5 slots
            for i in range(5):
                # If this slot was NOT held by the player...
                if i not in self.held_indices:
                    # ...Replace the card in this slot with a new one from the stub
                    if self.stub:
                        new_card = self.stub.pop(0) 
                        self.hand[i] = new_card
            
            # 3. Update the UI
            for i, c in enumerate(self.hand):
                self.cards[i].card_val = c
                # REMOVED RESET LINE: self.cards[i].is_held = False 
            
            self.sound.play("deal")
            
            # 4. Evaluate
            rank, mult = self.sim.evaluate_hand_score(self.hand)
            win_val = (mult * self.coins_bet) * self.denom
            
            if win_val > 0:
                self.sound.play("win")
                self.last_win_rank = rank
                self.win_target = win_val 
                self.bankroll += win_val
            else:
                # Clear highlight if final hand is a loser
                self.last_win_rank = None
            
            self.state = "IDLE"
            self.btn_deal.text = "DEAL"

    def handle_click(self, pos):
        for m in self.meters:
            if m.check_click(pos):
                self.sound.play("bet")
                return

        if self.state == "DECISION":
            for i, slot in enumerate(self.cards):
                if slot.rect.collidepoint(pos):
                    slot.is_held = not slot.is_held
                    if slot.is_held: self.held_indices.append(i)
                    else: self.held_indices.remove(i)

    def draw_variant_label(self):
        """Draws the dynamic variant label in the bottom-left corner."""
        label_text = f"Deuces Wild ({self.sim.variant})"
        text_surf = self.assets.font_ui.render(label_text, True, C_WHITE)
        # Position: Left-aligned, near the bottom edge
        self.screen.blit(text_surf, (20, 750))

    def draw_denom_badge(self):
        """Draws the yellow oval indicator for the denomination."""
        # 1. Convert to Cents
        cents = int(self.denom * 100)
        text = f"{cents}¢"
        
        # 2. Define Shape (Between BET MAX and DEAL)
        center_x, center_y = 730, 725
        radius_x, radius_y = 40, 25
        rect = pygame.Rect(center_x - radius_x, center_y - radius_y, radius_x * 2, radius_y * 2)
        
        # 3. Draw Oval
        pygame.draw.ellipse(self.screen, (255, 215, 0), rect) # Gold Fill
        pygame.draw.ellipse(self.screen, C_BLACK, rect, 2)    # Black Border
        
        # 4. Draw Text
        font = pygame.font.SysFont("timesnewroman", 28, bold=True)
        txt_surf = font.render(text, True, (200, 0, 0)) # Red Text
        txt_rect = txt_surf.get_rect(center=(center_x, center_y))
        self.screen.blit(txt_surf, txt_rect)

    def draw(self):
        self.screen.fill(C_BLACK)
        self.paytable.draw(self.screen, self.coins_bet, self.last_win_rank)
        
        pygame.draw.rect(self.screen, C_BG_BLUE, (0, 310, SCREEN_W, 310))
        pygame.draw.line(self.screen, C_WHITE, (0, 310), (SCREEN_W, 310), 2)
        pygame.draw.line(self.screen, C_WHITE, (0, 620), (SCREEN_W, 620), 2)
        
        for c in self.cards: c.draw(self.screen)
        
        if self.win_display < self.win_target:
            self.win_display += self.denom 
            if self.win_display >= self.win_target: 
                self.win_display = self.win_target
            
        self.meter_win.draw(self.screen, self.assets, self.win_display, self.denom)
        self.meter_bet.draw(self.screen, self.assets, self.coins_bet * self.denom, self.denom)
        self.meter_credit.draw(self.screen, self.assets, self.bankroll, self.denom)
        
        # Draw the dynamic variant label
        self.draw_variant_label()
        
        # Draw the denom badge
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.MOUSEBUTTONUP: self.handle_click(event.pos)
            self.draw()
            self.clock.tick(FPS)
        pygame.quit(); sys.exit()

if __name__ == "__main__":
    app = IGT_Machine()
    app.run()