import sys
import random
import copy
import os
import csv
import datetime
from collections import Counter, deque
from dw_sim_engine import DeucesWildSim

# ---------------------------------------------------------
# 📊 OPTIONAL MODULES (Plotting & EV Solver)
# ---------------------------------------------------------
try:
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False

try:
    import dw_exact_solver
    EV_AVAILABLE = True
except ImportError:
    EV_AVAILABLE = False

# ==========================================
# 🧬 CONFIGURATION & DEFAULTS
# ==========================================
DEFAULT_LINES = 5
DEFAULT_VARIANT = "AIRPORT"
DEFAULT_START_BANKROLL = 40.00
DEFAULT_FLOOR = 70.00   # 🛡️ THE DOOM SLOPE HARD DECK
DEFAULT_CEILING = 120.00
LOGGING_ENABLED = True

# --- AMY BOT DEFAULTS ---
AMY_MODE_DEFAULT = False
AMY_LADDER_DEFAULT = [0.05, 0.10, 0.25] 

# --- PROTOCOL DEFAULTS ---
PROTOCOL_MODE_DEFAULT = True # Default to ON for safety

class ProtocolGuardian:
    """
    🛡️ THE AIRPORT PROTOCOL ENFORCER
    Monitors the session in real-time and triggers stops based on
    the Research Rules (Vacuum, Tease, Zombie, Hard Deck, Sniper).
    """
    def __init__(self, start_bankroll):
        self.start = start_bankroll
        self.spike_hand_idx = -1
        self.triggered = False
        self.trigger_reason = None
        
    def check(self, hands_played, current_bankroll):
        if self.triggered: return self.trigger_reason
        
        # 1. SNIPER EXCEPTION (Win Limit: +20%)
        # Note: If start is $100, trigger is $120.
        if current_bankroll >= (self.start * 1.20):
            self.triggered = True
            self.trigger_reason = "SNIPER_WIN"
            return "SNIPER_WIN"

        # 2. VACUUM CHECK (First 15 Hands: -25%)
        # Note: If start is $100, trigger is $75.
        if hands_played <= 15 and current_bankroll <= (self.start * 0.75):
            self.triggered = True
            self.trigger_reason = "VACUUM_STOP"
            return "VACUUM_STOP"

        # 3. THE TEASE (Sub-Surface Check)
        # Rule: Spike > Start, then drop < Start within 5 hands
        if current_bankroll > self.start:
            self.spike_hand_idx = hands_played
            
        if self.spike_hand_idx != -1: # We surfaced once
            if current_bankroll < self.start: # Now underwater
                if (hands_played - self.spike_hand_idx) <= 5:
                    self.triggered = True
                    self.trigger_reason = "TEASE_EXIT"
                    return "TEASE_EXIT"

        # 4. ZOMBIE THRESHOLD (Hand 40)
        # Rule: Underwater at Hand 40 -> Time Limit (Immediate Stop in Sim)
        if hands_played == 40 and current_bankroll < self.start:
            self.triggered = True
            self.trigger_reason = "ZOMBIE_LIMIT"
            return "ZOMBIE_LIMIT"

        # 5. HARD DECK (Hand 66)
        # Rule: Statistical Point of No Return
        if hands_played >= 66:
            self.triggered = True
            self.trigger_reason = "HARD_DECK"
            return "HARD_DECK"
            
        return None

