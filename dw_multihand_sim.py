import sys
import random
import copy
import os
import csv
import datetime
from collections import Counter, deque
from dw_sim_engine import DeucesWildSim
from dw_pay_constants import PAYTABLES 
from dw_logger import SessionLogger

# ---------------------------------------------------------
# 📊 OPTIONAL MODULES
# ---------------------------------------------------------
try:
    import dw_exact_solver
    EV_AVAILABLE = True
except ImportError:
    EV_AVAILABLE = False

try:
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
DEFAULT_FLOOR = 70.00
DEFAULT_CEILING = 120.00
LOGGING_ENABLED = True

AMY_MODE_DEFAULT = False
AMY_LADDER_DEFAULT = [0.05, 0.10, 0.25] 
PROTOCOL_MODE_DEFAULT = True 

class ProtocolGuardian:
    def __init__(self, start_bankroll):
        self.start = start_bankroll
        self.spike_hand_idx = -1
        self.triggered = False
        self.trigger_reason = None
        
    def check(self, hands_played, current_bankroll):
        if self.triggered: return self.trigger_reason
        if current_bankroll >= (self.start * 1.20):
            self.triggered = True; self.trigger_reason = "SNIPER_WIN"; return "SNIPER_WIN"
        if hands_played <= 15 and current_bankroll <= (self.start * 0.75):
            self.triggered = True; self.trigger_reason = "VACUUM_STOP"; return "VACUUM_STOP"
        if current_bankroll > self.start:
            self.spike_hand_idx = hands_played
        if self.spike_hand_idx != -1: 
            if current_bankroll < self.start:
                if (hands_played - self.spike_hand_idx) <= 5:
                    self.triggered = True; self.trigger_reason = "TEASE_EXIT"; return "TEASE_EXIT"
        if hands_played == 40 and current_bankroll < self.start:
            self.triggered = True; self.trigger_reason = "ZOMBIE_LIMIT"; return "ZOMBIE_LIMIT"
        if hands_played >= 66:
            self.triggered = True; self.trigger_reason = "HARD_DECK"; return "HARD_DECK"
        return None

def run_multihand_session(hand_str, num_lines, variant, denom, wheel_active=False):
    """
    Runs a simulation session (used for Batch Mode).
    """
    sim = DeucesWildSim(variant=variant, denom=denom)
    hand = sim.normalize_input(hand_str)
    if len(hand) != 5: return 0.0, {}

    held_cards = sim.pro_strategy(hand)
    action_display = "Redraw" if len(held_cards) == 0 else ("Held All" if len(held_cards) == 5 else "Hold")
    held_display = " ".join(held_cards)
    
    ev_val = 0.0
    if EV_AVAILABLE:
        try:
            hold_indices = [i for i, c in enumerate(hand) if c in held_cards]
            pt = dw_exact_solver.PAYTABLES[variant]
            ev_val = dw_exact_solver.calculate_exact_ev(hand, hold_indices, pt)
        except: pass

    wheel_mult = 1
    w1 = 1; w2 = 1
    wheel_str = ""
    if wheel_active and hasattr(sim, 'wheel') and sim.wheel:
        wheel_mult, w1, w2 = sim.wheel.spin()
        if wheel_mult > 1: wheel_str = f" ({w1}x{w2}={wheel_mult}x) 🔥"

    full_deck = sim.core.get_fresh_deck()
    dealt_set = set(hand)
    if not dealt_set.issubset(set(full_deck)): return 0.0, {}
    stub = [c for c in full_deck if c not in dealt_set]
    final_hands = sim.core.draw_from_stub(held_cards, stub, num_lines=num_lines)
    
    total_winnings = 0.0
    base_bet = sim.bet_amount
    cost = (base_bet * 2) if wheel_active else base_bet
    total_bet = cost * num_lines
    lines_won = 0
    results = []
    
    for fh in final_hands:
        rank_name, mult = sim.evaluate_hand_score(fh)
        if mult > 0: lines_won += 1
        total_winnings += (mult * base_bet) * wheel_mult
        results.append(rank_name)

    net_result = total_winnings - total_bet
    counts = Counter(results)
    interests = ["NATURAL_ROYAL", "FOUR_DEUCES", "WILD_ROYAL", "FIVE_OAK", "STRAIGHT_FLUSH", "FOUR_OAK", "FULL_HOUSE", "FLUSH"]
    top_hits = [f"{k.replace('_',' ').title()}({v})" for k,v in counts.items() if k in interests and v > 0]
    hit_str = ", ".join(top_hits) if top_hits else "No Jackpots"
    
    log_data = {
        "Variant": variant, "Wheel_Mode": str(wheel_active), "Denom": denom, "Lines": num_lines,
        "Hand_Dealt": " ".join(hand), "Held_Cards": held_display, "Action": action_display,
        "EV": round(ev_val, 4), "Wheel_Mult": wheel_mult, "Wheel_Outer": w1, "Wheel_Inner": w2,
        "Net_Result": round(net_result, 2), "Wins": lines_won, "Hit_Summary": hit_str + wheel_str,
        "Best_Hit": top_hits[0].split('(')[0] if top_hits else "None"
    }
    return net_result, log_data

