"""
dw_strategy_definitions.py
STRATEGY REGISTRY (Variant-Aware)

Contains the Atomic Rules and Priority Lists for Deuces Wild variants.
Derived from Exact Math CSVs via dw_strategy_compiler.py
"""

import itertools

# ==============================================================================
# 🧠 HELPER FUNCTIONS (ROBUST PAT HAND & DRAW DETECTION)
# ==============================================================================

def _get_cards(indices, hand):
    return [hand[i] for i in indices]

# --- 1. PAT HAND DETECTORS (Wild Aware & Subset Friendly) ---

def holds_natural_royal(ranks, suits, hand):
    if 2 in ranks: return None
    if len(set(suits)) == 1 and set(ranks) == {10, 11, 12, 13, 14}:
        return hand
    return None

def holds_wild_royal(ranks, suits, hand):
    deuce_indices = [i for i, r in enumerate(ranks) if r == 2]
    natural_indices = [i for i, r in enumerate(ranks) if r != 2]
    
    if natural_indices:
        first_suit = suits[natural_indices[0]]
        if any(suits[i] != first_suit for i in natural_indices): return None
        if any(ranks[i] < 10 for i in natural_indices): return None
            
    return hand

def holds_five_of_a_kind(ranks, suits, hand):
    non_deuces = [r for r in ranks if r != 2]
    if len(set(non_deuces)) <= 1:
        return hand
    return None

def holds_five_aces(ranks, suits, hand):
    if holds_five_of_a_kind(ranks, suits, hand):
        non_deuces = [r for r in ranks if r != 2]
        if not non_deuces or non_deuces[0] == 14: return hand
    return None

def holds_five_3_4_5(ranks, suits, hand):
    if holds_five_of_a_kind(ranks, suits, hand):
        non_deuces = [r for r in ranks if r != 2]
        if non_deuces and non_deuces[0] in [3, 4, 5]: return hand
    return None

def holds_five_6_to_k(ranks, suits, hand):
    if holds_five_of_a_kind(ranks, suits, hand):
        non_deuces = [r for r in ranks if r != 2]
        if non_deuces and 6 <= non_deuces[0] <= 13: return hand
    return None

def holds_straight_flush(ranks, suits, hand):
    deuce_indices = [i for i, r in enumerate(ranks) if r == 2]
    natural_indices = [i for i, r in enumerate(ranks) if r != 2]
    
    if natural_indices:
        first_suit = suits[natural_indices[0]]
        if any(suits[i] != first_suit for i in natural_indices): return None
            
    if not natural_indices: return hand 
    natural_ranks = sorted([ranks[i] for i in natural_indices])
    
    # Check standard span
    if (natural_ranks[-1] - natural_ranks[0]) <= 4:
        if len(set(natural_ranks)) == len(natural_ranks): return hand
    
    # Check wheel span (A-2-3-4-5) where A=14 becomes 1
    if 14 in natural_ranks:
        wheel_ranks = sorted([1 if r == 14 else r for r in natural_ranks])
        if (wheel_ranks[-1] - wheel_ranks[0]) <= 4:
            if len(set(wheel_ranks)) == len(wheel_ranks): return hand
    return None

def _holds_wild_sf_3_strict(ranks, suits, hand):
    """
    Special strict detector for 3-card Wild Straight Flushes (1 Deuce + 2 Naturals).
    Enforces TIGHT connectivity (Span <= 2) to avoid holding garbage like 4-8-2.
    """
    # 1. Must be exactly 3 cards
    if len(ranks) != 3: return None
    
    # 2. Must be 1 Deuce + 2 Naturals
    deuces = ranks.count(2)
    if deuces != 1: return None
    
    natural_indices = [i for i, r in enumerate(ranks) if r != 2]
    
    # 3. Naturals Must be Suited
    s1 = suits[natural_indices[0]]
    s2 = suits[natural_indices[1]]
    if s1 != s2: return None
    
    # 4. Check Connectivity (The "Span" Test)
    r1 = ranks[natural_indices[0]]
    r2 = ranks[natural_indices[1]]
    
    low, high = sorted((r1, r2))
    
    # Standard Span
    span = high - low
    
    # Wheel Case (Ace = 14)
    if high == 14:
        # If low is 3, 4, 5... Ace connects as 1.
        # But if low is K, Q... Ace connects as 14.
        if low <= 5: # Wheel attempt
            span = low - 1 # (e.g. 3 - 1 = 2)
    
    # CRITICAL FIX: Only allow span <= 2 (Connected or 1 Gap)
    # 6,7 (Span 1) -> OK
    # 6,8 (Span 2) -> OK
    # 6,9 (Span 3) -> REJECT (Hold Deuce Only)
    if span <= 2:
        return hand
        
    return None