def run_multihand_session(hand_str, num_lines, variant, denom):
    """
    Runs a single hand across N lines.
    Returns: (net_result, log_data_dict)
    """
    sim = DeucesWildSim(variant=variant, denom=denom)
    
    # 1. Parse Hand
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
    ev_display = ""
    if EV_AVAILABLE:
        try:
            hold_indices = [i for i, c in enumerate(hand) if c in held_cards]
            pt = dw_exact_solver.PAYTABLES[variant]
            ev_val = dw_exact_solver.calculate_exact_ev(hand, hold_indices, pt)
            ev_display = f" | EV: {ev_val:.4f}"
        except Exception:
            ev_display = " | EV: Err"

    # Only print details if we are running a single session interactively
    # (To avoid spamming console in batch mode, handled in main loop)
    pass 

    # 3. Build Stub
    full_deck = sim.get_deck()
    dealt_set = set(hand)
    stub_template = [c for c in full_deck if c not in dealt_set]
    
    if len(stub_template) != 47:
        print("❌ Error: Deck integrity failed.")
        return 0.0, {}

    # 4. Loop
    results = []
    total_winnings = 0.0
    bet_per_line = sim.bet_amount 
    total_bet = bet_per_line * num_lines
    draw_count = 5 - len(held_cards)
    
    lines_won = 0  # Track count of winning lines
    
    for i in range(num_lines):
        current_stub = copy.copy(stub_template)
        random.shuffle(current_stub)
        drawn = current_stub[:draw_count]
        final_hand = held_cards + drawn
        
        rank_name, payout_mult = sim.evaluate_hand(final_hand)
        
        if payout_mult > 0:
            lines_won += 1
            
        total_winnings += (payout_mult * bet_per_line)
        results.append(rank_name)

    # 5. Result
    net_result = total_winnings - total_bet
    
    # Concise Hits Report
    counts = Counter(results)
    top_hits = []
    interests = ["Natural Royal", "Four Deuces", "Wild Royal", "5 of a Kind", "Straight Flush", "4 of a Kind", "Full House", "Flush"]
    
    hit_summary_list = []
    for hit_type in interests:
        if counts[hit_type] > 0:
            top_hits.append(f"{hit_type}({counts[hit_type]})")
            hit_summary_list.append(hit_type)
    
    hit_str = ", ".join(top_hits) if top_hits else "No Jackpots"
    primary_hit = hit_summary_list[0] if hit_summary_list else "None"
    
    # 6. Build Log Data Dictionary
    log_data = {
        "Variant": variant,
        "Denom": denom,
        "Lines": num_lines,
        "Hand_Dealt": " ".join(hand),
        "Held_Cards": held_display,
        "Action": action_display,
        "EV": round(ev_val, 4),
        "Net_Result": round(net_result, 2),
        "Wins": lines_won,
        "Hit_Summary": hit_str,
        "Best_Hit": primary_hit
    }
    
    return net_result, log_data

def generate_random_hand_str(sim_engine):
    """Generates a random 5-card hand string."""
    deck = sim_engine.get_deck()
    hand = deck[:5]
    return " ".join(hand)

