"""
dw_fast_solver.py
High-Performance Logic Engine (v6.0 - Strategy Aware)

Uses the Variant-Specific Strategy Playlists to determine optimal holds instantly.
"""
import dw_strategy_definitions
from dw_strategy_definitions import STRATEGY_MAP

# Map '2'->2 ... 'A'->14 for logic comparisons
RANK_MAP = {r: i for i, r in enumerate("..23456789TJQKA", 0)} 
# Fix: The enum above puts 2 at index 2. Perfect.

def get_rank_int(card_str):
    # 'Th' -> 'T' -> 10
    r = card_str[0]
    if r.isdigit(): return int(r)
    if r == 'T': return 10
    if r == 'J': return 11
    if r == 'Q': return 12
    if r == 'K': return 13
    if r == 'A': return 14
    return 0

def solve_hand(hand, paytable_dict=None):
    """
    Determines the best hold for a given hand.
    
    :param hand: List of strings ['2h', 'Ad', ...]
    :param paytable_dict: (Optional) Used to identify variant name if passed in metadata,
                          or we default to NSUD if simple dict.
    :return: (best_hold_cards, dummy_ev)
             Note: dummy_ev is 0.0 because this is a logic solver.
             The UI calculates real EV using exact_solver if needed.
    """
    # 1. Identify Variant
    # We try to detect the variant from the paytable object if it has a name,
    # otherwise we default to BONUS_DEUCES if the paytable matches its signature,
    # or fallback to NSUD.
    
    variant_name = "NSUD" # Default
    
    # Heuristic: Check specific payouts to guess variant if not explicit
    if paytable_dict:
        if paytable_dict.get("FIVE_ACES") == 80:
            variant_name = "BONUS_DEUCES_10_4"
        elif paytable_dict.get("FIVE_OAK") == 16:
            variant_name = "NSUD"
            
    # 2. Parse Hand
    # Convert ['2h', 'Ad'] to integers for the strategy functions
    ranks = [get_rank_int(c) for c in hand]
    suits = [c[1] for c in hand]
    
    # 3. Get Strategy Playlist
    strategy = STRATEGY_MAP.get(variant_name, STRATEGY_MAP["NSUD"])
    
    # 4. Determine Bucket (Deuce Count)
    num_deuces = ranks.count(2)
    bucket_rules = strategy.get(num_deuces, [])
    
    # 5. Iterate Rules
    for rule_func in bucket_rules:
        held_cards = rule_func(ranks, suits, hand)
        if held_cards is not None:
            # We found our move!
            return held_cards, 0.0 # Return 0.0 EV (UI handles display)
            
    # Fallback (Should never happen if discard_all is in list)
    return [], 0.0