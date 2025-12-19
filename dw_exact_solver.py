import itertools
import sys
import multiprocessing
from dw_pay_constants import PAYTABLES  # <--- NEW IMPORT: Single Source of Truth

# ==========================================
# 🧬 CONFIGURATION: PAY TABLES (Per Credit)
# ==========================================
# Multiplied by 5 later for Max Bet display
# [REMOVED: Hard-coded PAYTABLES dictionary]
# Source: dw_pay_constants.py (ADR: The Pay Table Quarantine)

# ==========================================
# 🛠️ CORE UTILITIES
# ==========================================

def get_rank_val(card_str):
    """Converts card string (e.g., 'Th', '2s') to integer rank."""
    if card_str.startswith('10'):
        r = 'T'
    else:
        r = card_str[0].upper()
    
    mapping = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, 
               '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
    return mapping[r]

def normalize_hand(input_str):
    """Parses user input like '2h 2s 10c' into ['2h', '2s', 'tc'] (lowercase suits)"""
    parts = input_str.strip().split()
    # Handle comma separation if user pastes list like "2h, 2s, 5c"
    if len(parts) == 1 and ',' in input_str:
        parts = input_str.replace(',', ' ').split()

    normalized = []
    valid_ranks = "23456789TJQKA"
    valid_suits = "SHDC"
    
    for p in parts:
        p = p.upper()
        if p.startswith("10"):
            p = "T" + p[2:]
            
        if len(p) < 2: continue # Skip empty garbage
            
        r, s = p[0], p[1]
        # Basic validation
        if r not in valid_ranks or s not in valid_suits:
             continue 
        normalized.append(p.lower())
        
    if len(normalized) != 5:
        return None
        
    return normalized

# ==========================================
# 🧠 EVALUATION ENGINE (PATCHED v2.1)
# ==========================================

def evaluate_hand(hand, pt):
    ranks = [c[0] for c in hand]
    deuces = ranks.count('2')
    non_deuce_ranks = [get_rank_val(c) for c in hand if c[0] != '2']
    non_deuce_ranks.sort()
    
    # Flush Check (Ignore Deuce Suits)
    non_deuce_suits = [c[1] for c in hand if c[0] != '2']
    if len(non_deuce_suits) == 0: is_flush = True 
    else: is_flush = len(set(non_deuce_suits)) == 1
    
    # 1. Natural Royal
    if is_flush and deuces == 0 and set(ranks) == {'t','j','q','k','a'}: return pt["NATURAL_ROYAL"]
    # 2. Four Deuces
    if deuces == 4: return pt["FOUR_DEUCES"]
    # 3. Wild Royal
    needed = {10,11,12,13,14}
    if is_flush and deuces > 0 and set(non_deuce_ranks).issubset(needed): return pt["WILD_ROYAL"]

    # 4. Five of a Kind
    counts = {x:non_deuce_ranks.count(x) for x in set(non_deuce_ranks)}
    max_k = max(counts.values()) if counts else 0
    if deuces + max_k >= 5: return pt["FIVE_OAK"]

    # 5. Straight Flush
    if is_flush:
        if not non_deuce_ranks: return pt["STRAIGHT_FLUSH"]
        span = non_deuce_ranks[-1] - non_deuce_ranks[0]
        if len(set(non_deuce_ranks)) == len(non_deuce_ranks):
             if span <= 4: return pt["STRAIGHT_FLUSH"]
             if 14 in non_deuce_ranks: # Wheel
                 wheel_vals = [1 if x==14 else x for x in non_deuce_ranks]
                 wheel_vals.sort()
                 if (wheel_vals[-1] - wheel_vals[0]) <= 4: return pt["STRAIGHT_FLUSH"]

    # 6. Four of a Kind
    if deuces + max_k >= 4: return pt["FOUR_OAK"]

    # 7. Full House
    if deuces == 0:
        if 3 in counts.values() and 2 in counts.values(): return pt["FULL_HOUSE"]
    if deuces == 1:
        if list(counts.values()).count(2) == 2: return pt["FULL_HOUSE"]
            
    # 8. Flush
    if is_flush: return pt["FLUSH"]
    
    # 9. Straight
    unique_vals = sorted(list(set(non_deuce_ranks)))
    if len(unique_vals) + deuces >= 5:
        span = unique_vals[-1] - unique_vals[0]
        if span <= 4: return pt["STRAIGHT"]
        if 14 in unique_vals:
            wheel = [1 if x==14 else x for x in unique_vals]
            wheel.sort()
            if (wheel[-1] - wheel[0]) <= 4: return pt["STRAIGHT"]

    # 10. Three of a Kind
    if deuces + max_k >= 3: return pt["THREE_OAK"]
        
    return 0

