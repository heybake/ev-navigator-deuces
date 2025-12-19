"""
dw_sim_engine.py
STRATEGY & ECONOMICS LAYER (Hybrid v3.2 - User Verified)
"""

import random
import itertools
from dw_core_engine import DeucesWildCore
from dw_pay_constants import PAYTABLES

class DoubleWheel:
    """
    🎡 THE DUAL-WHEEL PHYSICS ENGINE
    """
    def __init__(self):
        self.outer_weights = [1]*20 + [2]*40 + [3]*30 + [4]*10
        self.inner_weights = [2]*45 + [3]*45 + [4]*10
        
    def spin(self):
        if random.random() > (1 / 5.049):
            return 1, 1, 1 
        val_a = random.choice(self.outer_weights)
        val_b = random.choice(self.inner_weights)
        return (val_a * val_b), val_a, val_b

class DeucesWildSim:
    def __init__(self, variant="NSUD", bankroll=40.00, denom=0.25, max_credits=5, floor=18.75, ceiling=60.00):
        self.variant = variant.upper()
        self.bankroll = float(bankroll)
        self.denom = float(denom)
        self.bet_amount = float(denom * max_credits)
        self.floor = float(floor)
        self.ceiling = float(ceiling)
        self.deal_count = 0
        
        self.core = DeucesWildCore()
        self.wheel = DoubleWheel()
        self.paytable = self._get_paytable_settings()

    def _get_paytable_settings(self):
        """
        Returns the payout dictionary based on User Verified tables.
        Refactored: Imports immutable data from dw_pay_constants.
        Source: ADR 'The Pay Table Quarantine'
        """
        # Direct Lookup from Registry
        if self.variant in PAYTABLES:
            return PAYTABLES[self.variant]

        # Fallback for safety (though normally shouldn't happen if inputs are validated)
        # Defaulting to NSUD as a safe baseline
        print(f"⚠️ Warning: Unknown variant '{self.variant}'. Defaulting to NSUD.")
        return PAYTABLES["NSUD"]

    # --- CORE BRIDGE ---
    def normalize_input(self, s): return self.core.normalize_input(s)
    def get_rank_val(self, c): return {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'T':10,'J':11,'Q':12,'K':13,'A':14}[c[0].upper()]

    def evaluate_hand_score(self, hand):
        rank_key = self.core.identify_hand(hand)
        # No special Split logic needed for this version of DBW
        return rank_key, self.paytable.get(rank_key, 0)

    def evaluate_hand(self, hand): return self.evaluate_hand_score(hand)

    # --- STRATEGY HELPERS ---
    def get_repeated_cards(self, hand, count_needed):
        rank_map = {}
        for c in hand:
            r = c[0]
            if r not in rank_map: rank_map[r] = []
            rank_map[r].append(c)
        return [c for r in rank_map if len(rank_map[r]) >= count_needed for c in rank_map[r]]

    def check_straight_flush_draw(self, cards):
        suits = [c[1] for c in cards]
        if len(set(suits)) != 1: return False
        vals = sorted([self.get_rank_val(c) for c in cards])
        if not vals: return True
        return (vals[-1] - vals[0]) <= 4

    def check_open_straight_draw(self, cards):
        vals = sorted([self.get_rank_val(c) for c in cards])
        if len(vals) != 4: return False
        if (vals[-1] - vals[0]) == 3: return (14 not in vals)
        return False

    # ==========================================
    # 🧠 ADAPTIVE STRATEGY (Updated for Flush=2)
    # ==========================================
    def pro_strategy(self, hand):
        deuces = [c for c in hand if c[0] == '2']
        non_deuces = [c for c in hand if c[0] != '2']
        current_rank, _ = self.evaluate_hand(hand)
        
        # --- 4 DEUCES ---
        if len(deuces) == 4: return hand

        # --- 3 DEUCES ---
        if len(deuces) == 3:
            if current_rank in ["NATURAL_ROYAL", "WILD_ROYAL", "FIVE_OAK"]: return hand
            return deuces

        # --- 2 DEUCES ---
        if len(deuces) == 2:
            if current_rank in ["NATURAL_ROYAL", "WILD_ROYAL", "FIVE_OAK", "STRAIGHT_FLUSH"]: return hand
            
            # 4 to Royal
            royals = {10,11,12,13,14}
            for combo in itertools.combinations(non_deuces, 2):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals): return deuces + list(combo)

            # Made Flush Logic
            if current_rank == "FLUSH":
                # If DBW (Flush pays 2), we BREAK IT to hunt 5OAK (pays 16) or SF (pays 13)
                if self.variant == "DBW": pass 
                elif self.variant == "AIRPORT": return hand
                else: pass # NSUD breaks it too

            if current_rank == "STRAIGHT": pass 

            # Made 4 of a Kind
            pair_cards = self.get_repeated_cards(non_deuces, 2)
            if pair_cards: return deuces + pair_cards

            # 4 to Straight Flush
            for combo in itertools.combinations(non_deuces, 2):
                if self.check_straight_flush_draw(combo):
                    vals = sorted([self.get_rank_val(c) for c in combo])
                    if vals[-1] - vals[0] <= 2: return deuces + list(combo) # Strict
            
            return deuces

        # --- 1 DEUCE ---
        if len(deuces) == 1:
            if current_rank in ["NATURAL_ROYAL", "WILD_ROYAL", "FIVE_OAK", "STRAIGHT_FLUSH"]: return hand
            
            # 4 to Wild Royal
            royals = {10,11,12,13,14}
            for combo in itertools.combinations(non_deuces, 3):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals): return deuces + list(combo)
            
            if current_rank == "FULL_HOUSE": return hand
            
            # Made Flush Logic
            if current_rank == "FLUSH":
                if self.variant == "DBW": pass # Break Flush (Pays 2)
                elif self.variant == "AIRPORT": return hand
                else: return hand 

            if current_rank == "STRAIGHT": return hand
            if current_rank == "FOUR_OAK": return hand

            # 4 to Wild SF
            for combo in itertools.combinations(non_deuces, 3):
                if self.check_straight_flush_draw(combo): return deuces + list(combo)
            
            # Made 3 of a Kind
            pair_cards = self.get_repeated_cards(non_deuces, 2)
            if pair_cards: return deuces + pair_cards
            
            # 3 to Wild Royal
            for combo in itertools.combinations(non_deuces, 2):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals): return deuces + list(combo)
            
            # 3 to SF (Special DBW High SF Payout)
            if self.variant == "DBW":
                for combo in itertools.combinations(non_deuces, 2):
                     if self.check_straight_flush_draw(combo):
                        vals = sorted([self.get_rank_val(c) for c in combo])
                        if vals[-1] - vals[0] <= 2: return deuces + list(combo)

            return deuces

        # --- 0 DEUCES ---
        if len(deuces) == 0:
            if current_rank == "NATURAL_ROYAL": return hand
            # In DBW, Flush pays 2 (same as Straight). We hold it, but it's weak.
            if current_rank in ["STRAIGHT_FLUSH", "FOUR_OAK", "FULL_HOUSE", "FLUSH", "STRAIGHT", "THREE_OAK"]: return hand
                
            royals = {10,11,12,13,14}
            # 4 to Royal
            for combo in itertools.combinations(non_deuces, 4):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals): return list(combo)

            # 4 to SF
            for combo in itertools.combinations(non_deuces, 4):
                if self.check_straight_flush_draw(combo): return list(combo)
            
            # 3 to Royal
            for combo in itertools.combinations(non_deuces, 3):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals): return list(combo)

            # 4 to Flush
            # If Flush pays 2, drawing to it is barely worth it (~0.38 EV). 
            # But better than Discard All (~0.32). So we keep it.
            for combo in itertools.combinations(non_deuces, 4):
                suits = {c[1] for c in combo}
                if len(suits) == 1: return list(combo)
            
            # Pair
            pair_cards = self.get_repeated_cards(hand, 2)
            if pair_cards: return pair_cards
            
            # 4 to Open Straight
            for combo in itertools.combinations(non_deuces, 4):
                if self.check_open_straight_draw(combo): return list(combo)

            return []
        return []