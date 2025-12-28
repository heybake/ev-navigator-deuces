import itertools
import random
from collections import Counter
from dw_pay_constants import PAYTABLES

# ==============================================================================
# 🧮 DEUCES WILD EXACT SOLVER (HYBRID ENGINE)
# ==============================================================================
# Features "Turbo Mode" for heavy draws using Monte Carlo
# and Robust Input Normalization to prevent crashes.

COINS_PER_HAND = 5  # Standard Max Bet for EV calculations

def evaluate_hand(hand, paytable):
    """
    Evaluates a 5-card hand and returns the payout (multiplied by coins).
    """
    # 1. Normalize Input
    hand = [c[0].upper() + c[1].lower() for c in hand]
    
    # 2. Parse Hand
    ranks = [c[0] for c in hand]
    suits = [c[1] for c in hand]
    
    # 3. Count Deuces
    num_deuces = ranks.count('2')
    
    base_payout = 0

    # 4. Handle Natural Royal (No Deuces)
    if num_deuces == 0:
        is_flush = len(set(suits)) == 1
        rank_vals = sorted(["23456789TJQKA".index(r) for r in ranks])
        # A-2-3-4-5 Straight Check
        if set(rank_vals) == {0, 1, 2, 3, 12}: 
             is_straight = True
        else:
             is_straight = (rank_vals[-1] - rank_vals[0] == 4) and (len(set(rank_vals)) == 5)
             
        if is_flush and is_straight:
            if rank_vals[0] == 8: # 10, J, Q, K, A
                base_payout = paytable["NATURAL_ROYAL"]
            else:
                base_payout = paytable["STRAIGHT_FLUSH"]
        elif num_deuces == 0 and ranks.count(ranks[0]) == 4:
             pass # Fallthrough to robust

    # 5. Histogram Logic (Handles Wilds)
    if base_payout == 0:
        non_deuces = [r for r in ranks if r != '2']
        counts = Counter(non_deuces)
        most_common = counts.most_common(1)
        max_count = most_common[0][1] if non_deuces else 0
        total_count = max_count + num_deuces
        
    # FIVE OF A KIND
        if total_count == 5:
            if num_deuces == 4:
                if "FOUR_DEUCES_ACE" in paytable and 'A' in non_deuces:
                    base_payout = paytable["FOUR_DEUCES_ACE"]
                else:
                    base_payout = paytable["FOUR_DEUCES"]
            else:
                # NEW ROBUST LOGIC: Check Rank First, Then Paytable
                # We know most_common exists because total_count=5 and num_deuces<4
                five_oak_rank = most_common[0][0] 

                # Tier 1: Aces
                if five_oak_rank == 'A' and "FIVE_ACES" in paytable:
                    base_payout = paytable["FIVE_ACES"]
                # Tier 2: 3s, 4s, 5s
                elif five_oak_rank in ['3', '4', '5'] and "FIVE_3_4_5" in paytable:
                    base_payout = paytable["FIVE_3_4_5"]
                # Tier 3: 6 through King
                elif five_oak_rank in ['6', '7', '8', '9', 'T', 'J', 'Q', 'K'] and "FIVE_6_TO_K" in paytable:
                    base_payout = paytable["FIVE_6_TO_K"]
                # Fallback: Generic 5OAK
                else:
                    base_payout = paytable.get("FIVE_OAK", 15)

        # Fallback Robust Evaluator
        if base_payout == 0:
            non_deuce_suits = [c[1] for c in hand if c[0] != '2']
            is_flush = len(set(non_deuce_suits)) <= 1
            vals = [ "23456789TJQKA".index(r) for r in non_deuces ]
            
            is_straight = False
            if not vals: is_straight = True
            else:
                unique_vals = sorted(list(set(vals)))
                if len(vals) == len(unique_vals):
                     if (unique_vals[-1] - unique_vals[0]) <= 4: is_straight = True
                     if 12 in unique_vals: # Ace Low
                         low_vals = [v if v!=12 else -1 for v in unique_vals]
                         low_vals.sort()
                         if (low_vals[-1] - low_vals[0]) <= 4: is_straight = True

            if is_flush and is_straight:
                if num_deuces > 0: base_payout = paytable["WILD_ROYAL"]
                else: base_payout = paytable["STRAIGHT_FLUSH"]
            elif total_count == 4:
                base_payout = paytable["FOUR_OAK"]
            elif total_count == 3:
                # Full House
                if num_deuces == 0 and len(counts) == 2: base_payout = paytable["FULL_HOUSE"]
                elif num_deuces == 1 and len(counts) == 2: base_payout = paytable["FULL_HOUSE"]
                elif total_count == 3: pass # Wait, drop to flush/straight check first
            
            if base_payout == 0:
                if is_flush: base_payout = paytable["FLUSH"]
                elif is_straight: base_payout = paytable["STRAIGHT"]
                elif total_count == 3: base_payout = paytable["THREE_OAK"]

    return base_payout * COINS_PER_HAND

def calculate_exact_ev(hand, hold_indices, paytable):
    deck = [r+s for r in "23456789TJQKA" for s in "shdc"]
    norm_hand = [c[0].upper() + c[1].lower() for c in hand]
    held_cards = [norm_hand[i] for i in hold_indices]
    stub = [c for c in deck if c not in norm_hand]
    num_to_draw = 5 - len(held_cards)
    
    if num_to_draw >= 4:
        SAMPLE_SIZE = 5000 if num_to_draw == 4 else 15000
        total_payout = 0
        for _ in range(SAMPLE_SIZE):
            drawn = random.sample(stub, num_to_draw)
            final_hand = held_cards + drawn
            total_payout += evaluate_hand(final_hand, paytable)
        return total_payout / SAMPLE_SIZE
    else:
        total_payout = 0
        count = 0
        for drawn in itertools.combinations(stub, num_to_draw):
            final_hand = held_cards + list(drawn)
            total_payout += evaluate_hand(final_hand, paytable)
            count += 1
        return total_payout / count if count > 0 else 0.0

def solve_hand_silent(hand, paytable):
    best_ev = -1; best_hold = []
    norm_hand = [c[0].upper() + c[1].lower() for c in hand]
    for i in range(32):
        hold_idx = []
        for j in range(5):
            if (i >> j) & 1: hold_idx.append(j)
        ev = calculate_exact_ev(norm_hand, hold_idx, paytable)
        if ev > best_ev:
            best_ev = ev; best_hold = [hand[k] for k in hold_idx]
    return best_hold, best_ev