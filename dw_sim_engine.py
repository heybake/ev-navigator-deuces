"""
dw_sim_engine.py
STRATEGY & ECONOMICS LAYER (Hybrid v4.0 - Decoupled)
Now uses 'dw_strategy_definitions.py' for logic.
"""

import random
import itertools
from dw_core_engine import DeucesWildCore
from dw_pay_constants import PAYTABLES
from dw_strategy_definitions import STRATEGY_MATRIX

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
        
        self.core = DeucesWildCore()
        self.wheel = DoubleWheel()
        self.paytable = self._get_paytable_settings()
        self.strategy_list = STRATEGY_MATRIX.get(self.variant, STRATEGY_MATRIX["NSUD"])

    def _get_paytable_settings(self):
        if self.variant in PAYTABLES:
            return PAYTABLES[self.variant]
        print(f"⚠️ Warning: Unknown variant '{self.variant}'. Defaulting to NSUD.")
        return PAYTABLES["NSUD"]

    # --- CORE BRIDGE ---
    def normalize_input(self, s): return self.core.normalize_input(s)
    def get_rank_val(self, c): 
        r = c[0].upper()
        mapping = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'T':10,'J':11,'Q':12,'K':13,'A':14}
        return mapping[r]

    def evaluate_hand_score(self, hand):
        rank_key = self.core.identify_hand(hand)
        return rank_key, self.paytable.get(rank_key, 0)
    
    def evaluate_hand(self, hand): return self.evaluate_hand_score(hand)

    # ==========================================
    # 🧠 RULE ENGINE (Phase 1 Refactor)
    # ==========================================
    
    def pro_strategy(self, hand):
        """
        Executes the strategy matrix for the current variant.
        """
        deuces = [c for c in hand if c[0] == '2']
        count = len(deuces)
        
        # 1. Get the Priority List for this number of Deuces
        rules = self.strategy_list.get(count, [])
        
        # 2. Iterate Rules
        for rule_name, action in rules:
            target_cards = self._check_rule(rule_name, hand, deuces)
            if target_cards is not None:
                # Rule Matched! Return the hold.
                return target_cards
        
        # Fallback (Should typically be covered by 'DISCARD_ALL' or 'HOLD_DEUCES')
        return deuces

    def _check_rule(self, rule_name, hand, deuces):
        """
        Maps Matrix strings (e.g., '4_TO_ROYAL') to logic checks.
        Returns: LIST of cards to hold if True, else None.
        """
        non_deuces = [c for c in hand if c[0] != '2']
        current_rank, _ = self.evaluate_hand(hand) # Core Ranker

        # --- TERMINAL HANDS (Already Made) ---
        if rule_name == "HOLD_ALL": return hand
        if rule_name == "HOLD_DEUCES": return deuces
        if rule_name == "DISCARD_ALL": return []
        
        # --- PRE-CALCULATED RANKS ---
        # If the hand is ALREADY a Made Hand (e.g. Pat Royal), we just check the Core Rank.
        if rule_name == current_rank: return hand

        # Specific Made Hand Checks (Groupings used in Strategy)
        if rule_name == "MADE_FULL_HOUSE" and current_rank == "FULL_HOUSE": return hand
        if rule_name == "MADE_FLUSH" and current_rank == "FLUSH": return hand
        if rule_name == "MADE_STRAIGHT" and current_rank == "STRAIGHT": return hand
        if rule_name == "MADE_4OAK" and current_rank == "FOUR_OAK": return hand
        if rule_name == "MADE_3OAK" and current_rank == "THREE_OAK":
             # Strategy often holds 3OAK over draws. 
             # We must identify the triplet.
             return deuces + self._get_repeated_cards(non_deuces, 3 - len(deuces))
        
        # --- DRAW LOGIC ---
        royals = {10,11,12,13,14}
        
        if rule_name == "4_TO_ROYAL":
            # N Deuces + (4-N) Royals. Suited.
            needed = 4 - len(deuces)
            for combo in itertools.combinations(non_deuces, needed):
                if self._is_suited_royals(combo, royals): return deuces + list(combo)

        if rule_name == "4_TO_SF_TOUCHING":
             # Strict: 0 Gaps (e.g., 6-7).
             # Used in 2 Deuces logic.
             needed = 2 # 2 Deuces + 2 Cards
             for combo in itertools.combinations(non_deuces, needed):
                 if self._is_straight_flush_draw(combo, max_span=needed): # Span 2 = Touching
                     return deuces + list(combo)

        if rule_name == "4_TO_SF_OPEN":
             # Standard SF Draw
             needed = 4 - len(deuces)
             for combo in itertools.combinations(non_deuces, needed):
                 if self._is_straight_flush_draw(combo): return deuces + list(combo)

        if rule_name == "3_TO_ROYAL":
            needed = 3 - len(deuces)
            for combo in itertools.combinations(non_deuces, needed):
                if self._is_suited_royals(combo, royals): return deuces + list(combo)

        if rule_name == "3_TO_SF_CONNECT":
             # 3 card SF draw (1 Deuce + 2 suited OR 0 Deuce + 3 suited)
             needed = 3 - len(deuces)
             for combo in itertools.combinations(non_deuces, needed):
                 if self._is_straight_flush_draw(combo): return deuces + list(combo)
        
        if rule_name == "4_TO_FLUSH":
            # Only relevant for 0 Deuces
            for combo in itertools.combinations(non_deuces, 4):
                if len({c[1] for c in combo}) == 1: return list(combo)

        if rule_name == "TWO_PAIR":
            # 0 Deuces
            pair1 = self._get_repeated_cards(non_deuces, 2)
            if len(pair1) == 4: return pair1 # 2 Pairs is 4 cards
        
        if rule_name == "PAIR":
            pair = self._get_repeated_cards(non_deuces, 2)
            if pair: return pair[:2] # Just one pair
            
        if rule_name == "4_TO_STRAIGHT_OPEN":
            # 0 Deuces: 4 cards, Open Ended (Span 3, No Ace)
            for combo in itertools.combinations(non_deuces, 4):
                vals = sorted([self.get_rank_val(c) for c in combo])
                if (vals[-1] - vals[0] == 3) and (14 not in vals): return list(combo)

        return None

    # --- HELPERS ---
    def _get_repeated_cards(self, cards, count):
        rank_map = {}
        for c in cards:
            r = c[0]
            rank_map.setdefault(r, []).append(c)
        # Return all pairs/trips found
        res = []
        for r in rank_map:
            if len(rank_map[r]) >= count:
                res.extend(rank_map[r])
        return res

    def _is_suited_royals(self, cards, royal_set):
        vals = {self.get_rank_val(c) for c in cards}
        suits = {c[1] for c in cards}
        return len(suits) == 1 and vals.issubset(royal_set)

    def _is_straight_flush_draw(self, cards, max_span=4):
        suits = {c[1] for c in cards}
        if len(suits) != 1: return False
        vals = sorted([self.get_rank_val(c) for c in cards])
        if not vals: return True
        return (vals[-1] - vals[0]) <= max_span