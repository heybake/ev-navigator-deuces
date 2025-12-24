"""
dw_strategy_definitions.py
STRATEGY REGISTRY (Phase 2 - Bonus Deuces Added)

Contains the Ordered Priority Lists (Strategy Matrix) for Deuces Wild variants.
Logic derived from 'NSUD_Core_Strategy.txt', 'Airport_Deuces_Strategy.txt', 
and 'Bonus_Deuces_Solver_Output.csv'.

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
    # 💎 BONUS DEUCES - THE JACKPOT HUNTER
    # 5 Aces = 80. 4 Deuces+Ace = 400.
    # Source: Generated Solver Data (10k Hands)
    # ==========================================
    "BONUS_DEUCES": {
        4: [
            ("4_DEUCES_ACE", "HOLD_ALL"),   # Pays 400 (EV 2000) -> HOLD
            ("4_DEUCES", "HOLD_DEUCES")     # Pays 200 (EV 1085 > 1000) -> BREAK Kicker
        ],
        
        3: [
            ("FIVE_ACES", "HOLD"),          # Pays 80 (EV 400) -> HOLD
            ("3_DEUCES", "HOLD_DEUCES"),    # EV 75.8. BEATS Wild Royal (25) and 5OAK (20)
            ("WILD_ROYAL", "HOLD_DEUCES"),  # Intentionally Break
            ("FIVE_OAK", "HOLD_DEUCES")     # Intentionally Break
        ],
        
        2: [
            ("NATURAL_ROYAL", "HOLD"),
            ("FIVE_ACES", "HOLD"),      
            ("WILD_ROYAL", "HOLD"),         # Pays 25 (EV 125 > 18.5)
            ("FIVE_OAK", "HOLD"),           # Pays 20 (EV 100 > 18.5)
            ("STRAIGHT_FLUSH", "HOLD"), 
            ("4_TO_ROYAL", "DRAW_COMBINATION"), # EV 42 > 18.5
            ("2_DEUCES", "HOLD_DEUCES") 
        ],
        
        1: [
            ("NATURAL_ROYAL", "HOLD"),
            ("FIVE_ACES", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_OAK", "HOLD"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"), # EV ~23.8
            ("MADE_FULL_HOUSE", "HOLD"),        # EV 20
            ("MADE_FLUSH", "HOLD"),             # EV 15
            ("MADE_STRAIGHT", "HOLD"),          # EV 5
            ("MADE_4OAK", "HOLD"),              # EV 20
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"), 
            ("1_DEUCE", "HOLD_DEUCES")          # EV 4.67
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
            ("DISCARD_ALL", "REDRAW")
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