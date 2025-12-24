"""
dw_sim_engine.py
CORE SIMULATION LOGIC (v4.3 - Flush Logic Hotfix)

Features:
- Robust Input Normalization
- Bonus Deuces Logic (4 Deuces w/ Ace, 5 Aces)
- Wheel Mechanics Stub
- Bet Amount Calculation (Fixes Multi-Hand Crash)
- FIXED: Wild Flush Logic (Deuces ignore suit)
"""

import random
import re
from collections import Counter
from dw_core_engine import DeucesWildCore
from dw_pay_constants import PAYTABLES
import dw_exact_solver

# --- WHEEL MECHANIC STUB ---
class DeucesBonusWheel:
    def __init__(self):
        # Format: (Multiplier, Coins, Segment_ID)
        self.ranges = {
            (1, 600): (1, 40, 1),
            (601, 850): (2, 80, 2),
            (851, 950): (3, 120, 3),
            (951, 990): (4, 160, 4),
            (991, 1000): (5, 200, 1) 
        }

    def spin(self):
        rng = random.randint(1, 1000)
        for (low, high), result in self.ranges.items():
            if low <= rng <= high:
                return result
        return (1, 40, 1)

# ----------------------------------------------------------------

class DeucesWildSim:
    def __init__(self, variant="NSUD", denom=0.25):
        self.variant = variant
        self.denom = denom
        self.pay_table = PAYTABLES.get(variant, PAYTABLES["NSUD"])
        self.paytable = self.pay_table # Legacy Alias
        self.core = DeucesWildCore()
        
        # --- BET LOGIC (Fixes 'no attribute bet_amount') ---
        # DBW requires 10 coins (5 bet + 5 feature). Standard is 5.
        coins_per_hand = 10 if variant == "DBW" else 5
        self.bet_amount = denom * coins_per_hand
        
        # Wheel Logic
        if variant == "DBW":
            self.wheel = DeucesBonusWheel()
        else:
            self.wheel = None

    def set_variant(self, variant_name):
        if variant_name in PAYTABLES:
            self.variant = variant_name
            self.pay_table = PAYTABLES[variant_name]
            self.paytable = self.pay_table
            
            # Update Bet Logic on switch
            coins_per_hand = 10 if variant_name == "DBW" else 5
            self.bet_amount = self.denom * coins_per_hand
            
            if variant_name == "DBW":
                if self.wheel is None: self.wheel = DeucesBonusWheel()
            else:
                self.wheel = None
            print(f"Sim: Switched to {variant_name}")
        else:
            print(f"Sim: Variant {variant_name} not found.")

    def get_card_rank(self, card):
        ranks = "23456789TJQKA"
        return ranks.index(card[0])

    def normalize_input(self, hand_str):
        if isinstance(hand_str, list): return hand_str
        
        # 1. Convert '10' to 'T'
        temp = hand_str.replace("10", "T")
        
        # 2. Extract using Regex
        matches = re.findall(r'([2-9TJQKA][shdc])', temp, re.IGNORECASE)
        
        # 3. Standardize Case
        return [c[0].upper() + c[1].lower() for c in matches]

    def evaluate_hand(self, hand):
        return self.evaluate_hand_score(hand)

    def pro_strategy(self, hand):
        best_hold, _ = dw_exact_solver.solve_hand_silent(hand, self.pay_table)
        return best_hold

    def evaluate_hand_score(self, hand):
        """
        Main Evaluator (Standard + Bonus Logic).
        """
        ranks = [c[0] for c in hand]
        
        # --- FIXED FLUSH LOGIC ---
        # A flush relies ONLY on the suits of non-deuce cards.
        # If I have 3 Clubs and 2 Deuces (Heart, Spade), it IS a Club Flush.
        non_deuce_suits = [c[1] for c in hand if c[0] != '2']
        
        deuce_count = ranks.count('2')
        non_deuces = [r for r in ranks if r != '2']
        rank_counts = Counter(non_deuces)
        
        # If set has 0 (all deuces) or 1 item, it's a flush.
        is_flush = len(set(non_deuce_suits)) <= 1
        
        # 1. NATURAL ROYAL
        if deuce_count == 0 and is_flush:
            if set(ranks) == set("TJQKA"):
                return "NATURAL_ROYAL", self.pay_table["NATURAL_ROYAL"]

        # 2. FOUR DEUCES (Check Kicker)
        if deuce_count == 4:
            if non_deuces and non_deuces[0] == 'A':
                if "FOUR_DEUCES_ACE" in self.pay_table:
                    return "FOUR_DEUCES_ACE", self.pay_table["FOUR_DEUCES_ACE"]
            return "FOUR_DEUCES", self.pay_table["FOUR_DEUCES"]

        # 3. WILD ROYAL
        if is_flush:
            if all(r in set("TJQKA") for r in non_deuces):
                return "WILD_ROYAL", self.pay_table["WILD_ROYAL"]

        # 4. FIVE OF A KIND (Check 5 Aces)
        if non_deuces:
            most_common_rank, count = rank_counts.most_common(1)[0]
            total_count = count + deuce_count
        else:
            total_count = deuce_count

        if total_count >= 5:
            if non_deuces and all(r == 'A' for r in non_deuces):
                 if "FIVE_ACES" in self.pay_table:
                    return "FIVE_ACES", self.pay_table["FIVE_ACES"]
            return "FIVE_OAK", self.pay_table["FIVE_OAK"]

        # 5. STRAIGHT FLUSH
        if is_flush:
            idx_ranks = sorted([self.get_card_rank(r + 's') for r in non_deuces])
            if not idx_ranks:
                pass
            else:
                span = idx_ranks[-1] - idx_ranks[0]
                distinct_count = len(set(idx_ranks))
                valid_sf = False
                
                # Normal
                if span <= 4 and deuce_count >= (span + 1 - distinct_count):
                    valid_sf = True
                
                # Wheel
                if 12 in idx_ranks and not valid_sf:
                    wheel_ranks = sorted([-1 if r == 12 else r for r in idx_ranks])
                    w_span = wheel_ranks[-1] - wheel_ranks[0]
                    if w_span <= 4 and deuce_count >= (w_span + 1 - distinct_count):
                        valid_sf = True
                        
                if valid_sf:
                    return "STRAIGHT_FLUSH", self.pay_table["STRAIGHT_FLUSH"]

        # 6. FOUR OF A KIND
        if total_count >= 4:
            return "FOUR_OAK", self.pay_table["FOUR_OAK"]

        # 7. FULL HOUSE
        is_full_house = False
        if deuce_count == 0:
            if len(rank_counts) == 2 and 3 in rank_counts.values(): is_full_house = True
        elif deuce_count == 1:
            if len(rank_counts) == 2 and list(rank_counts.values()) == [2, 2]: is_full_house = True
        
        if is_full_house:
            return "FULL_HOUSE", self.pay_table["FULL_HOUSE"]

        # 8. FLUSH
        if is_flush:
            return "FLUSH", self.pay_table["FLUSH"]

        # 9. STRAIGHT
        idx_ranks = sorted([self.get_card_rank(r + 's') for r in non_deuces])
        distinct_ranks = sorted(list(set(idx_ranks)))
        span = distinct_ranks[-1] - distinct_ranks[0] if distinct_ranks else 0
        distinct_count = len(distinct_ranks)
        
        valid_straight = False
        if span <= 4 and deuce_count >= (5 - distinct_count):
             valid_straight = True
             
        if 12 in distinct_ranks and not valid_straight:
             wheel_ranks = sorted([-1 if r == 12 else r for r in distinct_ranks])
             w_span = wheel_ranks[-1] - wheel_ranks[0]
             if w_span <= 4 and deuce_count >= (5 - distinct_count):
                 valid_straight = True
                 
        if valid_straight:
            return "STRAIGHT", self.pay_table["STRAIGHT"]

        # 10. THREE OF A KIND
        if total_count >= 3:
            return "THREE_OAK", self.pay_table["THREE_OAK"]

        # 11. LOSER
        return "LOSER", 0