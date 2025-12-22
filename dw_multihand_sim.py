import sys
import random
import copy
import os
import csv
import datetime
from collections import Counter, deque
from dw_sim_engine import DeucesWildSim
# NEW: Import Registry for Dynamic Menu
from dw_pay_constants import PAYTABLES 

# ---------------------------------------------------------
# 📊 OPTIONAL MODULES (EV Solver & Plot Tools)
# ---------------------------------------------------------
try:
    import dw_exact_solver
    EV_AVAILABLE = True
except ImportError:
    EV_AVAILABLE = False

try:
    # 🌟 Integration with "Mission Control" Plotter
    from dw_plot_tools import generate_mission_control_plot
    PLOT_TOOLS_AVAILABLE = True
except ImportError:
    PLOT_TOOLS_AVAILABLE = False
    print("⚠️ Warning: 'dw_plot_tools.py' not found. Visualization disabled.")

# ==========================================
# 🧬 CONFIGURATION & DEFAULTS
# ==========================================
DEFAULT_LINES = 5
DEFAULT_VARIANT = "NSUD" 
DEFAULT_START_BANKROLL = 40.00
DEFAULT_FLOOR = 70.00   # 🛡️ THE DOOM SLOPE HARD DECK
DEFAULT_CEILING = 120.00
LOGGING_ENABLED = True

# --- AMY BOT DEFAULTS ---
AMY_MODE_DEFAULT = False
AMY_LADDER_DEFAULT = [0.05, 0.10, 0.25] 

# --- PROTOCOL DEFAULTS ---
PROTOCOL_MODE_DEFAULT = True 

class ProtocolGuardian:
    """
    🛡️ THE AIRPORT PROTOCOL ENFORCER
    Monitors the session in real-time and triggers stops.
    """
    def __init__(self, start_bankroll):
        self.start = start_bankroll
        self.spike_hand_idx = -1
        self.triggered = False
        self.trigger_reason = None
        
    def check(self, hands_played, current_bankroll):
        if self.triggered: return self.trigger_reason
        
        # 1. SNIPER EXCEPTION (Win Limit: +20%)
        if current_bankroll >= (self.start * 1.20):
            self.triggered = True
            self.trigger_reason = "SNIPER_WIN"
            return "SNIPER_WIN"

        # 2. VACUUM CHECK (First 15 Hands: -25%)
        if hands_played <= 15 and current_bankroll <= (self.start * 0.75):
            self.triggered = True
            self.trigger_reason = "VACUUM_STOP"
            return "VACUUM_STOP"

        # 3. THE TEASE (Sub-Surface Check)
        if current_bankroll > self.start:
            self.spike_hand_idx = hands_played
            
        if self.spike_hand_idx != -1: # We surfaced once
            if current_bankroll < self.start: # Now underwater
                if (hands_played - self.spike_hand_idx) <= 5:
                    self.triggered = True
                    self.trigger_reason = "TEASE_EXIT"
                    return "TEASE_EXIT"

        # 4. ZOMBIE THRESHOLD (Hand 40)
        if hands_played == 40 and current_bankroll < self.start:
            self.triggered = True
            self.trigger_reason = "ZOMBIE_LIMIT"
            return "ZOMBIE_LIMIT"

        # 5. HARD DECK (Hand 66)
        if hands_played >= 66:
            self.triggered = True
            self.trigger_reason = "HARD_DECK"
            return "HARD_DECK"
            
        return None

