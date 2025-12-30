"""
dw_fast_solver.py
High-Performance Logic Engine (v9.0 - Multi-Hold Support)

Features:
- Auto-Detects Variant.
- Returns a list of the top 2 possible holds based on strategy priority.
- Provides Metadata for UI/Trainer feedback.
"""
import dw_strategy_definitions
from dw_strategy_definitions import STRATEGY_MAP
from dw_exact_solver import calculate_exact_ev

# Map '2'->2 ... 'A'->14 for logic comparisons
RANK_MAP = {r: i for i, r in enumerate("..23456789TJQKA", 0)} 

def get_rank_int(card_str):
    r = card_str[0].upper()
    if r.isdigit(): return int(r)
    if r == 'T': return 10
    if r == 'J': return 11
    if r == 'Q': return 12
    if r == 'K': return 13
    if r == 'A': return 14
    return 0

def _detect_variant(paytable):
    if not paytable: return "NSUD"
    if paytable.get("FIVE_ACES") == 80: return "BONUS_DEUCES_10_4"
    if paytable.get("FIVE_OAK") == 12: return "AIRPORT"
    if paytable.get("FOUR_DEUCES") == 500: return "LOOSE_DEUCES"
    return "NSUD"

def solve_hand(hand, paytable_dict=None):
    """
    Exhaustively scans the strategy playlist to find the Best and Runner-Up holds.
    Returns: A list of dicts: [{'held': list, 'ev': float, 'info': dict}, ...]
    """
    variant_name = _detect_variant(paytable_dict)
    strategy = STRATEGY_MAP.get(variant_name, STRATEGY_MAP["NSUD"])

    clean_hand = [c[0].upper() + c[1].lower() for c in hand]
    ranks = [get_rank_int(c) for c in clean_hand]
    suits = [c[1] for c in clean_hand]
    
    num_deuces = ranks.count(2)
    bucket_rules = strategy.get(num_deuces, [])
    
    found_plays = []
    seen_combinations = [] # To ensure unique card sets

    # Iterate through ALL rules in the playlist
    for index, rule_func in enumerate(bucket_rules):
        held_cards = rule_func(ranks, suits, clean_hand)
        
        if held_cards is not None:
            # Check if this set of cards is unique (avoid duplicate holds)
            sorted_hold = sorted(held_cards)
            if sorted_hold not in seen_combinations:
                seen_combinations.append(sorted_hold)
                
                # Calculate EV for this specific hold
                hold_indices = []
                temp_hand = list(clean_hand)
                for h_card in held_cards:
                    if h_card in temp_hand:
                        idx = temp_hand.index(h_card)
                        hold_indices.append(idx)
                        temp_hand[idx] = "USED"
                
                ev = calculate_exact_ev(clean_hand, hold_indices, paytable_dict)
                
                play_data = {
                    "held": held_cards,
                    "ev": ev,
                    "info": {
                        "bucket": num_deuces,
                        "rule_idx": index,
                        "rule_name": dw_strategy_definitions.get_pretty_name(rule_func),
                        "total_rules": len(bucket_rules)
                    }
                }
                found_plays.append(play_data)

        # Stop if we found top 2 to keep speed high
        if len(found_plays) >= 2:
            break

    # If Discard All wasn't reached, evaluate it as a potential Runner-Up
    if len(found_plays) < 2:
        ev_all = calculate_exact_ev(clean_hand, [], paytable_dict)
        if [] not in seen_combinations:
            found_plays.append({
                "held": [],
                "ev": ev_all,
                "info": {"bucket": num_deuces, "rule_idx": 99, "rule_name": "DISCARD ALL"}
            })

    return found_plays

# ==========================================
# 🧪 INDEPENDENT TEST SUITE
# ==========================================
if __name__ == "__main__":
    from dw_pay_constants import PAYTABLES
    
    # Test Case: NSUD variant, Hand with multiple viable holds
    # Hand: 2h, 2s, 4h, Th, Kh (Pat Flush vs 2 Deuces)
    test_hand = ["2h", "2s", "4h", "Th", "Kh"]
    pt = PAYTABLES["NSUD"]
    
    print(f"🕵️  AUDITING SOLVER: {test_hand}")
    results = solve_hand(test_hand, pt)
    
    for i, res in enumerate(results, 1):
        label = "BEST" if i == 1 else "RUNNER-UP"
        h_str = " ".join(res['held']) if res['held'] else "DISCARD ALL"
        print(f"   {label}: {h_str:<15} | EV: {res['ev']:.4f} | Rule: {res['info']['rule_name']}")