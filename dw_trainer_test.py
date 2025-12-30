import pygame
import os
import sys
import math
import platform

# ==============================================================================
# 🌍 UNIVERSAL ENVIRONMENT SETUP (PC + ANDROID)
# ==============================================================================
# Pydroid 3 Sandbox Escape: Force CWD to script location
if "ANDROID_ARGUMENT" in os.environ:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Windows Taskbar Fix (Only runs on PC)
if os.name == 'nt':
    try:
        import ctypes
        appid = 'ev_navigator.deuces_wild.universal.v10'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    except: pass

# Import Core Logic
import dw_sim_engine
import dw_fast_solver
import dw_exact_solver
import dw_strategy_definitions 
from dw_pay_constants import PAYTABLES

# ==============================================================================
# 📐 UNIVERSAL SCALING ENGINE
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
    # This prevents the "IMAX Effect" on large monitors
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

# CONFIG FLAGS
IS_MOBILE = "ANDROID_ARGUMENT" in os.environ
FPS_LIMIT = 30 if IS_MOBILE else 60
FULLSCREEN_FLAG = pygame.FULLSCREEN if IS_MOBILE else pygame.RESIZABLE

# FRAME RATE TARGETS
FPS_ACTIVE = FPS_LIMIT
FPS_IDLE = 15 if IS_MOBILE else 30

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

# ASSETS
ASSET_DIR = os.path.join("images", "cards")
SOUND_DIR = "sounds"
CARD_SIZE = (s(142), s(215))

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
# 🖼️ ASSET MANAGER (SCALED FONTS)
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
        # Fallback fonts
        try:
            self.font_log_bold = pygame.font.SysFont("Segoe UI Symbol", s_font(16), bold=True)
            self.font_log = pygame.font.SysFont("Segoe UI Symbol", s_font(16))
        except:
            self.font_log_bold = pygame.font.SysFont("Arial", s_font(16), bold=True)
            self.font_log = pygame.font.SysFont("Arial", s_font(16))
            
        self.font_tiny = pygame.font.SysFont("Arial", s_font(13))
        self.font_micro = pygame.font.SysFont("Arial", s_font(11), bold=True)
        self.font_menu_title = pygame.font.SysFont("Arial Black", s_font(24))
        self.font_menu_item = pygame.font.SysFont("Arial", s_font(22), bold=True)
        self._load_textures()

    def _load_textures(self):
        print(f"Loading assets from: {os.path.abspath(ASSET_DIR)}")
        ranks = "23456789TJQKA"; suits = "shdc"
        count = 0
        for s_char in suits:
            for r in ranks:
                key = r + s_char
                path = os.path.join(ASSET_DIR, f"{key}.png")
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert_alpha()
                        self.cards[key] = pygame.transform.smoothscale(img, CARD_SIZE)
                        count += 1
                    except Exception as e: print(f"Error loading {key}: {e}")
        
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
# 🧠 STRATEGY PANEL
# ==============================================================================
class StrategyPanel:
    def __init__(self, x, y, w, h, assets, machine):
        self.rect = s_rect(x, y, w, h)
        self.assets = assets
        self.machine = machine
        self.results = [] 
        
        cx = self.rect.centerx
        btn_y = self.rect.top + s(750) 
        self.btn_setup = PhysicalButton(
            pygame.Rect(cx - s(90), btn_y, s(180), s(50)), 
            "SESSION SETUP", 
            self.machine.act_open_session_setup
        )

    def set_results(self, results):
        self.results = results

    def reset(self):
        self.results = []

    def draw(self, screen):
        pygame.draw.rect(screen, (30, 35, 40), self.rect)
        pygame.draw.line(screen, (100,100,100), (self.rect.right,0), (self.rect.right, PHYSICAL_H), 2)

        self.btn_setup.update(pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0])
        self.btn_setup.draw(screen, self.assets.font_ui)

        if not self.results: return

        best_info = self.results[0]['info']
        bucket_idx = best_info['bucket']
        best_rule_idx = best_info['rule_idx']
        best_ev = self.results[0]['ev']

        runner_up_idx = -1
        runner_up_ev = 0.0
        if len(self.results) > 1:
            runner_up_info = self.results[1]['info']
            runner_up_idx = runner_up_info['rule_idx']
            runner_up_ev = self.results[1]['ev']

        header_h = s(50)
        header_rect = pygame.Rect(self.rect.left, self.rect.top, self.rect.width, header_h)
        pygame.draw.rect(screen, (20, 25, 30), header_rect)
        pygame.draw.line(screen, (100, 100, 100), (self.rect.left, self.rect.top+header_h), (self.rect.right, self.rect.top+header_h), 2)
        
        title_str = f"{bucket_idx} DEUCE STRATEGY"
        title = self.assets.font_ui.render(title_str, True, C_YEL_TEXT)
        screen.blit(title, title.get_rect(center=header_rect.center))

        variant = self.machine.sim.variant
        strat_map = dw_strategy_definitions.STRATEGY_MAP.get(variant, dw_strategy_definitions.STRATEGY_NSUD)
        rules = strat_map.get(bucket_idx, [])

        max_items = 28
        start_idx = max(0, best_rule_idx - 6)
        end_idx = min(len(rules), start_idx + max_items)
        if end_idx - start_idx < max_items: start_idx = max(0, end_idx - max_items)

        row_h = s(24)
        y = self.rect.top + s(70)
        x_off = self.rect.left + s(35)

        for i in range(start_idx, end_idx):
            rule_func = rules[i]
            name = dw_strategy_definitions.get_pretty_name(rule_func)
            
            is_best = (i == best_rule_idx)
            is_runner = (i == runner_up_idx)
            
            if is_best: col = C_WHITE
            elif is_runner: col = C_SILVER
            elif i < best_rule_idx: col = (100, 100, 100)
            else: col = (160, 160, 160)

            if is_best:
                row_rect = pygame.Rect(self.rect.left, y - s(2), self.rect.width, s(22))
                pygame.draw.rect(screen, (40, 60, 40), row_rect)

            cx_dot = self.rect.left + s(18)
            cy_dot = y + s(7)
            dot_rad = s(6)
            
            if is_best:
                pygame.draw.circle(screen, C_GOLD_HELD, (cx_dot, cy_dot), dot_rad)
                pygame.draw.circle(screen, C_BLACK, (cx_dot, cy_dot), dot_rad, 1)
                name += f" ({best_ev:.4f})"
            elif is_runner:
                pygame.draw.circle(screen, C_SILVER, (cx_dot, cy_dot), dot_rad)
                pygame.draw.circle(screen, C_BLACK, (cx_dot, cy_dot), dot_rad, 1)
                name += f" ({runner_up_ev:.4f})"

            txt = self.assets.font_tiny.render(name, True, col)
            screen.blit(txt, (x_off, y))
            y += row_h