def run_multihand_session(hand_str, num_lines, variant, denom, wheel_active=False):
    """
    Runs a single hand across N lines.
    UPDATED: Uses Certified Class III Core for dealing/drawing.
    """
    # Instantiate the new Engine Wrapper
    sim = DeucesWildSim(variant=variant, denom=denom)
    
    # 1. Parse Hand (Delegated to Core)
    hand = sim.normalize_input(hand_str)
    if len(hand) != 5:
        print(f"❌ Error: Invalid Hand ({hand_str})")
        return 0.0, {}

    # 2. Strategy & EV Calculation
    held_cards = sim.pro_strategy(hand)
    
    # Format Action String
    if len(held_cards) == 5: 
        action_display = "Held All"
        held_display = " ".join(held_cards)
    elif len(held_cards) == 0: 
        action_display = "Redraw"
        held_display = ""
    else: 
        action_display = "Hold"
        held_display = " ".join(held_cards)
    
    # Calculate Truth EV if available
    ev_val = 0.0
    if EV_AVAILABLE:
        try:
            hold_indices = [i for i, c in enumerate(hand) if c in held_cards]
            pt = dw_exact_solver.PAYTABLES[variant]
            ev_val = dw_exact_solver.calculate_exact_ev(hand, hold_indices, pt)
        except Exception:
            pass

    # --- 🎡 WHEEL MECHANIC ---
    wheel_mult = 1
    w1 = 1 
    w2 = 1 
    wheel_str = ""
    
    if wheel_active:
        # Use the DoubleWheel class inside sim if available
        if hasattr(sim, 'wheel') and sim.wheel:
            wheel_mult, w1, w2 = sim.wheel.spin()
        else:
            wheel_mult = 1
            
        if wheel_mult > 1:
            wheel_str = f" ({w1}x{w2}={wheel_mult}x) 🔥"

    # 3. PHYSICS & DRAW (The Update)
    full_deck = sim.core.get_fresh_deck()
    dealt_set = set(hand)
    
    # Validation: Ensure input cards are valid deck cards
    if not dealt_set.issubset(set(full_deck)):
        print("❌ Error: Hand contains invalid cards.")
        return 0.0, {}

    stub = [c for c in full_deck if c not in dealt_set]
    
    # 4. EXECUTE DRAW (Certified Core)
    final_hands = sim.core.draw_from_stub(held_cards, stub, num_lines=num_lines)
    
    # 5. SCORING
    results = []
    total_winnings = 0.0
    
    # Cost Logic
    base_bet_per_line = sim.bet_amount
    actual_cost_per_line = base_bet_per_line * 2 if wheel_active else base_bet_per_line
    total_bet = actual_cost_per_line * num_lines
    
    lines_won = 0 
    
    for final_hand in final_hands:
        # Use new scoring method
        rank_name, base_payout_mult = sim.evaluate_hand_score(final_hand)
        
        if base_payout_mult > 0:
            lines_won += 1
            
        line_win = (base_payout_mult * base_bet_per_line) * wheel_mult
        total_winnings += line_win
        
        results.append(rank_name)

    # 6. Result
    net_result = total_winnings - total_bet
    
    # Concise Hits Report
    counts = Counter(results)
    top_hits = []
    interests = ["NATURAL_ROYAL", "FOUR_DEUCES", "WILD_ROYAL", "FIVE_OAK", "STRAIGHT_FLUSH", "FOUR_OAK", "FULL_HOUSE", "FLUSH"]
    # Map back to readable names if needed, or use Core names directly.
    
    hit_summary_list = []
    for hit_type in interests:
        if counts[hit_type] > 0:
            readable = hit_type.replace('_', ' ').title()
            top_hits.append(f"{readable}({counts[hit_type]})")
            hit_summary_list.append(readable)
    
    hit_str = ", ".join(top_hits) if top_hits else "No Jackpots"
    primary_hit = hit_summary_list[0] if hit_summary_list else "None"
    
    # 7. Build Log Data Dictionary
    log_data = {
        "Variant": variant,
        "Wheel_Mode": str(wheel_active),
        "Denom": denom,
        "Lines": num_lines,
        "Hand_Dealt": " ".join(hand),
        "Held_Cards": held_display,
        "Action": action_display,
        "EV": round(ev_val, 4),
        "Wheel_Mult": wheel_mult,
        "Wheel_Outer": w1,
        "Wheel_Inner": w2,
        "Net_Result": round(net_result, 2),
        "Wins": lines_won,
        "Hit_Summary": hit_str + wheel_str,
        "Best_Hit": primary_hit
    }
    
    return net_result, log_data