def generate_random_hand_str(sim_engine):
    hand, _ = sim_engine.core.deal_hand()
    return " ".join(hand)

# ==========================================
# 🧠 THE EV COACH (INTERACTIVE MODE)
# ==========================================
def run_interactive_coach(variant, denom, wheel_active):
    """
    The new [E]nter Hand Mode.
    Asks user for a hold, compares it to the Solver, and shows the cost of errors.
    """
    sim = DeucesWildSim(variant=variant)
    print(f"\n🎓 EV COACH ACTIVATED ({variant})")
    
    # 1. Get Hand
    raw = input("Enter Hand (e.g. '2h 2s 5c...'): ")
    hand = sim.normalize_input(raw)
    if len(hand) != 5:
        print("❌ Invalid Hand.")
        return

    print(f"\n🃏 Hand: {'  '.join(hand)}")
    
    # 2. Ask User for Hold
    user_input = input("Which cards do you hold? (e.g. '2h 2s' or 'all' or 'none'): ")
    user_hold = []
    
    if user_input.lower() in ['none', '', 'discard all']:
        user_hold = []
    elif user_input.lower() in ['all', 'hold all', 'keep']:
        user_hold = hand[:]
    else:
        # Parse user input flexibly
        user_parts = sim.normalize_input(user_input)
        # Validate they are in the hand
        for c in user_parts:
            if c in hand: user_hold.append(c)
            else: print(f"⚠️ Warning: {c} is not in the hand (ignoring).")
    
    # 3. Calculate User EV
    user_ev = 0.0
    max_ev = 0.0
    best_hold = []
    
    if EV_AVAILABLE:
        print("🤔 Analyzing probabilities...")
        pt = dw_exact_solver.PAYTABLES[variant]
        
        # User EV
        user_indices = [i for i, c in enumerate(hand) if c in user_hold]
        user_ev = dw_exact_solver.calculate_exact_ev(hand, user_indices, pt)
        
        # Solver EV (Max)
        best_hold, max_ev = dw_exact_solver.solve_hand_silent(hand, pt)
    else:
        print("❌ Error: Solver module not found.")
        return

    # 4. The Verdict
    print("-" * 40)
    
    # Format Holds for Display
    u_str = " ".join(user_hold) if user_hold else "Discard All"
    b_str = " ".join(best_hold) if best_hold else "Discard All"
    
    diff = max_ev - user_ev
    is_perfect = diff < 0.001
    
    if is_perfect:
        print(f"✅ PERFECT PLAY!")
        print(f"   You Held: {u_str}")
        print(f"   EV:       {user_ev:.4f}")
    else:
        print(f"❌ MISTAKE DETECTED")
        print(f"   You Held:  {u_str:<15} (EV: {user_ev:.4f})")
        print(f"   Optimal:   {b_str:<15} (EV: {max_ev:.4f})")
        print(f"   COST:      -${diff:.4f} per coin")
        
        # Calculate real money cost
        cost_money = diff * denom
        if wheel_active: cost_money *= 2 # Wheel doubles bet, so errors cost double? (Debatable, but EV is per unit)
        print(f"   Real Cost: -${cost_money:.2f} (at current denom)")

    print("-" * 40)
    input("Press Enter to continue...")

