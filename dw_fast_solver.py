"""
dw_fast_solver.py
High-Performance Logic Engine (v6.2 - Auto-Detect)

Now features "Paytable Fingerprinting" to ensure the Strategy matches the Machine.
"""
import dw_strategy_definitions
from dw_strategy_definitions import STRATEGY_MAP
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

def _detect_variant(paytable):
    """
    Fingerprints the paytable to select the correct Strategy Playlist.
    """
    if not paytable: return "NSUD"
    
    # SIGNATURE: Bonus Deuces (5 Aces pays 80)
    if paytable.get("FIVE_ACES") == 80:
        return "BONUS_DEUCES_10_4"
    
    # SIGNATURE: Airport / Illinois (5OAK pays 12)
    if paytable.get("FIVE_OAK") == 12:
        return "AIRPORT"
        
    # SIGNATURE: Loose Deuces (4 Deuces pays 500)
    if paytable.get("FOUR_DEUCES") == 500:
        return "LOOSE_DEUCES"
        
    # Default to NSUD
    return "NSUD"

def solve_hand(hand, paytable_dict=None):
    """
    Determines the best hold for a given hand and its EV.
    Auto-detects variant to prevent Strategy Mismatches.
    
    :param hand: List of strings ['2h', 'Ad', ...]
    :param paytable_dict: Used to identify variant and calc EV.
    :return: (best_hold_cards, calculated_ev)
    """
    # 1. Detect Variant from Paytable Signature (ROBUST FIX)
    variant_name = _detect_variant(paytable_dict)
    
    # 2. Load Strategy Playlist
    strategy = STRATEGY_MAP.get(variant_name, STRATEGY_MAP["NSUD"])

    # 3. Parse Hand
    clean_hand = [c[0].upper() + c[1].lower() for c in hand]
    ranks = [get_rank_int(c) for c in clean_hand]
    suits = [c[1] for c in clean_hand]
    
    # 4. Determine Bucket (Deuce Count)
    num_deuces = ranks.count(2)
    bucket_rules = strategy.get(num_deuces, [])
    
    # 5. Iterate Rules (The "Playlist")
    for rule_func in bucket_rules:
        held_cards = rule_func(ranks, suits, clean_hand)
        
        if held_cards is not None:
            # We found the best move according to the Playlist.
            # Now we calculate its exact EV for reporting.
            try:
                # Map held strings back to indices for the exact solver
                hold_indices = []
                temp_hand = list(clean_hand)
                for h_card in held_cards:
                    if h_card in temp_hand:
                        idx = temp_hand.index(h_card)
                        hold_indices.append(idx)
                        temp_hand[idx] = "USED" 
                
                ev = calculate_exact_ev(clean_hand, hold_indices, paytable_dict)
                return held_cards, ev
                
            except Exception:
                return held_cards, 0.0
            
    # Fallback (Discard All)
    # This acts as the "Zero Deuces" bottom catch-all if not defined
    try:
        ev = calculate_exact_ev(clean_hand, [], paytable_dict)
        return [], ev
    except:
        return [], 0.0