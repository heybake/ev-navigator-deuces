"""
dw_stats_helper.py
Logic module for Session Statistics, Hit Rates, and Variance Analysis.
Decouples math/data from the UI.
"""

# ==============================================================================
# 1. DATA CONSTANTS
# ==============================================================================

# Canonical List of Hand Types (Order matters for UI display)
HAND_TYPES = [
    "NATURAL_ROYAL",
    "FOUR_DEUCES",
    "WILD_ROYAL",
    "FIVE_ACES",       # Bonus/DBW specific
    "FIVE_3_4_5",      # Bonus/DBW specific
    "FIVE_6_TO_K",     # Bonus/DBW specific
    "FIVE_OF_A_KIND",  # General 5OAK
    "STRAIGHT_FLUSH",
    "FOUR_OF_A_KIND",
    "FULL_HOUSE",
    "FLUSH",
    "STRAIGHT",
    "THREE_OF_A_KIND",
    "LOSER"
]

# UI Labels for the Hand Types
HAND_LABELS = {
    "NATURAL_ROYAL": "ROYAL FLUSH",
    "FOUR_DEUCES": "4 DEUCES",
    "WILD_ROYAL": "WILD ROYAL",
    "FIVE_ACES": "5 ACES",
    "FIVE_3_4_5": "5 3s-5s",
    "FIVE_6_TO_K": "5 6s-Ks",
    "FIVE_OF_A_KIND": "5 OF A KIND",
    "STRAIGHT_FLUSH": "STR FLUSH",
    "FOUR_OF_A_KIND": "4 OF A KIND",
    "FULL_HOUSE": "FULL HOUSE",
    "FLUSH": "FLUSH",
    "STRAIGHT": "STRAIGHT",
    "THREE_OF_A_KIND": "3 OF A KIND",
    "LOSER": "NOTHING"
}

# THEORETICAL PROBABILITIES (Per Hand)
# Source: Standard Combinatorial Analysis
THEORETICAL_PROBS = {
    # NSUD (Not So Ugly Deuces) - VERIFIED (~99.73%)
    "NSUD": {
        "NATURAL_ROYAL":   0.000022,
        "FOUR_DEUCES":     0.000201,
        "WILD_ROYAL":      0.001918,
        "FIVE_OF_A_KIND":  0.003186,
        "STRAIGHT_FLUSH":  0.004183,
        "FOUR_OF_A_KIND":  0.064560,
        "FULL_HOUSE":      0.021677,
        "FLUSH":           0.016335,
        "STRAIGHT":        0.055627,
        "THREE_OF_A_KIND": 0.284770,
        "LOSER":           0.547521
    },
    
    # Placeholders for other variants (Empty dict = "No Data")
    # The UI will just show "---" for expected values until we fill these.
    "LOOSE_DEUCES": {},
    "AIRPORT": {},
    "BONUS_DEUCES_10_4": {},
    "DBW": {}
}

# ==============================================================================
# 2. LOGIC FUNCTIONS
# ==============================================================================

def normalize_variant_name(raw_name):
    """
    Maps internal or complex variant IDs to canonical keys.
    Example: "NSUD_v15_Optimized" -> "NSUD"
    """
    if not raw_name: return "NSUD"
    
    u = raw_name.upper()
    if "NSUD" in u: return "NSUD"
    if "LOOSE" in u: return "LOOSE_DEUCES"
    if "AIRPORT" in u: return "AIRPORT"
    if "BONUS" in u and "10" in u: return "BONUS_DEUCES_10_4"
    if "DBW" in u: return "DBW"
    
    return "NSUD" # Default fallback

def get_theoretical_freqs(variant_key):
    """Safe lookup that returns {} if data missing."""
    key = normalize_variant_name(variant_key)
    return THEORETICAL_PROBS.get(key, {})

def compute_hit_stats(session_data):
    """
    Processes a list of hand records (dicts) and returns a robust comparison list.
    """
    if not session_data:
        return []

    total_hands = len(session_data)
    
    # 1. Determine Variant
    raw_variant = session_data[0].get('variant', 'NSUD')
    theo_map = get_theoretical_freqs(raw_variant)
    
    # 2. Count Actuals
    counts = {k: 0 for k in HAND_TYPES}
    for d in session_data:
        rank = d.get('result', {}).get('rank', 'LOSER')
        if rank in counts:
            counts[rank] += 1
        else:
            counts['LOSER'] += 1 
            
    # 3. Build Comparison Rows
    report = []
    
    for key in HAND_TYPES:
        actual_count = counts.get(key, 0)
        theo_prob = theo_map.get(key, None)
        
        # Skip rows that have 0 count AND no theoretical data (keeps UI clean)
        if actual_count == 0 and theo_prob is None:
            continue
            
        actual_pct = (actual_count / total_hands) * 100
        
        row = {
            'label': HAND_LABELS.get(key, key),
            'count': actual_count,
            'actual_pct': actual_pct,
            'theo_pct': (theo_prob * 100) if theo_prob is not None else None,
            'diff': 0.0
        }
        
        if row['theo_pct'] is not None:
            row['diff'] = actual_pct - row['theo_pct']
            
        report.append(row)
        
    return report