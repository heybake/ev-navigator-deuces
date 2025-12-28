"""
dw_strategy_definitions.py
STRATEGY REGISTRY (Variant-Aware)

Contains the Atomic Rules and Priority Lists for Deuces Wild variants.
Derived from Exact Math CSVs.
"""

# ==============================================================================
# 🧪 ATOMIC RULE FUNCTIONS (The Logic)
# Each function takes (ranks, suits) and returns a list of held cards or None.
# ==============================================================================

def _get_cards(indices, original_hand):
    return [original_hand[i] for i in indices]

def holds_natural_royal(ranks, suits, hand):
    if len(set(suits)) == 1: # Flush
        if set(ranks) == {10, 11, 12, 13, 14}:
            return hand # Hold All
    return None

def holds_4_deuces_ace(ranks, suits, hand):
    if 14 in ranks: # Ace is 14
        return hand
    return None

def holds_4_deuces(ranks, suits, hand):
    deuce_indices = [i for i, r in enumerate(ranks) if r == 2]
    return _get_cards(deuce_indices, hand)

def holds_five_aces(ranks, suits, hand):
    if ranks.count(14) == 4:
        return hand
    return None

def holds_five_3_4_5(ranks, suits, hand):
    non_2 = [r for r in ranks if r != 2]
    if len(non_2) == 4 and len(set(non_2)) == 1:
        if non_2[0] in [3, 4, 5]: return hand
    return None

def holds_five_6_to_k(ranks, suits, hand):
    non_2 = [r for r in ranks if r != 2]
    if len(non_2) == 4 and len(set(non_2)) == 1:
        if 6 <= non_2[0] <= 13: return hand
    return None

def holds_wild_royal(ranks, suits, hand):
    if len(set(suits)) == 1:
        needed = {10, 11, 12, 13, 14}
        current = set(ranks)
        non_2 = current - {2}
        if non_2.issubset(needed): return hand
    return None

def holds_5_of_a_kind(ranks, suits, hand):
    non_2 = [r for r in ranks if r != 2]
    if not non_2: return hand # 5 Deuces covered by 4 deuces logic usually
    counts = {x: non_2.count(x) for x in non_2}
    max_count = max(counts.values())
    if max_count + ranks.count(2) == 5: return hand
    return None

def holds_straight_flush(ranks, suits, hand):
    if len(set(suits)) != 1: return None
    non_2 = sorted([r for r in ranks if r != 2])
    if not non_2: return hand
    span = non_2[-1] - non_2[0]
    # Check Ace Low Wheel A-2-3-4-5
    check_ranks = list(non_2)
    if 14 in check_ranks:
        check_ranks_low = [1 if r==14 else r for r in check_ranks]
        check_ranks_low.sort()
        span_low = check_ranks_low[-1] - check_ranks_low[0]
        if span_low <= 4 and len(set(check_ranks_low)) == len(check_ranks_low): return hand
    
    if span <= 4 and len(set(non_2)) == len(non_2): return hand
    return None

def holds_4_of_a_kind(ranks, suits, hand):
    for r in set(ranks):
        if ranks.count(r) == 4:
            indices = [i for i, x in enumerate(ranks) if x == r]
            return _get_cards(indices, hand)
    return None

def holds_4_to_royal(ranks, suits, hand):
    needed = {10, 11, 12, 13, 14}
    deuces_indices = [i for i, r in enumerate(ranks) if r == 2]
    for s_char in 'shdc':
        suit_indices = [i for i, (r, s) in enumerate(zip(ranks, suits)) if s == s_char and r != 2]
        royal_indices = [i for i in suit_indices if ranks[i] in needed]
        if len(royal_indices) + len(deuces_indices) == 4:
            return _get_cards(royal_indices + deuces_indices, hand)
    return None

def holds_3_deuces(ranks, suits, hand):
    deuce_indices = [i for i, r in enumerate(ranks) if r == 2]
    return _get_cards(deuce_indices, hand)

def holds_full_house(ranks, suits, hand):
    # Only called if 0 or 1 deuce usually
    counts = {r: ranks.count(r) for r in ranks}
    if 2 in counts.values() and 3 in counts.values(): return hand
    return None

def holds_flush(ranks, suits, hand):
    if len(set(suits)) == 1: return hand
    return None

def holds_straight(ranks, suits, hand):
    u_ranks = sorted(list(set(ranks)))
    if len(u_ranks) != 5: return None
    if u_ranks[-1] - u_ranks[0] == 4: return hand
    if u_ranks == [2, 3, 4, 5, 14]: return hand # Wheel
    return None

def holds_3_of_a_kind(ranks, suits, hand):
    non_2 = [r for r in ranks if r != 2]
    counts = {x: non_2.count(x) for x in non_2}
    deuces = [i for i, r in enumerate(ranks) if r == 2]
    for rank, count in counts.items():
        if count + len(deuces) == 3:
            rank_indices = [i for i, r in enumerate(ranks) if r == rank]
            return _get_cards(deuces + rank_indices, hand)
    return None

def holds_3_to_royal(ranks, suits, hand):
    needed = {10, 11, 12, 13, 14}
    deuces_indices = [i for i, r in enumerate(ranks) if r == 2]
    for s_char in 'shdc':
        suit_indices = [i for i, (r, s) in enumerate(zip(ranks, suits)) if s == s_char and r != 2]
        royal_indices = [i for i in suit_indices if ranks[i] in needed]
        if len(royal_indices) + len(deuces_indices) == 3:
            return _get_cards(royal_indices + deuces_indices, hand)
    return None

