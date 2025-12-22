"""
dw_strategy_definitions.py
STRATEGY REGISTRY (Phase 1 Refactor)

Contains the Ordered Priority Lists (Strategy Matrix) for Deuces Wild variants.
Logic derived from 'NSUD_Core_Strategy.txt' and 'Airport_Deuces_Strategy.txt'.

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
            # DBW BREAKS FLUSH (Pays 2): Fall through to Deuces
            ("2_DEUCES", "HOLD_DEUCES")
        ],
        1: [
            ("NATURAL_ROYAL", "HOLD"),
            ("WILD_ROYAL", "HOLD"),
            ("FIVE_OAK", "HOLD"),
            ("STRAIGHT_FLUSH", "HOLD"),
            ("4_TO_ROYAL", "DRAW_COMBINATION"),
            ("MADE_FULL_HOUSE", "HOLD"),
            # MADE FLUSH: Pays 2. EV is 10. Deuce EV ~5. Hold Flush.
            ("MADE_FLUSH", "HOLD"), 
            ("MADE_STRAIGHT", "HOLD"),
            ("MADE_4OAK", "HOLD"),
            ("4_TO_SF_OPEN", "DRAW_COMBINATION"),
            ("MADE_3OAK", "HOLD"),
            ("3_TO_ROYAL", "DRAW_COMBINATION"),
            # DBW Special: High SF Payout (13) boosts 3-card SF draws
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
            # DBW 4_TO_FLUSH: Pays 2. EV < Discard All. REMOVED.
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
            # HYPER-AGGRESSION: In some versions, you even break a Wild Royal to hunt the 4th Deuce!
            # For this definition, we will play it standard but keep the priority high.
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
            # CRITICAL DIFFERENCE: We prioritize Deuces over most "Made Hands" like 4OAK
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