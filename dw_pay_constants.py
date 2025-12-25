"""
dw_pay_constants.py
IMMUTABLE REGISTRY of Deuces Wild Pay Tables.
Single Source of Truth for Simulation and Solver.

Source: Architectural Decision Record (Dec 18, 2025)
Constraint: NO LOGIC. Data Only.
"""

PAYTABLES = {
    "NSUD": {
        "NATURAL_ROYAL": 800,
        "FOUR_DEUCES": 200,
        "WILD_ROYAL": 25,
        "FIVE_OAK": 16,
        "STRAIGHT_FLUSH": 10,
        "FOUR_OAK": 4,
        "FULL_HOUSE": 4,
        "FLUSH": 3,
        "STRAIGHT": 2,
        "THREE_OAK": 1,
        "NOTHING": 0,
        "ERROR": 0
    },
    "AIRPORT": {
        "NATURAL_ROYAL": 800,
        "FOUR_DEUCES": 200,
        "WILD_ROYAL": 20,
        "FIVE_OAK": 12,
        "STRAIGHT_FLUSH": 9,
        "FOUR_OAK": 4,
        "FULL_HOUSE": 4,
        "FLUSH": 3,
        "STRAIGHT": 2,
        "THREE_OAK": 1,
        "NOTHING": 0,
        "ERROR": 0
    },
    "DBW": {
        "NATURAL_ROYAL": 800,
        "FOUR_DEUCES": 200,
        "WILD_ROYAL": 25,
        "FIVE_OAK": 16,      # Aggressive
        "STRAIGHT_FLUSH": 13, # The "Bribe"
        "FOUR_OAK": 4,
        "FULL_HOUSE": 3,      # The "Tax"
        "FLUSH": 2,           # The "Killer"
        "STRAIGHT": 2,
        "THREE_OAK": 1,
        "NOTHING": 0,
        "ERROR": 0
    },
    "LOOSE_DEUCES": {
        "NATURAL_ROYAL": 800,
        "FOUR_DEUCES": 500,  # 500 * 5 coins = 2500 Jackpot!
        "WILD_ROYAL": 25,
        "FIVE_OAK": 15,      # Note: Lower than NSUD (16)
        "STRAIGHT_FLUSH": 10,
        "FOUR_OAK": 4,
        "FULL_HOUSE": 4,
        "FLUSH": 3,
        "STRAIGHT": 2,
        "THREE_OAK": 1,
        "NOTHING": 0,
        "ERROR": 0
    },
"BONUS_DEUCES_10_4": { 
        "NATURAL_ROYAL": 800,
        "FOUR_DEUCES_ACE": 400,
        "FOUR_DEUCES": 200,
        "FIVE_ACES": 80,
        "FIVE_3_4_5": 40,        # The new middle tier
        "FIVE_6_TO_K": 20,       # The new low tier (Must match solver output!)
        "WILD_ROYAL": 25,
        "STRAIGHT_FLUSH": 10,
        "FOUR_OAK": 4,
        "FULL_HOUSE": 3,
        "FLUSH": 3,
        "STRAIGHT": 1,
        "THREE_OAK": 1
    },
}