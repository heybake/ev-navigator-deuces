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
SCREEN_W, SCREEN_H = 1600, 850 
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

# --- PANEL THEMES ---
C_PANEL_BG    = (40, 45, 50)     # Dark Gray for Config
C_NB_BG       = (255, 255, 255)  # Paper White
C_NB_TEXT     = (20, 20, 20)     # Ink Black
C_NB_RED      = (200, 0, 0)      # Standard Red Ink
C_NB_BLACK    = (0, 0, 0)        # Standard Black Ink
C_NB_HIGHLIGHT= (255, 230, 80)   # High-vis Yellow
C_NB_LINES    = (200, 200, 200)  # Faint rule lines
C_GRAPH_BG    = (20, 25, 30)     # Dark Slate for Graph
C_GRAPH_GRID  = (50, 60, 70)     # Faint Grid
C_GRAPH_LINE_G= (0, 255, 100)    # Winning Line
C_GRAPH_LINE_R= (255, 80, 80)    # Losing Line
C_GRAPH_BASE  = (100, 100, 255)  # Baseline Blue
C_GRAPH_CEIL  = (0, 200, 0)      # Ceiling Line (Green)
C_GRAPH_FLOOR = (200, 0, 0)      # Floor Line (Red)

# --- IGT MENU THEME ---
C_IGT_BG      = (0, 0, 130)      # Deep Blue Background
C_IGT_GOLD    = (218, 165, 32)   # Goldenrod Border
C_IGT_RED     = (200, 0, 0)      # Red Inset
C_IGT_TXT_BG  = (0, 0, 80)       # Dark Blue Text Box
C_IGT_TXT     = (0, 255, 255)    # Cyan Text
C_IGT_TXT_SEL = (255, 255, 0)    # Yellow Text (Selected)

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
        self.font_ui = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_grid = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_vfd = pygame.font.SysFont("Impact", 32)
        self.font_lbl = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_msg = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_log_bold = pygame.font.SysFont("Segoe UI Symbol", 16, bold=True)
        self.font_log = pygame.font.SysFont("Segoe UI Symbol", 16)
        self.font_tiny = pygame.font.SysFont("Arial", 12)
        
        # New Fonts for IGT Menu
        self.font_menu_title = pygame.font.SysFont("Arial Black", 24)
        self.font_menu_item = pygame.font.SysFont("Arial Narrow", 22, bold=True)
        
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
# 🎮 GAME SELECTOR SCREEN (IGT STYLE)
# ==============================================================================
class GameSelectorScreen:
    def __init__(self, rect, assets, machine, variants):
        self.rect = rect
        self.assets = assets
        self.machine = machine
        self.variants = variants
        self.buttons = []
        self._layout_buttons()

    def _layout_buttons(self):
        # 4 Columns grid
        cols = 4
        btn_w, btn_h = 220, 100
        gap_x, gap_y = 20, 30
        
        # Calculate start pos to center the grid
        total_w = (cols * btn_w) + ((cols - 1) * gap_x)
        start_x = self.rect.centerx - (total_w // 2)
        start_y = self.rect.top + 100
        
        for i, variant in enumerate(self.variants):
            row = i // cols
            col = i % cols
            x = start_x + (col * (btn_w + gap_x))
            y = start_y + (row * (btn_h + gap_y))
            
            # Text Formatting
            clean_name = variant.replace("_", " ")
            lines = []
            if "BONUS DEUCES" in clean_name:
                lines = ["BONUS", "DEUCES", "10 / 4" if "10 4" in clean_name else ""]
            elif "NSUD" in clean_name:
                lines = ["NOT SO", "UGLY", "DEUCES"]
            elif "AIRPORT" in clean_name:
                lines = ["AIRPORT", "DEUCES", ""]
            else:
                lines = [clean_name, "", ""]
                
            self.buttons.append({
                "rect": pygame.Rect(x, y, btn_w, btn_h),
                "variant": variant,
                "lines": lines
            })

    def handle_click(self, pos):
        for btn in self.buttons:
            if btn["rect"].collidepoint(pos):
                self.machine.act_select_game(btn["variant"])
                return True
        return False

    def draw(self, screen):
        # Full BG
        pygame.draw.rect(screen, C_IGT_BG, self.rect)
        
        # Title
        t = self.assets.font_vfd.render("SELECT A GAME", True, C_IGT_GOLD)
        screen.blit(t, t.get_rect(center=(self.rect.centerx, self.rect.top + 50)))
        
        mouse_pos = pygame.mouse.get_pos()
        
        for btn in self.buttons:
            r = btn["rect"]
            hover = r.collidepoint(mouse_pos)
            
            # 1. Gold Border
            border_col = C_WHITE if hover else C_IGT_GOLD
            pygame.draw.rect(screen, border_col, r, border_radius=8)
            
            # 2. Red Inset
            inset = r.inflate(-6, -6)
            pygame.draw.rect(screen, C_IGT_RED, inset, border_radius=6)
            
            # 3. Text Box
            txt_box = inset.inflate(-10, -10)
            pygame.draw.rect(screen, C_IGT_TXT_BG, txt_box, border_radius=4)
            
            # 4. Text
            y_off = -20
            for line in btn["lines"]:
                if not line: continue
                col = C_IGT_TXT_SEL if hover else C_IGT_TXT
                txt = self.assets.font_menu_item.render(line, True, col)
                screen.blit(txt, txt.get_rect(center=(r.centerx, r.centery + y_off)))
                y_off += 22

# ==============================================================================
# ⚙️ CONFIG PANEL (LEFT SIDE)
# ==============================================================================
class ConfigPanel:
    def __init__(self, x, y, w, h, assets, machine):
        self.rect = pygame.Rect(x, y, w, h)
        self.assets = assets
        self.machine = machine
        
        self.denoms = [0.05, 0.10, 0.25, 0.50, 1.00]
        self.denom_idx = 2 
        self.floor_pct = 70; self.ceil_pct = 125

        self.buttons = []
        cx = self.rect.centerx
        
        # Removed Variant Button (Moved to Main Menu)
        
        # 1. Denom
        self.buttons.append(PhysicalButton((cx-90, 60, 180, 40), "DENOM >", self.cycle_denom))
        
        # 2. Bankroll
        self.buttons.append(PhysicalButton((cx-90, 140, 50, 40), "-", lambda: self.adj_bankroll(-1)))
        self.buttons.append(PhysicalButton((cx+40, 140, 50, 40), "+", lambda: self.adj_bankroll(1)))
        
        # 3. Floor
        self.buttons.append(PhysicalButton((cx-90, 220, 50, 40), "-", lambda: self.adj_floor(-1)))
        self.buttons.append(PhysicalButton((cx+40, 220, 50, 40), "+", lambda: self.adj_floor(1)))

        # 4. Ceiling
        self.buttons.append(PhysicalButton((cx-90, 300, 50, 40), "-", lambda: self.adj_ceil(-1)))
        self.buttons.append(PhysicalButton((cx+40, 300, 50, 40), "+", lambda: self.adj_ceil(1)))
        
        self.update_machine_limits()

    def update_machine_limits(self):
        self.machine.denom = self.denoms[self.denom_idx]
        start = self.machine.start_bankroll
        self.machine.floor_val = (start * (self.floor_pct / 100))
        self.machine.ceil_val = (start * (self.ceil_pct / 100))
        self.machine.graph_panel.set_limits(self.machine.floor_val, self.machine.ceil_val)

    def cycle_denom(self):
        if self.machine.state != "IDLE": return
        self.denom_idx = (self.denom_idx + 1) % len(self.denoms)
        self.update_machine_limits()

    def _get_step_multiplier(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]: return 100
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]: return 25
        return 10

    def adj_bankroll(self, direction):
        if self.machine.state != "IDLE": return
        step = self._get_step_multiplier()
        new_val = self.machine.start_bankroll + (step * direction)
        if new_val < 10: new_val = 10
        self.machine.start_bankroll = new_val
        self.machine.bankroll = new_val 
        self.machine.graph_panel.reset(new_val) 
        self.update_machine_limits()

    def adj_floor(self, direction):
        step = self._get_step_multiplier()
        new_val = self.floor_pct + (step * direction)
        self.floor_pct = max(0, min(100, new_val))
        self.update_machine_limits()

    def adj_ceil(self, direction):
        step = self._get_step_multiplier()
        new_val = self.ceil_pct + (step * direction)
        self.ceil_pct = max(105, new_val)
        self.update_machine_limits()

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        for b in self.buttons:
            b.update(mouse_pos, mouse_down)

    def draw(self, screen):
        pygame.draw.rect(screen, C_PANEL_BG, self.rect)
        pygame.draw.line(screen, (100,100,100), (self.rect.right,0), (self.rect.right,SCREEN_H), 2)
        
        # Title
        title = self.assets.font_ui.render("FLIGHT PLAN", True, C_YEL_TEXT)
        screen.blit(title, (self.rect.centerx - title.get_width()//2, 15))
        
        # 1. Denom
        lbl = self.assets.font_lbl.render(f"DENOM: ${self.denoms[self.denom_idx]:.2f}", True, C_WHITE)
        screen.blit(lbl, (self.rect.centerx - lbl.get_width()//2, 40))
        
        # 2. Bankroll
        lbl = self.assets.font_lbl.render("START BANKROLL", True, C_WHITE)
        screen.blit(lbl, (self.rect.centerx - lbl.get_width()//2, 120))
        val = self.assets.font_vfd.render(f"${self.machine.start_bankroll:.0f}", True, C_DIGITAL_GRN)
        screen.blit(val, (self.rect.centerx - val.get_width()//2, 150))
        
        # 3. Floor
        lbl = self.assets.font_lbl.render("FLOOR (STOP LOSS)", True, C_WHITE)
        screen.blit(lbl, (self.rect.centerx - lbl.get_width()//2, 200))
        
        txt = f"{self.floor_pct}% (${self.machine.floor_val:.0f})"
        val = self.assets.font_ui.render(txt, True, C_DIGITAL_RED)
        screen.blit(val, (self.rect.centerx - val.get_width()//2, 235))
        
        # 4. Ceiling
        lbl = self.assets.font_lbl.render("CEILING (TARGET)", True, C_WHITE)
        screen.blit(lbl, (self.rect.centerx - lbl.get_width()//2, 280))
        
        txt = f"{self.ceil_pct}% (${self.machine.ceil_val:.0f})"
        val = self.assets.font_ui.render(txt, True, C_DIGITAL_GRN)
        screen.blit(val, (self.rect.centerx - val.get_width()//2, 315))

        for b in self.buttons: b.draw(screen, self.assets.font_ui)
        help_txt = self.assets.font_tiny.render("Shift=25%, Ctrl=100% Steps", True, (150,150,150))
        screen.blit(help_txt, (self.rect.centerx - help_txt.get_width()//2, 820))

# ==============================================================================
# 📈 GRAPH PANEL
# ==============================================================================
class GraphPanel:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.start_bankroll = 100.0
        self.history = [100.0] 
        self.view_window_size = 50 
        self.floor_val = 0
        self.ceil_val = 200

    def add_point(self, bankroll):
        self.history.append(bankroll)
    
    def set_limits(self, floor, ceil):
        self.floor_val = floor
        self.ceil_val = ceil
        
    def reset(self, start_val):
        self.start_bankroll = start_val
        self.history = [start_val]

    def draw(self, screen, scroll_offset_index=0):
        pygame.draw.rect(screen, C_GRAPH_BG, self.rect)
        pygame.draw.rect(screen, (80, 80, 80), self.rect, 2)
        
        lbl = self.font.render("MISSION CONTROL", True, (150, 150, 150))
        screen.blit(lbl, (self.rect.left + 10, self.rect.top + 5))
        
        if not self.history: return

        total_points = len(self.history)
        if total_points <= self.view_window_size:
            data_slice = self.history; start_idx = 0
        else:
            end_idx = max(self.view_window_size, min(total_points, total_points - scroll_offset_index))
            start_idx = end_idx - self.view_window_size
            data_slice = self.history[start_idx : end_idx]

        if not data_slice: return

        # Scale Y to include Limits!
        vals = data_slice + [self.floor_val, self.ceil_val, self.start_bankroll]
        min_val = min(vals)
        max_val = max(vals)
        
        padding_y = (max_val - min_val) * 0.1 if max_val != min_val else 10
        min_view = min_val - padding_y
        max_view = max_val + padding_y
        range_y = max_view - min_view
        if range_y == 0: range_y = 1
        
        step_x = (self.rect.width - 20) / (len(data_slice) - 1) if len(data_slice) > 1 else 0
        
        def to_screen(i, val):
            px = self.rect.left + 10 + (i * step_x)
            norm = (val - min_view) / range_y
            py = self.rect.bottom - 10 - (norm * (self.rect.height - 30))
            return (px, py)
            
        if self.floor_val > 0:
            fy = to_screen(0, self.floor_val)[1]
            if self.rect.top < fy < self.rect.bottom:
                pygame.draw.line(screen, C_GRAPH_FLOOR, (self.rect.left, fy), (self.rect.right, fy), 1)
                
        cy = to_screen(0, self.ceil_val)[1]
        if self.rect.top < cy < self.rect.bottom:
            pygame.draw.line(screen, C_GRAPH_CEIL, (self.rect.left, cy), (self.rect.right, cy), 1)

        base_y = to_screen(0, self.start_bankroll)[1]
        if self.rect.top < base_y < self.rect.bottom:
            pygame.draw.line(screen, C_GRAPH_BASE, (self.rect.left, base_y), (self.rect.right, base_y), 1)

        for i in range(len(data_slice)):
            if (start_idx + i) % 10 == 0:
                px = to_screen(i, 0)[0]
                pygame.draw.line(screen, C_GRAPH_GRID, (px, self.rect.top+20), (px, self.rect.bottom-10), 1)

        if len(data_slice) > 1:
            points = [to_screen(i, v) for i, v in enumerate(data_slice)]
            curr_val = data_slice[-1]
            col = C_GRAPH_LINE_G if curr_val >= self.start_bankroll else C_GRAPH_LINE_R
            pygame.draw.lines(screen, col, False, points, 2)
            pygame.draw.circle(screen, C_WHITE, (int(points[-1][0]), int(points[-1][1])), 4)
            screen.blit(self.font.render(f"${curr_val:.2f}", True, C_WHITE), (self.rect.left + 10, self.rect.bottom - 20))

# ==============================================================================
# 📜 LOG PANEL
# ==============================================================================
class LogPanel:
    def __init__(self, x, y, w, h, assets):
        self.rect = pygame.Rect(x, y, w, h)
        self.assets = assets
        self.logs = [] 
        self.scroll_y = 0 
        self.entry_height = 110
        self.content_height = 0
        self.header_h = 75
        self.total_bet = 0.0; self.total_won = 0.0; self.total_hands = 0
        self.is_dragging = False; self.drag_start_y = 0; self.scroll_start_y = 0; self.thumb_rect = pygame.Rect(0,0,0,0) 

    def add_entry(self, hand_num, deal_cards, final_cards, held_indices, ev_data, result_data, bet_amount):
        entry = {
            'id': hand_num, 'deal': deal_cards, 'final': final_cards, 'held_idx': held_indices,
            'ev': ev_data, 'result': result_data, 'bet': bet_amount
        }
        self.logs.insert(0, entry)
        self.content_height = len(self.logs) * self.entry_height
        self.total_hands += 1; self.total_bet += bet_amount; self.total_won += result_data['win']

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(mouse_pos): self.scroll_y -= event.y * 20; self._clamp_scroll()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.thumb_rect.collidepoint(mouse_pos):
                self.is_dragging = True; self.drag_start_y = mouse_pos[1]; self.scroll_start_y = self.scroll_y
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                delta_y = mouse_pos[1] - self.drag_start_y
                view_h = self.rect.height - self.header_h
                if self.content_height > view_h and view_h > 0:
                    ratio = self.content_height / view_h
                    self.scroll_y = self.scroll_start_y + (delta_y * ratio)
                    self._clamp_scroll()

    def _clamp_scroll(self):
        view_h = self.rect.height - self.header_h
        max_scroll = max(0, self.content_height - view_h)
        if self.scroll_y < 0: self.scroll_y = 0
        if self.scroll_y > max_scroll: self.scroll_y = max_scroll

    def get_scroll_index_offset(self):
        if self.entry_height == 0: return 0
        return int(self.scroll_y / self.entry_height)

    def _calculate_hud_stats(self):
        rtp = (self.total_won / self.total_bet * 100) if self.total_bet > 0 else 0.0
        hits = sum(1 for log in self.logs if log['result']['win'] > 0)
        hit_rate = (hits / self.total_hands * 100) if self.total_hands > 0 else 0.0
        last_10 = self.logs[:10]
        if not last_10: l10_rate = 0.0
        else:
            l10_hits = sum(1 for log in last_10 if log['result']['win'] > 0)
            l10_rate = (l10_hits / len(last_10)) * 100
        return rtp, hit_rate, l10_rate

    def draw_cards_text(self, screen, cards, x, y, highlights=None):
        suit_map = {'s': '♠', 'c': '♣', 'h': '♥', 'd': '♦'}
        font = self.assets.font_log_bold
        char_w = 35 
        for i, card in enumerate(cards):
            current_x = x + (i * char_w)
            if highlights and i in highlights:
                bg_rect = pygame.Rect(current_x - 2, y, char_w - 2, 20)
                pygame.draw.rect(screen, C_NB_HIGHLIGHT, bg_rect)
            rank = card[0]; suit_char = card[1]
            symbol = suit_map.get(suit_char, suit_char)
            color = C_NB_RED if suit_char in 'hd' else C_NB_BLACK
            txt = font.render(f"{rank}{symbol}", True, color)
            screen.blit(txt, (current_x, y))

    def draw(self, screen):
        pygame.draw.rect(screen, C_NB_BG, self.rect)
        pygame.draw.rect(screen, C_NB_TEXT, self.rect, 2)
        pygame.draw.rect(screen, (240, 240, 240), (self.rect.left, self.rect.top, self.rect.width, self.header_h))
        pygame.draw.line(screen, C_NB_TEXT, (self.rect.left, self.rect.top + self.header_h), (self.rect.right, self.rect.top + self.header_h), 2)
        
        title = self.assets.font_ui.render("LABORATORY NOTEBOOK", True, C_NB_TEXT)
        screen.blit(title, (self.rect.centerx - title.get_width()//2, self.rect.top + 5))
        
        rtp, hit_rate, l10_rate = self._calculate_hud_stats()
        stats_font = self.assets.font_log_bold
        line1_str = f"HANDS: {self.total_hands}   |   RTP: {rtp:.1f}%"
        screen.blit(stats_font.render(line1_str, True, (80, 80, 80)), (self.rect.centerx - 100, self.rect.top + 30))
        
        hot_str = " 🔥" if l10_rate >= 50 else ""
        line2_str = f"HIT RATE: {hit_rate:.0f}%   (L10: {l10_rate:.0f}%{hot_str})"
        screen.blit(stats_font.render(line2_str, True, (200, 0, 0) if l10_rate >= 50 else (80, 80, 80)), (self.rect.centerx - 100, self.rect.top + 50))

        clip_rect = pygame.Rect(self.rect.left, self.rect.top + self.header_h, self.rect.width, self.rect.height - self.header_h)
        original_clip = screen.get_clip()
        screen.set_clip(clip_rect)
        
        start_y = (self.rect.top + self.header_h + 10) - self.scroll_y
        for i, log in enumerate(self.logs):
            y = start_y + (i * self.entry_height)
            if y + self.entry_height < self.rect.top or y > self.rect.bottom: continue
            
            pygame.draw.line(screen, C_NB_LINES, (self.rect.left + 10, y + self.entry_height - 10), (self.rect.right - 20, y + self.entry_height - 10))
            id_txt = self.assets.font_log_bold.render(f"#{log['id']}", True, (100, 100, 100))
            screen.blit(id_txt, (self.rect.left + 15, y))
            
            win_amt = log['result']['win']
            win_str = f"WIN: ${win_amt:.2f} ({log['result']['rank']})" if win_amt > 0 else "Result: Loss"
            win_col = (0, 150, 0) if win_amt > 0 else (150, 150, 150)
            screen.blit(self.assets.font_log_bold.render(win_str, True, win_col), (self.rect.left + 70, y))
            
            screen.blit(self.assets.font_log.render("Deal:", True, C_NB_TEXT), (self.rect.left + 15, y + 25))
            self.draw_cards_text(screen, log['deal'], self.rect.left + 70, y + 25, highlights=log['held_idx'])
            screen.blit(self.assets.font_log.render("Final:", True, C_NB_TEXT), (self.rect.left + 15, y + 50))
            self.draw_cards_text(screen, log['final'], self.rect.left + 70, y + 50, highlights=log['held_idx'])
            
            user_ev = log['ev']['user']; max_ev = log['ev']['max']; diff = max_ev - user_ev
            str_user = f"{user_ev:.2f}"; str_diff = f"{diff:.2f}"; str_max = f"{max_ev:.2f}"
            if diff < 0.01: dec_txt = self.assets.font_log_bold.render(f"✅ Optimal ({str_user})", True, (0, 120, 0))
            elif diff < 0.05: dec_txt = self.assets.font_log_bold.render(f"⚠️ Alternate (-{str_diff} EV)", True, (200, 140, 0))
            else: dec_txt = self.assets.font_log_bold.render(f"❌ Error: -{str_diff} EV (Max: {str_max})", True, C_NB_RED)
            screen.blit(dec_txt, (self.rect.left + 15, y + 75))

        screen.set_clip(original_clip)
        if self.content_height > clip_rect.height:
            bar_h = clip_rect.height
            thumb_h = max(30, (clip_rect.height / self.content_height) * bar_h)
            scroll_percent = self.scroll_y / (self.content_height - clip_rect.height)
            thumb_y = clip_rect.top + (scroll_percent * (bar_h - thumb_h))
            self.thumb_rect = pygame.Rect(self.rect.right - 14, thumb_y, 12, thumb_h)
            pygame.draw.rect(screen, (230, 230, 230), (self.rect.right - 14, clip_rect.top, 12, bar_h))
            pygame.draw.rect(screen, (150, 150, 150) if not self.is_dragging else (100, 100, 100), self.thumb_rect, border_radius=4)
        else: self.thumb_rect = pygame.Rect(0,0,0,0)

# ==============================================================================
# 🧩 UI COMPONENTS
# ==============================================================================
class PhysicalButton:
    def __init__(self, rect, text, callback, color=C_BTN_FACE):
        self.rect = pygame.Rect(rect); self.text = text; self.callback = callback; self.color = color
        self.hover = False; self.is_pressed = False
    def update(self, mouse_pos, mouse_down):
        self.hover = self.rect.collidepoint(mouse_pos)
        if self.hover and mouse_down: self.is_pressed = True
        elif self.is_pressed and self.hover and not mouse_down: self.callback(); self.is_pressed = False
        else: self.is_pressed = False
    def draw(self, screen, font):
        draw_rect = self.rect.move(2, 2) if self.is_pressed else self.rect
        if not self.is_pressed: pygame.draw.rect(screen, C_BTN_SHADOW, self.rect.move(4, 4), border_radius=6)
        pygame.draw.rect(screen, (255, 255, 200) if self.hover else self.color, draw_rect, border_radius=6)
        pygame.draw.rect(screen, C_BLACK, draw_rect, 2, border_radius=6)
        txt = font.render(self.text, True, C_BLACK)
        screen.blit(txt, txt.get_rect(center=draw_rect.center))

class ClickableMeter:
    def __init__(self, x_center, y_base, label, color, default_is_credits=True):
        self.x_center = x_center; self.y_base = y_base; self.label = label; self.color = color
        self.show_credits = default_is_credits; self.rect = pygame.Rect(x_center - 60, y_base, 120, 60)
    def check_click(self, pos):
        if self.rect.collidepoint(pos): self.show_credits = not self.show_credits; return True
        return False
    def draw(self, screen, assets, dollar_value, denom):
        val_str = f"{int(dollar_value / denom)}" if self.show_credits else f"${dollar_value:.2f}"
        lbl = assets.font_lbl.render(self.label, True, C_YEL_TEXT)
        val = assets.font_vfd.render(val_str, True, self.color)
        screen.blit(lbl, (self.x_center - lbl.get_width()//2, self.y_base))
        screen.blit(val, (self.x_center - val.get_width()//2, self.y_base + 20))

class VolumeButton:
    def __init__(self, x, y, sound_manager):
        self.rect = pygame.Rect(x, y, 40, 40); self.sm = sound_manager; self.level = 2 
        self.levels = [0.0, 0.3, 0.6, 1.0]; self.sm.set_volume(self.levels[self.level])
    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            self.level = (self.level + 1) % 4; self.sm.set_volume(self.levels[self.level])
            if self.level > 0: self.sm.play("bet")
            return True
        return False
    def draw(self, screen):
        pygame.draw.rect(screen, (50, 50, 50), self.rect, border_radius=5)
        pygame.draw.rect(screen, C_WHITE, self.rect, 2, border_radius=5)
        cx, cy = self.rect.centerx, self.rect.centery
        poly_color = C_WHITE if self.level > 0 else (150, 150, 150)
        pygame.draw.polygon(screen, poly_color, [(cx-8, cy-5), (cx-8, cy+5), (cx+2, cy+10), (cx+2, cy-10)])
        if self.level >= 1: pygame.draw.arc(screen, poly_color, (cx-5, cy-6, 14, 12), -math.pi/2.5, math.pi/2.5, 2)
        if self.level >= 2: pygame.draw.arc(screen, poly_color, (cx-5, cy-10, 18, 20), -math.pi/2.5, math.pi/2.5, 2)
        if self.level >= 3: pygame.draw.arc(screen, poly_color, (cx-5, cy-14, 22, 28), -math.pi/2.5, math.pi/2.5, 2)
        if self.level == 0: pygame.draw.line(screen, C_DIGITAL_RED, (cx-10, cy-10), (cx+10, cy+10), 3)

class CardSlot:
    def __init__(self, x, y, assets):
        self.rect = pygame.Rect(x, y, CARD_SIZE[0], CARD_SIZE[1])
        self.assets = assets; self.card_val = None; self.is_face_up = False; self.is_held = False
    def draw(self, screen):
        img = self.assets.cards[self.card_val] if (self.is_face_up and self.card_val in self.assets.cards) else self.assets.back
        screen.blit(img, self.rect)
        if self.is_held and self.is_face_up:
            stamp = pygame.Rect(self.rect.centerx - 40, self.rect.top - 30, 80, 26)
            pygame.draw.rect(screen, C_DIGITAL_RED, stamp)
            lbl = self.assets.font_ui.render("HELD", True, C_YEL_TEXT)
            screen.blit(lbl, lbl.get_rect(center=stamp.center))

class PaytableDisplay:
    def __init__(self, assets, pay_data):
        self.rect = pygame.Rect(260, 20, 960, 360) 
        self.assets = assets; self.data = pay_data
        master = ["NATURAL_ROYAL", "FOUR_DEUCES_ACE", "FOUR_DEUCES", "FIVE_ACES", "FIVE_3_4_5", "FIVE_6_TO_K", "WILD_ROYAL", "FIVE_OAK", "STRAIGHT_FLUSH", "FOUR_OAK", "FULL_HOUSE", "FLUSH", "STRAIGHT", "THREE_OAK"]
        self.rows = [k for k in master if k in pay_data]
        self.labels = {"NATURAL_ROYAL":"ROYAL FLUSH", "FOUR_DEUCES_ACE":"4 DEUCES + A", "FOUR_DEUCES":"4 DEUCES", "FIVE_ACES":"5 ACES", "FIVE_3_4_5":"5 3s 4s 5s", "FIVE_6_TO_K":"5 6s THRU Ks", "WILD_ROYAL":"WILD ROYAL", "FIVE_OAK":"5 OF A KIND", "STRAIGHT_FLUSH":"STR FLUSH", "FOUR_OAK":"4 OF A KIND", "FULL_HOUSE":"FULL HOUSE", "FLUSH":"FLUSH", "STRAIGHT":"STRAIGHT", "THREE_OAK":"3 OF A KIND"}
    def draw(self, screen, coins_bet, winning_rank=None):
        pygame.draw.rect(screen, C_BG_BLUE, self.rect)
        col_w = (self.rect.width - 160) // 5
        active_x = self.rect.left + 160 + ((coins_bet - 1) * col_w)
        pygame.draw.rect(screen, C_RED_ACTIVE, (active_x, self.rect.top, col_w, self.rect.height))
        for i in range(5): pygame.draw.line(screen, C_YEL_TEXT, (self.rect.left + 160 + (i*col_w), self.rect.top), (self.rect.left + 160 + (i*col_w), self.rect.bottom), 2)
        start_y = self.rect.top + 15
        for i, key in enumerate(self.rows):
            y = start_y + (i * 25); col = C_WHITE if key == winning_rank else C_YEL_TEXT
            screen.blit(self.assets.font_grid.render(self.labels.get(key, key), True, col), (self.rect.left + 10, y))
            base = self.data.get(key, 0)
            for c in range(1, 6):
                val = 4000 if key == "NATURAL_ROYAL" and c == 5 else base * c
                val_surf = self.assets.font_grid.render(str(val), True, C_YEL_TEXT)
                screen.blit(val_surf, (self.rect.left + 160 + ((c-1)*col_w) + col_w - val_surf.get_width() - 10, y))
        pygame.draw.rect(screen, C_YEL_TEXT, self.rect, 2)

# ==============================================================================
# 🎮 MAIN SYSTEM
# ==============================================================================
class IGT_Machine:
    def __init__(self):
        pygame.init(); pygame.mixer.init(); os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("EV Navigator - Deuces Wild Trainer (Mission Control)")
        self.clock = pygame.time.Clock()
        self.assets = AssetManager(); self.sound = SoundManager()
        self.available_variants = list(PAYTABLES.keys()); self.variant_idx = 0 
        self.sim = dw_sim_engine.DeucesWildSim(variant=self.available_variants[self.variant_idx])
        self.core = self.sim.core
        self.paytable = PaytableDisplay(self.assets, self.sim.paytable)
        
        # 1. State Init
        self.state = "IDLE"; self.start_bankroll = 100.00; self.bankroll = 100.00
        self.coins_bet = 5; self.denom = 0.25
        self.floor_val = 0; self.ceil_val = 200 
        self.win_display = 0.0; self.win_target = 0.0; self.last_win_rank = None
        self.hand = []; self.stub = []; self.held_indices = []; self.deal_snapshot = []
        
        # 2. Panel Init
        self.log_panel = LogPanel(1240, 20, 340, 500, self.assets) # Moved Right
        self.graph_panel = GraphPanel(1240, 530, 340, 300, self.assets.font_tiny)
        self.config_panel = ConfigPanel(0, 0, 240, 850, self.assets, self) # New Left Panel
        
        # 3. Game Selector Overlay
        # It covers the game area (240 to 1600)
        self.game_selector = GameSelectorScreen(pygame.Rect(240, 0, 1360, 850), self.assets, self, self.available_variants)
        
        # Shifted Game Area
        start_x = 360
        self.cards = [CardSlot(start_x + (i * 152), 410, self.assets) for i in range(5)]
        
        self.auto_hold_active = False; self.auto_play_active = False; self.last_action_time = 0; self.advice_msg = None        
        self.hands_played = 0; self._init_buttons(); self._init_meters(); 
        self.vol_btn = VolumeButton(1150, 785, self.sound) # Shifted
        
        self.config_panel.update_machine_limits()

    def _init_buttons(self):
        y = 780; h = 50
        start_x = 340
        self.buttons = [
            PhysicalButton((start_x, y, 120, h), "MORE GAMES", self.act_open_menu), # Updated Callback
            PhysicalButton((start_x + 130, y, 90, h), "AUTO HOLD", self.act_toggle_auto_hold, color=C_DIGITAL_YEL),
            PhysicalButton((start_x + 230, y, 110, h), "AUTO PLAY", self.act_toggle_auto_play, color=C_BTN_FACE),
            PhysicalButton((start_x + 350, y, 90, h), "BET ONE", self.act_bet_one),
            PhysicalButton((start_x + 450, y, 90, h), "BET MAX", self.act_bet_max),
            PhysicalButton((start_x + 600, y, 150, h), "DEAL", self.act_deal_draw, color=(255, 215, 0))
        ]
        self.btn_auto_hold = self.buttons[1]; self.btn_auto_play = self.buttons[2]; self.btn_deal = self.buttons[-1]

    def _init_meters(self):
        self.meter_win = ClickableMeter(400, 680, "WIN", C_DIGITAL_RED)
        self.meter_bet = ClickableMeter(740, 680, "BET", C_DIGITAL_YEL)
        self.meter_credit = ClickableMeter(1080, 680, "CREDIT", C_DIGITAL_RED, default_is_credits=False)
        self.meters = [self.meter_win, self.meter_bet, self.meter_credit]

    def act_toggle_auto_hold(self):
        self.auto_hold_active = not self.auto_hold_active
        self.btn_auto_hold.text = "AUTO: ON" if self.auto_hold_active else "AUTO HOLD"
        self.btn_auto_hold.color = C_DIGITAL_GRN if self.auto_hold_active else C_DIGITAL_YEL
        if self.auto_hold_active and self.state == "DECISION": self.run_solver()

    def act_toggle_auto_play(self):
        self.auto_play_active = not self.auto_play_active
        self.btn_auto_play.text = "STOP" if self.auto_play_active else "AUTO PLAY"
        self.btn_auto_play.color = C_DIGITAL_RED if self.auto_play_active else C_BTN_FACE
        if self.auto_play_active: self.last_action_time = pygame.time.get_ticks()

    def run_solver(self):
        best_cards, _ = dw_fast_solver.solve_hand(self.hand, self.sim.paytable)
        self.held_indices = []
        for i, card in enumerate(self.hand):
            is_best = card in best_cards
            self.cards[i].is_held = is_best
            if is_best: self.held_indices.append(i)
        self.advice_msg = None if best_cards else "ADVICE: DRAW ALL"
        self.sound.play("bet")

    def act_open_menu(self):
        if self.state == "IDLE":
            self.state = "GAME_SELECT"
            self.sound.play("bet")

    def act_select_game(self, new_variant):
        # Callback from GameSelectorScreen
        self.sim = dw_sim_engine.DeucesWildSim(variant=new_variant)
        self.core = self.sim.core
        self.paytable = PaytableDisplay(self.assets, self.sim.paytable)
        self.graph_panel.reset(self.bankroll) 
        self.sound.play("bet")
        pygame.display.set_caption(f"IGT Game King Replica ({new_variant})")
        self.state = "IDLE"

    def act_bet_one(self):
        if self.state != "IDLE": return
        self.coins_bet = 1 if self.coins_bet >= 5 else self.coins_bet + 1
        self.sound.play("bet")

    def act_bet_max(self):
        if self.state != "IDLE": return
        self.coins_bet = 5; self.sound.play("bet"); self.act_deal_draw()

    def act_deal_draw(self):
        if self.state == "IDLE":
            if self.floor_val > 0 and self.bankroll <= self.floor_val:
                self.auto_play_active = False
                self.advice_msg = "⚠️ FLOOR HIT: MISSION ABORTED"
                self.act_toggle_auto_play() 
                return
            if self.ceil_val > 0 and self.bankroll >= self.ceil_val:
                self.auto_play_active = False
                self.advice_msg = "🎯 CEILING HIT: MISSION SUCCESS"
                self.act_toggle_auto_play()
                return

            cost = self.coins_bet * self.denom
            if self.bankroll < cost: return
            self.bankroll -= cost
            
            self.win_display = 0.0; self.win_target = 0.0; self.last_win_rank = None; self.advice_msg = None 
            self.hand, self.stub = self.core.deal_hand()
            self.deal_snapshot = list(self.hand)
            self.hands_played += 1; self.held_indices = []
            
            for i, c in enumerate(self.hand):
                self.cards[i].card_val = c; self.cards[i].is_face_up = True; self.cards[i].is_held = False
            
            rank, mult = self.sim.evaluate_hand_score(self.hand)
            if mult > 0: self.last_win_rank = rank
            
            self.sound.play("deal"); self.state = "DECISION"; self.btn_deal.text = "DRAW"
            if self.auto_hold_active or self.auto_play_active: self.run_solver()
            
        elif self.state == "DECISION":
            self.advice_msg = None
            optimal_hold, _ = dw_fast_solver.solve_hand(self.hand, self.sim.paytable)
            opt_indices = [i for i, c in enumerate(self.hand) if c in optimal_hold]
            max_ev = dw_exact_solver.calculate_exact_ev(self.hand, opt_indices, self.sim.paytable)
            user_hold_cards = [self.hand[i] for i in self.held_indices]
            if set(user_hold_cards) == set(optimal_hold): user_ev = max_ev
            else: user_ev = dw_exact_solver.calculate_exact_ev(self.hand, self.held_indices, self.sim.paytable)
            max_ev_disp = max_ev * self.coins_bet; user_ev_disp = user_ev * self.coins_bet
            logged_held_indices = list(self.held_indices)

            self.core.shuffle(self.stub)
            for i in range(5):
                if i not in self.held_indices:
                    if self.stub: self.hand[i] = self.stub.pop(0)
            for i, c in enumerate(self.hand): self.cards[i].card_val = c
            
            self.sound.play("deal")
            rank, mult = self.sim.evaluate_hand_score(self.hand)
            win_val = (mult * self.coins_bet) * self.denom
            
            if win_val > 0:
                self.sound.play("win"); self.last_win_rank = rank
                self.win_target = win_val; self.bankroll += win_val
            else: self.last_win_rank = None
                
            bet_val = (self.coins_bet * self.denom)
            self.log_panel.add_entry(self.hands_played, self.deal_snapshot, list(self.hand), logged_held_indices, {'user': user_ev_disp, 'max': max_ev_disp}, {'win': win_val, 'rank': rank.replace('_',' ')}, bet_val)
            self.graph_panel.add_point(self.bankroll)
            self.state = "IDLE"; self.btn_deal.text = "DEAL"

    def handle_click(self, pos):
        # 1. Config Panel Clicks (Always Active)
        if self.config_panel.rect.collidepoint(pos):
            for b in self.config_panel.buttons:
                if b.rect.collidepoint(pos): b.callback()
            return

        # 2. Game Selector Clicks
        if self.state == "GAME_SELECT":
            self.game_selector.handle_click(pos)
            return

        # 3. Standard Game Clicks
        if self.vol_btn.check_click(pos): return
        for m in self.meters:
            if m.check_click(pos): self.sound.play("bet"); return
        if self.state == "DECISION":
            for i, slot in enumerate(self.cards):
                if slot.rect.collidepoint(pos):
                    self.advice_msg = None; slot.is_held = not slot.is_held
                    if slot.is_held: self.held_indices.append(i)
                    else: self.held_indices.remove(i)

    def update_auto_play(self):
        if not self.auto_play_active: return
        now = pygame.time.get_ticks()
        if now - self.last_action_time > 400:
            self.last_action_time = now; self.act_deal_draw()

    def draw(self):
        self.screen.fill(C_BLACK)
        
        # Always draw Side Panels
        self.config_panel.draw(self.screen)
        self.log_panel.draw(self.screen)
        scroll_offset = self.log_panel.get_scroll_index_offset()
        self.graph_panel.draw(self.screen, scroll_offset_index=scroll_offset)
        
        if self.state == "GAME_SELECT":
            self.game_selector.draw(self.screen)
        else:
            # Draw Main Game
            self.paytable.draw(self.screen, self.coins_bet, self.last_win_rank)
            
            off_x = 240; game_w = 1000
            pygame.draw.rect(self.screen, C_BG_BLUE, (off_x, 380, game_w, 280))
            pygame.draw.line(self.screen, C_WHITE, (off_x, 380), (off_x+game_w, 380), 2)
            pygame.draw.line(self.screen, C_WHITE, (off_x, 660), (off_x+game_w, 660), 2)
            
            self.vol_btn.draw(self.screen)
            if self.advice_msg:
                msg = self.assets.font_msg.render(self.advice_msg, True, C_CYAN_MSG)
                center_x = 240 + (1000 // 2) 
                bg = msg.get_rect(center=(center_x, 395)).inflate(20, 10)
                pygame.draw.rect(self.screen, (0,0,50), bg, border_radius=5)
                pygame.draw.rect(self.screen, C_CYAN_MSG, bg, 2, border_radius=5)
                self.screen.blit(msg, msg.get_rect(center=(center_x, 395)))
                
            if self.auto_play_active: self.screen.blit(self.assets.font_ui.render("PILOT ENGAGED", True, C_DIGITAL_GRN), (300+off_x, 835))
            self.screen.blit(self.assets.font_lbl.render(f"DEALS: {self.hands_played}", True, C_YEL_TEXT), (30+off_x, 750))
            self.screen.blit(self.assets.font_ui.render(f"Deuces Wild ({self.sim.variant})", True, C_WHITE), (20+off_x, 835))

            for c in self.cards: c.draw(self.screen)
            if self.win_display < self.win_target: self.win_display += self.denom; self.win_display = min(self.win_display, self.win_target)
            
            for m in self.meters:
                val = self.win_display if m.label == "WIN" else (self.coins_bet * self.denom if m.label == "BET" else self.bankroll)
                m.draw(self.screen, self.assets, val, self.denom)
            
            # Denom Badge
            cx, cy = 910, 680 + 30; rect = pygame.Rect(cx-40, cy-25, 80, 50)
            pygame.draw.ellipse(self.screen, (255, 215, 0), rect); pygame.draw.ellipse(self.screen, C_BLACK, rect, 2)
            txt_str = f"{int(self.denom*100)}¢" if self.denom < 1.0 else f"${int(self.denom)}"
            txt = pygame.font.SysFont("timesnewroman", 28, bold=True).render(txt_str, True, (200, 0, 0))
            self.screen.blit(txt, txt.get_rect(center=(cx, cy)))

            mouse_pos = pygame.mouse.get_pos(); mouse_down = pygame.mouse.get_pressed()[0]
            for b in self.buttons: b.update(mouse_pos, mouse_down); b.draw(self.screen, self.assets.font_ui)
            
        # Config buttons always update (unless covered, but they are left panel)
        for b in self.config_panel.buttons: b.update(pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0])
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.update_auto_play()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.MOUSEBUTTONUP: 
                    self.handle_click(event.pos)
                    self.log_panel.handle_event(event)
                elif event.type in [pygame.MOUSEWHEEL, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                    self.log_panel.handle_event(event)
                elif event.type == pygame.KEYUP:
                    if self.state == "GAME_SELECT": continue
                    if event.key == pygame.K_a: self.act_toggle_auto_hold()
                    elif event.key == pygame.K_p: self.act_toggle_auto_play()
                    elif event.key == pygame.K_SPACE: self.act_deal_draw()
            self.draw(); self.clock.tick(FPS)
        pygame.quit(); sys.exit()

if __name__ == "__main__":
    app = IGT_Machine()
    app.run()