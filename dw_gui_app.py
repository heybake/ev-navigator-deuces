import pygame
import os
import sys
# Ensure dw_sim_engine.py is in the same directory or python path
import dw_sim_engine

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
# 🖼️ ASSET MANAGER (UPDATED to load Joker)
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

        # 2. Load Joker (NEW SECTION)
        joker_path = os.path.join(ASSET_DIR, "joker.png")
        if os.path.exists(joker_path):
            try:
                img = pygame.image.load(joker_path).convert_alpha()
                # Map the image to the 'JOKER' key used by the engine backend
                self.cards['JOKER'] = pygame.transform.smoothscale(img, CARD_SIZE)
                print("Loaded Joker image.")
            except Exception as e: print(f"Error loading Joker: {e}")
        else:
             print("Warning: joker.png not found.")

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
            pygame.draw.rect(screen, C_HELD_BORDER, self.rect, 4)
            stamp_rect = pygame.Rect(self.rect.centerx - 40, self.rect.bottom - 45, 80, 26)
            pygame.draw.rect(screen, C_HELD_BORDER, stamp_rect)
            lbl = self.assets.font_ui.render("HELD", True, C_BLACK)
            screen.blit(lbl, lbl.get_rect(center=stamp_rect.center))

class PaytableDisplay:
    def __init__(self, assets, pay_data):
        self.assets = assets
        self.data = pay_data
        self.rect = pygame.Rect(30, 20, 964, 280)
        self.rows = ["NATURAL_ROYAL", "FOUR_DEUCES", "WILD_ROYAL", "FIVE_OAK", "STRAIGHT_FLUSH", "FOUR_OAK", "FULL_HOUSE", "FLUSH", "STRAIGHT", "THREE_OAK"]
        self.labels = {"NATURAL_ROYAL": "ROYAL FLUSH", "FOUR_DEUCES": "4 DEUCES", "WILD_ROYAL": "WILD ROYAL", "FIVE_OAK": "5 OF A KIND", "STRAIGHT_FLUSH": "STR FLUSH", "FOUR_OAK": "4 OF A KIND", "FULL_HOUSE": "FULL HOUSE", "FLUSH": "FLUSH", "STRAIGHT": "STRAIGHT", "THREE_OAK": "3 OF A KIND"}

    def draw(self, screen, coins_bet, winning_rank=None):
        pygame.draw.rect(screen, C_BG_BLUE, self.rect)
        pygame.draw.rect(screen, C_WHITE, self.rect, 2)
        
        row_h = 25
        col_w = (self.rect.width - 160) // 5
        active_x = self.rect.left + 160 + ((coins_bet - 1) * col_w)
        pygame.draw.rect(screen, C_RED_ACTIVE, (active_x, self.rect.top, col_w, self.rect.height))
        
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
                val_surf = self.assets.font_grid.render(str(val), True, C_WHITE)
                screen.blit(val_surf, (x + col_w - val_surf.get_width() - 10, y))

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
        
        # Initialize Engine
        self.sim = dw_sim_engine.DeucesWildSim(variant="NSUD")
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
            PhysicalButton((30, y, w, h), "MORE GAMES", lambda: None),
            PhysicalButton((130, y, w, h), "SPEED", lambda: None),
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
            
            self.hand, self.stub = self.core.deal_hand()
            self.held_indices = []
            
            for i, c in enumerate(self.hand):
                self.cards[i].card_val = c
                self.cards[i].is_face_up = True
                self.cards[i].is_held = False
            
            self.sound.play("deal")
            self.state = "DECISION"
            self.btn_deal.text = "DRAW"
            
        elif self.state == "DECISION":
            held_cards = [self.hand[i] for i in self.held_indices]
            final_list = self.core.draw_from_stub(held_cards, self.stub)
            self.hand = final_list[0]
            
            for i, c in enumerate(self.hand):
                self.cards[i].card_val = c
                self.cards[i].is_held = False
            self.sound.play("deal")
            
            rank, mult = self.sim.evaluate_hand_score(self.hand)
            win_val = (mult * self.coins_bet) * self.denom
            
            if win_val > 0:
                self.sound.play("win")
                self.last_win_rank = rank
                self.win_target = win_val 
                self.bankroll += win_val
            
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