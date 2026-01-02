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
        "WILD_ROYAL": 25,
        "FIVE_OAK": 15,
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
        "THREE_OAK": 1,
        "NOTHING": 0,
        "ERROR": 0
    },
    "SUPER_DEUCES": {
        "NATURAL_ROYAL": 800,
        "FOUR_DEUCES_ACE": 400,  # Pays 2000 for 5 coins
        "FOUR_DEUCES": 200,      # Pays 1000 for 5 coins
        "FIVE_OAK_1_DEUCE": 160, # Pays 800 for 5 coins (The Jackpot Hand)
        "WILD_ROYAL": 25,        # Pays 125 for 5 coins
        "FIVE_OAK": 10,          # Standard 5OAK (Pays 50)
        "STRAIGHT_FLUSH": 8,     # Pays 40
        "FOUR_OAK": 4,
        "FULL_HOUSE": 3,
        "FLUSH": 2,
        "STRAIGHT": 2,
        "THREE_OAK": 1,
        "NOTHING": 0,
        "ERROR": 0
    }
}

# -----------------------------------------------------------------------------
# THEORETICAL HIT FREQUENCIES (Probability 0.0 to 1.0)
# Used for "Diff" calculations in Session Reports.
# Source: Wizard of Odds & internal Simulations.
# -----------------------------------------------------------------------------

VARIANT_STATS = {
    # NOT SO UGLY DEUCES (NSUD) - 99.73% Return
    "NSUD": {
        "NATURAL_ROYAL": 0.000022,  # ~1 in 45,000
        "FOUR_DEUCES":   0.000208,  # ~1 in 4,800
        "WILD_ROYAL":    0.001964,
        "FIVE_OAK":      0.003215,
        "STRAIGHT_FLUSH": 0.004245,
        "FOUR_OAK":      0.065200,
        "FULL_HOUSE":    0.021500,
        "FLUSH":         0.016500,
        "STRAIGHT":      0.054500,
        "THREE_OAK":     0.285500
    },
    
    # BONUS DEUCES WILD (10/4/3/3) - 97.36% Return
    # Source: Wizard of Odds (Table 10/4)
    "BONUS_DEUCES_10_4": {
        "NATURAL_ROYAL": 0.000024,
        "FOUR_DEUCES_ACE": 0.000027, 
        "FOUR_DEUCES":   0.000154,
        "WILD_ROYAL":    0.002076,
        "FIVE_ACES":     0.000339,
        "FIVE_3_4_5":    0.000795,
        "FIVE_6_TO_K":   0.002082,
        "STRAIGHT_FLUSH": 0.004102,
        "FOUR_OAK":      0.063714,
        "FULL_HOUSE":    0.021104,
        "FLUSH":         0.024585,
        "STRAIGHT":      0.040118,
        "THREE_OAK":     0.287091
    },

    # LOOSE DEUCES (15/10/4/4/3) - 100.97% Return
    # Source: Wizard of Odds
    "LOOSE_DEUCES": {
        "NATURAL_ROYAL": 0.000023,
        "FOUR_DEUCES":   0.000213,  # Higher frequency (strategy chases deuces)
        "WILD_ROYAL":    0.001918,
        "FIVE_OAK":      0.003225,
        "STRAIGHT_FLUSH": 0.004245,
        "FOUR_OAK":      0.063750,
        "FULL_HOUSE":    0.021200,
        "FLUSH":         0.024500,
        "STRAIGHT":      0.040500,
        "THREE_OAK":     0.288000
    },

    # AIRPORT DEUCES (25/15/9/4/4/3) - 98.9% Return
    # Source: Casino City Times / Wizard of Odds
    "AIRPORT": {
        "NATURAL_ROYAL": 0.000022,
        "FOUR_DEUCES":   0.000187,  # ~1 in 5,348 (Lower than NSUD because you hold pairs over deuce draws sometimes)
        "WILD_ROYAL":    0.001800,
        "FIVE_OAK":      0.003200,
        "STRAIGHT_FLUSH": 0.004100,
        "FOUR_OAK":      0.064000,
        "FULL_HOUSE":    0.026000,  # Higher freq (Strategy chases FH because it pays 4)
        "FLUSH":         0.021000,  # Higher freq (Strategy chases Flush because it pays 3)
        "STRAIGHT":      0.054000,
        "THREE_OAK":     0.285000
    },
    
    # DOUBLE BONUS DEUCES (25/16/13/4/3/2) - 97.7% Return
    # Source: Wizard of Odds (16/13 variant)
    "DBW": {
        "NATURAL_ROYAL": 0.000022,
        "FOUR_DEUCES":   0.000204,
        "WILD_ROYAL":    0.001925,
        "FIVE_OAK":      0.003500,  # Aggressive chase for 16
        "STRAIGHT_FLUSH": 0.004300, # Aggressive chase for 13
        "FOUR_OAK":      0.065000,
        "FULL_HOUSE":    0.021000,
        "FLUSH":         0.016000,  # Very low (Strategy dumps flushes because they only pay 2)
        "STRAIGHT":      0.054000,
        "THREE_OAK":     0.284000
    },

    # SUPER DEUCES WILD (Based on Machine Specs)
    # Volatility: HIGH. 5OAK is king.
    # Note: Stats approximated from Bonus Deuces 10/4 until Sim Run confirms.
    "SUPER_DEUCES": {
        "NATURAL_ROYAL": 0.000024,
        "FOUR_DEUCES_ACE": 0.000027,
        "FOUR_DEUCES":   0.000154,
        "FIVE_OAK_1_DEUCE": 0.000020, # Estimated deal freq for 4 naturals + 1 deuce
        "WILD_ROYAL":    0.002076,
        "FIVE_OAK":      0.003200,    # General 5OAK pool
        "STRAIGHT_FLUSH": 0.004100,
        "FOUR_OAK":      0.063700,
        "FULL_HOUSE":    0.021100,
        "FLUSH":         0.024500,
        "STRAIGHT":      0.040100,
        "THREE_OAK":     0.287000
    }
}