def holds_any_pair(ranks, suits, hand):
    found_pairs = []
    for r in set(ranks):
        if r == 2: continue
        indices = [i for i, x in enumerate(ranks) if x == r]
        if len(indices) == 2: found_pairs.append(r)
    
    if not found_pairs: return None
    
    # If multiple pairs (Two Pair), we usually hold one. Logic: High Pair > Low Pair?
    # In Deuces, all pairs are roughly equal trash, but higher rank has minor value
    best_rank = found_pairs[0]
    
    # Tie breaker for Two Pair: Priority is usually irrelevant in Deuces (both are "trash"), 
    # but exact math prefers High Pair slightly.
    def pair_value(r):
        if r == 14: return 3
        if r in [3, 4, 5]: return 2
        return 1
        
    if len(found_pairs) > 1:
        found_pairs.sort(key=pair_value, reverse=True)
        best_rank = found_pairs[0]
        
    indices = [i for i, x in enumerate(ranks) if x == best_rank]
    return _get_cards(indices, hand)

def holds_2_to_royal(ranks, suits, hand):
    needed = {10, 11, 12, 13, 14}
    for s_char in 'shdc':
        indices = [i for i, (r, s) in enumerate(zip(ranks, suits)) if s == s_char and r in needed]
        if len(indices) == 2:
            return _get_cards(indices, hand)
    return None

def holds_4_to_straight_flush_conn(ranks, suits, hand):
    # 4 to Straight Flush (Connected, No Gaps is preferred but this checks general range)
    for s_char in 'shdc':
        indices = [i for i, (r, s) in enumerate(zip(ranks, suits)) if s == s_char and r != 2]
        if len(indices) == 4:
            vals = sorted([ranks[i] for i in indices])
            # Check connectedness. 
            # In strict strategy, "Open Ended" vs "Inside" matters.
            # This simplified rule checks span <= 4.
            if vals[-1] - vals[0] <= 4: return _get_cards(indices, hand)
    return None

def holds_2_deuces(ranks, suits, hand):
    deuce_indices = [i for i, r in enumerate(ranks) if r == 2]
    if len(deuce_indices) == 2: return _get_cards(deuce_indices, hand)
    return None

def holds_1_deuce(ranks, suits, hand):
    deuce_indices = [i for i, r in enumerate(ranks) if r == 2]
    if len(deuce_indices) == 1: return _get_cards(deuce_indices, hand)
    return None

def discard_all(ranks, suits, hand):
    return []

# ==============================================================================
# 📋 PRIORITY PLAYLISTS
# ==============================================================================

STRATEGY_BONUS_DEUCES = {
    4: [holds_natural_royal, holds_4_deuces_ace, holds_4_deuces],
    3: [holds_natural_royal, holds_wild_royal, holds_five_aces, holds_five_3_4_5, holds_five_6_to_k, holds_3_deuces],
    2: [holds_natural_royal, holds_wild_royal, holds_five_aces, holds_five_3_4_5, holds_five_6_to_k, holds_straight_flush, holds_4_to_royal, holds_2_deuces],
    1: [
        holds_natural_royal, 
        holds_wild_royal, 
        holds_five_aces, 
        holds_five_3_4_5, 
        holds_five_6_to_k, 
        holds_straight_flush, 
        holds_4_to_royal, 
        holds_full_house, 
        holds_3_of_a_kind, 
        holds_flush, 
        holds_straight, 
        holds_3_to_royal, 
        holds_4_to_straight_flush_conn, 
        holds_1_deuce
    ],
    0: [
        holds_natural_royal, 
        holds_4_to_royal, 
        holds_straight_flush, 
        holds_5_of_a_kind, 
        holds_4_of_a_kind,
        holds_full_house,
        holds_flush,
        holds_straight,
        holds_3_of_a_kind,
        holds_4_to_straight_flush_conn,
        holds_3_to_royal,
        holds_any_pair, 
        holds_2_to_royal,  
        discard_all
    ]
}

STRATEGY_NSUD = {
    4: [holds_4_deuces],
    3: [holds_wild_royal, holds_5_of_a_kind, holds_3_deuces],
    2: [holds_wild_royal, holds_5_of_a_kind, holds_straight_flush, holds_4_to_royal, holds_2_deuces],
    1: [holds_wild_royal, holds_5_of_a_kind, holds_straight_flush, holds_4_to_royal, holds_full_house, holds_3_of_a_kind, holds_flush, holds_straight, holds_3_to_royal, holds_1_deuce],
    0: [
        holds_natural_royal, 
        holds_4_to_royal, 
        holds_straight_flush, 
        holds_4_of_a_kind,
        holds_full_house, 
        holds_flush, 
        holds_straight, 
        holds_3_of_a_kind, 
        holds_4_to_straight_flush_conn, 
        holds_3_to_royal, 
        holds_any_pair, 
        holds_4_to_royal, 
        discard_all
    ]
}

# The Map
STRATEGY_MAP = {
    "NSUD": STRATEGY_NSUD,
    "BONUS_DEUCES_10_4": STRATEGY_BONUS_DEUCES,
    # Fallbacks for other variants can map to NSUD for now
    "AIRPORT": STRATEGY_NSUD, 
    "LOOSE_DEUCES": STRATEGY_NSUD
}

# ==============================================================================
# 🏷️ UI UTILITIES
# ==============================================================================
def get_pretty_name(func_obj):
    """
    Converts 'holds_wild_royal' -> 'WILD ROYAL'
    """
    if not func_obj: return "DISCARD ALL"
    # Get function name
    raw = func_obj.__name__
    # Strip prefix
    clean = raw.replace("holds_", "").replace("_", " ").upper()
    # Manual overrides for clarity
    if "4 TO STRAIGHT FLUSH" in clean: return "4 TO STRAIGHT FLUSH"
    if "3 TO ROYAL" in clean: return "3 TO ROYAL"
    if "5 OF A KIND" in clean: return "5 OF A KIND"
    return clean