# ==========================================
# 🎮 INTERACTIVE MAIN LOOP
# ==========================================
if __name__ == "__main__":
    print("==========================================")
    print("🧬 MULTI-HAND SIMULATOR (v6.4 - AMY RESTORED)")
    print("==========================================")
    
    variant = DEFAULT_VARIANT
    lines = DEFAULT_LINES
    wheel_active = False
    denom_default = AMY_LADDER_DEFAULT[0] 
    start_bank = DEFAULT_START_BANKROLL
    floor = DEFAULT_FLOOR
    ceiling = DEFAULT_CEILING
    logging_on = LOGGING_ENABLED
    amy_mode = AMY_MODE_DEFAULT
    protocol_mode = PROTOCOL_MODE_DEFAULT
    amy_ladder = AMY_LADDER_DEFAULT[:]
    current_bankroll = start_bank
    denom = denom_default
    dealer_sim = DeucesWildSim()
    
    while True:
        log_s = "ON" if logging_on else "OFF"
        amy_s = "ON" if amy_mode else "OFF"
        prot_s = "ON" if protocol_mode else "OFF"
        
        print(f"\n[Wallet: ${start_bank:.2f} | Floor ${floor:.2f} | Ceiling ${ceiling:.2f}]")
        print(f"[Config: {lines} Lines | {variant} | Wheel: {wheel_active} | Denom ${denom_default:.2f}]")
        print(f"[Bots: Amy={amy_s} | Proto={prot_s}]")
        print("Options: (R)andom Batch | (E)nter Hand | (W)heel | (P)rotocol | (S)ettings | (A)my | (Q)uit")
        choice = input(">> ").strip().upper()
        
        if choice == 'Q': break
        elif choice == 'A': amy_mode = not amy_mode
        elif choice == 'P': protocol_mode = not protocol_mode
        elif choice == 'W': wheel_active = not wheel_active
        
        elif choice == 'E':
            run_interactive_coach(variant, denom_default, wheel_active)
                
        elif choice == 'S':
            print("\n--- SETTINGS ---")
            print("1. Set Lines")
            print(f"2. Set Base Denom (Curr: ${denom_default:.2f})")
            print("3. Switch Variant") 
            print(f"4. Set Bankroll (Curr: ${start_bank:.2f})")
            print(f"5. Set Floor (Curr: ${floor:.2f})")
            print(f"6. Set Ceiling (Curr: ${ceiling:.2f})")
            
            sub = input("Select: ").strip()
            if sub == '1': 
                try: lines = int(input("Lines: "))
                except: pass
            elif sub == '2':
                try: denom_default = float(input("Denom: "))
                except: pass
            elif sub == '3':
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
                try: start_bank = float(input("Start Bank: "))
                except: pass
            elif sub == '5':
                try: floor = float(input("Floor: "))
                except: pass
            elif sub == '6':
                try: ceiling = float(input("Ceiling: "))
                except: pass

        elif choice == 'R':
            try: batch_count = int(input("Sessions [1]: ") or 1)
            except: batch_count = 1
            print(f"🚀 Launching {batch_count} sessions...")
            
            for session_idx in range(1, batch_count + 1):
                current_bankroll = start_bank
                denom = denom_default
                win_history = deque(maxlen=10)
                hands_played = 0
                guardian = ProtocolGuardian(start_bank) if protocol_mode else None
                
                logger = None
                if logging_on:
                    logger = SessionLogger(variant, amy_mode, protocol_mode, session_idx)
                
                try:
                    stop_reason = "Running"
                    while current_bankroll > floor and current_bankroll < ceiling:
                        
                        # ==========================================
                        # 🤖 AMY BOT LOGIC (RESTORED)
                        # ==========================================
                        amy_note = ""
                        if amy_mode and len(amy_ladder) >= 3:
                            # 1. Determine Current Level
                            try: level_idx = amy_ladder.index(denom)
                            except: level_idx = 0; denom = amy_ladder[0]
                            
                            # 2. Set Window Size
                            window_size = 10 if level_idx == 0 else (5 if level_idx == 1 else 3)
                            
                            # 3. Check Stats
                            if len(win_history) >= window_size:
                                recent_wins = list(win_history)[-window_size:]
                                win_sum = sum(recent_wins)
                                ratio = win_sum / (lines * window_size)
                                
                                liquidity = current_bankroll - floor
                                cost_at_10 = amy_ladder[1] * 5 * lines
                                cost_at_25 = amy_ladder[2] * 5 * lines
                                
                                # LEVEL 1 -> 2 (Climb)
                                if level_idx == 0:
                                    if ratio >= 0.5 and liquidity >= (cost_at_10 * 10):
                                        denom = amy_ladder[1]
                                        amy_note = "UP_10"
                                        win_history.clear()
                                # LEVEL 2 -> 3 (Climb)
                                elif level_idx == 1:
                                    if ratio >= 0.5 and liquidity >= (cost_at_25 * 10):
                                        denom = amy_ladder[2]
                                        amy_note = "UP_25"
                                        win_history.clear()
                                    elif ratio < 0.5:
                                        denom = amy_ladder[0]
                                        amy_note = "DOWN_05"
                                        win_history.clear()
                                # LEVEL 3 (Retreat)
                                elif level_idx >= 2:
                                    if ratio <= 0.5:
                                        denom = amy_ladder[0]
                                        amy_note = "DOWN_05"
                                        win_history.clear()
                        # ==========================================

                        random_hand = generate_random_hand_str(dealer_sim)
                        net, log_data = run_multihand_session(random_hand, lines, variant, denom, wheel_active)
                        current_bankroll += net
                        hands_played += 1
                        
                        # Update History for Amy
                        win_history.append(log_data["Wins"])
                        
                        proto_trig = ""
                        if protocol_mode and guardian:
                            res = guardian.check(hands_played, current_bankroll)
                            if res:
                                proto_trig = res; stop_reason = f"PROTOCOL ({res})"
                                if logger:
                                    log_data["Protocol_Trigger"] = res
                                    log_data["Hand_ID"] = hands_played
                                    log_data["Bankroll"] = round(current_bankroll, 2)
                                    log_data["Amy_Trigger"] = amy_note
                                    logger.log(log_data)
                                break
                        
                        if logger:
                            log_data["Protocol_Trigger"] = proto_trig
                            log_data["Hand_ID"] = hands_played
                            log_data["Bankroll"] = round(current_bankroll, 2)
                            log_data["Amy_Trigger"] = amy_note
                            logger.log(log_data)
                            
                        if current_bankroll <= floor: stop_reason = "BUST"
                        if current_bankroll >= ceiling: stop_reason = "WIN"
                        
                    tag = "WIN" if "WIN" in stop_reason else "LOSS"
                    print(f"   Session {session_idx}: {tag} [{stop_reason}] | Hands: {hands_played} | Final: ${current_bankroll:.2f}")
                finally:
                    if logger:
                        logger.close()
                        if PLOT_TOOLS_AVAILABLE:
                            generate_mission_control_plot(logger.get_filepath(), floor=floor, ceiling=ceiling)
            print("🏁 Batch Complete.")