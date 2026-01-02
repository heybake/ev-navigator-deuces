import pygame
import sys
import os
import csv
import datetime
import math

# Pydroid 3 Sandbox Escape
if "ANDROID_ARGUMENT" in os.environ:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Windows Taskbar Fix
if os.name == 'nt':
    try:
        import ctypes
        appid = 'ev_navigator.deuces_wild.universal.v20'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    except: pass

# --- IMPORTS ---
import dw_sim_engine
import dw_fast_solver
import dw_exact_solver
import dw_strategy_definitions 
from dw_pay_constants import PAYTABLES
from dw_universal_lib import *
import dw_stats_helper

# ==============================================================================
# 📝 SESSION LOGGER
# ==============================================================================
class SessionLogger:
    def __init__(self):
        self.active = False
        self.filepath = None
        self.writer = None
        self.file_handle = None

    def start_session(self, variant_name):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dw_session_{timestamp}.csv"
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(base_dir, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        self.filepath = os.path.join(log_dir, filename)
        
        try:
            self.file_handle = open(self.filepath, mode='w', newline='', encoding='utf-8')
            self.writer = csv.writer(self.file_handle)
            headers = [
                "HandID", "Time", "Variant", "Bankroll_Start", "Denom", "Coins", "Bet_Cost",
                "Deal_1", "Deal_2", "Deal_3", "Deal_4", "Deal_5",
                "Held_Indices", "Auto_Hold_Used",
                "Final_1", "Final_2", "Final_3", "Final_4", "Final_5",
                "Result_Rank", "Win_Amt", "Profit",
                "EV_User", "EV_Max", "EV_Error", "Perfect_Play"
            ]
            self.writer.writerow(headers)
            self.file_handle.flush()
            self.active = True
            print(f"📝 Logging started: {self.filepath}")
        except Exception as e:
            print(f"❌ Logging Failed: {e}")
            self.active = False

    def log_hand(self, data):
        if not self.active or not self.writer: return
        
        t_str = datetime.datetime.now().strftime("%H:%M:%S")
        ev_user = data.get('ev_user', 0)
        ev_max = data.get('ev_max', 0)
        err = ev_max - ev_user
        is_perfect = (err < 0.0001)
        profit = data.get('win', 0) - data.get('cost', 0)
        deal = data.get('deal', [])
        final = data.get('final', [])
        def get_c(lst, i): return lst[i] if i < len(lst) else ""
        
        row = [
            data.get('id'), t_str, data.get('variant'), 
            f"{data.get('bank_start'):.2f}", data.get('denom'), data.get('coins'), f"{data.get('cost'):.2f}",
            get_c(deal,0), get_c(deal,1), get_c(deal,2), get_c(deal,3), get_c(deal,4),
            str(data.get('held_idx')), data.get('auto_hold'),
            get_c(final,0), get_c(final,1), get_c(final,2), get_c(final,3), get_c(final,4),
            data.get('rank'), f"{data.get('win'):.2f}", f"{profit:.2f}",
            f"{ev_user:.4f}", f"{ev_max:.4f}", f"{err:.4f}", str(is_perfect)
        ]
        try:
            self.writer.writerow(row)
            self.file_handle.flush()
        except: pass

    def close_session(self):
        if self.file_handle:
            self.file_handle.close()
        self.active = False

# ==============================================================================
# 📊 SESSION STATS SCREEN (With File Manager & Pro Graphs)
# ==============================================================================
class SessionStatsScreen:
    def __init__(self, rect, assets, machine):
        self.rect = rect
        self.assets = assets
        self.machine = machine
        self.active_tab = "OVERVIEW"
        self.tabs = ["OVERVIEW", "STRATEGY", "LUCK", "HITS", "GRAPHS", "LOGS"]
        self.tab_buttons = []
        
        # Log Management
        self.log_files = [] 
        self.selected_filename = None 
        
        self.stats = {}
        self.hit_stats = [] 
        self.session_data = [] # Stores full hand history for graphs
        self.current_filename = "Active Session"
        self._init_ui()

    def _init_ui(self):
        # Tabs - Squeeze 6 tabs into the same space
        tab_w = s(140) 
        tab_h = s(50)
        total_w = len(self.tabs) * tab_w
        start_x = self.rect.centerx - (total_w // 2)
        y = self.rect.top + s(60)
        
        self.tab_buttons = []
        for i, tab in enumerate(self.tabs):
            self.tab_buttons.append({
                "rect": pygame.Rect(start_x + (i * tab_w), y, tab_w, tab_h),
                "label": tab,
                "action": lambda t=tab: self._set_tab(t)
            })
            
        # Close Button
        self.btn_close = PhysicalButton(
            pygame.Rect(self.rect.centerx - s(60), self.rect.bottom - s(80), s(120), s(50)),
            "CLOSE", self._close, color=C_DIGITAL_RED
        )

    def _set_tab(self, tab):
        self.active_tab = tab
        if tab == "LOGS":
            self._scan_logs()
        self.machine.sound.play("bet")

    def _close(self):
        self.machine.state = "IDLE"
        self.machine.sound.play("bet")

    def _scan_logs(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(base_dir, "logs")
        self.log_files = []
        if os.path.exists(log_dir):
            raw_files = [f for f in os.listdir(log_dir) if f.endswith(".csv")]
            raw_files.sort(reverse=True) 
            
            for f in raw_files:
                path = os.path.join(log_dir, f)
                is_empty = False
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        if len(fh.readlines()) <= 1:
                            is_empty = True
                except:
                    is_empty = True 
                
                self.log_files.append({
                    'name': f,
                    'empty': is_empty
                })

    def _delete_log(self, filename):
        if self.machine.logger.active and self.machine.logger.filepath:
            active_file = os.path.basename(self.machine.logger.filepath)
            if filename == active_file:
                print("Cannot delete active session log.")
                self.machine.sound.play("bet") 
                return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "logs", filename)
        try:
            os.remove(path)
            self.machine.sound.play("bet") # Standard click for delete
            self._scan_logs()
            if filename == self.current_filename:
                self.stats = {}
                self.session_data = []
                self.current_filename = "Deleted File"
            if filename == self.selected_filename:
                self.selected_filename = None
        except Exception as e:
            print(f"Error deleting file: {e}")

    def load_active_session(self):
        raw_data = self.machine.log_panel.logs[::-1]
        if not raw_data:
            self.stats = {}
            self.session_data = []
            self.active_tab = "LOGS" 
            self._scan_logs()
            return

        self.current_filename = "Active Session"
        self._calculate_stats(raw_data)
        self.active_tab = "OVERVIEW"

    def load_from_file(self, filename):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "logs", filename)
        data = []
        try:
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    deal = [row[f'Deal_{i}'] for i in range(1,6)]
                    final = [row[f'Final_{i}'] for i in range(1,6)]
                    
                    held_str = row['Held_Indices'].replace('[','').replace(']','').replace(' ','')
                    held_idx = [int(x) for x in held_str.split(',')] if held_str else []
                    
                    entry = {
                        'id': int(row['HandID']),
                        'variant': row['Variant'],
                        'time': row.get('Time', ''),
                        'bank_start': float(row['Bankroll_Start']),
                        'denom': float(row['Denom']),
                        'bet': float(row['Bet_Cost']),
                        'deal': deal, 'final': final,
                        'held_idx': held_idx,
                        'ev': {'user': float(row['EV_User']), 'max': float(row['EV_Max'])},
                        'result': {'rank': row['Result_Rank'], 'win': float(row['Win_Amt'])}
                    }
                    data.append(entry)
            
            self.current_filename = filename
            self._calculate_stats(data)
            self.active_tab = "OVERVIEW"
            self.machine.sound.play("rollup")
        except Exception as e:
            print(f"Failed to load log: {e}")

    def _calculate_stats(self, data):
        self.session_data = data 
        total_hands = len(data)
        if total_hands == 0: return

        variant = data[0].get('variant', 'Unknown')
        start_time = data[0].get('time', 'Unknown')

        total_bet = sum(d['bet'] for d in data)
        total_won = sum(d['result']['win'] for d in data)
        net = total_won - total_bet
        rtp = (total_won / total_bet * 100) if total_bet > 0 else 0
        
        errors = 0; cost_errors = 0.0; perfect_hands = 0
        err_1deuce = 0; count_1deuce = 0
        err_pairs = 0; count_pairs = 0
        err_flush = 0; count_flush = 0   
        err_3royal = 0; count_3royal = 0 
        
        expected_return_dollars = 0.0 
        
        for d in data:
            user_ev_coins = d['ev']['user'] 
            max_ev_coins = d['ev']['max']
            denom_val = d['denom']
            
            expected_return_dollars += user_ev_coins * denom_val
            
            diff = max_ev_coins - user_ev_coins
            if diff > 0.0001:
                errors += 1
                cost_errors += (diff * denom_val)
            else:
                perfect_hands += 1
                
            deuces = sum(1 for c in d['deal'] if c[0] == '2')
            
            # Leak Detection
            if deuces == 1:
                count_1deuce += 1
                if diff > 0.0001: err_1deuce += 1
            elif deuces == 0:
                ranks = [c[0] for c in d['deal']]
                suits = [c[1] for c in d['deal']]
                rank_set = set(ranks)
                suit_counts = {s: suits.count(s) for s in set(suits)}
                
                if len(rank_set) < 5: 
                    count_pairs += 1
                    if diff > 0.0001: err_pairs += 1
                
                if 4 in suit_counts.values():
                    count_flush += 1
                    if diff > 0.0001: err_flush += 1
                    
                for s_key, count in suit_counts.items():
                    if count >= 3:
                        suited_ranks = [r for i, r in enumerate(ranks) if suits[i] == s_key]
                        royals = sum(1 for r in suited_ranks if r in ['T','J','Q','K','A','10','11','12','13','14'])
                        if royals == 3:
                            count_3royal += 1
                            if diff > 0.0001: err_3royal += 1
                            break 

        perfect_pct = (perfect_hands / total_hands) * 100
        luck_diff = total_won - expected_return_dollars

        self.stats = {
            'variant': variant,
            'time': start_time,
            'hands': total_hands,
            'net': net,
            'rtp': rtp,
            'perfect_pct': perfect_pct,
            'errors': errors,
            'cost': cost_errors,
            'ev_gen': expected_return_dollars, 
            'luck': luck_diff,
            'err_1d': (err_1deuce, count_1deuce),
            'err_pair': (err_pairs, count_pairs),
            'err_flush': (err_flush, count_flush),
            'err_3royal': (err_3royal, count_3royal)
        }
        
        self.hit_stats = dw_stats_helper.compute_hit_stats(data)

    def handle_click(self, pos):
        for btn in self.tab_buttons:
            if btn["rect"].collidepoint(pos):
                btn["action"]()
                return

        if self.btn_close.rect.collidepoint(pos):
            self.btn_close.callback()
            return

        if self.active_tab == "LOGS":
            # Reconstruct geometry exactly as in draw()
            panel_rect = self.rect.inflate(s(-100), s(-100))
            content_rect = pygame.Rect(panel_rect.left + s(40), panel_rect.top + s(140), panel_rect.width - s(80), panel_rect.height - s(220))
            
            start_y = content_rect.top
            line_h = s(55) 
            
            for i, file_data in enumerate(self.log_files):
                if i > 8: break 
                
                f_name = file_data['name']
                is_empty = file_data['empty']
                y = start_y + (i * line_h)
                
                btn_w, btn_h = s(80), s(35)
                btn_y = y + s(10)
                del_rect = pygame.Rect(content_rect.right - s(100), btn_y, btn_w, btn_h)
                load_rect = pygame.Rect(content_rect.right - s(200), btn_y, btn_w, btn_h)
                row_rect = pygame.Rect(content_rect.left, y, content_rect.width, line_h)
                
                if del_rect.collidepoint(pos):
                    self._delete_log(f_name)
                    return
                elif load_rect.collidepoint(pos):
                    if not is_empty:
                        self.load_from_file(f_name)
                    else:
                        self.machine.sound.play("bet")
                    return
                elif row_rect.collidepoint(pos):
                    self.selected_filename = f_name
                    self.machine.sound.play("bet")
                    return

    def draw(self, screen):
        # Dim Background
        s_surf = pygame.Surface((PHYSICAL_W, PHYSICAL_H), pygame.SRCALPHA)
        s_surf.fill((0, 0, 0, 230))
        screen.blit(s_surf, (0,0))

        # Panel Body
        panel_rect = self.rect.inflate(s(-100), s(-100))
        pygame.draw.rect(screen, C_PANEL_BG, panel_rect, border_radius=s(12))
        pygame.draw.rect(screen, C_IGT_GOLD, panel_rect, s(3), border_radius=s(12))

        # Header
        title = self.assets.font_vfd.render(f"SESSION REPORT: {self.current_filename}", True, C_IGT_GOLD)
        screen.blit(title, title.get_rect(center=(self.rect.centerx, self.rect.top + s(30))))

        # Draw Tabs
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.tab_buttons:
            r = btn["rect"]
            hover = r.collidepoint(mouse_pos)
            is_active = (btn["label"] == self.active_tab)
            col = C_IGT_TXT_SEL if is_active else (C_BTN_FACE if not hover else (200, 200, 255))
            pygame.draw.rect(screen, col, r, border_radius=s(6))
            pygame.draw.rect(screen, C_BLACK, r, s(2), border_radius=s(6))
            txt = self.assets.font_ui.render(btn["label"], True, C_BLACK)
            screen.blit(txt, txt.get_rect(center=r.center))

        # Content Area
        content_rect = pygame.Rect(panel_rect.left + s(40), panel_rect.top + s(140), panel_rect.width - s(80), panel_rect.height - s(220))

        if self.active_tab == "LOGS":
            self._draw_logs_tab(screen, content_rect)
        elif not self.stats:
            msg = self.assets.font_ui.render("NO DATA LOADED", True, C_WHITE)
            screen.blit(msg, msg.get_rect(center=content_rect.center))
        elif self.active_tab == "OVERVIEW":
            self._draw_overview(screen, content_rect)
        elif self.active_tab == "STRATEGY":
            self._draw_strategy(screen, content_rect)
        elif self.active_tab == "LUCK":
            self._draw_luck(screen, content_rect)
        elif self.active_tab == "HITS":
            self._draw_hits(screen, content_rect)
        elif self.active_tab == "GRAPHS":
            self._draw_graphs_tab(screen, content_rect)

        # Close Button
        self.btn_close.update(mouse_pos, pygame.mouse.get_pressed()[0])
        self.btn_close.draw(screen, self.assets.font_ui)

    def _draw_overview(self, screen, rect):
        stats = self.stats
        
        v_name = stats.get('variant', 'Unknown')
        t_stamp = stats.get('time', 'Unknown')
        
        header_y = rect.top
        info_str = f"GAME: {v_name}   |   STARTED: {t_stamp}"
        info_surf = self.assets.font_ui.render(info_str, True, C_IGT_GOLD)
        screen.blit(info_surf, info_surf.get_rect(center=(rect.centerx, header_y)))
        
        pygame.draw.line(screen, (80, 80, 80), (rect.left + s(20), header_y + s(30)), (rect.right - s(20), header_y + s(30)), 2)

        col1 = rect.left + s(50)
        col2 = rect.centerx + s(50)
        y = rect.top + s(60) 
        gap = s(50)

        self._draw_metric(screen, "TOTAL HANDS", str(stats['hands']), col1, y, C_WHITE)
        y += gap
        self._draw_metric(screen, "NET PROFIT", f"${stats['net']:.2f}", col1, y, C_DIGITAL_GRN if stats['net'] >= 0 else C_DIGITAL_RED)
        y += gap
        self._draw_metric(screen, "ACTUAL RTP", f"{stats['rtp']:.1f}%", col1, y, C_YEL_TEXT)
        
        y = rect.top + s(60)
        grade_col = C_DIGITAL_GRN if stats['perfect_pct'] > 99 else (C_YEL_TEXT if stats['perfect_pct'] > 95 else C_DIGITAL_RED)
        self._draw_metric(screen, "ACCURACY", f"{stats['perfect_pct']:.2f}%", col2, y, grade_col)
        y += gap
        self._draw_metric(screen, "TOTAL ERRORS", str(stats['errors']), col2, y, C_WHITE)
        y += gap
        self._draw_metric(screen, "COST OF ERRORS", f"-${stats['cost']:.2f}", col2, y, C_DIGITAL_RED)

    def _draw_strategy(self, screen, rect):
        stats = self.stats
        x = rect.left + s(50)
        y = rect.top + s(20)
        gap = s(45) 
        
        screen.blit(self.assets.font_ui.render("LEAK FINDER:", True, C_IGT_GOLD), (x, y))
        y += gap + s(10)
        
        def draw_row(label, data):
            err, tot = data
            rate = (err/tot*100) if tot > 0 else 0.0
            
            col = C_DIGITAL_GRN
            if rate > 0: col = (255, 200, 0)
            if rate > 2: col = C_DIGITAL_RED
            if tot == 0: col = (100, 100, 100) 
            
            txt_str = f"{label}: {err} Errors / {tot} ({rate:.1f}%)"
            screen.blit(self.assets.font_log.render(txt_str, True, col), (x, non_local_y[0]))
            non_local_y[0] += gap

        non_local_y = [y]
        
        draw_row("1-DEUCE HANDS", stats.get('err_1d', (0,0)))
        draw_row("PAIR HANDS (0 Deuces)", stats.get('err_pair', (0,0)))
        draw_row("FLUSH TRAPS (4-Suited)", stats.get('err_flush', (0,0)))
        draw_row("ROYAL TEASES (3-Royal)", stats.get('err_3royal', (0,0)))

    def _draw_luck(self, screen, rect):
        stats = self.stats
        x = rect.left + s(50)
        y = rect.top + s(20)
        gap = s(60)
        
        expected_net_win = stats['net'] - stats['luck']
        
        self._draw_metric(screen, "EXPECTED WIN", f"${expected_net_win:.2f}", x, y, C_CYAN_MSG)
        y += gap
        self._draw_metric(screen, "ACTUAL WIN", f"${stats['net']:.2f}", x, y, C_WHITE)
        y += gap
        
        luck = stats['luck']
        lbl = "GOOD LUCK" if luck > 0 else "BAD LUCK"
        col = C_DIGITAL_GRN if luck > 0 else C_DIGITAL_RED
        self._draw_metric(screen, "LUCK FACTOR", f"{lbl} (${luck:.2f})", x, y, col)

    def _draw_hits(self, screen, rect):
        headers = ["HAND", "COUNT", "ACTUAL", "THEO", "DIFF"]
        x_offsets = [0, 220, 320, 440, 560]
        y = rect.top + s(10)
        
        for i, h in enumerate(headers):
            screen.blit(self.assets.font_tiny.render(h, True, C_IGT_GOLD), (rect.left + s(x_offsets[i]), y))
        y += s(35)
        
        if not self.hit_stats: return

        for row in self.hit_stats:
            col = C_WHITE
            if row['theo_pct'] is not None:
                if row['diff'] > 0.05: col = C_DIGITAL_GRN
                elif row['diff'] < -0.05: col = C_DIGITAL_RED
            
            lbl = self.assets.font_log.render(row['label'], True, C_WHITE)
            cnt = self.assets.font_log.render(str(row['count']), True, C_WHITE)
            act = self.assets.font_log.render(f"{row['actual_pct']:.2f}%", True, col)
            
            theo_str = f"{row['theo_pct']:.2f}%" if row['theo_pct'] is not None else "---"
            theo = self.assets.font_log.render(theo_str, True, C_SILVER)
            
            diff_str = f"{row['diff']:+.2f}%" if row['theo_pct'] is not None else "---"
            diff = self.assets.font_log.render(diff_str, True, col)

            screen.blit(lbl, (rect.left + s(x_offsets[0]), y))
            screen.blit(cnt, (rect.left + s(x_offsets[1]), y))
            screen.blit(act, (rect.left + s(x_offsets[2]), y))
            screen.blit(theo, (rect.left + s(x_offsets[3]), y))
            screen.blit(diff, (rect.left + s(x_offsets[4]), y))
            y += s(28)

    def _draw_graphs_tab(self, screen, rect):
        if not self.session_data:
            msg = self.assets.font_ui.render("NO DATA FOR GRAPH", True, C_WHITE)
            screen.blit(msg, msg.get_rect(center=rect.center))
            return

        # 1. Prepare Data
        history_actual = [0.0]
        history_expected = [0.0]
        cum_act = 0.0
        cum_exp = 0.0
        
        for d in self.session_data:
            bet = d['bet']
            won = d['result']['win']
            ev_gross = d['ev']['user'] * d['denom']
            
            cum_act += (won - bet)
            cum_exp += (ev_gross - bet)
            
            history_actual.append(cum_act)
            history_expected.append(cum_exp)
            
        # 2. Define Layout (Margins for Axis Labels)
        margin_left = s(80) 
        margin_bottom = s(40)
        margin_top = s(60) 
        margin_right = s(20)
        
        graph_rect = pygame.Rect(
            rect.left + margin_left, 
            rect.top + margin_top, 
            rect.width - margin_left - margin_right, 
            rect.height - margin_top - margin_bottom
        )
        
        pygame.draw.rect(screen, (20, 20, 25), graph_rect) 
        pygame.draw.rect(screen, (60, 60, 60), graph_rect, 2) 

        # 3. Calculate Scale & Range
        all_vals = history_actual + history_expected
        min_val = min(all_vals)
        max_val = max(all_vals)
        min_val = min(min_val, 0)
        max_val = max(max_val, 0)
        
        val_range = max_val - min_val
        if val_range == 0: val_range = 10 
        
        padding = val_range * 0.1
        view_min = min_val - padding
        view_max = max_val + padding
        view_h = view_max - view_min
        
        total_points = len(history_actual)
        
        # 4. Grid System (Dynamic Scaling)
        raw_step = view_h / 5 
        magnitude = 10 ** math.floor(math.log10(raw_step)) if raw_step > 0 else 1
        base_step = raw_step / magnitude
        
        if base_step < 2: nice_step = 1 * magnitude
        elif base_step < 5: nice_step = 2 * magnitude
        elif base_step < 10: nice_step = 5 * magnitude
        else: nice_step = 10 * magnitude
        
        start_grid = math.ceil(view_min / nice_step) * nice_step
        current_grid = start_grid
        
        font_axis = self.assets.font_tiny 
        
        while current_grid <= view_max:
            norm_y = (current_grid - view_min) / view_h
            screen_y = graph_rect.bottom - (norm_y * graph_rect.height)
            
            if graph_rect.top <= screen_y <= graph_rect.bottom:
                col = (100, 100, 100) if abs(current_grid) < 0.01 else (40, 40, 50)
                width = 2 if abs(current_grid) < 0.01 else 1
                pygame.draw.line(screen, col, (graph_rect.left, screen_y), (graph_rect.right, screen_y), width)
                
                label_str = f"${int(current_grid)}"
                lbl = font_axis.render(label_str, True, (150, 150, 150))
                screen.blit(lbl, (graph_rect.left - lbl.get_width() - s(8), screen_y - s(6)))
                
            current_grid += nice_step

        # X-Axis Grid
        x_step = max(1, total_points // 5)
        for i in range(0, total_points, x_step):
            screen_x = graph_rect.left + (i / (total_points - 1)) * graph_rect.width
            pygame.draw.line(screen, (40, 40, 50), (screen_x, graph_rect.top), (screen_x, graph_rect.bottom), 1)
            lbl = font_axis.render(str(i), True, (150, 150, 150))
            screen.blit(lbl, (screen_x - (lbl.get_width() // 2), graph_rect.bottom + s(5)))

        # 5. Draw The Data Lines
        step_x = graph_rect.width / (total_points - 1) if total_points > 1 else 0
        
        def to_screen(i, val):
            x = graph_rect.left + (i * step_x)
            norm = (val - view_min) / view_h
            y = graph_rect.bottom - (norm * graph_rect.height)
            return (x, y)

        pts_act = [to_screen(i, v) for i, v in enumerate(history_actual)]
        pts_exp = [to_screen(i, v) for i, v in enumerate(history_expected)]
        
        if len(pts_act) > 1:
            pygame.draw.lines(screen, C_CYAN_MSG, False, pts_exp, 3) 
            pygame.draw.lines(screen, C_DIGITAL_GRN, False, pts_act, 2) 

        # 6. Legend
        legend_y = rect.top + s(10)
        start_x = rect.left + s(20)
        
        pygame.draw.rect(screen, (30, 30, 40), (start_x, legend_y, s(300), s(40)), border_radius=s(5))
        pygame.draw.rect(screen, (60, 60, 60), (start_x, legend_y, s(300), s(40)), 1, border_radius=s(5))
        
        pygame.draw.line(screen, C_CYAN_MSG, (start_x + s(10), legend_y + s(20)), (start_x + s(40), legend_y + s(20)), 3)
        l1 = self.assets.font_tiny.render("EXPECTED", True, C_CYAN_MSG)
        screen.blit(l1, (start_x + s(50), legend_y + s(12)))
        
        pygame.draw.line(screen, C_DIGITAL_GRN, (start_x + s(150), legend_y + s(20)), (start_x + s(180), legend_y + s(20)), 2)
        l2 = self.assets.font_tiny.render("ACTUAL", True, C_DIGITAL_GRN)
        screen.blit(l2, (start_x + s(190), legend_y + s(12)))

    def _draw_logs_tab(self, screen, rect):
        start_y = rect.top
        line_h = s(55) 
        
        if not self.log_files:
            msg = self.assets.font_ui.render("NO LOG FILES FOUND", True, (150, 150, 150))
            screen.blit(msg, msg.get_rect(center=rect.center))
            return

        for i, file_data in enumerate(self.log_files):
            if i > 8: break 
            
            f_name = file_data['name']
            is_empty = file_data['empty']
            y = start_y + (i * line_h)
            
            is_current = (f_name == self.current_filename)
            is_selected = (f_name == self.selected_filename)
            is_active_session = (self.machine.logger.active and f_name == os.path.basename(self.machine.logger.filepath))
            
            if is_selected: row_col = (60, 80, 100)
            elif is_current: row_col = (40, 60, 40)
            else: row_col = (40, 40, 50) if i % 2 == 0 else (30, 30, 40)
            
            pygame.draw.rect(screen, row_col, (rect.left, y, rect.width, line_h))
            
            col = C_WHITE
            if is_empty: col = (120, 120, 120)
            elif is_current: col = C_IGT_TXT_SEL
            
            display_name = f_name
            if is_empty: display_name += " (EMPTY)"
            
            txt = self.assets.font_log.render(display_name, True, col)
            screen.blit(txt, (rect.left + s(20), y + s(15)))
            
            btn_w, btn_h = s(80), s(35)
            btn_y = y + s(10)
            
            load_rect = pygame.Rect(rect.right - s(200), btn_y, btn_w, btn_h)
            if not is_empty:
                pygame.draw.rect(screen, (50, 100, 50), load_rect, border_radius=4)
                pygame.draw.rect(screen, C_WHITE, load_rect, 1, border_radius=4)
                lt = self.assets.font_tiny.render("LOAD", True, C_WHITE)
            else:
                pygame.draw.rect(screen, (60, 60, 60), load_rect, border_radius=4)
                lt = self.assets.font_tiny.render("LOAD", True, (100, 100, 100))
            screen.blit(lt, lt.get_rect(center=load_rect.center))
            
            del_rect = pygame.Rect(rect.right - s(100), btn_y, btn_w, btn_h)
            del_col = (100, 50, 50) if not is_active_session else (60, 60, 60)
            pygame.draw.rect(screen, del_col, del_rect, border_radius=4)
            pygame.draw.rect(screen, (150, 150, 150), del_rect, 1, border_radius=4)
            dt = self.assets.font_tiny.render("DEL", True, (200, 200, 200) if not is_active_session else (100, 100, 100))
            screen.blit(dt, dt.get_rect(center=del_rect.center))

    def _draw_metric(self, screen, label, value, x, y, val_color):
        lbl_surf = self.assets.font_ui.render(label, True, (180, 180, 180))
        val_surf = self.assets.font_vfd.render(value, True, val_color)
        screen.blit(lbl_surf, (x, y))
        screen.blit(val_surf, (x + s(250), y - s(5)))

# ==============================================================================
# 🧠 STRATEGY PANEL (Update)
# ==============================================================================
class StrategyPanel:
    def __init__(self, x, y, w, h, assets, machine):
        self.rect = s_rect(x, y, w, h)
        self.assets = assets
        self.machine = machine
        self.results = [] 
        
        cx = self.rect.centerx
        # Moved UP to avoid bottom edge
        btn_y = self.rect.top + s(720) 
        self.btn_setup = PhysicalButton(
            pygame.Rect(cx - s(100), btn_y, s(200), s(45)), 
            "SESSION SETUP", 
            self.machine.act_open_session_setup
        )
        # Session Stats Button
        self.btn_stats = PhysicalButton(
            pygame.Rect(cx - s(100), btn_y + s(55), s(200), s(45)), 
            "SESSION STATS", 
            self.machine.act_open_stats
            # Default Color (Grey) matches Setup Button
        )

    def set_results(self, results):
        self.results = results

    def reset(self):
        self.results = []

    def draw(self, screen):
        pygame.draw.rect(screen, (30, 35, 40), self.rect)
        pygame.draw.line(screen, (100,100,100), (self.rect.right,0), (self.rect.right, PHYSICAL_H), 2)

        mouse_pos = pygame.mouse.get_pos(); mouse_down = pygame.mouse.get_pressed()[0]
        self.btn_setup.update(mouse_pos, mouse_down)
        self.btn_setup.draw(screen, self.assets.font_ui)
        
        self.btn_stats.update(mouse_pos, mouse_down)
        self.btn_stats.draw(screen, self.assets.font_ui)

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
        
        # --- LOGGING TOGGLE (Top Right of Setup) ---
        state_txt = "ON" if self.machine.logging_enabled else "OFF"
        state_col = C_DIGITAL_GRN if self.machine.logging_enabled else C_DIGITAL_RED
        self.btn_log = PhysicalButton(
            s_rect(1420, 20, 150, 50), f"LOGGING: {state_txt}", self._toggle_log, color=state_col
        )

    def _toggle_log(self):
        # Toggle functionality
        if self.machine.logging_enabled:
            # Turn OFF
            self.machine.logging_enabled = False
            self.machine.logger.close_session()
            self.btn_log.text = "LOGGING: OFF"
            self.btn_log.color = C_DIGITAL_RED
        else:
            # Turn ON
            self.machine.logging_enabled = True
            self.machine.logger.start_session(self.machine.sim.variant)
            self.btn_log.text = "LOGGING: ON"
            self.btn_log.color = C_DIGITAL_GRN
        
        self.machine.sound.play("bet")

    def _adj_bank(self, amt): self.temp_bank = max(0, self.temp_bank + amt)
    def _set_bank(self, val): self.temp_bank = val
    def _set_denom(self, val): self.temp_denom = val
    def _set_floor(self, val): self.temp_floor_pct = val
    def _set_ceil(self, val): self.temp_ceil_pct = val
    
    def _confirm(self):
        self.machine.start_bankroll = self.temp_bank; self.machine.bankroll = self.temp_bank
        self.machine.denom = self.temp_denom; self.machine.floor_pct = self.temp_floor_pct; self.machine.ceil_pct = self.temp_ceil_pct
        self.machine.update_machine_limits(); self.machine.graph_panel.reset(self.temp_bank)
        
        # --- FIXED: Reset Cashed Out flag so button can work next time ---
        self.machine.cashed_out = False
        
        self.machine.state = "IDLE"; self.machine.sound.play("rollup")

    def _new_session(self):
        self.machine.start_new_session()
        self.machine.state = "SESSION_SETUP" # KEEP USER ON SETUP SCREEN
        self.temp_bank = self.machine.start_bankroll; self.temp_denom = self.machine.denom
        self.temp_floor_pct = self.machine.floor_pct; self.temp_ceil_pct = self.machine.ceil_pct
        self.machine.sound.play("deal")

    def handle_click(self, pos):
        # Check Logging Toggle first (it's physically outside the main loop of buttons)
        if self.btn_log.rect.collidepoint(pos):
            self.btn_log.callback()
            return

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
        
        # Draw Standard Buttons
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
            
        # Draw Logging Toggle (using update/draw pattern)
        self.btn_log.update(mouse_pos, pygame.mouse.get_pressed()[0])
        self.btn_log.draw(screen, self.assets.font_ui)

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

    def add_entry(self, hand_num, deal_cards, final_cards, held_indices, ev_data, result_data, bet_amount, denom, variant):
        entry = {
            'id': hand_num, 'deal': deal_cards, 'final': final_cards, 'held_idx': held_indices, 
            'ev': ev_data, 'result': result_data, 'bet': bet_amount,
            'denom': denom, 'variant': variant
        }
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
        font = self.assets.font_log_bold; char_w = s(35)
        for i, card in enumerate(cards):
            current_x = x + (i * char_w)
            if highlights and i in highlights:
                pygame.draw.rect(screen, C_NB_HIGHLIGHT, (current_x - s(2), y, char_w - s(2), s(20)))
            
            rank = card[0]; suit_char = card[1]
            color = C_NB_RED if suit_char in 'hd' else C_NB_BLACK
            
            # USE SAFE SYMBOL LOOKUP
            suit_sym = self.assets.get_symbol(suit_char)
            text = f"{rank}{suit_sym}"
            
            screen.blit(font.render(text, True, color), (current_x, y))

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
            
            # --- Rank Label ---
            raw_rank = log['result']['rank']
            disp_rank = RANK_DISPLAY_MAP.get(raw_rank, raw_rank.replace('_', ' ')) 
            if len(disp_rank) > 16: disp_rank = disp_rank[:14] + ".."
            screen.blit(self.assets.font_log_bold.render(disp_rank, True, C_NB_BLACK), (self.rect.left + s(70), y))
            
            # --- Financials (Right Align + Logic) ---
            win_val = log['result']['win']
            bet_val = log['bet']
            diff = win_val - bet_val
            
            if diff > 0.001:
                # WIN (Green)
                fin_color = (0, 180, 0)
                fin_txt = f"${win_val:.2f}"
            elif abs(diff) < 0.001:
                # PUSH (Grey)
                fin_color = C_PUSH_GREY 
                fin_txt = f"${win_val:.2f}"
            else:
                # LOSS (Red) -> Show Cost
                fin_color = C_RED_ACTIVE
                fin_txt = f"${bet_val:.2f}"
            
            fin_surf = self.assets.font_log_bold.render(fin_txt, True, fin_color)
            x_draw = self.rect.right - s(20) - fin_surf.get_width()
            screen.blit(fin_surf, (x_draw, y))
            
            screen.blit(self.assets.font_log.render("Deal:", True, C_NB_TEXT), (self.rect.left + s(15), y + s(25)))
            self.draw_cards_text(screen, log['deal'], self.rect.left + s(70), y + s(25), highlights=log['held_idx'])
            screen.blit(self.assets.font_log.render("Final:", True, C_NB_TEXT), (self.rect.left + s(15), y + s(50)))
            self.draw_cards_text(screen, log['final'], self.rect.left + s(70), y + s(50), highlights=log['held_idx'])
            
            user_ev = log['ev']['user']; max_ev = log['ev']['max']; diff_ev = max_ev - user_ev
            
            if diff_ev < 0.01: dec = f"Optimal ({user_ev:.2f})"; col = (0, 120, 0)
            elif diff_ev < 0.05: dec = f"Alternate (-{diff_ev:.2f} EV)"; col = (200, 140, 0)
            else: dec = f"Error: -{diff_ev:.2f} EV (Max: {max_ev:.2f})"; col = C_NB_RED
            
            screen.blit(self.assets.font_log.render(dec, True, col), (self.rect.left + s(15), y + s(75)))

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
             
        pygame.display.set_caption("EV Navigator - Universal (v20)")
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
        
        # --- FIXED: ADD CASHED OUT STATE ---
        self.cashed_out = False 
        
        # --- LOGGING ---
        self.logger = SessionLogger()
        self.logging_enabled = True # DEFAULT ON
        self.logger.start_session(self.sim.variant)
        
        # SCALED LAYOUT INITS
        self.log_panel = LogPanel(1240, 20, 340, 500, self.assets)
        self.graph_panel = GraphPanel(1240, 530, 340, 300, self.assets.font_tiny)
        self.strategy_panel = StrategyPanel(0, 0, 240, 850, self.assets, self)
        
        # Overlay Screens (Full Scaled Rect)
        full_overlay = s_rect(240, 0, 1360, 850)
        self.codex_screen = CodexScreen(full_overlay, self.assets, self)
        self.game_selector = GameSelectorScreen(full_overlay, self.assets, self, self.available_variants)
        self.session_setup = SessionSetupScreen(full_overlay, self.assets, self)
        
        # NEW: Session Stats
        self.stats_screen = SessionStatsScreen(full_overlay, self.assets, self)
        
        start_x = 360
        self.cards = [CardSlot(start_x + (i * 152), 410, self.assets) for i in range(5)]
        
        self.auto_hold_active = False; self.auto_play_active = False; self.last_action_time = 0; self.advice_msg = None
        self.hands_played = 0; self._init_buttons(); self._init_meters(); self.vol_btn = VolumeButton(1192, 785, self.sound)
        self.update_machine_limits()
        
        # NEW: Denom Rect for Clicking
        self.denom_rect = pygame.Rect(s(910) + X_OFFSET - s(40), s(680) + Y_OFFSET + s(30) - s(25), s(80), s(50))

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
        
        # NEW: Cash Out Button (Hidden by default)
        self.btn_cash_out = PhysicalButton(s_rect(1127, 700, 100, 40), "CASH OUT", self.act_cash_out, color=C_DIGITAL_GRN)

    def _init_meters(self):
        self.meter_win = ClickableMeter(400, 680, "WIN", C_DIGITAL_RED)
        self.meter_bet = ClickableMeter(740, 680, "BET", C_DIGITAL_YEL)
        self.meter_credit = ClickableMeter(1080, 680, "CREDIT", C_DIGITAL_RED, default_is_credits=False)
        self.meters = [self.meter_win, self.meter_bet, self.meter_credit]

    @property
    def is_limit_reached(self):
        hit_floor = (self.floor_val > 0 and self.bankroll <= self.floor_val)
        hit_ceil = (self.ceil_val > 0 and self.bankroll >= self.ceil_val)
        return hit_floor or hit_ceil

    def act_cash_out(self):
        self.sound.play("voucher", maxtime=5000)
        self.bankroll = 0.00
        self.win_display = 0.00
        self.advice_msg = "CASHED OUT: $0.00"
        self.cashed_out = True

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

        # --- FIX: Auto Play implies Auto Hold ---
        if self.auto_hold_active or self.auto_play_active:
            self.held_indices = []
            for i, card in enumerate(self.hand):
                if card in best_cards: 
                    self.cards[i].is_held = True; self.held_indices.append(i)
            if len(results) > 1:
                second_cards = results[1]['held']
                for i, card in enumerate(self.hand):
                    if card in second_cards: self.cards[i].is_runner_up = True
            self.advice_msg = None if best_cards else "ADVICE: DRAW ALL"
            if not self.auto_play_active: self.sound.play("bet")
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
    def act_open_stats(self):
        # Pause Auto-Play
        if self.auto_play_active: self.act_toggle_auto_play()
        
        if self.state == "IDLE":
            self.state = "STATS"
            # Auto-Load logic
            if self.hands_played > 0:
                self.stats_screen.load_active_session()
            else:
                self.stats_screen._scan_logs()
                self.stats_screen.active_tab = "LOGS"
            self.sound.play("bet")

    def act_select_game(self, new_variant):
        self.sim = dw_sim_engine.DeucesWildSim(variant=new_variant)
        self.core = self.sim.core
        self.paytable = PaytableDisplay(self.assets, self.sim.paytable)
        self.graph_panel.reset(self.bankroll)
        self.sound.play("bet")
        pygame.display.set_caption(f"IGT Game King Replica ({new_variant})")
        self.state = "IDLE"
        
        # New Log for new game
        self.logger.close_session()
        if self.logging_enabled:
            self.logger.start_session(new_variant)

    def act_bet_one(self):
        if self.state != "IDLE": return
        self.coins_bet = 1 if self.coins_bet >= 5 else self.coins_bet + 1
        self.sound.play("bet")
    def act_bet_max(self):
        if self.state != "IDLE": return
        self.coins_bet = 5; self.sound.play("bet"); self.act_deal_draw()
    def act_deal_draw(self):
        if self.state == "IDLE":
            # --- FIXED: PREVENT DEALING IF CASHED OUT ---
            if self.cashed_out:
                self.advice_msg = "PLEASE RESET BANKROLL"
                return

            if self.floor_val > 0 and self.bankroll <= self.floor_val: 
                self.auto_play_active = False; self.advice_msg = "FLOOR HIT: CASH OUT?"; self.act_toggle_auto_play()
                if self.auto_play_active: return 
            if self.ceil_val > 0 and self.bankroll >= self.ceil_val: 
                self.auto_play_active = False; self.advice_msg = "CEILING HIT: CASH OUT!"; self.act_toggle_auto_play()
                if self.auto_play_active: return

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
            
            # --- DATA COLLECTION PACKET ---
            data_packet = {
                'id': self.hands_played, 'variant': self.sim.variant,
                'bank_start': self.bankroll - win_val + bet_val, # Reconstruct start bank
                'denom': self.denom, 'coins': self.coins_bet, 'cost': bet_val,
                'deal': self.deal_snapshot, 'final': list(self.hand),
                'held_idx': logged_held_indices, 
                'auto_hold': self.auto_hold_active or self.auto_play_active,
                'rank': rank, 'win': win_val,
                'ev_user': user_ev_disp, 'ev_max': max_ev_disp
            }
            
            self.log_panel.add_entry(
                self.hands_played, self.deal_snapshot, list(self.hand), logged_held_indices, 
                {'user': user_ev_disp, 'max': max_ev_disp}, {'win': win_val, 'rank': rank}, bet_val,
                self.denom, self.sim.variant
            )
            
            # --- SEND TO DISK ---
            if self.logging_enabled:
                self.logger.log_hand(data_packet)
                
            self.graph_panel.add_point(self.bankroll)
            self.state = "IDLE"; self.btn_deal.text = "DEAL"

    def handle_click(self, pos):
        if self.state == "IDLE":
             # Strategy Panel Buttons
             if self.strategy_panel.btn_setup.rect.collidepoint(pos): self.strategy_panel.btn_setup.callback(); self.sound.play("bet"); return
             if self.strategy_panel.btn_stats.rect.collidepoint(pos): self.strategy_panel.btn_stats.callback(); return
             
             # NEW: Denom Click -> Setup
             if self.denom_rect.collidepoint(pos): self.act_open_session_setup(); return

        if self.state == "GAME_SELECT": self.game_selector.handle_click(pos); return
        if self.state == "SESSION_SETUP": self.session_setup.handle_click(pos); return
        if self.state == "CODEX": self.codex_screen.handle_click(pos); return
        if self.state == "STATS": self.stats_screen.handle_click(pos); return
        
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
        
        # Check Cash Out (Only if Limit Reached AND Not Cashed Out)
        if self.is_limit_reached and not self.cashed_out and self.btn_cash_out.rect.collidepoint(pos):
            self.btn_cash_out.callback()
            return

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
        
        # Denom Circle (Clickable Area Visual)
        cx, cy = s(910) + X_OFFSET, s(680) + Y_OFFSET + s(30); rect = pygame.Rect(cx-s(40), cy-s(25), s(80), s(50))
        pygame.draw.ellipse(self.screen, (255, 215, 0), rect); pygame.draw.ellipse(self.screen, C_BLACK, rect, s(2))
        txt_str = f"${int(self.denom)}" if self.denom >= 1.0 else f"{int(self.denom*100)}¢"
        txt = self.assets.font_vfd.render(txt_str, True, C_RED_ACTIVE)
        self.screen.blit(txt, txt.get_rect(center=rect.center))
        
        mouse_pos = pygame.mouse.get_pos(); mouse_down = pygame.mouse.get_pressed()[0]
        
        # Draw Standard Buttons
        for b in self.buttons: b.update(mouse_pos, mouse_down); b.draw(self.screen, self.assets.font_ui)
        
        # Draw Cash Out Button (Only if Limit Reached AND Not Cashed Out)
        if self.is_limit_reached and not self.cashed_out:
            self.btn_cash_out.update(mouse_pos, mouse_down)
            self.btn_cash_out.draw(self.screen, self.assets.font_ui)

    def draw(self):
        self.screen.fill(C_BLACK)
        self.strategy_panel.draw(self.screen)
        self.log_panel.draw(self.screen)
        self.graph_panel.draw(self.screen)
        if self.state == "GAME_SELECT": self.game_selector.draw(self.screen)
        elif self.state == "SESSION_SETUP": self.session_setup.draw(self.screen)
        elif self.state == "CODEX": self._draw_main_game_elements(); self.codex_screen.draw(self.screen)
        elif self.state == "STATS": self.stats_screen.draw(self.screen)
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
        # Logging reset handled in select_game called above or we explicitly restart it?
        # act_select_game handles logger restart.

if __name__ == "__main__":
    app = IGT_Machine()
    app.run()