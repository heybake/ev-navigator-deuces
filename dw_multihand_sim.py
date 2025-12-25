import sys
import random
import os
import datetime
from collections import Counter
from dw_sim_engine import DeucesWildSim
from dw_pay_constants import PAYTABLES 

# --- MODULE IMPORTS (The Micro-Services) ---
from dw_logger import SessionLogger
from dw_protocol_guardian import ProtocolGuardian
from dw_bot_amy import AmyBot

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

def run_multihand_session(hand_str, num_lines, variant, denom, wheel_active=False):
    """Runs a simulation session (used for Batch Mode)."""
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
    
    # --- UPDATE: Add the Bonus Deuces specific keys here ---
    interests = [
        "NATURAL_ROYAL", 
        "FOUR_DEUCES_ACE",  # New Jackpot
        "FOUR_DEUCES", 
        "FIVE_ACES",        # New Jackpot
        "FIVE_3_4_5",       # New Jackpot
        "FIVE_6_TO_K",      # New Payout
        "WILD_ROYAL", 
        "FIVE_OAK", 
        "STRAIGHT_FLUSH", 
        "FOUR_OAK", 
        "FULL_HOUSE", 
        "FLUSH"
    ]
    
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

def run_interactive_coach(variant, denom, wheel_active):
    """The [E]nter Hand Mode with EV Coaching."""
    sim = DeucesWildSim(variant=variant)
    print(f"\n🎓 EV COACH ACTIVATED ({variant})")
    
    raw = input("Enter Hand (e.g. '2h 2s 5c...'): ")
    hand = sim.normalize_input(raw)
    if len(hand) != 5:
        print("❌ Invalid Hand.")
        return

    print(f"\n🃏 Hand: {'  '.join(hand)}")
    user_input = input("Which cards do you hold? (e.g. '2h 2s' or 'all' or 'none'): ")
    user_hold = []
    
    if user_input.lower() in ['none', '', 'discard all']: user_hold = []
    elif user_input.lower() in ['all', 'hold all', 'keep']: user_hold = hand[:]
    else:
        user_parts = sim.normalize_input(user_input)
        for c in user_parts:
            if c in hand: user_hold.append(c)
    
    if EV_AVAILABLE:
        print("🤔 Analyzing probabilities...")
        pt = dw_exact_solver.PAYTABLES[variant]
        user_indices = [i for i, c in enumerate(hand) if c in user_hold]
        user_ev = dw_exact_solver.calculate_exact_ev(hand, user_indices, pt)
        best_hold, max_ev = dw_exact_solver.solve_hand_silent(hand, pt)
        
        diff = max_ev - user_ev
        u_str = " ".join(user_hold) if user_hold else "Discard All"
        b_str = " ".join(best_hold) if best_hold else "Discard All"
        
        print("-" * 40)
        if diff < 0.001:
            print(f"✅ PERFECT PLAY! (EV: {user_ev:.4f})")
        else:
            print(f"❌ MISTAKE DETECTED")
            print(f"   You Held:  {u_str:<15} (EV: {user_ev:.4f})")
            print(f"   Optimal:   {b_str:<15} (EV: {max_ev:.4f})")
            cost_money = diff * denom * (2 if wheel_active else 1)
            print(f"   Real Cost: -${cost_money:.2f} (per hand)")
        print("-" * 40)
        input("Press Enter to continue...")
    else:
        print("❌ Solver not available.")

# ==========================================
# 🎮 INTERACTIVE MAIN LOOP
# ==========================================
if __name__ == "__main__":
    print("==========================================")
    print("🧬 MULTI-HAND SIMULATOR (v7.2 - MICROSERVICE)")
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
        elif choice == 'E': run_interactive_coach(variant, denom_default, wheel_active)
        
        elif choice == 'S':
            print("\n--- SETTINGS ---")
            print("1. Set Lines")
            print(f"2. Set Base Denom (Curr: ${denom_default:.2f})")
            print("3. Switch Variant") 
            print(f"4. Set Bankroll (Curr: ${start_bank:.2f})")
            print(f"5. Set Floor (Curr: ${floor:.2f})")
            print(f"6. Set Ceiling (Curr: ${ceiling:.2f})")
            print(f"7. Toggle Logging (Current: {log_s})")
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

        elif choice == 'R':
            try: batch_count = int(input("Sessions [1]: ") or 1)
            except: batch_count = 1
            print(f"🚀 Launching {batch_count} sessions...")
            
            for session_idx in range(1, batch_count + 1):
                current_bankroll = start_bank
                denom = denom_default
                hands_played = 0
                
                # --- INSTANTIATE AGENTS ---
                guardian = ProtocolGuardian(start_bank) if protocol_mode else None
                amy_bot = AmyBot(amy_ladder, lines) if amy_mode else None
                logger = SessionLogger(variant, amy_mode, protocol_mode, session_idx) if logging_on else None
                
                try:
                    stop_reason = "Running"
                    while current_bankroll > floor and current_bankroll < ceiling:
                        
                        # 1. AMY DECISION
                        amy_note = ""
                        if amy_bot:
                            denom, amy_note = amy_bot.decide_denom(denom, current_bankroll, floor)
                        
                        # 2. RUN HAND
                        random_hand = generate_random_hand_str(dealer_sim)
                        net, log_data = run_multihand_session(random_hand, lines, variant, denom, wheel_active)
                        current_bankroll += net
                        hands_played += 1
                        
                        # 3. AMY RECORD
                        if amy_bot:
                            amy_bot.record_result(log_data["Wins"])

                        # 4. PROTOCOL CHECK
                        proto_trig = ""
                        if guardian:
                            res = guardian.check(hands_played, current_bankroll)
                            if res:
                                proto_trig = res; stop_reason = f"PROTOCOL ({res})"
                                if logger:
                                    log_data.update({"Protocol_Trigger": res, "Hand_ID": hands_played, "Bankroll": round(current_bankroll, 2), "Amy_Trigger": amy_note})
                                    logger.log(log_data)
                                break
                        
                        if logger:
                            log_data.update({"Protocol_Trigger": proto_trig, "Hand_ID": hands_played, "Bankroll": round(current_bankroll, 2), "Amy_Trigger": amy_note})
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