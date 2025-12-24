"""
dw_exact_solver.py
THE MATHEMATICAL BRAIN (v5.1 - Patch)

Features:
- Exact Expected Value (EV) calculation.
- Supports Bonus Deuces (5 Aces, 4 Deuces w/ Ace).
- FIXED: Case-Insensitive Inputs.
- FIXED: Wild Flush Logic (Deuces ignore suit).
"""

from itertools import combinations
from collections import Counter
from dw_pay_constants import PAYTABLES

def get_rank_index(rank_char):
    # Ensure rank is found regardless of case, though we normalize before calling.
    return "23456789TJQKA".index(rank_char.upper())

def get_deck():
    ranks = "23456789TJQKA"
    suits = "shdc"
    return [r+s for r in ranks for s in suits]

def evaluate_hand(hand, pay_table):
    """
    Evaluates a 5-card hand against the paytable.
    Includes Bonus Deuces logic (Kickers).
    """
    # -------------------------------------------------------
    # 0. NORMALIZE INPUTS (Fixes Case Sensitivity Crash)
    # -------------------------------------------------------
    # Force ranks to Upper, suits to lower.
    # Handles inputs like 'ts', 'Ah', '2C'
    clean_hand = [(c[0].upper(), c[1].lower()) for c in hand]
    
    ranks = [c[0] for c in clean_hand]
    suits = [c[1] for c in clean_hand]
    deuce_count = ranks.count('2')
    non_deuces = [r for r in ranks if r != '2']
    
    # -------------------------------------------------------
    # 0. FLUSH LOGIC (Fixes Wild Flush Bug)
    # -------------------------------------------------------
    # A flush exists if all NON-DEUCE cards share the same suit.
    # The deuces simply adopt that suit.
    non_deuce_suits = [c[1] for c in clean_hand if c[0] != '2']
    if not non_deuce_suits:
        is_flush = True # 5 Deuces is technically suited (doesn't matter, pays 5OAK/4Deuces)
    else:
        is_flush = len(set(non_deuce_suits)) == 1

    # -------------------------------------------------------
    # 1. NATURAL ROYAL FLUSH
    # -------------------------------------------------------
    # Must be 0 deuces and "Natural" flush (all actual suits match)
    # Re-check suits including deuces for Natural Royal requirement
    is_natural_suited = len(set(suits)) == 1
    
    if deuce_count == 0 and is_natural_suited:
        if set(ranks) == set("TJQKA"):
            return pay_table["NATURAL_ROYAL"]

    # -------------------------------------------------------
    # 2. FOUR DEUCES (Check Kicker)
    # -------------------------------------------------------
    if deuce_count == 4:
        if non_deuces and non_deuces[0] == 'A':
            if "FOUR_DEUCES_ACE" in pay_table:
                return pay_table["FOUR_DEUCES_ACE"]
        return pay_table["FOUR_DEUCES"]

    # -------------------------------------------------------
    # 3. WILD ROYAL FLUSH
    # -------------------------------------------------------
    if is_flush:
        if all(r in set("TJQKA") for r in non_deuces):
            return pay_table["WILD_ROYAL"]

    # -------------------------------------------------------
    # 4. FIVE OF A KIND (Check 5 Aces)
    # -------------------------------------------------------
    if non_deuces:
        counts = Counter(non_deuces)
        most_common_rank, count = counts.most_common(1)[0]
        total_count = count + deuce_count
    else:
        total_count = deuce_count

    if total_count >= 5:
        if non_deuces and all(r == 'A' for r in non_deuces):
             if "FIVE_ACES" in pay_table:
                return pay_table["FIVE_ACES"]
        return pay_table["FIVE_OAK"]

    # -------------------------------------------------------
    # 5. STRAIGHT FLUSH
    # -------------------------------------------------------
    if is_flush:
        idx_ranks = sorted([get_rank_index(r) for r in non_deuces])
        if not idx_ranks:
            pass 
        else:
            span = idx_ranks[-1] - idx_ranks[0]
            distinct_count = len(set(idx_ranks))
            valid_sf = False
            
            if span <= 4 and deuce_count >= (span + 1 - distinct_count):
                valid_sf = True
            
            if 12 in idx_ranks and not valid_sf:
                wheel_ranks = sorted([-1 if r == 12 else r for r in idx_ranks])
                w_span = wheel_ranks[-1] - wheel_ranks[0]
                if w_span <= 4 and deuce_count >= (w_span + 1 - distinct_count):
                    valid_sf = True
                    
            if valid_sf:
                return pay_table["STRAIGHT_FLUSH"]

    # -------------------------------------------------------
    # 6. FOUR OF A KIND
    # -------------------------------------------------------
    if total_count >= 4:
        return pay_table["FOUR_OAK"]

    # -------------------------------------------------------
    # 7. FULL HOUSE
    # -------------------------------------------------------
    is_full_house = False
    if deuce_count == 0:
        counts = Counter(non_deuces)
        if len(counts) == 2 and 3 in counts.values(): is_full_house = True
    elif deuce_count == 1:
        counts = Counter(non_deuces)
        if len(counts) == 2 and list(counts.values()) == [2, 2]: is_full_house = True
            
    if is_full_house:
        return pay_table["FULL_HOUSE"]

    # -------------------------------------------------------
    # 8. FLUSH
    # -------------------------------------------------------
    if is_flush:
        return pay_table["FLUSH"]

    # -------------------------------------------------------
    # 9. STRAIGHT
    # -------------------------------------------------------
    idx_ranks = sorted([get_rank_index(r) for r in non_deuces])
    distinct_ranks = sorted(list(set(idx_ranks)))
    span = distinct_ranks[-1] - distinct_ranks[0] if distinct_ranks else 0
    distinct_count = len(distinct_ranks)
    
    valid_straight = False
    if span <= 4 and deuce_count >= (5 - distinct_count):
         valid_straight = True
         
    if 12 in distinct_ranks and not valid_straight:
         wheel_ranks = sorted([-1 if r == 12 else r for r in distinct_ranks])
         w_span = wheel_ranks[-1] - wheel_ranks[0]
         if w_span <= 4 and deuce_count >= (5 - distinct_count):
             valid_straight = True
             
    if valid_straight:
        return pay_table["STRAIGHT"]

    # -------------------------------------------------------
    # 10. THREE OF A KIND
    # -------------------------------------------------------
    if total_count >= 3:
        return pay_table["THREE_OAK"]

    return 0