def holds_straight(ranks, suits, hand):
    natural_indices = [i for i, r in enumerate(ranks) if r != 2]
    if not natural_indices: return hand

    natural_ranks = sorted([ranks[i] for i in natural_indices])
    
    if (natural_ranks[-1] - natural_ranks[0]) <= 4:
        if len(set(natural_ranks)) == len(natural_ranks): return hand
    if 14 in natural_ranks:
        wheel_ranks = sorted([1 if r == 14 else r for r in natural_ranks])
        if (wheel_ranks[-1] - wheel_ranks[0]) <= 4:
            if len(set(wheel_ranks)) == len(wheel_ranks): return hand
    return None

def holds_flush(ranks, suits, hand):
    natural_indices = [i for i, r in enumerate(ranks) if r != 2]
    if not natural_indices: return hand
    first_suit = suits[natural_indices[0]]
    if any(suits[i] != first_suit for i in natural_indices): return None
    return hand

def holds_full_house(ranks, suits, hand):
    if len(ranks) != 5: return None 
    num_deuces = ranks.count(2)
    non_deuces = [r for r in ranks if r != 2]
    counts = {r: non_deuces.count(r) for r in set(non_deuces)}
    
    if num_deuces == 0:
        return hand if sorted(counts.values()) == [2, 3] else None
    elif num_deuces == 1:
        return hand if sorted(counts.values()) == [2, 2] else None
    return None

# --- 2. DEUCE COUNTERS ---

def holds_4_deuces_ace(ranks, suits, hand):
    if ranks.count(2) == 4 and 14 in ranks: return hand
    return None

def holds_4_deuces(ranks, suits, hand):
    if ranks.count(2) == 4:
        return [c for c in hand if c[0] in ['2', '1', 2]] 
    return None

def holds_3_deuces(ranks, suits, hand):
    if ranks.count(2) == 3:
        return [hand[i] for i, r in enumerate(ranks) if r == 2]
    return None

def holds_2_deuces(ranks, suits, hand):
    if ranks.count(2) == 2:
        return [hand[i] for i, r in enumerate(ranks) if r == 2]
    return None

def holds_1_deuce(ranks, suits, hand):
    if ranks.count(2) == 1:
        return [hand[i] for i, r in enumerate(ranks) if r == 2]
    return None

# --- 3. DRAW LOGIC ---

def _find_best_subset_by_rule(ranks, suits, hand, rule_func, target_len):
    indices = range(5)
    for combo in itertools.combinations(indices, target_len):
        sub_ranks = [ranks[i] for i in combo]
        sub_suits = [suits[i] for i in combo]
        sub_hand = [hand[i] for i in combo]
        if rule_func(sub_ranks, sub_suits, sub_hand):
            return sub_hand
    return None

def holds_4_to_royal(ranks, suits, hand):
    return _find_best_subset_by_rule(ranks, suits, hand, holds_wild_royal, 4)

def holds_3_to_royal(ranks, suits, hand):
    return _find_best_subset_by_rule(ranks, suits, hand, holds_wild_royal, 3)

def holds_2_to_royal(ranks, suits, hand):
    return _find_best_subset_by_rule(ranks, suits, hand, holds_wild_royal, 2)

def holds_4_to_straight_flush_conn(ranks, suits, hand):
    return _find_best_subset_by_rule(ranks, suits, hand, holds_straight_flush, 4)

def holds_3_to_straight_flush_conn(ranks, suits, hand):
    return _find_best_subset_by_rule(ranks, suits, hand, holds_straight_flush, 3)

def holds_3_to_straight_flush_conn_strict(ranks, suits, hand):
    """
    STRICT VERSION for NSUD/AIRPORT: Rejects gaps > 1 (e.g. 4-8-W).
    """
    return _find_best_subset_by_rule(ranks, suits, hand, _holds_wild_sf_3_strict, 3)

def holds_4_to_flush(ranks, suits, hand):
    return _find_best_subset_by_rule(ranks, suits, hand, holds_flush, 4)

def holds_4_to_straight(ranks, suits, hand):
    return _find_best_subset_by_rule(ranks, suits, hand, holds_straight, 4)

def holds_four_of_a_kind(ranks, suits, hand):
    return _find_best_subset_by_rule(ranks, suits, hand, holds_five_of_a_kind, 4)

