"""
dw_strategy_definitions.py
STRATEGY REGISTRY (Phase 4 - Bonus Deuces 10/4/3/3 Finalized)

Contains the Ordered Priority Lists (Strategy Matrix) for Deuces Wild variants.
AXIOM: The Engine iterates this list top-to-bottom. The first match wins.
"""

STRATEGY_MATRIX = {
    # ==========================================
    # 🦆 NSUD (16/10) - AGGRESSIVE
    # Source: NSUD_Core_Strategy.txt
    # ==========================================
    "NSUD": {
        4: [("HOLD_ALL", "HOLD")], 
        
        3: [
            ("NATURAL_ROYAL", "HOLD"), 
            ("WILD_ROYAL", "HOLD"),     
            ("FIVE_OAK", "HOLD"),       
            ("3_DEUCES", "HOLD_DEUCES")
        ],
        
        2: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),     
            ("FIVE_OAK", "HOLD"),       
            ("STRAIGHT_FLUSH", "HOLD"), 
            ("4_TO_ROYAL", "DRAW_COMBINATION"), 
            ("MADE_4OAK", "HOLD"),      
            ("4_TO_SF_TOUCHING", "DRAW_COMBINATION"), 
            # TRAP: We BREAK Made Flush/Straight here by falling through to Deuces
            ("2_DEUCES", "HOLD_DEUCES") 
        ],
        
        1: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),     
            ("FIVE_OAK", "HOLD"),       
            ("STRAIGHT_FLUSH", "HOLD"), 
            ("4_TO_ROYAL", "DRAW_COMBINATION"), 
            ("MADE_FULL_HOUSE", "HOLD"),
            ("MADE_FLUSH", "HOLD"),     
            ("MADE_STRAIGHT", "HOLD"),  
            ("MADE_4OAK", "HOLD"),      
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"), 
            ("MADE_3OAK", "HOLD"),      
            ("3_TO_ROYAL", "DRAW_COMBINATION"), 
            ("3_TO_SF_CONNECT", "DRAW_COMBINATION"), 
            ("1_DEUCE", "HOLD_DEUCES")  
        ],
        
        0: [
            ("NATURAL_ROYAL", "HOLD"),  
            ("4_TO_ROYAL", "DRAW_COMBINATION"), 
            ("STRAIGHT_FLUSH", "HOLD"), 
            ("MADE_4OAK", "HOLD"),      
            ("MADE_FULL_HOUSE", "HOLD"),
            ("MADE_FLUSH", "HOLD"),     
            ("MADE_STRAIGHT", "HOLD"),  
            ("MADE_3OAK", "HOLD"),      
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"), 
            ("3_TO_ROYAL", "DRAW_COMBINATION"), 
            ("4_TO_FLUSH", "DRAW_COMBINATION"), 
            ("TWO_PAIR", "HOLD"),       
            ("PAIR", "HOLD"),           
            ("4_TO_STRAIGHT_OPEN", "DRAW_COMBINATION"), 
            ("3_TO_SF_CONNECT", "DRAW_COMBINATION"),    
            ("DISCARD_ALL", "REDRAW")   
        ]
    },

    # ==========================================
    # ✈️ AIRPORT (12/9) - DEFENSIVE
    # Source: Airport_Deuces_Strategy.txt
    # ==========================================
    "AIRPORT": {
        4: [("HOLD_ALL", "HOLD")], 
        
        3: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),     
            ("FIVE_OAK", "HOLD"),       
            ("3_DEUCES", "HOLD_DEUCES") 
        ],
        
        2: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),     
            ("FIVE_OAK", "HOLD"),       
            ("STRAIGHT_FLUSH", "HOLD"), 
            ("MADE_4OAK", "HOLD"),      
            ("4_TO_ROYAL", "DRAW_COMBINATION"), 
            ("4_TO_SF_TOUCHING", "DRAW_COMBINATION"), 
            ("MADE_FLUSH", "HOLD"),     
            ("2_DEUCES", "HOLD_DEUCES") 
        ],
        
        1: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),     
            ("FIVE_OAK", "HOLD"),       
            ("STRAIGHT_FLUSH", "HOLD"), 
            ("4_TO_ROYAL", "DRAW_COMBINATION"), 
            ("MADE_FULL_HOUSE", "HOLD"),
            ("MADE_FLUSH", "HOLD"),     
            ("MADE_4OAK", "HOLD"),      
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"), 
            ("MADE_3OAK", "HOLD"),      
            ("MADE_STRAIGHT", "HOLD"),  
            ("3_TO_ROYAL", "DRAW_COMBINATION"), 
            ("4_TO_STRAIGHT_OPEN", "DRAW_COMBINATION"), 
            ("1_DEUCE", "HOLD_DEUCES")  
        ],
        
        0: [
            ("NATURAL_ROYAL", "HOLD"),  
            ("4_TO_ROYAL", "DRAW_COMBINATION"), 
            ("STRAIGHT_FLUSH", "HOLD"), 
            ("MADE_4OAK", "HOLD"),      
            ("MADE_FULL_HOUSE", "HOLD"),
            ("MADE_FLUSH", "HOLD"),     
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"), 
            ("MADE_3OAK", "HOLD"),      
            ("MADE_STRAIGHT", "HOLD"),  
            ("3_TO_ROYAL", "DRAW_COMBINATION"), 
            ("4_TO_STRAIGHT_OPEN", "DRAW_COMBINATION"), 
            ("4_TO_FLUSH", "DRAW_COMBINATION"), 
            ("TWO_PAIR", "HOLD"),       
            ("PAIR", "HOLD"),           
            ("DISCARD_ALL", "REDRAW")   
        ]
    },
    
    # ==========================================
    # 💎 BONUS DEUCES (10/4/3/3)
    # Generated from 10k Samples (v9.4 Engine)
    # ==========================================
    "BONUS_DEUCES_10_4": {
        4: [
            ("4_DEUCES_ACE", "HOLD_ALL"),       # EV 2000 > 1085
            ("4_DEUCES", "HOLD_DEUCES")         # Break kicker (EV 1085)
        ],
        
        3: [
            ("FIVE_ACES", "HOLD"),              # EV 400 > 81
            ("FIVE_3_4_5", "HOLD"),             # EV 200 > 81
            ("WILD_ROYAL", "HOLD"),             # EV 125 > 81
            ("FIVE_6_TO_K", "HOLD"),            # EV 100 > 81
            ("3_DEUCES", "HOLD_DEUCES")         # EV 81.5
        ],
        
        2: [
            ("NATURAL_ROYAL", "HOLD"),
            ("FIVE_ACES", "HOLD"),
            ("FIVE_3_4_5", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_6_TO_K", "HOLD"),
            ("STRAIGHT_FLUSH", "HOLD"),         # Pays 50 > 18.6
            ("4_TO_ROYAL", "DRAW_COMBINATION"), # Natural 4-Royal EV ~98
            ("2_DEUCES", "HOLD_DEUCES")         # EV 18.6 (Beats Pat Flush @ 15)
        ],
        
        1: [
            ("NATURAL_ROYAL", "HOLD"),
            ("FIVE_ACES", "HOLD"),
            ("FIVE_3_4_5", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_6_TO_K", "HOLD"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"),
            ("MADE_FULL_HOUSE", "HOLD"),        # 15 > 4.73
            ("MADE_FLUSH", "HOLD"),             # 15 > 4.73
            ("MADE_3OAK", "HOLD"),              # 10-12 > 4.73 (Includes Pair+Deuce)
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"), # 11.1 > 4.73
            ("MADE_STRAIGHT", "HOLD"),          # 5 > 4.73
            ("4_TO_SF_GAP", "DRAW_COMBINATION"),  # 9.5 > 4.73
            ("3_TO_ROYAL", "DRAW_COMBINATION"),   # 5.3 > 4.73
            ("3_TO_SF_CONNECT", "DRAW_COMBINATION"), # 4.9 > 4.73
            ("4_TO_FLUSH", "DRAW_COMBINATION"),   # 4.87 > 4.73 (Aggressive!)
            ("1_DEUCE", "HOLD_DEUCES")
        ],
        
        0: [
            ("NATURAL_ROYAL", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("MADE_4OAK", "HOLD"),
            ("MADE_FULL_HOUSE", "HOLD"),
            ("MADE_FLUSH", "HOLD"),
            ("MADE_3OAK", "HOLD"),
            ("MADE_STRAIGHT", "HOLD"),
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"),
            ("3_TO_ROYAL", "DRAW_COMBINATION"),
            ("4_TO_SF_GAP", "DRAW_COMBINATION"),
            ("4_TO_FLUSH", "DRAW_COMBINATION"),
            ("PAIR", "HOLD"),                   # EV 2.7
            ("3_TO_SF_CONNECT", "DRAW_COMBINATION"), # 2.42 > 1.47
            ("3_TO_SF_GAP", "DRAW_COMBINATION"),     # 2.04 > 1.47
            ("3_TO_FLUSH", "DRAW_COMBINATION"),      # 1.67 > 1.47
            ("2_TO_ROYAL", "DRAW_COMBINATION"),      # 1.56 > 1.47
            ("DISCARD_ALL", "REDRAW")           # EV 1.47
        ]
    },

    # ==========================================
    # 🎡 DBW (Hybrid) - FLUSH HATER
    # Flush Pays 2. 5OAK Pays 16. SF Pays 13.
    # Source: Logic Definitions
    # ==========================================
    "DBW": {
        4: [("HOLD_ALL", "HOLD")],
        3: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_OAK", "HOLD"),
            ("3_DEUCES", "HOLD_DEUCES")
        ],
        2: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_OAK", "HOLD"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"),
            ("MADE_4OAK", "HOLD"),
            ("4_TO_SF_TOUCHING", "DRAW_COMBINATION"),
            ("2_DEUCES", "HOLD_DEUCES")
        ],
        1: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_OAK", "HOLD"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"),
            ("MADE_FULL_HOUSE", "HOLD"),
            ("MADE_FLUSH", "HOLD"), 
            ("MADE_STRAIGHT", "HOLD"),
            ("MADE_4OAK", "HOLD"),
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"),
            ("MADE_3OAK", "HOLD"),
            ("3_TO_ROYAL", "DRAW_COMBINATION"),
            ("3_TO_SF_CONNECT", "DRAW_COMBINATION"), 
            ("1_DEUCE", "HOLD_DEUCES")
        ],
        0: [
            ("NATURAL_ROYAL", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("MADE_4OAK", "HOLD"),
            ("MADE_FULL_HOUSE", "HOLD"),
            ("MADE_FLUSH", "HOLD"),
            ("MADE_STRAIGHT", "HOLD"),
            ("MADE_3OAK", "HOLD"),
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"),
            ("3_TO_ROYAL", "DRAW_COMBINATION"),
            ("TWO_PAIR", "HOLD"),
            ("PAIR", "HOLD"),
            ("4_TO_STRAIGHT_OPEN", "DRAW_COMBINATION"),
            ("3_TO_SF_CONNECT", "DRAW_COMBINATION"),
            ("DISCARD_ALL", "REDRAW")
        ]
    },
    
    # ==========================================
    # 🎰 LOOSE DEUCES (2500 Coin Jackpot)
    # The 4-Deuce Payout is the primary driver.
    # ==========================================
    "LOOSE_DEUCES": {
        4: [("HOLD_ALL", "HOLD")],
        3: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_OAK", "HOLD"),
            ("3_DEUCES", "HOLD_DEUCES") 
        ],
        2: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_OAK", "HOLD"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"),
            ("2_DEUCES", "HOLD_DEUCES") 
        ],
        1: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_OAK", "HOLD"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"),
            ("MADE_FULL_HOUSE", "HOLD"),
            ("MADE_FLUSH", "HOLD"),
            ("MADE_STRAIGHT", "HOLD"),
            ("MADE_4OAK", "HOLD"),
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"),
            ("3_TO_ROYAL", "DRAW_COMBINATION"),
            ("1_DEUCE", "HOLD_DEUCES")
        ],
        0: [
            ("NATURAL_ROYAL", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("MADE_4OAK", "HOLD"),
            ("MADE_FULL_HOUSE", "HOLD"),
            ("MADE_FLUSH", "HOLD"),
            ("MADE_STRAIGHT", "HOLD"),
            ("MADE_3OAK", "HOLD"),
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"),
            ("3_TO_ROYAL", "DRAW_COMBINATION"),
            ("4_TO_FLUSH", "DRAW_COMBINATION"),
            ("TWO_PAIR", "HOLD"),
            ("PAIR", "HOLD"),
            ("4_TO_STRAIGHT_OPEN", "DRAW_COMBINATION"),
            ("3_TO_SF_CONNECT", "DRAW_COMBINATION"),
            ("DISCARD_ALL", "REDRAW")
        ]
    }
}

# ==========================================
# ⚙️ GENERATOR CONFIGURATION
# Input definitions for dw_strategy_generator.py
# ==========================================
GAME_VARIANTS = {
    "BONUS_DEUCES_10_4": {
        "name": "Bonus Deuces Wild (10/4/3/3)",
        "paytable": {
            "NATURAL_ROYAL": 800,    # Standard 800 (4000 total)
            "FOUR_DEUCES_ACE": 400,  # 2000 total
            "FOUR_DEUCES": 200,      # 1000 total
            "FIVE_ACES": 80,         # 400 total
            "FIVE_3_4_5": 40,        # 200 total (The Critical Differentiator)
            "FIVE_6_TO_K": 20,       # 100 total (Explicit Key)
            "WILD_ROYAL": 25,        # 125 total
            "STRAIGHT_FLUSH": 10,    # 50 total
            "FOUR_OAK": 4,           # 20 total
            "FULL_HOUSE": 3,         # 15 total
            "FLUSH": 3,              # 15 total
            "STRAIGHT": 1,           # 5 total
            "THREE_OAK": 1           # 5 total
        }
    }
}