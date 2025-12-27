"""
dw_fast_solver.py
High-Performance Logic Engine (v6.1 - Hybrid)

Uses Variant-Specific Strategy Playlists to determine optimal holds instantly,
then uses the Exact Solver to calculate the precise EV for that hold.
"""
import dw_strategy_definitions
from dw_strategy_definitions import STRATEGY_MAP

# We need the math engine to calculate the Score (EV) of the chosen move.
from dw_exact_solver import calculate_exact_ev

# Map '2'->2 ... 'A'->14 for logic comparisons
RANK_MAP = {r: i for i, r in enumerate("..23456789TJQKA", 0)} 

def get_rank_int(card_str):
    # 'Th' -> 'T' -> 10
    r = card_str[0].upper()
    if r.isdigit(): return int(r)
    if r == 'T': return 10
    if r == 'J': return 11
    if r == 'Q': return 12
    if r == 'K': return 13
    if r == 'A': return 14
    return 0

def solve_hand(hand, paytable_dict=None):
    """
    Determines the best hold for a given hand and its EV.
    
    :param hand: List of strings ['2h', 'Ad', ...]
    :param paytable_dict: Used to identify variant and calc EV.
    :return: (best_hold_cards, calculated_ev)
    """
    # 1. Identify Variant
    variant_name = "NSUD" # Default
    if paytable_dict:
        # Heuristic to switch to Bonus Deuces logic if paytable matches
        if paytable_dict.get("FIVE_ACES") == 80:
            variant_name = "BONUS_DEUCES_10_4"
        elif paytable_dict.get("FIVE_OAK") == 16:
            variant_name = "NSUD"
            
    # 2. Parse Hand (Normalize first)
    # Ensure standard format for logic comparisons
    clean_hand = [c[0].upper() + c[1].lower() for c in hand]
    ranks = [get_rank_int(c) for c in clean_hand]
    suits = [c[1] for c in clean_hand]
    
    # 3. Get Strategy Playlist
    strategy = STRATEGY_MAP.get(variant_name, STRATEGY_MAP["NSUD"])
    
    # 4. Determine Bucket (Deuce Count)
    num_deuces = ranks.count(2)
    bucket_rules = strategy.get(num_deuces, [])
    
    # 5. Iterate Rules
    for rule_func in bucket_rules:
        held_cards = rule_func(ranks, suits, clean_hand)
        
        if held_cards is not None:
            # --- CRITICAL FIX: Calculate Real EV ---
            # We found the best move. Now we calculate its EV so the
            # Tests pass and the Logger has data.
            try:
                # Map held strings back to indices for the exact solver
                hold_indices = []
                temp_hand = list(clean_hand)
                for h_card in held_cards:
                    if h_card in temp_hand:
                        idx = temp_hand.index(h_card)
                        hold_indices.append(idx)
                        # Mask to handle duplicates (e.g. 2s, 2s in custom decks)
                        temp_hand[idx] = "USED" 
                
                ev = calculate_exact_ev(clean_hand, hold_indices, paytable_dict)
                return held_cards, ev
                
            except Exception:
                # Fallback if math fails (should not happen with verified solver)
                return held_cards, 0.0
            
    # Fallback (Discard All)
    # Calculate EV of drawing 5 new cards
    try:
        ev = calculate_exact_ev(clean_hand, [], paytable_dict)
        return [], ev
    except:
        return [], 0.0