# ==========================================
# 🧠 EXACT EV ENGINE
# ==========================================

def calculate_ev_for_hold(hand, hold, pay_table):
    deck = get_deck()
    remaining_deck = [c for c in deck if c not in hand]
    
    draw_count = 5 - len(hold)
    
    if draw_count == 0:
        return evaluate_hand(hold, pay_table) * 5
    
    total_payout = 0
    possible_draws = list(combinations(remaining_deck, draw_count))
    
    for draw in possible_draws:
        final_hand = list(hold) + list(draw)
        total_payout += evaluate_hand(final_hand, pay_table) * 5
        
    return total_payout / len(possible_draws)

def calculate_exact_ev(hand, hold_indices, pay_table):
    # Wrapper for Unit Tests
    hold = [hand[i] for i in hold_indices]
    return calculate_ev_for_hold(hand, hold, pay_table)

def solve_hand_silent(hand, pay_table):
    max_ev = -1.0
    best_hold = []
    
    for i in range(len(hand) + 1):
        for hold in combinations(hand, i):
            current_ev = calculate_ev_for_hold(hand, hold, pay_table)
            if current_ev > max_ev:
                max_ev = current_ev
                best_hold = list(hold)
                
    return best_hold, max_ev

def solve_hand(hand, pay_table):
    best_hold, max_ev = solve_hand_silent(hand, pay_table)
    print(f"Hand: {hand}")
    print(f"Best Hold: {best_hold}")
    print(f"Max EV: {max_ev:.4f}")
    return best_hold, max_ev