def holds_3_of_a_kind(ranks, suits, hand):
    return _find_best_subset_by_rule(ranks, suits, hand, holds_five_of_a_kind, 3)

def holds_any_pair(ranks, suits, hand):
    non_deuces = [r for r in ranks if r != 2]
    counts = {r: non_deuces.count(r) for r in set(non_deuces)}
    pairs = [r for r, c in counts.items() if c >= 2]
    if pairs:
        target_rank = max(pairs) 
        return [hand[i] for i, r in enumerate(ranks) if r == target_rank]
    return None

def holds_one_ace(ranks, suits, hand):
    if 14 in ranks:
        for i, r in enumerate(ranks):
            if r == 14: return [hand[i]]
    return None

def discard_all(ranks, suits, hand):
    return []


# ==============================================================================
# 📋 STRATEGY PLAYLISTS (FINAL CORRECTED)
# ==============================================================================

# >>>> STRATEGY_NSUD
STRATEGY_NSUD = {
    4: [holds_natural_royal, holds_4_deuces],
    3: [
        holds_wild_royal, 
        holds_five_of_a_kind,   # 5OAK > 3 Deuces in NSUD
        holds_3_deuces
    ],
    2: [holds_wild_royal, holds_five_of_a_kind, holds_straight_flush, holds_4_to_royal, holds_4_to_straight_flush_conn, holds_2_deuces],
    1: [
        holds_wild_royal, holds_five_of_a_kind, holds_straight_flush, 
        holds_4_to_royal, holds_full_house, 
        holds_4_to_straight_flush_conn, 
        holds_four_of_a_kind,
        holds_flush, holds_straight, holds_3_of_a_kind, 
        holds_3_to_royal, 
        # UPDATED: Use STRICT version for NSUD
        holds_3_to_straight_flush_conn_strict, 
        holds_1_deuce
    ],
    0: [
        holds_natural_royal, holds_4_to_royal, holds_straight_flush, 
        holds_4_to_straight_flush_conn, holds_3_to_royal, holds_full_house, 
        holds_flush, holds_straight, holds_3_of_a_kind, holds_4_to_flush, 
        holds_any_pair, holds_4_to_straight, 
        discard_all
    ],
}

# >>>> STRATEGY_BONUS_DEUCES_10_4
STRATEGY_BONUS_DEUCES_10_4 = {
    4: [holds_4_deuces_ace, holds_4_deuces],
    3: [holds_five_aces, holds_five_3_4_5, holds_wild_royal, holds_five_6_to_k, holds_3_deuces],
    2: [holds_five_aces, holds_five_3_4_5, holds_wild_royal, holds_five_6_to_k, holds_straight_flush, holds_4_to_royal, holds_4_to_straight_flush_conn, holds_2_deuces],
    1: [
        holds_five_aces, holds_five_3_4_5, holds_wild_royal, holds_five_6_to_k, 
        holds_straight_flush, holds_4_to_royal, holds_full_house, 
        holds_4_to_straight_flush_conn, 
        holds_four_of_a_kind,
        holds_flush,
        holds_3_of_a_kind,
        # Note: Bonus Deuces is generally looser, but can use strict if needed. 
        # Keeping standard for now unless testing proves otherwise.
        holds_3_to_straight_flush_conn, 
        holds_straight,
        holds_1_deuce,
        holds_3_to_royal
    ],
    0: [
        holds_natural_royal, holds_4_to_royal, holds_straight_flush, 
        holds_4_to_straight_flush_conn, holds_3_to_royal, holds_full_house, 
        holds_flush, holds_straight, holds_3_of_a_kind, holds_4_to_flush, 
        holds_any_pair, discard_all
    ],
}

# >>>> STRATEGY_AIRPORT
STRATEGY_AIRPORT = {
    4: [holds_natural_royal, holds_4_deuces],
    3: [
        holds_wild_royal, 
        holds_3_deuces,         # Airport holds Deuces over 5OAK
        holds_five_of_a_kind
    ],
    2: [
        holds_wild_royal, holds_five_of_a_kind, holds_straight_flush, 
        holds_4_to_royal, holds_4_to_straight_flush_conn, holds_2_deuces
    ],
    1: [
        holds_wild_royal, holds_five_of_a_kind, holds_straight_flush, 
        holds_4_to_royal, holds_full_house, 
        holds_4_to_straight_flush_conn, 
        holds_four_of_a_kind,
        holds_flush, holds_straight, holds_3_of_a_kind, holds_3_to_royal, 
        # UPDATED: Use STRICT version for AIRPORT (Fixed Span Error)
        holds_3_to_straight_flush_conn_strict, 
        holds_1_deuce
    ],
    0: [
        holds_natural_royal, holds_4_to_royal, holds_straight_flush, 
        holds_4_to_straight_flush_conn, holds_3_to_royal, holds_full_house, 
        holds_flush, holds_straight, holds_3_of_a_kind, holds_4_to_flush, 
        holds_any_pair, holds_4_to_straight, 
        discard_all
    ],
}