def generate_random_hand_str(sim_engine):
    """Generates a random 5-card hand string using the Core."""
    hand, _ = sim_engine.core.deal_hand()
    return " ".join(hand)

def setup_logger(variant, amy_active, protocol_active, session_idx=None):
    """
    Initializes CSV logging with Batch support and Telemetry.
    """
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_tag = "_AMY" if amy_active else ""
    proto_tag = "_PROTO" if protocol_active else ""
    session_tag = f"_S{session_idx}" if session_idx is not None else ""
    filename = f"logs/session_{variant}{mode_tag}{proto_tag}{session_tag}_{timestamp}.csv"
    
    fieldnames = [
        "Hand_ID", "Variant", "Wheel_Mode", "Lines", "Denom", "Bankroll", 
        "Net_Result", "EV", "Wheel_Mult", "Wheel_Outer", "Wheel_Inner",
        "Hand_Dealt", "Held_Cards", "Action", "Wins", "Best_Hit", "Hit_Summary",
        "Amy_Win_Count", "Amy_Trigger", "Protocol_Trigger" 
    ]
    
    f = open(filename, 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    if session_idx is None or session_idx % 10 == 0:
        print(f"   📝 Log Started: {filename}")
        
    return f, writer, filename

# ==========================================
# 🎮 INTERACTIVE MAIN LOOP
# ==========================================

if __name__ == "__main__":
    print("==========================================")
    print("🧬 MULTI-HAND SIMULATOR (v6.1 - DYNAMIC)")
    print("==========================================")
    
    # Session State
    variant = DEFAULT_VARIANT
    lines = DEFAULT_LINES
    wheel_active = True if variant == "DBW" else False
    denom_default = AMY_LADDER_DEFAULT[0] 
    start_bank = DEFAULT_START_BANKROLL
    floor = DEFAULT_FLOOR
    ceiling = DEFAULT_CEILING
    logging_on = LOGGING_ENABLED
    
    # Bot States
    amy_mode = AMY_MODE_DEFAULT
    protocol_mode = PROTOCOL_MODE_DEFAULT
    amy_ladder = AMY_LADDER_DEFAULT[:]
    
    current_bankroll = start_bank
    denom = denom_default
    
    # Used for generating random hands in the loop
    dealer_sim = DeucesWildSim()
    
    while True:
        log_status = "ON" if logging_on else "OFF"
        amy_status = "ON" if amy_mode else "OFF"
        proto_status = "ON" if protocol_mode else "OFF"
        wh_status = "ON (10 Coins)" if wheel_active else "OFF (5 Coins)"
        plot_status = "READY" if PLOT_TOOLS_AVAILABLE else "MISSING"
        
        print(f"\n[Wallet Config: Start ${start_bank:.2f} | Floor ${floor:.2f} | Ceiling ${ceiling:.2f}]")
        print(f"[Game Config: {lines} Lines | {variant} | Wheel: {wh_status} | Base Denom ${denom_default:.2f}]")
        print(f"[Bots: Amy={amy_status} | Protocol={proto_status}] Plot Tools: {plot_status}")
        print("Options: (R)andom Batch | (E)nter Hand | (W)heel Toggle | (P)rotocol | (S)ettings | (A)my | (Q)uit")
        choice = input(">> ").strip().upper()
        
        if choice == 'Q':
            break

        elif choice == 'A':
            amy_mode = not amy_mode
            print(f"🤖 AMY MODE: {amy_mode}")

        elif choice == 'P':
            protocol_mode = not protocol_mode
            print(f"🛡️ PROTOCOL GUARD: {protocol_mode}")
            
        elif choice == 'W':
            wheel_active = not wheel_active
            print(f"🎡 Wheel Feature is now: {'ENABLED' if wheel_active else 'DISABLED'}")

        elif choice == 'S':
            print("\n--- SETTINGS ---")
            print("1. Set Lines")
            print(f"2. Set Base Denom (Curr: ${denom_default:.2f})")
            print("3. Switch Variant") # <--- DYNAMIC MENU OPTION
            print(f"4. Set Bankroll (Curr: ${start_bank:.2f})")
            print(f"5. Set Floor (Curr: ${floor:.2f})")
            print(f"6. Set Ceiling (Curr: ${ceiling:.2f})")
            print(f"7. Toggle Logging (Current: {log_status})")
            print(f"8. Set Amy Ladder (Curr: {amy_ladder})")
            
            sub = input("Select: ").strip()
            
            if sub == '1':
                try: lines = int(input(f"Lines (Curr: {lines}): "))
                except: pass
            elif sub == '2':
                try: 
                    denom_default = float(input(f"Denom (Curr: ${denom_default:.2f}): $"))
                except: pass
            elif sub == '3':
                # 🌟 DYNAMIC MENU: Reads from PAYTABLES 🌟
                available = list(PAYTABLES.keys())
                print("\nAvailable Variants:")
                for i, k in enumerate(available, 1):
                    print(f"{i}. {k}")
                try:
                    v_idx = int(input("Select Number: ")) - 1
                    if 0 <= v_idx < len(available):
                        variant = available[v_idx]
                        print(f"✅ Switched to {variant}")
                except: print("❌ Invalid Selection")

            elif sub == '4':
                try: start_bank = float(input(f"Start Bank (Curr: ${start_bank:.2f}): $"))
                except: pass
            elif sub == '5':
                try: floor = float(input(f"Floor (Curr: ${floor:.2f}): $"))
                except: pass
            elif sub == '6':
                try: ceiling = float(input(f"Ceiling (Curr: ${ceiling:.2f}): $"))
                except: pass
            elif sub == '7':
                logging_on = not logging_on
            elif sub == '8':
                try:
                    val = input("Enter 3 denoms (e.g. 0.05, 0.10, 0.25): ")
                    parts = [float(x.strip()) for x in val.split(',')]
                    if len(parts) == 3:
                        amy_ladder = parts
                        denom_default = amy_ladder[0] 
                        print(f"✅ Amy Ladder set to: {amy_ladder}")
                    else:
                        print("❌ Error: Must provide exactly 3 values.")
                except:
                    print("❌ Error: Invalid format.")

        elif choice == 'E':
            raw_hand = input("\nEnter Hand: ")
            if raw_hand.strip():
                net, _ = run_multihand_session(raw_hand, lines, variant, denom_default, wheel_active)
                print(f"   💵 Result: ${net:+.2f}")

        elif choice == 'R':
            # BATCH SESSION LOGIC
            print(f"\n🎲 BATCH SESSION CONFIGURATION")
            try:
                batch_count = int(input("Number of Sessions to Run [1]: ") or 1)
            except: batch_count = 1
            
            print(f"🚀 Launching {batch_count} sessions...")
            print("-" * 60)
            
            sessions_won = 0
            sessions_lost = 0
            total_hands_across_batch = 0
            protocol_stops = Counter()
            
            # --- BATCH LOOP ---
            for session_idx in range(1, batch_count + 1):
                # 1. Reset State
                current_bankroll = start_bank
                denom = denom_default
                win_history = deque(maxlen=10)
                hands_played = 0
                
                # PROTOCOL INIT
                guardian = ProtocolGuardian(start_bank) if protocol_mode else None
                
                # 2. Setup Logger
                log_file = None
                writer = None
                log_filename = None
                if logging_on:
                    log_file, writer, log_filename = setup_logger(variant, amy_mode, protocol_mode, session_idx)
                
                try:
                    stop_reason = "Running"
                    
                    # --- SESSION LOOP ---
                    while current_bankroll > floor and current_bankroll < ceiling:
                        
                        # Amy Logic (Simplified)
                        amy_note = ""
                        window_debug = ""
                        
                        if amy_mode and len(amy_ladder) >= 3:
                            try: level_idx = amy_ladder.index(denom)
                            except: level_idx = 0; denom = amy_ladder[0]
                            
                            window_size = 10 if level_idx == 0 else (5 if level_idx == 1 else 3)
                            
                            if len(win_history) >= window_size:
                                recent_wins = list(win_history)[-window_size:]
                                win_sum = sum(recent_wins)
                                ratio = win_sum / (lines * window_size)
                                window_debug = f"[{win_sum}/{lines*window_size}]"
                                
                                liquidity = current_bankroll - floor
                                cost_at_10 = amy_ladder[1] * 5 * lines
                                cost_at_25 = amy_ladder[2] * 5 * lines
                                
                                if level_idx == 0:
                                    if ratio >= 0.5 and liquidity >= (cost_at_10 * 10):
                                        denom = amy_ladder[1]; amy_note = "UP_10"
                                        win_history.clear()
                                elif level_idx == 1:
                                    if ratio >= 0.5 and liquidity >= (cost_at_25 * 10):
                                        denom = amy_ladder[2]; amy_note = "UP_25"
                                        win_history.clear()
                                    elif ratio < 0.5:
                                        denom = amy_ladder[0]; amy_note = "DOWN_05"
                                        win_history.clear()
                                elif level_idx >= 2:
                                    if ratio <= 0.5:
                                        denom = amy_ladder[0]; amy_note = "DOWN_05"
                                        win_history.clear()
                        
                        # Run Hand
                        random_hand = generate_random_hand_str(dealer_sim)
                        net, log_data = run_multihand_session(random_hand, lines, variant, denom, wheel_active)
                        current_bankroll += net
                        hands_played += 1
                        
                        wins_this_hand = log_data["Wins"]
                        win_history.append(wins_this_hand)
                        
                        # --- PROTOCOL CHECK ---
                        proto_trigger = ""
                        if protocol_mode and guardian:
                            res = guardian.check(hands_played, current_bankroll)
                            if res:
                                proto_trigger = res
                                stop_reason = f"PROTOCOL ({res})"
                                
                                # Log final hand then break
                                log_data["Protocol_Trigger"] = res
                                log_data["Hand_ID"] = hands_played
                                log_data["Bankroll"] = round(current_bankroll, 2)
                                log_data["Amy_Win_Count"] = window_debug
                                log_data["Amy_Trigger"] = amy_note
                                if writer: writer.writerow(log_data)
                                break
                        
                        if writer:
                            log_data["Protocol_Trigger"] = proto_trigger
                            log_data["Hand_ID"] = hands_played
                            log_data["Bankroll"] = round(current_bankroll, 2)
                            log_data["Amy_Win_Count"] = window_debug
                            log_data["Amy_Trigger"] = amy_note
                            writer.writerow(log_data)
                            
                        if current_bankroll <= floor: stop_reason = "BUST (Floor)"
                        if current_bankroll >= ceiling: stop_reason = "WIN (Ceiling)"
                    
                    # --- END OF SESSION ---
                    total_hands_across_batch += hands_played
                    
                    if "WIN" in stop_reason or "SNIPER" in stop_reason:
                        result_tag = "WIN"
                        sessions_won += 1
                    else:
                        result_tag = "LOSS"
                        sessions_lost += 1
                    
                    if protocol_mode and guardian and guardian.triggered:
                        protocol_stops[guardian.trigger_reason] += 1
                        
                    print(f"   Session {session_idx}: {result_tag} [{stop_reason}] | Hands: {hands_played} | Final: ${current_bankroll:.2f}")
                
                finally:
                    if log_file: 
                        log_file.close()
                        # 🌟 ALWAYS PLOT (No Limit)
                        if PLOT_TOOLS_AVAILABLE and log_filename:
                            generate_mission_control_plot(log_filename, floor=floor, ceiling=ceiling)

            # --- BATCH REPORT ---
            print("-" * 60)
            print(f"🏁 BATCH COMPLETE")
            print(f"   Sessions: {batch_count}")
            print(f"   Wins: {sessions_won}")
            print(f"   Losses: {sessions_lost}")
            print(f"   Avg Hands per Session: {total_hands_across_batch / batch_count:.1f}")
            if protocol_mode:
                print("   🛡️ PROTOCOL TRIGGERS:")
                for k, v in protocol_stops.items():
                    print(f"      - {k}: {v}")
            print("=" * 60)