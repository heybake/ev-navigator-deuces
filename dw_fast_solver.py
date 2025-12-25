"""
dw_fast_solver.py
High-Performance Hybrid Solver for Real-Time UI (v5.4 - Full Integrity)

Features:
- Fast Integer-based Evaluation.
- Hybrid Monte Carlo / Exact Math.
- UPDATED: Supports Tiered 5-of-a-Kind (Aces vs 3/4/5 vs 6-K).
- INCLUDES: Performance Benchmarking Block.
"""
import random
import itertools
import time
from collections import Counter

# --- FAST EVALUATOR (Integer Based) ---
# Maps '2'->0 ... 'A'->12
RANK_MAP = {r: i for i, r in enumerate("23456789TJQKA")}

def get_rank_int(card_str):
    return RANK_MAP[card_str[0]]

def get_suit_int(card_str):
    return card_str[1] 

def evaluate_fast(ranks, suits, pay_table):
    """
    Optimized evaluator that takes pre-processed lists of ranks and suits.
    """
    # 1. FLUSH CHECK
    # Identify Deuces (0 is '2')
    deuce_count = ranks.count(0) 
    
    # Filter Non-Deuces
    non_deuces = [r for r in ranks if r != 0]
    non_deuce_suits = [s for r, s in zip(ranks, suits) if r != 0]
    
    # Valid flush if all non-deuces share one suit
    is_flush = len(set(non_deuce_suits)) <= 1
    
    # 2. ROYAL / STRAIGHT FLUSH
    if is_flush:
        if not non_deuces: 
             pass # 5 Deuces -> Caught by 5OAK check
        else:
            # Natural Royal: No deuces, A-K-Q-J-T (8,9,10,11,12)
            if deuce_count == 0 and set(non_deuces) == {8,9,10,11,12}:
                return pay_table.get("NATURAL_ROYAL", 800)
            
            # Wild Royal (All non-deuces >= 8 (Ten))
            if all(r >= 8 for r in non_deuces):
                 if len(set(non_deuces)) == len(non_deuces):
                     return pay_table.get("WILD_ROYAL", 25)
            
            # Straight Flush (Span <= 4)
            uniq = sorted(list(set(non_deuces)))
            if not uniq:
                pass
            else:
                span = uniq[-1] - uniq[0]
                if span <= 4:
                    return pay_table.get("STRAIGHT_FLUSH", 9)
                # Wheel Check (A=12, 3=1, 4=2, 5=3)
                if 12 in uniq:
                    wheel_uniq = sorted([(-1 if r == 12 else r) for r in uniq])
                    w_span = wheel_uniq[-1] - wheel_uniq[0]
                    if w_span <= 4:
                        return pay_table.get("STRAIGHT_FLUSH", 9)

    # 3. N-OF-A-KIND
    if non_deuces:
        counts = Counter(non_deuces)
        # Most common rank and its count
        most_common = counts.most_common(1)[0]
        five_oak_rank = most_common[0]
        most_common_count = most_common[1]
        total_oak = most_common_count + deuce_count
    else:
        total_oak = 5 # 5 Deuces
        five_oak_rank = 12 # Treat as Aces
    
    # 4 DEUCES
    if deuce_count == 4:
        # Bonus Logic: Ace Kicker (Ace is 12)
        if "FOUR_DEUCES_ACE" in pay_table and non_deuces and non_deuces[0] == 12: 
             return pay_table["FOUR_DEUCES_ACE"]
        return pay_table.get("FOUR_DEUCES", 200)

    # 5 OF A KIND (Tiered Logic)
    if total_oak >= 5:
        # Tier 1: 5 Aces (Rank 12)
        if five_oak_rank == 12:
            if "FIVE_ACES" in pay_table: return pay_table["FIVE_ACES"]
            return pay_table.get("FIVE_OAK", 15)
        
        # Tier 2: 5 3s, 4s, 5s (Ranks 1, 2, 3)
        if 1 <= five_oak_rank <= 3:
            if "FIVE_3_4_5" in pay_table: return pay_table["FIVE_3_4_5"]
            return pay_table.get("FIVE_OAK", 15)
            
        # Tier 3: 5 6s thru Ks (Ranks 4-11)
        if "FIVE_6_TO_K" in pay_table: return pay_table["FIVE_6_TO_K"]
        
        # Generic Fallback
        return pay_table.get("FIVE_OAK", 15)
    
    if total_oak == 4:
        return pay_table.get("FOUR_OAK", 4)
    
    if total_oak == 3:
        # Full House check
        is_fh = False
        if deuce_count == 0:
            if len(counts) == 2 and 3 in counts.values(): is_fh = True
        elif deuce_count == 1:
            if len(counts) == 2 and list(counts.values()) == [2, 2]: is_fh = True
        
        if is_fh: return pay_table.get("FULL_HOUSE", 4)

    # FLUSH (Rank independent)
    if is_flush:
        return pay_table.get("FLUSH", 2) 

    # STRAIGHT (Non-Flush)
    uniq = sorted(list(set(non_deuces)))
    if len(uniq) + deuce_count >= 5:
        if uniq:
            span = uniq[-1] - uniq[0]
            if span <= 4 and deuce_count >= (5 - len(uniq)): 
                 return pay_table.get("STRAIGHT", 2)
            
            # Wheel Straight
            if 12 in uniq:
                wheel_uniq = sorted([(-1 if r == 12 else r) for r in uniq])
                w_span = wheel_uniq[-1] - wheel_uniq[0]
                if w_span <= 4 and deuce_count >= (5 - len(uniq)):
                    return pay_table.get("STRAIGHT", 2)

    if total_oak == 3:
        return pay_table.get("THREE_OAK", 1)

    return 0