# ==============================================================================
# 📖 CODEX SCREEN
# ==============================================================================
class CodexScreen:
    def __init__(self, rect, assets, machine):
        self.rect = rect
        self.assets = assets
        self.machine = machine
        self.active_bucket = 0
        self.buttons = []
        self._init_tabs()

    def _init_tabs(self):
        tab_w = s(120)
        tab_h = s(40)
        start_x = self.rect.centerx - (2.5 * tab_w)
        y = self.rect.top + s(80)
        
        for i in range(5):
            self.buttons.append({
                "rect": pygame.Rect(start_x + (i * tab_w), y, tab_w, tab_h),
                "label": f"{i} DEUCES",
                "val": i,
                "action": lambda v=i: self._set_bucket(v)
            })
        
        close_w, close_h = s(120), s(50)
        self.buttons.append({
            "rect": pygame.Rect(self.rect.centerx - (close_w//2), self.rect.bottom - s(80), close_w, close_h),
            "label": "CLOSE", "action": self._close, "col": C_DIGITAL_RED
        })

    def _set_bucket(self, val):
        self.active_bucket = val; self.machine.sound.play("bet")
    def _close(self):
        self.machine.state = "IDLE"; self.machine.sound.play("bet")
    def handle_click(self, pos):
        for btn in self.buttons:
            if btn["rect"].collidepoint(pos): btn["action"](); return

    def draw(self, screen):
        s_surf = pygame.Surface((PHYSICAL_W, PHYSICAL_H), pygame.SRCALPHA)
        s_surf.fill((0, 0, 0, 220)) 
        screen.blit(s_surf, (0,0))
        
        panel_rect = self.rect.inflate(s(-100), s(-100))
        pygame.draw.rect(screen, C_PANEL_BG, panel_rect, border_radius=s(12))
        pygame.draw.rect(screen, C_IGT_GOLD, panel_rect, s(3), border_radius=s(12))
        
        title = self.assets.font_vfd.render("STRATEGY CODEX", True, C_IGT_GOLD)
        screen.blit(title, title.get_rect(center=(self.rect.centerx, self.rect.top + s(50))))
        
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            r = btn["rect"]; hover = r.collidepoint(mouse_pos)
            is_active = (btn.get("val") == self.active_bucket)
            col = btn.get("col", C_BTN_FACE)
            if is_active: col = C_IGT_TXT_SEL
            elif hover: col = (200, 200, 255)
            pygame.draw.rect(screen, col, r, border_radius=s(6))
            pygame.draw.rect(screen, C_BLACK, r, s(2), border_radius=s(6))
            txt = self.assets.font_ui.render(btn["label"], True, C_BLACK)
            screen.blit(txt, txt.get_rect(center=r.center))

        content_rect = pygame.Rect(panel_rect.left + s(40), panel_rect.top + s(140), panel_rect.width - s(80), panel_rect.height - s(200))
        pygame.draw.rect(screen, (20, 25, 30), content_rect, border_radius=s(8))
        
        variant = self.machine.sim.variant
        strat_map = dw_strategy_definitions.STRATEGY_MAP.get(variant, dw_strategy_definitions.STRATEGY_NSUD)
        rules = strat_map.get(self.active_bucket, [])
        col_limit = 15
        col1_x = content_rect.left + s(40)
        col2_x = content_rect.centerx + s(40)
        start_y = content_rect.top + s(30)
        row_step = s(30)
        
        for i, rule in enumerate(rules):
            name = dw_strategy_definitions.get_pretty_name(rule)
            if i < col_limit: x = col1_x; y = start_y + (i * row_step)
            else: x = col2_x; y = start_y + ((i - col_limit) * row_step)
            
            screen.blit(self.assets.font_ui.render(f"{i+1}.", True, C_IGT_GOLD), (x, y))
            screen.blit(self.assets.font_ui.render(name, True, C_WHITE), (x + s(40), y))

# ==============================================================================
# 🎮 SESSION SETUP SCREEN
# ==============================================================================
class SessionSetupScreen:
    def __init__(self, rect, assets, machine):
        self.rect = rect
        self.assets = assets
        self.machine = machine
        self.temp_bank = machine.start_bankroll
        self.temp_denom = machine.denom
        self.temp_floor_pct = machine.floor_pct
        self.temp_ceil_pct = machine.ceil_pct
        self.buttons = []
        self._init_layout()

    def _init_layout(self):
        col_w = self.rect.width // 3
        c1_x = self.rect.left + (col_w * 0.5)
        c2_x = self.rect.left + (col_w * 1.5)
        c3_x = self.rect.left + (col_w * 2.5)
        
        btn_w, btn_h = s(80), s(50)
        gap = s(60)
        
        bills = [5, 10, 20, 100]
        y_start = self.rect.top + s(150)
        for i, amt in enumerate(bills):
            self.buttons.append({"rect": pygame.Rect(c1_x - s(90), y_start + (i*gap), btn_w, btn_h), "text": f"+ ${amt}", "col": C_DIGITAL_GRN, "action": lambda a=amt: self._adj_bank(a)})
            self.buttons.append({"rect": pygame.Rect(c1_x + s(10), y_start + (i*gap), btn_w, btn_h), "text": f"- ${amt}", "col": C_DIGITAL_RED, "action": lambda a=amt: self._adj_bank(-a)})
        
        self.buttons.append({"rect": pygame.Rect(c1_x - s(60), y_start + s(260), s(120), s(40)), "text": "RESET $0", "col": C_BTN_FACE, "action": lambda: self._set_bank(0)})

        denoms = [0.05, 0.10, 0.25, 0.50, 1.00]
        y_start = self.rect.top + s(150)
        for i, d in enumerate(denoms):
            self.buttons.append({"rect": pygame.Rect(c2_x - s(60), y_start + (i*gap), s(120), s(50)), "text": f"${d:.2f}", "type": "denom", "val": d, "action": lambda val=d: self._set_denom(val)})

        floors = [50, 60, 70, 80, 90]
        y_start = self.rect.top + s(150)
        for i, p in enumerate(floors):
            self.buttons.append({"rect": pygame.Rect(c3_x - s(130) + (i * s(55)), y_start, s(50), s(40)), "text": f"{p}%", "type": "floor", "val": p, "action": lambda val=p: self._set_floor(val)})
            
        ceils = [110, 120, 130, 150, 200]
        y_start = self.rect.top + s(300)
        for i, p in enumerate(ceils):
            self.buttons.append({"rect": pygame.Rect(c3_x - s(130) + (i * s(55)), y_start, s(50), s(40)), "text": f"{p}%", "type": "ceil", "val": p, "action": lambda val=p: self._set_ceil(val)})

        conf_w, conf_h = s(200), s(60)
        self.buttons.append({"rect": pygame.Rect(self.rect.centerx + s(20), self.rect.bottom - s(100), conf_w, conf_h), "text": "CONFIRM SETUP", "col": C_DIGITAL_GRN, "action": self._confirm})
        self.buttons.append({"rect": pygame.Rect(self.rect.centerx - s(220), self.rect.bottom - s(100), conf_w, conf_h), "text": "NEW SESSION", "col": C_DIGITAL_RED, "action": self._new_session})

    def _adj_bank(self, amt): self.temp_bank = max(0, self.temp_bank + amt)
    def _set_bank(self, val): self.temp_bank = val
    def _set_denom(self, val): self.temp_denom = val
    def _set_floor(self, val): self.temp_floor_pct = val
    def _set_ceil(self, val): self.temp_ceil_pct = val
    
    def _confirm(self):
        self.machine.start_bankroll = self.temp_bank; self.machine.bankroll = self.temp_bank
        self.machine.denom = self.temp_denom; self.machine.floor_pct = self.temp_floor_pct; self.machine.ceil_pct = self.temp_ceil_pct
        self.machine.update_machine_limits(); self.machine.graph_panel.reset(self.temp_bank)
        self.machine.state = "IDLE"; self.machine.sound.play("rollup")

    def _new_session(self):
        self.machine.start_new_session()
        self.temp_bank = self.machine.start_bankroll; self.temp_denom = self.machine.denom
        self.temp_floor_pct = self.machine.floor_pct; self.temp_ceil_pct = self.machine.ceil_pct
        self.machine.sound.play("deal"); self.machine.state = "IDLE"

    def handle_click(self, pos):
        for btn in self.buttons:
            if btn["rect"].collidepoint(pos): btn["action"](); self.machine.sound.play("bet"); return

    def draw(self, screen):
        pygame.draw.rect(screen, C_IGT_BG, self.rect)
        title = self.assets.font_vfd.render("SESSION SETUP", True, C_IGT_GOLD)
        screen.blit(title, title.get_rect(center=(self.rect.centerx, self.rect.top + s(40))))
        
        col_w = self.rect.width // 3
        c1_x = self.rect.left + (col_w * 0.5)
        c2_x = self.rect.left + (col_w * 1.5)
        c3_x = self.rect.left + (col_w * 2.5)
        
        t1 = self.assets.font_ui.render("BANKROLL", True, C_WHITE); screen.blit(t1, t1.get_rect(center=(c1_x, self.rect.top + s(90))))
        val1 = self.assets.font_vfd.render(f"${self.temp_bank:.0f}", True, C_DIGITAL_GRN); screen.blit(val1, val1.get_rect(center=(c1_x, self.rect.top + s(120))))
        
        t2 = self.assets.font_ui.render("DENOMINATION", True, C_WHITE); screen.blit(t2, t2.get_rect(center=(c2_x, self.rect.top + s(90))))
        t3 = self.assets.font_ui.render("SESSION LIMITS", True, C_WHITE); screen.blit(t3, t3.get_rect(center=(c3_x, self.rect.top + s(90))))
        
        f_val = self.temp_bank * (self.temp_floor_pct / 100)
        lbl_f = self.assets.font_ui.render(f"STOP LOSS: {self.temp_floor_pct}% (${f_val:.0f})", True, C_DIGITAL_RED)
        screen.blit(lbl_f, lbl_f.get_rect(center=(c3_x, self.rect.top + s(130))))
        
        c_val = self.temp_bank * (self.temp_ceil_pct / 100)
        lbl_c = self.assets.font_ui.render(f"TARGET: {self.temp_ceil_pct}% (${c_val:.0f})", True, C_DIGITAL_GRN)
        screen.blit(lbl_c, lbl_c.get_rect(center=(c3_x, self.rect.top + s(280))))

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            r = btn["rect"]; hover = r.collidepoint(mouse_pos)
            fill_col = btn.get("col", C_BTN_FACE); border_col = C_BLACK
            
            if btn.get("type") == "denom" and btn["val"] == self.temp_denom: fill_col = C_IGT_TXT_SEL; border_col = C_WHITE
            elif btn.get("type") == "floor" and btn["val"] == self.temp_floor_pct: fill_col = C_DIGITAL_RED; border_col = C_WHITE
            elif btn.get("type") == "ceil" and btn["val"] == self.temp_ceil_pct: fill_col = C_DIGITAL_GRN; border_col = C_WHITE
            elif hover: fill_col = (255, 255, 200)

            pygame.draw.rect(screen, fill_col, r, border_radius=s(6))
            pygame.draw.rect(screen, border_col, r, s(2), border_radius=s(6))
            screen.blit(self.assets.font_ui.render(btn["text"], True, C_BLACK), self.assets.font_ui.render(btn["text"], True, C_BLACK).get_rect(center=r.center))

# ==============================================================================
# 🎮 GAME SELECTOR SCREEN
# ==============================================================================
class GameSelectorScreen:
    def __init__(self, rect, assets, machine, variants):
        self.rect = rect; self.assets = assets; self.machine = machine; self.variants = variants; self.buttons = []; self._layout_buttons()

    def _layout_buttons(self):
        cols = 4
        btn_w, btn_h = s(220), s(100)
        gap_x, gap_y = s(20), s(30)
        total_w = (cols * btn_w) + ((cols - 1) * gap_x)
        start_x = self.rect.centerx - (total_w // 2)
        start_y = self.rect.top + s(150)

        for i, variant in enumerate(self.variants):
            r = i // cols; c = i % cols
            x = start_x + (c * (btn_w + gap_x))
            y = start_y + (r * (btn_h + gap_y))
            
            clean_name = variant.replace("_", " ")
            if "BONUS" in clean_name: lines = ["BONUS", "DEUCES", "10 / 4" if "10 4" in clean_name else ""]
            elif "NSUD" in clean_name: lines = ["NOT SO", "UGLY", "DEUCES"]
            elif "AIRPORT" in clean_name: lines = ["AIRPORT", "DEUCES", ""]
            else: lines = [clean_name, "", ""]
            
            self.buttons.append({"rect": pygame.Rect(x, y, btn_w, btn_h), "variant": variant, "lines": lines})

    def handle_click(self, pos):
        for btn in self.buttons:
            if btn["rect"].collidepoint(pos): self.machine.act_select_game(btn["variant"]); return True
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, C_IGT_BG, self.rect)
        t = self.assets.font_vfd.render("SELECT A GAME", True, C_IGT_GOLD)
        screen.blit(t, t.get_rect(center=(self.rect.centerx, self.rect.top + s(50))))
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            r = btn["rect"]; hover = r.collidepoint(mouse_pos); border_col = C_WHITE if hover else C_IGT_GOLD
            pygame.draw.rect(screen, border_col, r, border_radius=s(8))
            pygame.draw.rect(screen, C_IGT_RED, r.inflate(s(-6), s(-6)), border_radius=s(6))
            pygame.draw.rect(screen, C_IGT_TXT_BG, r.inflate(s(-16), s(-16)), border_radius=s(4))
            y_off = s(-20)
            for line in btn["lines"]:
                if not line: continue
                col = C_IGT_TXT_SEL if hover else C_IGT_TXT
                txt = self.assets.font_menu_item.render(line, True, col)
                screen.blit(txt, txt.get_rect(center=(r.centerx, r.centery + y_off)))
                y_off += s(22)

# ==============================================================================
# 📈 GRAPH PANEL
# ==============================================================================
class GraphPanel:
    def __init__(self, x, y, w, h, font):
        self.rect = s_rect(x, y, w, h)
        self.font = font
        self.history = []
        self.floor_val = 0; self.ceil_val = 200; self.start_bankroll = 100
        self.selected_hand_id = None; self.scroll_offset = 0; self.view_window_size = 50

    def reset(self, start_bank):
        self.history = []
        self.start_bankroll = start_bank
        self.scroll_offset = 0
        self.selected_hand_id = None

    def set_limits(self, floor, ceil):
        self.floor_val = floor
        self.ceil_val = ceil

    def add_point(self, bankroll):
        self.history.append(bankroll)
        if self.scroll_offset > 0: self.scroll_offset += 1 

    def center_view_on(self, target_id):
        total = len(self.history)
        if target_id < 0 or target_id >= total: return
        new_offset = total - target_id - (self.view_window_size // 2)
        max_offset = max(0, total - self.view_window_size)
        self.scroll_offset = max(0, min(new_offset, max_offset))

    def handle_click(self, pos):
        if not self.rect.collidepoint(pos): return None
        if not self.history: return None
        
        total_points = len(self.history)
        if total_points <= self.view_window_size:
            data_slice = self.history; start_idx = 0
        else:
            end_idx = max(self.view_window_size, total_points - self.scroll_offset)
            start_idx = max(0, end_idx - self.view_window_size)
            end_idx = min(total_points, start_idx + self.view_window_size)
            data_slice = self.history[start_idx : end_idx]
        
        data_slice_len = len(data_slice)
        if data_slice_len < 2: return None
        
        step_x = (self.rect.width - s(20)) / (len(data_slice) - 1)
        rel_x = pos[0] - (self.rect.left + s(10))
        clicked_i = int(round(rel_x / step_x))
        
        if 0 <= clicked_i < data_slice_len:
            actual_hand_id = start_idx + clicked_i
            return actual_hand_id
        return None

    def draw(self, screen):
        pygame.draw.rect(screen, C_GRAPH_BG, self.rect)
        pygame.draw.rect(screen, (80, 80, 80), self.rect, s(2))
        lbl = self.font.render("BANKROLL TREND", True, (150, 150, 150))
        screen.blit(lbl, (self.rect.left + s(10), self.rect.top + s(5)))

        if not self.history: return

        total_points = len(self.history)
        if total_points <= self.view_window_size:
            data_slice = self.history; start_idx = 0
        else:
            end_idx = max(self.view_window_size, total_points - self.scroll_offset)
            start_idx = max(0, end_idx - self.view_window_size)
            end_idx = min(total_points, start_idx + self.view_window_size)
            data_slice = self.history[start_idx : end_idx]
            
        if not data_slice: return

        vals = data_slice + [self.floor_val, self.ceil_val, self.start_bankroll]
        min_val = min(vals); max_val = max(vals)
        padding_y = (max_val - min_val) * 0.1 if max_val != min_val else 10
        min_view = min_val - padding_y; max_view = max_val + padding_y
        range_y = max_view - min_view; range_y = 1 if range_y == 0 else range_y
        step_x = (self.rect.width - s(20)) / (len(data_slice) - 1) if len(data_slice) > 1 else 0

        def to_screen(i, val):
            px = self.rect.left + s(10) + (i * step_x)
            norm = (val - min_view) / range_y
            py = self.rect.bottom - s(10) - (norm * (self.rect.height - s(30)))
            return (px, py)

        if self.floor_val > 0:
            fy = to_screen(0, self.floor_val)[1]
            if self.rect.top < fy < self.rect.bottom:
                pygame.draw.line(screen, C_GRAPH_FLOOR, (self.rect.left, fy), (self.rect.right, fy), 1)
                lbl = self.font.render(f"FLOOR ${self.floor_val:.0f}", True, C_GRAPH_FLOOR)
                screen.blit(lbl, (self.rect.left + s(5), fy + s(2)))

        cy = to_screen(0, self.ceil_val)[1]
        if self.rect.top < cy < self.rect.bottom:
            pygame.draw.line(screen, C_GRAPH_CEIL, (self.rect.left, cy), (self.rect.right, cy), 1)
            lbl = self.font.render(f"TARGET ${self.ceil_val:.0f}", True, C_GRAPH_CEIL)
            screen.blit(lbl, (self.rect.left + s(5), cy - s(12)))

        base_y = to_screen(0, self.start_bankroll)[1]
        if self.rect.top < base_y < self.rect.bottom:
            pygame.draw.line(screen, C_GRAPH_BASE, (self.rect.left, base_y), (self.rect.right, base_y), 1)
            lbl = self.font.render(f"START ${self.start_bankroll:.0f}", True, C_GRAPH_BASE)
            screen.blit(lbl, (self.rect.left + s(5), base_y - s(12)))

        for i in range(len(data_slice)):
            if (start_idx + i) % 10 == 0:
                px = to_screen(i, 0)[0]
                pygame.draw.line(screen, C_GRAPH_GRID, (px, self.rect.top+s(20)), (px, self.rect.bottom-s(10)), 1)

        if len(data_slice) > 1:
            points = [to_screen(i, v) for i, v in enumerate(data_slice)]
            col = C_GRAPH_LINE_G if data_slice[-1] >= self.start_bankroll else C_GRAPH_LINE_R
            pygame.draw.lines(screen, col, False, points, s(2))
            pygame.draw.circle(screen, C_WHITE, (int(points[-1][0]), int(points[-1][1])), s(3))

        if self.selected_hand_id is not None:
            if start_idx <= self.selected_hand_id < start_idx + len(data_slice):
                local_i = self.selected_hand_id - start_idx
                val = data_slice[local_i]
                pt = to_screen(local_i, val)
                pygame.draw.line(screen, C_CYAN_MSG, (pt[0], self.rect.top), (pt[0], self.rect.bottom), 1)
                pygame.draw.circle(screen, C_CYAN_MSG, (int(pt[0]), int(pt[1])), s(5), s(2))
                lbl = self.font.render(f"#{self.selected_hand_id}: ${val:.2f}", True, C_CYAN_MSG)
                screen.blit(lbl, (pt[0] + s(5), pt[1] - s(20)))

# ==============================================================================
# 📜 LOG PANEL
# ==============================================================================
class LogPanel:
    def __init__(self, x, y, w, h, assets):
        self.rect = s_rect(x, y, w, h)
        self.assets = assets
        self.reset()
        self.scroll_y = 0
        self.entry_height = s(110)
        self.content_height = 0
        self.header_h = s(75)
        self.is_dragging = False; self.drag_start_y = 0; self.scroll_start_y = 0;
        self.thumb_rect = pygame.Rect(0,0,0,0)
        self.highlighted_id = None

    def reset(self):
        self.logs = []; self.total_bet = 0.0; self.total_won = 0.0; self.total_hands = 0
        self.content_height = 0; self.scroll_y = 0; self.highlighted_id = None

    def add_entry(self, hand_num, deal_cards, final_cards, held_indices, ev_data, result_data, bet_amount):
        entry = {'id': hand_num, 'deal': deal_cards, 'final': final_cards, 'held_idx': held_indices, 'ev': ev_data, 'result': result_data, 'bet': bet_amount}
        self.logs.insert(0, entry)
        self.content_height = len(self.logs) * self.entry_height
        self.total_hands += 1; self.total_bet += bet_amount; self.total_won += result_data['win']

    def scroll_to_hand(self, hand_id):
        self.highlighted_id = hand_id
        target_idx = -1
        for i, log in enumerate(self.logs):
            if log['id'] == hand_id: target_idx = i; break
        if target_idx != -1:
            self.scroll_y = target_idx * self.entry_height
            self._clamp_scroll()

    def handle_click(self, pos):
        if not self.rect.collidepoint(pos) or self.thumb_rect.collidepoint(pos): return None
        rel_y = pos[1] - (self.rect.top + self.header_h + s(10)) + self.scroll_y
        if rel_y < 0: return None
        clicked_idx = int(rel_y // self.entry_height)
        if 0 <= clicked_idx < len(self.logs):
            return self.logs[clicked_idx]['id']
        return None

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(mouse_pos):
            self.scroll_y -= event.y * s(20); self._clamp_scroll()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.thumb_rect.collidepoint(mouse_pos):
            self.is_dragging = True; self.drag_start_y = mouse_pos[1]; self.scroll_start_y = self.scroll_y
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            delta_y = mouse_pos[1] - self.drag_start_y
            view_h = self.rect.height - self.header_h
            if self.content_height > view_h and view_h > 0:
                bar_h = view_h; ratio = bar_h / self.content_height
                self.scroll_y = self.scroll_start_y + (delta_y / ratio); self._clamp_scroll()

    def _clamp_scroll(self):
        view_h = self.rect.height - self.header_h
        max_scroll = max(0, self.content_height - view_h)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    def _calculate_hud_stats(self):
        rtp = (self.total_won / self.total_bet * 100) if self.total_bet > 0 else 0.0
        hits = sum(1 for log in self.logs if log['result']['win'] > 0)
        hit_rate = (hits / self.total_hands * 100) if self.total_hands > 0 else 0.0
        last_10 = self.logs[:10]
        l10_rate = (sum(1 for log in last_10 if log['result']['win'] > 0) / len(last_10) * 100) if last_10 else 0.0
        return rtp, hit_rate, l10_rate

    def draw_cards_text(self, screen, cards, x, y, highlights=None):
        suit_map = {'s': '♠', 'c': '♣', 'h': '♥', 'd': '♦'}
        font = self.assets.font_log_bold; char_w = s(35)
        for i, card in enumerate(cards):
            current_x = x + (i * char_w)
            if highlights and i in highlights:
                pygame.draw.rect(screen, C_NB_HIGHLIGHT, (current_x - s(2), y, char_w - s(2), s(20)))
            rank = card[0]; suit_char = card[1]
            color = C_NB_RED if suit_char in 'hd' else C_NB_BLACK
            screen.blit(font.render(f"{rank}{suit_map.get(suit_char, suit_char)}", True, color), (current_x, y))

    def draw(self, screen):
        pygame.draw.rect(screen, C_NB_BG, self.rect)
        pygame.draw.rect(screen, C_NB_TEXT, self.rect, s(2))
        pygame.draw.rect(screen, (240, 240, 240), (self.rect.left, self.rect.top, self.rect.width, self.header_h))
        pygame.draw.line(screen, C_NB_TEXT, (self.rect.left, self.rect.top + self.header_h), (self.rect.right, self.rect.top + self.header_h), s(2))
        title = self.assets.font_ui.render("HAND HISTORY", True, C_NB_TEXT)
        screen.blit(title, (self.rect.centerx - title.get_width()//2, self.rect.top + s(5)))
        
        rtp, hit_rate, l10_rate = self._calculate_hud_stats()
        screen.blit(self.assets.font_log_bold.render(f"HANDS: {self.total_hands} | RTP: {rtp:.1f}%", True, (80, 80, 80)), (self.rect.centerx - s(100), self.rect.top + s(30)))
        hot_str = " 🔥" if l10_rate >= 50 else ""
        screen.blit(self.assets.font_log_bold.render(f"HIT RATE: {hit_rate:.0f}% (L10: {l10_rate:.0f}%{hot_str})", True, (200, 0, 0) if l10_rate >= 50 else (80, 80, 80)), (self.rect.centerx - s(100), self.rect.top + s(50)))

        clip_rect = pygame.Rect(self.rect.left, self.rect.top + self.header_h, self.rect.width, self.rect.height - self.header_h)
        original_clip = screen.get_clip(); screen.set_clip(clip_rect)
        start_y = (self.rect.top + self.header_h + s(10)) - self.scroll_y
        
        for i, log in enumerate(self.logs):
            y = start_y + (i * self.entry_height)
            if y + self.entry_height < self.rect.top or y > self.rect.bottom: continue
            if log['id'] == self.highlighted_id:
                bg = pygame.Rect(self.rect.left + s(2), y, self.rect.width - s(16), self.entry_height)
                pygame.draw.rect(screen, (230, 240, 255), bg); pygame.draw.rect(screen, C_GRAPH_BASE, bg, s(2))
            pygame.draw.line(screen, C_NB_LINES, (self.rect.left + s(10), y + self.entry_height - s(10)), (self.rect.right - s(20), y + self.entry_height - s(10)))
            
            screen.blit(self.assets.font_log_bold.render(f"#{log['id']}", True, (100, 100, 100)), (self.rect.left + s(15), y))
            screen.blit(self.assets.font_log_bold.render(f"{log['result']['rank']}", True, C_NB_BLACK), (self.rect.left + s(70), y))
            win = log['result']['win']
            screen.blit(self.assets.font_log_bold.render(f"+${win:.2f}", True, (0, 150, 0) if win > 0 else (150, 150, 150)), (self.rect.right - s(80), y))
            
            screen.blit(self.assets.font_log.render("Deal:", True, C_NB_TEXT), (self.rect.left + s(15), y + s(25)))
            self.draw_cards_text(screen, log['deal'], self.rect.left + s(70), y + s(25), highlights=log['held_idx'])
            screen.blit(self.assets.font_log.render("Final:", True, C_NB_TEXT), (self.rect.left + s(15), y + s(50)))
            self.draw_cards_text(screen, log['final'], self.rect.left + s(70), y + s(50), highlights=log['held_idx'])
            
            user_ev = log['ev']['user']; max_ev = log['ev']['max']; diff = max_ev - user_ev
            if diff < 0.01: dec = f"✅ Optimal ({user_ev:.2f})"; col = (0, 120, 0)
            elif diff < 0.05: dec = f"⚠️ Alternate (-{diff:.2f} EV)"; col = (200, 140, 0)
            else: dec = f"❌ Error: -{diff:.2f} EV (Max: {max_ev:.2f})"; col = C_NB_RED
            screen.blit(self.assets.font_log_bold.render(dec, True, col), (self.rect.left + s(15), y + s(75)))

        screen.set_clip(original_clip)
        if self.content_height > clip_rect.height:
            bar_h = clip_rect.height; thumb_h = max(s(30), (clip_rect.height / self.content_height) * bar_h)
            scroll_percent = self.scroll_y / (self.content_height - clip_rect.height)
            self.thumb_rect = pygame.Rect(self.rect.right - s(14), clip_rect.top + (scroll_percent * (bar_h - thumb_h)), s(12), thumb_h)
            pygame.draw.rect(screen, (230, 230, 230), (self.rect.right - s(14), clip_rect.top, s(12), bar_h))
            pygame.draw.rect(screen, (150, 150, 150) if not self.is_dragging else (100, 100, 100), self.thumb_rect, border_radius=s(4))
        else: self.thumb_rect = pygame.Rect(0,0,0,0)

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

# ==============================================================================
# 🎮 MAIN SYSTEM (UNIVERSAL)
# ==============================================================================
class IGT_Machine:
    def __init__(self):
        try:
            icon_path = os.path.join("images", "app_icon.png")
            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path)
                pygame.display.set_icon(icon)
        except: pass

        self.screen = pygame.display.set_mode((PHYSICAL_W, PHYSICAL_H), FULLSCREEN_FLAG)
             
        pygame.display.set_caption("EV Navigator - Universal (v10)")
        self.clock = pygame.time.Clock()
        self.assets = AssetManager(); self.sound = SoundManager()
        self.available_variants = list(PAYTABLES.keys()); self.variant_idx = 0
        self.sim = dw_sim_engine.DeucesWildSim(variant=self.available_variants[self.variant_idx])
        self.core = self.sim.core
        self.paytable = PaytableDisplay(self.assets, self.sim.paytable)
        self.state = "IDLE"; self.start_bankroll = 100.00; self.bankroll = 100.00
        self.coins_bet = 5; self.denom = 0.25; self.floor_pct = 50; self.ceil_pct = 120; self.floor_val = 0; self.ceil_val = 200
        self.win_display = 0.0; self.win_target = 0.0; self.last_win_rank = None
        self.hand = []; self.stub = []; self.held_indices = []; self.deal_snapshot = []
        
        # SCALED LAYOUT INITS
        self.log_panel = LogPanel(1240, 20, 340, 500, self.assets)
        self.graph_panel = GraphPanel(1240, 530, 340, 300, self.assets.font_tiny)
        self.strategy_panel = StrategyPanel(0, 0, 240, 850, self.assets, self)
        
        # Overlay Screens (Full Scaled Rect)
        full_overlay = s_rect(240, 0, 1360, 850)
        self.codex_screen = CodexScreen(full_overlay, self.assets, self)
        self.game_selector = GameSelectorScreen(full_overlay, self.assets, self, self.available_variants)
        self.session_setup = SessionSetupScreen(full_overlay, self.assets, self)
        
        start_x = 360
        self.cards = [CardSlot(start_x + (i * 152), 410, self.assets) for i in range(5)]
        
        self.auto_hold_active = False; self.auto_play_active = False; self.last_action_time = 0; self.advice_msg = None
        self.hands_played = 0; self._init_buttons(); self._init_meters(); self.vol_btn = VolumeButton(1192, 785, self.sound)
        self.update_machine_limits()

    def update_machine_limits(self):
        self.floor_val = (self.start_bankroll * (self.floor_pct / 100))
        self.ceil_val = (self.start_bankroll * (self.ceil_pct / 100))
        self.graph_panel.set_limits(self.floor_val, self.ceil_val)
        
    def _init_buttons(self):
        y = 780; h = 50; start_x = 340
        self.buttons = [
            PhysicalButton(s_rect(start_x, y, 100, h), "STRATEGY", self.act_open_codex, color=(200, 200, 255)),
            PhysicalButton(s_rect(start_x + 110, y, 100, h), "MORE GAMES", self.act_open_menu),
            PhysicalButton(s_rect(start_x + 220, y, 90, h), "AUTO HOLD", self.act_toggle_auto_hold, color=C_BTN_FACE),
            PhysicalButton(s_rect(start_x + 320, y, 110, h), "AUTO PLAY", self.act_toggle_auto_play, color=C_BTN_FACE),
            PhysicalButton(s_rect(start_x + 440, y, 90, h), "BET ONE", self.act_bet_one),
            PhysicalButton(s_rect(start_x + 540, y, 90, h), "BET MAX", self.act_bet_max),
            PhysicalButton(s_rect(start_x + 690, y, 150, h), "DEAL", self.act_deal_draw, color=(255, 215, 0))
        ]
        self.btn_auto_hold = self.buttons[2]; self.btn_auto_play = self.buttons[3]; self.btn_deal = self.buttons[-1]
        
    def _init_meters(self):
        self.meter_win = ClickableMeter(400, 680, "WIN", C_DIGITAL_RED)
        self.meter_bet = ClickableMeter(740, 680, "BET", C_DIGITAL_YEL)
        self.meter_credit = ClickableMeter(1080, 680, "CREDIT", C_DIGITAL_RED, default_is_credits=False)
        self.meters = [self.meter_win, self.meter_bet, self.meter_credit]

    def act_toggle_auto_hold(self):
        self.auto_hold_active = not self.auto_hold_active
        self.btn_auto_hold.text = "AUTO: ON" if self.auto_hold_active else "AUTO HOLD"
        self.btn_auto_hold.color = C_DIGITAL_GRN if self.auto_hold_active else C_BTN_FACE
        if self.auto_hold_active and self.state == "DECISION": self.run_solver()
    def act_toggle_auto_play(self):
        self.auto_play_active = not self.auto_play_active
        self.btn_auto_play.text = "STOP" if self.auto_play_active else "AUTO PLAY"
        self.btn_auto_play.color = C_DIGITAL_RED if self.auto_play_active else C_BTN_FACE
        if self.auto_play_active: self.last_action_time = pygame.time.get_ticks()
    def run_solver(self):
        results = dw_fast_solver.solve_hand(self.hand, self.sim.paytable)
        self.strategy_panel.set_results(results)
        
        for c in self.cards: c.is_held = False; c.is_runner_up = False
        self.advice_msg = None
        
        if not results: return
        best_cards = results[0]['held']

        if self.auto_hold_active:
            self.held_indices = []
            for i, card in enumerate(self.hand):
                if card in best_cards: 
                    self.cards[i].is_held = True; self.held_indices.append(i)
            if len(results) > 1:
                second_cards = results[1]['held']
                for i, card in enumerate(self.hand):
                    if card in second_cards: self.cards[i].is_runner_up = True
            
            self.advice_msg = None if best_cards else "ADVICE: DRAW ALL"
            self.sound.play("bet")
        else:
            self.held_indices = []
    def act_open_menu(self):
        if self.state == "IDLE": self.state = "GAME_SELECT"; self.sound.play("bet")
    def act_open_session_setup(self):
        if self.state == "IDLE":
            self.state = "SESSION_SETUP"
            self.session_setup.temp_bank = self.bankroll; self.session_setup.temp_denom = self.denom
            self.session_setup.temp_floor_pct = self.floor_pct; self.session_setup.temp_ceil_pct = self.ceil_pct
            self.sound.play("bet")
    def act_open_codex(self):
        if self.state == "IDLE": self.state = "CODEX"; self.sound.play("bet")
    def act_select_game(self, new_variant):
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
            if self.floor_val > 0 and self.bankroll <= self.floor_val: self.auto_play_active = False; self.advice_msg = "FLOOR HIT: MISSION ABORTED"; self.act_toggle_auto_play(); return
            if self.ceil_val > 0 and self.bankroll >= self.ceil_val: self.auto_play_active = False; self.advice_msg = "CEILING HIT: MISSION SUCCESS"; self.act_toggle_auto_play(); return
            cost = self.coins_bet * self.denom
            if self.bankroll < cost: return
            self.bankroll -= cost
            self.win_display = 0.0; self.win_target = 0.0; self.last_win_rank = None; self.advice_msg = None
            self.hand, self.stub = self.core.deal_hand()
            self.deal_snapshot = list(self.hand)
            self.hands_played += 1; self.held_indices = []
            for i, c in enumerate(self.hand): self.cards[i].card_val = c; self.cards[i].is_face_up = True; self.cards[i].is_held = False; self.cards[i].is_runner_up = False
            self.sound.play("deal"); self.state = "DECISION"; self.btn_deal.text = "DRAW"; self.run_solver()
        elif self.state == "DECISION":
            self.advice_msg = None
            solver_res = dw_fast_solver.solve_hand(self.hand, self.sim.paytable)
            optimal_hold = solver_res[0]['held'] if solver_res else []
            opt_indices = [i for i, c in enumerate(self.hand) if c in optimal_hold]
            max_ev = dw_exact_solver.calculate_exact_ev(self.hand, opt_indices, self.sim.paytable)
            user_hold_cards = [self.hand[i] for i in self.held_indices]
            if set(user_hold_cards) == set(optimal_hold): user_ev = max_ev
            else: user_ev = dw_exact_solver.calculate_exact_ev(self.hand, self.held_indices, self.sim.paytable)
            max_ev_disp = (max_ev / 5) * self.coins_bet; user_ev_disp = (user_ev / 5) * self.coins_bet
            logged_held_indices = list(self.held_indices)
            self.core.shuffle(self.stub)
            for i in range(5):
                if i not in self.held_indices:
                    if self.stub: self.hand[i] = self.stub.pop(0)
            for i, c in enumerate(self.hand): self.cards[i].card_val = c
            self.sound.play("deal")
            rank, mult = self.sim.evaluate_hand_score(self.hand)
            win_val = (mult * self.coins_bet) * self.denom
            if win_val > 0: self.sound.play("win"); self.last_win_rank = rank; self.win_target = win_val; self.bankroll += win_val
            else: self.last_win_rank = None
            bet_val = (self.coins_bet * self.denom)
            self.log_panel.add_entry(self.hands_played, self.deal_snapshot, list(self.hand), logged_held_indices, {'user': user_ev_disp, 'max': max_ev_disp}, {'win': win_val, 'rank': rank.replace('_',' ')}, bet_val)
            self.graph_panel.add_point(self.bankroll)
            self.state = "IDLE"; self.btn_deal.text = "DEAL"

    def handle_click(self, pos):
        if self.state == "IDLE":
             if self.strategy_panel.btn_setup.rect.collidepoint(pos): self.strategy_panel.btn_setup.callback(); self.sound.play("bet"); return
        if self.state == "GAME_SELECT": self.game_selector.handle_click(pos); return
        if self.state == "SESSION_SETUP": self.session_setup.handle_click(pos); return
        if self.state == "CODEX": self.codex_screen.handle_click(pos); return
        
        clicked_hand_id = self.graph_panel.handle_click(pos)
        if clicked_hand_id is not None:
            if clicked_hand_id == self.log_panel.highlighted_id:
                self.log_panel.highlighted_id = None; self.graph_panel.selected_hand_id = None
            else:
                self.log_panel.scroll_to_hand(clicked_hand_id); self.graph_panel.selected_hand_id = clicked_hand_id
        
        clicked_log_id = self.log_panel.handle_click(pos)
        if clicked_log_id is not None:
            if clicked_log_id == self.graph_panel.selected_hand_id:
                self.graph_panel.selected_hand_id = None; self.log_panel.highlighted_id = None
            else:
                self.graph_panel.selected_hand_id = clicked_log_id
                self.log_panel.highlighted_id = clicked_log_id
                self.graph_panel.center_view_on(clicked_log_id)

        if self.state == "DECISION":
            for i, slot in enumerate(self.cards):
                if slot.rect.collidepoint(pos):
                    slot.is_held = not slot.is_held
                    if slot.is_held: self.held_indices.append(i)
                    else: self.held_indices.remove(i)
        if self.vol_btn.check_click(pos): return
        for m in self.meters:
            if m.check_click(pos): self.sound.play("bet"); return
        for btn in self.buttons:
            if btn.rect.collidepoint(pos): btn.callback(); self.sound.play("bet")

    def update_auto_play(self):
        if not self.auto_play_active: return
        now = pygame.time.get_ticks()
        if now - self.last_action_time > 400: self.last_action_time = now; self.act_deal_draw()

    def _draw_main_game_elements(self):
        self.paytable.draw(self.screen, self.coins_bet, self.last_win_rank)
        off_x = s(240) + X_OFFSET; game_w = s(1000)
        # Felt Area
        pygame.draw.rect(self.screen, C_FELT_GREEN, (off_x, s(380) + Y_OFFSET, game_w, s(280)))
        pygame.draw.line(self.screen, C_WHITE, (off_x, s(380) + Y_OFFSET), (off_x+game_w, s(380) + Y_OFFSET), s(2))
        pygame.draw.line(self.screen, C_WHITE, (off_x, s(660) + Y_OFFSET), (off_x+game_w, s(660) + Y_OFFSET), s(2))
        
        self.vol_btn.draw(self.screen)
        if self.advice_msg:
            col = C_GOLD_HELD if "DRAW ALL" in self.advice_msg else (C_DIGITAL_RED if "FLOOR" in self.advice_msg else C_DIGITAL_GRN)
            msg = self.assets.font_vfd.render(self.advice_msg, True, col)
            center_x = off_x + (game_w // 2)
            shadow = self.assets.font_vfd.render(self.advice_msg, True, C_BLACK)
            self.screen.blit(shadow, shadow.get_rect(center=(center_x + s(2), s(395) + Y_OFFSET + s(2))))
            self.screen.blit(msg, msg.get_rect(center=(center_x, s(395) + Y_OFFSET)))
        
        if self.auto_play_active: self.screen.blit(self.assets.font_ui.render("ENGAGED", True, C_DIGITAL_GRN), (s(440)+off_x, s(831) + Y_OFFSET))
        self.screen.blit(self.assets.font_lbl.render(f"DEALS: {self.hands_played}", True, C_YEL_TEXT), (s(30)+off_x, s(750) + Y_OFFSET))
        self.screen.blit(self.assets.font_ui.render(f"Deuces Wild ({self.sim.variant})", True, C_WHITE), (s(3)+off_x, s(831) + Y_OFFSET))
        
        for c in self.cards: c.draw(self.screen)
        
        if self.win_display < self.win_target: self.win_display += self.denom; self.win_display = min(self.win_display, self.win_target)
        for m in self.meters:
            val = self.win_display if m.label == "WIN" else (self.coins_bet * self.denom if m.label == "BET" else self.bankroll)
            m.draw(self.screen, self.assets, val, self.denom)
        
        cx, cy = s(910) + X_OFFSET, s(680) + Y_OFFSET + s(30); rect = pygame.Rect(cx-s(40), cy-s(25), s(80), s(50))
        pygame.draw.ellipse(self.screen, (255, 215, 0), rect); pygame.draw.ellipse(self.screen, C_BLACK, rect, s(2))
        txt_str = f"${int(self.denom)}" if self.denom >= 1.0 else f"{int(self.denom*100)}¢"
        txt = self.assets.font_vfd.render(txt_str, True, C_RED_ACTIVE)
        self.screen.blit(txt, txt.get_rect(center=rect.center))
        
        mouse_pos = pygame.mouse.get_pos(); mouse_down = pygame.mouse.get_pressed()[0]
        for b in self.buttons: b.update(mouse_pos, mouse_down); b.draw(self.screen, self.assets.font_ui)

    def draw(self):
        self.screen.fill(C_BLACK)
        self.strategy_panel.draw(self.screen)
        self.log_panel.draw(self.screen)
        self.graph_panel.draw(self.screen)
        if self.state == "GAME_SELECT": self.game_selector.draw(self.screen)
        elif self.state == "SESSION_SETUP": self.session_setup.draw(self.screen)
        elif self.state == "CODEX": self._draw_main_game_elements(); self.codex_screen.draw(self.screen)
        else: self._draw_main_game_elements()
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.update_auto_play()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                self.log_panel.handle_event(event)
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.handle_click(event.pos)
            self.draw()
            if self.state == "IDLE" and not self.auto_play_active: self.clock.tick(FPS_IDLE)
            else: self.clock.tick(FPS_ACTIVE)
        pygame.quit(); sys.exit()

    def start_new_session(self):
        self.variant_idx = 0; self.act_select_game(self.available_variants[self.variant_idx])
        self.start_bankroll = 100.00; self.bankroll = 100.00; self.denom = 0.25; self.coins_bet = 5
        self.floor_pct = 50; self.ceil_pct = 120; self.update_machine_limits()
        self.log_panel.reset(); self.graph_panel.reset(self.start_bankroll); self.strategy_panel.reset(); self.hands_played = 0
        self.state = "IDLE"; self.win_display = 0.0; self.win_target = 0.0; self.last_win_rank = None
        self.advice_msg = None; self.auto_hold_active = False; self.auto_play_active = False
        self.btn_auto_hold.text = "AUTO HOLD"; self.btn_auto_hold.color = C_BTN_FACE
        self.btn_auto_play.text = "AUTO PLAY"; self.btn_auto_play.color = C_BTN_FACE
        self.hand = []; self.stub = []; self.held_indices = []
        for c in self.cards: c.card_val = None; c.is_face_up = False; c.is_held = False; c.is_runner_up = False

if __name__ == "__main__":
    app = IGT_Machine()
    app.run()