# >>>> STRATEGY_LOOSE_DEUCES
STRATEGY_LOOSE_DEUCES = {
    4: [holds_natural_royal, holds_4_deuces],
    3: [
        holds_3_deuces,         # Priority over everything
        holds_wild_royal, 
        holds_five_of_a_kind
    ],
    2: [
        holds_wild_royal, holds_five_of_a_kind, holds_straight_flush, 
        holds_4_to_royal, holds_4_to_straight_flush_conn, holds_2_deuces
    ],
    1: [
        holds_wild_royal, holds_five_of_a_kind, holds_straight_flush, 
        holds_4_to_royal, holds_full_house, 
        holds_4_to_straight_flush_conn, 
        holds_four_of_a_kind,
        holds_flush, holds_straight, holds_3_of_a_kind, holds_3_to_royal, 
        # Loose Deuces pays well for 4 Deuces, so holding just the Deuce is often better 
        # than a weak SF draw. Strict is safer here too.
        holds_3_to_straight_flush_conn_strict, 
        holds_1_deuce
    ],
    0: [
        holds_natural_royal, holds_4_to_royal, holds_straight_flush, 
        holds_4_to_straight_flush_conn, holds_3_to_royal, holds_full_house, 
        holds_flush, holds_straight, holds_3_of_a_kind, holds_4_to_flush, 
        holds_any_pair, holds_4_to_straight, 
        discard_all
    ],
}

# >>>> STRATEGY_DBW
STRATEGY_DBW = {
    4: [holds_natural_royal, holds_4_deuces],
    3: [
        holds_five_aces, holds_five_3_4_5, holds_wild_royal, holds_five_6_to_k, 
        holds_five_of_a_kind,
        holds_3_deuces
    ],
    2: [
        holds_five_aces, holds_five_3_4_5, holds_wild_royal, holds_five_6_to_k, 
        holds_straight_flush, holds_4_to_royal, holds_4_to_straight_flush_conn, holds_2_deuces
    ],
    1: [
        holds_five_aces, holds_five_3_4_5, holds_wild_royal, holds_five_6_to_k, 
        holds_straight_flush, holds_4_to_royal, holds_full_house, 
        holds_flush, 
        holds_4_to_straight_flush_conn,
        holds_four_of_a_kind,
        holds_3_of_a_kind, holds_straight, holds_3_to_royal, 
        # DBW likely benefits from strict too, given the bonus structure favoring 5OAK
        holds_3_to_straight_flush_conn_strict, 
        holds_1_deuce
    ],
    0: [
        holds_natural_royal, holds_4_to_royal, holds_straight_flush, 
        holds_4_to_straight_flush_conn, holds_3_to_royal, holds_full_house, 
        holds_flush, holds_straight, holds_3_of_a_kind, holds_4_to_flush, 
        holds_any_pair, 
        holds_one_ace, 
        discard_all
    ],
}

# ==============================================================================
# 🗺️ THE MASTER MAP
# ==============================================================================
STRATEGY_MAP = {
    'NSUD': STRATEGY_NSUD,
    'BONUS_DEUCES_10_4': STRATEGY_BONUS_DEUCES_10_4,
    'AIRPORT': STRATEGY_AIRPORT, 
    'LOOSE_DEUCES': STRATEGY_LOOSE_DEUCES,
    'DBW': STRATEGY_DBW
}

# ==============================================================================
# 🏷️ UI UTILITIES
# ==============================================================================
def get_pretty_name(func_obj):
    if not func_obj: return "DISCARD ALL"
    raw = func_obj.__name__
    clean = raw.replace("holds_", "").replace("_", " ").upper()
    
    if "4 TO STRAIGHT FLUSH" in clean: return "4 TO STRAIGHT FLUSH"
    if "3 TO ROYAL" in clean: return "3 TO ROYAL"
    if "5 OF A KIND" in clean: return "5 OF A KIND"
    if "ONE ACE" in clean: return "ONE ACE"
    return clean