# --- HYBRID SOLVER ---
def solve_hand(hand_str_list, pay_table):
    """
    Returns the best hold (list of card strings).
    Uses Monte Carlo for heavy branches (discard > 2 cards).
    Uses Exact Math for light branches.
    """
    deck_ranks = "23456789TJQKA"
    deck_suits = "shdc"
    full_deck = [r+s for r in deck_ranks for s in deck_suits]
    
    # Remove dealt cards from deck
    remaining_deck = [c for c in full_deck if c not in hand_str_list]
    
    best_ev = -1.0
    best_hold = []
    
    # 32 Combinations
    for k in range(6): # 0 to 5 held cards
        for held_indices in itertools.combinations(range(5), k):
            held_cards = [hand_str_list[i] for i in held_indices]
            
            current_total_pay = 0.0
            iterations = 0
            
            num_to_draw = 5 - k
            
            if num_to_draw <= 2: 
                # -- EXACT MODE -- (Draw 0, 1, 2)
                for draw in itertools.combinations(remaining_deck, num_to_draw):
                    final_hand = held_cards + list(draw)
                    fr = [get_rank_int(c) for c in final_hand]
                    fs = [c[1] for c in final_hand]
                    current_total_pay += evaluate_fast(fr, fs, pay_table)
                    iterations += 1
                ev = current_total_pay / iterations
                
            else:
                # -- MONTE CARLO MODE -- (Draw 3, 4, 5)
                # Reduced sim count for speed, increase for precision
                SIM_COUNT = 2500
                for _ in range(SIM_COUNT):
                    draw = random.sample(remaining_deck, num_to_draw)
                    final_hand = held_cards + draw
                    fr = [get_rank_int(c) for c in final_hand]
                    fs = [c[1] for c in final_hand]
                    current_total_pay += evaluate_fast(fr, fs, pay_table)
                ev = current_total_pay / SIM_COUNT
            
            if ev > best_ev:
                best_ev = ev
                best_hold = list(held_cards)
                
    return best_hold, best_ev

# ==========================================
# ⚡ PERFORMANCE & INTEGRITY CHECK
# ==========================================
if __name__ == "__main__":
    print("🏎️  FAST SOLVER DIAGNOSTICS")
    print("----------------------------")
    
    # Test Data: 10/4/3/3 Bonus Deuces
    TEST_TABLE = {
        "NATURAL_ROYAL": 800, "FOUR_DEUCES": 200, "FIVE_ACES": 80,
        "FIVE_3_4_5": 40, "FIVE_6_TO_K": 20, "WILD_ROYAL": 25,
        "STRAIGHT_FLUSH": 10, "FOUR_OAK": 4, "FULL_HOUSE": 3,
        "FLUSH": 3, "STRAIGHT": 1, "THREE_OAK": 1
    }
    
    test_hands = [
        (['2s', '2h', '2c', '3d', '3s'], "Full House / 5OAK"), 
        (['As', 'Ks', 'Qs', 'Js', 'Ts'], "Natural Royal"),
        (['3s', '3h', '3c', '3d', '2s'], "5 of a Kind (Lows)"),
    ]
    
    start = time.time()
    runs = 100
    print(f"🔥 Warming up ({runs} runs)...")
    
    for _ in range(runs):
        for h, label in test_hands:
            bh, ev = solve_hand(h, TEST_TABLE)
            
    elapsed = time.time() - start
    print(f"✅ Completed in {elapsed:.4f}s")
    print(f"⚡ Speed: {runs * len(test_hands) / elapsed:.1f} hands/sec")
    
    # Verify specific Bonus Deuces logic
    print("\n🔍 Logic Verification (Bonus Deuces):")
    
    # Case 1: 5 3s (Should Pay 40)
    h1 = ['3s', '3h', '3c', '3d', '2s']
    fr = [get_rank_int(c) for c in h1]
    fs = [get_suit_int(c) for c in h1]
    pay1 = evaluate_fast(fr, fs, TEST_TABLE)
    print(f"   5 of a Kind (3s): Pay {pay1} [{'✅' if pay1==40 else '❌'}]")

    # Case 2: 5 8s (Should Pay 20)
    h2 = ['8s', '8h', '8c', '8d', '2s']
    fr2 = [get_rank_int(c) for c in h2]
    fs2 = [get_suit_int(c) for c in h2]
    pay2 = evaluate_fast(fr2, fs2, TEST_TABLE)
    print(f"   5 of a Kind (8s): Pay {pay2} [{'✅' if pay2==20 else '❌'}]")