# ==========================================
# 🔢 THE ENUMERATION SOLVER
# ==========================================

def calculate_exact_ev(hand_str_list, hold_indices, pt):
    suits = ['s', 'h', 'd', 'c']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    full_deck = [r.lower()+s for r in ranks for s in suits]
    
    held_cards = [hand_str_list[i] for i in hold_indices]
    stub = [c for c in full_deck if c not in hand_str_list]
    draw_count = 5 - len(held_cards)
    
    possible_draws = itertools.combinations(stub, draw_count)
    
    total_payout = 0
    combinations = 0
    
    for draw in possible_draws:
        final_hand = held_cards + list(draw)
        payout = evaluate_hand(final_hand, pt)
        total_payout += payout
        combinations += 1
        
    ev = (total_payout / combinations) * 5 
    return ev

def solve_hand_silent(hand, pt):
    # Optimized solver that doesn't print debug info, just returns best hold
    indices = range(5)
    powerset = []
    for i in range(len(indices) + 1):
        powerset.extend(itertools.combinations(indices, i))
    
    best_ev = -1
    best_hold = []
    
    for hold_indices in powerset:
        ev = calculate_exact_ev(hand, hold_indices, pt)
        if ev > best_ev:
            best_ev = ev
            best_hold = [hand[i] for i in hold_indices]
            
    return best_hold, best_ev

# ==========================================
# ⚡ MULTIPROCESSING WORKER
# ==========================================

def worker_process_hand(args):
    """
    Worker function to process a single hand in a separate process.
    args: (raw_hand_string, variant_name)
    """
    raw_hand, variant_name = args
    pt = PAYTABLES[variant_name]
    
    hand = normalize_hand(raw_hand)
    if not hand:
        return f"[ERROR] Invalid Input: {raw_hand}"
    
    # Run the solver
    bh, bev = solve_hand_silent(hand, pt)
    
    # Format output
    held_str = " ".join(bh) if bh else "Discard All"
    input_disp = " ".join(hand)
    return f"Hand: {input_disp:<15} -> Hold: {held_str:<15} (EV: {bev:.4f})"

# ==========================================
# 🎮 INTERACTIVE MAIN LOOP
# ==========================================

if __name__ == "__main__":
    # Support for Windows/Spawn methods
    multiprocessing.freeze_support()

    print("==========================================")
    print("🧬 DEUCES WILD EXACT SOLVER (v3.2 - TRI-CORE)")
    print("==========================================")
    
    current_variant = "NSUD"
    
    while True:
        print(f"\n[Current Mode: {current_variant}]")
        print("Options: (E)nter Hand | (B)atch Mode | (S)witch Variant | (Q)uit")
        choice = input(">> ").strip().upper()
        
        if choice == 'Q':
            break
            
        elif choice == 'S':
            print("\nSelect Variant:")
            print("1. NSUD (Aggressive: 16/10)")
            print("2. AIRPORT (Defensive: 12/9)")
            print("3. DBW (Hybrid: 16/13)")
            v = input("Select (1/2/3): ").strip()
            if v == '1': current_variant = "NSUD"
            elif v == '2': current_variant = "AIRPORT"
            elif v == '3': current_variant = "DBW"
        
        elif choice == 'E':
            raw_hand = input("\nEnter Hand: ")
            hand = normalize_hand(raw_hand)
            if hand:
                pt = PAYTABLES[current_variant]
                bh, bev = solve_hand_silent(hand, pt)
                held_str = " ".join(bh) if bh else "Discard All"
                print(f"\n✅ Result: {held_str} (EV: {bev:.4f})")

        elif choice == 'B':
            print("\n📥 PASTE HANDS BELOW (One per line).")
            print("   Press ENTER on a blank line to start processing.")
            print("-" * 40)
            
            batch_hands = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                if not line.strip():
                    break
                batch_hands.append(line)
            
            num_cores = multiprocessing.cpu_count()
            print(f"\n🚀 Firing up {num_cores} cores to process {len(batch_hands)} hands...")
            print(f"   (Calculates exact EV including 'Discard All' ~1.5m combos)")
            print("-" * 60)
            
            # Create task list: Tuple of (HandString, VariantName)
            tasks = [(h, current_variant) for h in batch_hands]
            
            # --- THE PARALLEL ENGINE ---
            with multiprocessing.Pool(processes=num_cores) as pool:
                # Map inputs to the worker function across all cores
                results = pool.map(worker_process_hand, tasks)
                
            # Print results as they are returned (in order)
            for res in results:
                print(res)
            
            print("-" * 60)
            print("✅ Batch Complete.")