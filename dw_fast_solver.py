"""
dw_fast_solver.py
High-Performance Hybrid Solver for Real-Time UI
"""
import random
import itertools
from collections import Counter

# --- FAST EVALUATOR (Integer Based) ---
# Maps '2'->0 ... 'A'->12
RANK_MAP = {r: i for i, r in enumerate("23456789TJQKA")}

def get_rank_int(card_str):
    return RANK_MAP[card_str[0]]

def get_suit_int(card_str):
    return card_str[1] # Keep suit as char 's','h','d','c' is fine

def evaluate_fast(ranks, suits, pay_table):
    """
    Optimized evaluator that takes pre-processed lists of ranks and suits.
    """
    # 1. FLUSH CHECK
    # In Deuces Wild, a flush is valid if all NON-DEUCE cards have same suit.
    # But wild cards assume that suit. So effectively, if unique suits <= 1
    # (ignoring deuces? No, usually we check all suits. 
    # If I have 2s(Wild) 2h(Wild) 4d 5d 6d -> It's a diamond flush.)
    # FASTEST WAY: Check if len(set(suits of non-wilds)) <= 1
    
    # Identify Deuces
    deuce_count = ranks.count(0) # 0 is '2'
    
    # Filter Non-Deuces
    non_deuces = [r for r in ranks if r != 0]
    non_deuce_suits = [s for r, s in zip(ranks, suits) if r != 0]
    
    is_flush = len(set(non_deuce_suits)) <= 1
    
    # 2. ROYAL / STRAIGHT FLUSH
    if is_flush:
        if not non_deuces: # 5 Deuces -> Natural Royal logic in some games, usually 5OAK
             pass # Will be caught by 5OAK check
        else:
            # Check Royal
            # Natural Royal: No deuces, A-K-Q-J-T
            if deuce_count == 0 and set(non_deuces) == {8,9,10,11,12}:
                return pay_table.get("NATURAL_ROYAL", 800)
            
            # Wild Royal
            # Union of non_deuces + deuces must be able to form T,J,Q,K,A
            # Simply: All non-deuces must be >= 8 (Ten) and unique
            # actually checking distinct count is better
            if all(r >= 8 for r in non_deuces):
                 # Check for duplicates? A Wild Royal implies unique ranks usually?
                 # Actually, standard Wild Royal just needs to look like one.
                 # If I have T T 2 2 2 -> T T T T A (5OAK). Not Royal.
                 # So yes, non_deuces must be unique for a Straight/Royal
                 if len(set(non_deuces)) == len(non_deuces):
                     return pay_table.get("WILD_ROYAL", 25)
            
            # Straight Flush
            # Ranks must span <= 4.
            # Convert non_deuces to sorted unique
            uniq = sorted(list(set(non_deuces)))
            if not uniq:
                pass
            else:
                span = uniq[-1] - uniq[0]
                if span <= 4:
                    return pay_table.get("STRAIGHT_FLUSH", 9)
                # Wheel Check (A,2,3,4,5) -> A=12. 
                # In DW, A-2-3-4-5 is a SF. 
                # non_deuces would be {12, 1, 2, 3} (if 2 wasn't wild).
                # Since 2 is wild, non_deuces are {12, 1, 2, 3} -> {12, 1, 2, 3}.
                # Actually, A is 12. 3 is 1. 4 is 2. 5 is 3.
                # Wheel ranks in 0-12 system: 12 (A), 1 (3), 2 (4), 3 (5). 
                # 0 is 2 (Wild).
                # If we have A(12), 3(1), 4(2).
                if 12 in uniq:
                    wheel_uniq = sorted([(-1 if r == 12 else r) for r in uniq])
                    w_span = wheel_uniq[-1] - wheel_uniq[0]
                    if w_span <= 4:
                        return pay_table.get("STRAIGHT_FLUSH", 9)

    # 3. N-OF-A-KIND
    # Count duplicates
    # Most common rank count + deuces
    if non_deuces:
        counts = Counter(non_deuces)
        most_common_count = counts.most_common(1)[0][1]
        total_oak = most_common_count + deuce_count
    else:
        total_oak = 5 # 5 Deuces
    
    # 4 DEUCES
    if deuce_count == 4:
        # Bonus Logic
        if "FOUR_DEUCES_ACE" in pay_table and non_deuces and non_deuces[0] == 12: # Ace
             return pay_table["FOUR_DEUCES_ACE"]
        return pay_table.get("FOUR_DEUCES", 200)

    if total_oak >= 5:
        # Bonus Logic for 5 Aces
        if "FIVE_ACES" in pay_table and non_deuces and all(r == 12 for r in non_deuces):
            return pay_table["FIVE_ACES"]
        return pay_table.get("FIVE_OAK", 15)
    
    if total_oak == 4:
        return pay_table.get("FOUR_OAK", 4)
    
    if total_oak == 3:
        # Full House check
        # To have FH with Wilds:
        # 2 Wilds: 2W + 1X + 1Y + 1Z -> 3OAK.
        # 1 Wild: 1W + 2X + 2Y -> Full House. 
        # 0 Wild: 3X + 2Y -> FH.
        is_fh = False
        if deuce_count == 0:
            if len(counts) == 2 and 3 in counts.values(): is_fh = True
        elif deuce_count == 1:
            if len(counts) == 2 and list(counts.values()) == [2, 2]: is_fh = True
        
        if is_fh: return pay_table.get("FULL_HOUSE", 4)
        # Else it's just 3OAK (checked at end)

    # FLUSH (Rank independent)
    if is_flush:
        return pay_table.get("FLUSH", 2) # Low pay in DW

    # STRAIGHT (Non-Flush)
    uniq = sorted(list(set(non_deuces)))
    if len(uniq) + deuce_count >= 5:
        # Standard Straight
        if uniq:
            span = uniq[-1] - uniq[0]
            # We need to fill (span - 1) gaps.
            # Distinct count = len(uniq). 
            # We need 5 total.
            # We need to cover the span.
            # Valid if: span <= 4 AND deuces >= (gaps)
            # gaps = (span + 1) - distinct_count
            if span <= 4 and deuce_count >= (5 - len(uniq)): # Simpler logic
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
            
            # DECISION: EXACT vs MONTE CARLO
            # If we hold 3, 4, or 5 cards, the tree is small -> Do Exact.
            # If we hold 0, 1, or 2 cards, the tree is huge -> Do Monte Carlo.
            
            current_total_pay = 0.0
            iterations = 0
            
            num_to_draw = 5 - k
            
            if num_to_draw <= 2: 
                # -- EXACT MODE -- (Draw 0, 1, 2)
                # Max 1081 iterations (Draw 2)
                for draw in itertools.combinations(remaining_deck, num_to_draw):
                    final_hand = held_cards + list(draw)
                    # Convert to fast ints
                    fr = [get_rank_int(c) for c in final_hand]
                    fs = [c[1] for c in final_hand]
                    current_total_pay += evaluate_fast(fr, fs, pay_table)
                    iterations += 1
                ev = current_total_pay / iterations
                
            else:
                # -- MONTE CARLO MODE -- (Draw 3, 4, 5)
                # Drawing 3 = 16k outcomes. Drawing 5 = 1.5M outcomes.
                # We sample 2500 times.
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
                
    return best_hold