def generate_plot(x_vals, y_vals, denoms, variant, lines, amy_active, session_idx=None):
    """
    Generates a rich visualization of the session.
    - Saves to 'plots/' folder
    - Colors points by denomination (Dynamic Scale)
    - Fixes alignment of Hand/Result using Zip
    - Supports Batch tagging
    """
    if not PLOT_AVAILABLE:
        return

    # 1. Setup Folder & Filename
    if not os.path.exists("plots"):
        os.makedirs("plots")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_tag = "_AMY" if amy_active else ""
    session_tag = f"_S{session_idx}" if session_idx is not None else ""
    filename = f"plots/plot_{variant}{mode_tag}{session_tag}_{timestamp}.png"

    plt.figure(figsize=(12, 6))
    
    # 2. Draw Base Line (Gray)
    plt.plot(x_vals, y_vals, linestyle='-', color='gray', alpha=0.5, linewidth=1, label='Balance', zorder=1)
    
    # 3. Dynamic Color Coding
    unique_denoms = sorted(list(set(denoms)))
    num_levels = len(unique_denoms)
    color_map = {}
    
    if num_levels <= 1:
        color_map = {unique_denoms[0]: '#2ca02c'} # Green
    elif num_levels == 2:
        color_map = {unique_denoms[0]: '#2ca02c', unique_denoms[1]: '#d62728'} # Green, Red
    elif num_levels == 3:
        color_map = {unique_denoms[0]: '#2ca02c', unique_denoms[1]: '#ff7f0e', unique_denoms[2]: '#d62728'} # Green, Orange, Red
    else:
        palette = ['#2ca02c', '#1f77b4', '#9467bd', '#ff7f0e', '#d62728', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        for i, d in enumerate(unique_denoms):
            color_map[d] = palette[i % len(palette)]
    
    # 4. Build Scatter Plot (Aligned)
    scatter_x = []
    scatter_y = []
    scatter_c = []
    
    for d, x, y in zip(denoms, x_vals[1:], y_vals[1:]):
        scatter_x.append(x)
        scatter_y.append(y)
        scatter_c.append(color_map.get(d, 'black'))

    if scatter_x:
        plt.scatter(scatter_x, scatter_y, c=scatter_c, s=25, zorder=2)
    
    # 5. Legend & Annotations
    legend_elements = [Line2D([0], [0], marker='o', color='w', markerfacecolor=color_map[d], label=f'${d:.2f}') for d in unique_denoms]
    
    if y_vals:
        max_val = max(y_vals)
        max_idx = y_vals.index(max_val)
        max_hand = x_vals[max_idx]
        
        plt.annotate(f'MAX: ${max_val:.2f}\n(Hand {max_hand})', 
                     xy=(max_hand, max_val), 
                     xytext=(0, 20), textcoords='offset points', ha='center',
                     arrowprops=dict(arrowstyle="->", color='black'),
                     fontweight='bold', 
                     bbox=dict(boxstyle="round,pad=0.3", fc="#fff7bc", ec="orange", alpha=0.9))

    title_extra = " (AMY BOT)" if amy_active else ""
    session_title = f" | Session {session_idx}" if session_idx else ""
    plt.title(f"Deuces Wild: {variant}{title_extra}{session_title}", fontsize=14, fontweight='bold')
    plt.xlabel("Deal Number", fontsize=12)
    plt.ylabel("Bankroll ($)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.axhline(y=y_vals[0], color='black', linestyle=':', alpha=0.5)
    if legend_elements:
        plt.legend(handles=legend_elements, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(filename)
    if session_idx is None or session_idx % 10 == 0:
        print(f"   📈 Chart Saved: {filename}")
    plt.close()

def setup_logger(variant, amy_active, protocol_active, session_idx=None):
    """Initializes CSV logging with Batch support."""
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_tag = "_AMY" if amy_active else ""
    proto_tag = "_PROTO" if protocol_active else ""
    session_tag = f"_S{session_idx}" if session_idx is not None else ""
    filename = f"logs/session_{variant}{mode_tag}{proto_tag}{session_tag}_{timestamp}.csv"
    
    fieldnames = [
        "Hand_ID", "Variant", "Lines", "Denom", "Bankroll", "Net_Result", "EV", 
        "Hand_Dealt", "Held_Cards", "Action", "Wins", "Best_Hit", "Hit_Summary",
        "Amy_Win_Count", "Amy_Trigger", "Protocol_Trigger" 
    ]
    
    f = open(filename, 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    if session_idx is None or session_idx % 10 == 0:
        print(f"   📝 Log Started: {filename}")
    return f, writer

# ==========================================
# 🎮 INTERACTIVE MAIN LOOP
# ==========================================

if __name__ == "__main__":
    print("==========================================")
    print("🧬 MULTI-HAND SIMULATOR (v5.1 - PROTOCOL + AMY CONTROL)")
    print("==========================================")
    
    # Session State
    variant = DEFAULT_VARIANT
    lines = DEFAULT_LINES
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
    
    dealer_sim = DeucesWildSim()
    
    while True:
        log_status = "ON" if logging_on else "OFF"
        amy_status = "ON" if amy_mode else "OFF"
        proto_status = "ON" if protocol_mode else "OFF"
        
        print(f"\n[Wallet Config: Start ${start_bank:.2f} | Floor ${floor:.2f} | Ceiling ${ceiling:.2f}]")
        print(f"[Game Config: {lines} Lines | {variant} | Base Denom ${denom_default:.2f}]")
        print(f"[Bots: Amy={amy_status} | Protocol={proto_status}] Ladder: {amy_ladder}")
        print("Options: (R)andom Batch Session | (E)nter Single Hand | (P)rotocol Toggle | (S)ettings | (A)my Toggle | (Q)uit")
        choice = input(">> ").strip().upper()
        
        if choice == 'Q':
            break

        elif choice == 'A':
            amy_mode = not amy_mode
            print(f"🤖 AMY MODE: {amy_mode}")

        elif choice == 'P':
            protocol_mode = not protocol_mode
            print(f"🛡️ PROTOCOL GUARD: {protocol_mode}")

        elif choice == 'S':
            print("\n--- SETTINGS ---")
            print("1. Set Lines")
            print(f"2. Set Base Denom (Curr: ${denom_default:.2f})")
            print("3. Switch Variant")
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
                v = input("Variant (1=NSUD, 2=Airport): ")
                variant = "NSUD" if v == '1' else "AIRPORT"
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
                        # Update default denom to match start of ladder
                        denom_default = amy_ladder[0] 
                        print(f"✅ Amy Ladder set to: {amy_ladder}")
                    else:
                        print("❌ Error: Must provide exactly 3 values.")
                except:
                    print("❌ Error: Invalid format.")

        elif choice == 'E':
            # Single Hand Evaluation
            raw_hand = input("\nEnter Hand: ")
            if raw_hand.strip():
                # For single hand, we print details to console
                net, _ = run_multihand_session(raw_hand, lines, variant, denom_default)
                print(f"   💵 Result: ${net:+.2f}")

        elif choice == 'R':
            # BATCH SESSION LOGIC
            print(f"\n🎲 BATCH SESSION CONFIGURATION")
            try:
                batch_count = int(input("Number of Sessions to Run [1]: ") or 1)
            except: batch_count = 1
            
            print(f"🚀 Launching {batch_count} sessions...")
            print(f"   (Stop Condition: Floor ${floor:.2f} or Ceiling ${ceiling:.2f})")
            print("-" * 60)
            
            sessions_won = 0
            sessions_lost = 0
            total_hands_across_batch = 0
            protocol_stops = Counter()
            
            # --- BATCH LOOP ---
            for session_idx in range(1, batch_count + 1):
                # 1. Reset State for new session
                current_bankroll = start_bank
                denom = denom_default if amy_mode else denom_default
                win_history = deque(maxlen=10)
                hands_played = 0
                plot_x = [0]
                plot_y = [current_bankroll]
                plot_denoms = []
                
                # PROTOCOL INIT
                guardian = ProtocolGuardian(start_bank) if protocol_mode else None
                
                # 2. Setup Logger
                log_file = None
                writer = None
                if logging_on:
                    log_file, writer = setup_logger(variant, amy_mode, protocol_mode, session_idx)
                
                try:
                    stop_reason = "Running"
                    
                    # --- SESSION LOOP ---
                    while current_bankroll > floor and current_bankroll < ceiling:
                        
                        # Amy Logic (Simplified for Batch Speed)
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
                        net, log_data = run_multihand_session(random_hand, lines, variant, denom)
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
                                
                                plot_x.append(hands_played)
                                plot_y.append(current_bankroll)
                                plot_denoms.append(denom)
                                break
                        
                        plot_x.append(hands_played)
                        plot_y.append(current_bankroll)
                        plot_denoms.append(denom)
                        
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
                        
                    # Print brief status
                    print(f"   Session {session_idx}: {result_tag} [{stop_reason}] | Hands: {hands_played} | Final: ${current_bankroll:.2f}")
                    
                    # Generate Plot
                    generate_plot(plot_x, plot_y, plot_denoms, variant, lines, amy_mode, session_idx)
                
                finally:
                    if log_file: log_file.close()

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