import random
import itertools

class DeucesWildSim:
    def __init__(self, variant="NSUD", bankroll=40.00, denom=0.25, max_credits=5, floor=18.75, ceiling=60.00):
        self.variant = variant.upper()
        self.bankroll = float(bankroll)
        self.denom = float(denom)
        self.bet_amount = float(denom * max_credits)
        self.floor = float(floor)
        self.ceiling = float(ceiling)
        self.deal_count = 0
        
        # Paytables (Per Credit)
        self.paytable = {
            "ROYAL": 800, 
            "FOUR_DEUCES": 200, 
            "WILD_ROYAL": 25 if self.variant == "NSUD" else 20,
            "FIVE_OAK": 16 if self.variant == "NSUD" else 12,
            "STRAIGHT_FLUSH": 10 if self.variant == "NSUD" else 9,
            "FOUR_OAK": 4, 
            "FULL_HOUSE": 4 if self.variant == "NSUD" else 4, 
            "FLUSH": 3, 
            "STRAIGHT": 2, 
            "THREE_OAK": 1, 
            "NOTHING": 0
        }

    # --- CORE MECHANICS ---
    def get_deck(self):
        suits = ['s', 'h', 'd', 'c']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        deck = [r+s for r in ranks for s in suits]
        random.shuffle(deck)
        return deck

    def get_rank_val(self, card):
        r = card[0].upper()
        mapping = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
        return mapping[r]
    
    def normalize_input(self, hand_str):
        # Cleans input string "2h 10s" -> ['2h', 'Ts']
        parts = hand_str.strip().replace(',', ' ').split()
        clean = []
        for p in parts:
            p = p.upper().replace('10', 'T')
            clean.append(p[0] + p[1].lower())
        return clean

    def evaluate_hand(self, hand):
        ranks = [c[0].upper() for c in hand]
        # ✅ FIX: Get suits of NON-DEUCES only to check for flush
        non_deuce_suits = [c[1].lower() for c in hand if c[0] != '2']
        
        deuces = ranks.count('2')
        
        rank_vals = [self.get_rank_val(c) for c in hand if c[0] != '2']
        rank_vals.sort()
        
        # ✅ FIX: Flush logic: if no non-deuces (5 deuces impossible) or all non-deuces match suit
        if len(non_deuce_suits) == 0:
            is_flush = True
        else:
            is_flush = len(set(non_deuce_suits)) == 1
        
        # 1. Natural Royal
        if is_flush and deuces == 0 and set(ranks) == {'T','J','Q','K','A'}:
            return ("Natural Royal", self.paytable["ROYAL"])
        
        # 2. Four Deuces
        if deuces == 4: return ("Four Deuces", self.paytable["FOUR_DEUCES"])
        
        # 3. Wild Royal
        if is_flush:
            needed = {10,11,12,13,14}
            # Only checking subset against needed is safer
            if set(rank_vals).issubset(needed) and deuces > 0:
                 return ("Wild Royal", self.paytable["WILD_ROYAL"])

        # 4. Five of a Kind
        counts = {x:rank_vals.count(x) for x in set(rank_vals)}
        max_k = max(counts.values()) if counts else 0
        if deuces + max_k >= 5: return ("5 of a Kind", self.paytable["FIVE_OAK"])

        # 5. Straight Flush
        if is_flush:
            # Case A: Natural SF or Deuces filling gaps
            if not rank_vals: 
                return ("Straight Flush", self.paytable["STRAIGHT_FLUSH"])
            
            unique_vals = sorted(list(set(rank_vals)))
            gaps = 0
            for i in range(len(unique_vals)-1):
                gaps += (unique_vals[i+1] - unique_vals[i] - 1)
            
            if gaps <= deuces: 
                return ("Straight Flush", self.paytable["STRAIGHT_FLUSH"])
            
            # Case B: Wheel Check (A-2-3-4-5) where A is 14
            if 14 in unique_vals:
                # Treat A as 1
                wheel = [1 if x==14 else x for x in unique_vals]
                wheel.sort()
                gaps_w = 0
                for i in range(len(wheel)-1):
                    gaps_w += (wheel[i+1] - wheel[i] - 1)
                
                # We need to ensure the span is within 5 cards
                span_w = wheel[-1] - wheel[0]
                # Count distinct ranks needed to fill
                needed = span_w - (len(wheel) - 1)
                
                if needed <= deuces and span_w <= 4: 
                    return ("Straight Flush", self.paytable["STRAIGHT_FLUSH"])

        # 6. Four of a Kind
        if deuces + max_k >= 4: return ("4 of a Kind", self.paytable["FOUR_OAK"])

        # 7. Full House
        if deuces == 0:
            if 3 in counts.values() and 2 in counts.values(): return ("Full House", self.paytable["FULL_HOUSE"])
        if deuces == 1:
            if list(counts.values()).count(2) == 2: return ("Full House", self.paytable["FULL_HOUSE"])
            
        # 8. Flush
        if is_flush: return ("Flush", self.paytable["FLUSH"])
        
        # 9. Straight
        unique_vals = sorted(list(set(rank_vals)))
        if len(unique_vals) + deuces >= 5:
            # Standard
            span = unique_vals[-1] - unique_vals[0]
            if span <= 4: return ("Straight", self.paytable["STRAIGHT"])
            # Wheel
            if 14 in unique_vals:
                wheel = [1 if x==14 else x for x in unique_vals]
                wheel.sort()
                span_w = wheel[-1] - wheel[0]
                if span_w <= 4: return ("Straight", self.paytable["STRAIGHT"])

        # 10. Three of a Kind
        if deuces + max_k >= 3: return ("3 of a Kind", self.paytable["THREE_OAK"])
        
        return ("Nothing", 0)

    # --- HELPER METHODS FOR STRATEGY ---
    def get_repeated_cards(self, hand, count_needed):
        """Returns the specific cards that form a pair/trips/quads."""
        rank_map = {}
        for c in hand:
            r = c[0]
            if r not in rank_map: rank_map[r] = []
            rank_map[r].append(c)
        
        result = []
        for r in rank_map:
            if len(rank_map[r]) >= count_needed:
                result.extend(rank_map[r])
        return result

    def check_straight_flush_draw(self, cards):
        # Returns True if cards form a valid SF draw
        suits = [c[1] for c in cards]
        if len(set(suits)) != 1: return False
        vals = sorted([self.get_rank_val(c) for c in cards])
        if not vals: return True
        span = vals[-1] - vals[0]
        # Allow gaps, but span must be <= 4 (e.g. 5,9 is a draw? No, 5,6,7,9 is)
        # Simplified: Check if they are within a 5-card window
        return span <= 4

    def check_open_straight_draw(self, cards):
        # 4 cards, consecutive, no Ace
        vals = sorted([self.get_rank_val(c) for c in cards])
        if len(vals) != 4: return False
        if (vals[-1] - vals[0]) == 3:
            if 14 in vals: return False
            return True
        return False

    def pro_strategy(self, hand):
        # 🧬 STANDARD / OPTIMAL STRATEGY ENGINE
        
        deuces = [c for c in hand if c[0] == '2']
        non_deuces = [c for c in hand if c[0] != '2']
        current_rank, _ = self.evaluate_hand(hand)
        
        # --- 4 DEUCES ---
        if len(deuces) == 4: return hand

        # --- 3 DEUCES ---
        if len(deuces) == 3:
            if current_rank in ["Natural Royal", "Wild Royal", "5 of a Kind"]: return hand
            return deuces

        # --- 2 DEUCES ---
        if len(deuces) == 2:
            # 1. Top Hands
            if current_rank in ["Natural Royal", "Wild Royal", "5 of a Kind", "Straight Flush"]: 
                return hand
            
            # 2. 4 to Royal
            royals = {10,11,12,13,14}
            found_royal_draw = False
            for combo in itertools.combinations(non_deuces, 2):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals):
                    found_royal_draw = True
                    return deuces + list(combo)

            # 3. Made Flush / Straight Decisions
            if current_rank == "Flush":
                if self.variant == "AIRPORT":
                    # Airport: KEEP Made Flush (15.00 > 14.85)
                    return hand
                else:
                    # ✅ FIX: NSUD: BREAK Made Flush (16.37 > 15.00)
                    pass 
                
            if current_rank == "Straight":
                pass # Break it in both variants

            # 4. Made 4 of a Kind
            pair_cards = self.get_repeated_cards(non_deuces, 2)
            if pair_cards: return deuces + pair_cards

            # 5. 4 to Straight Flush
            for combo in itertools.combinations(non_deuces, 2):
                if self.check_straight_flush_draw(combo):
                    # ✅ FIX: Tightened Logic for 2 Deuces
                    # Only hold if Touching or 1-Gap (Span <= 2).
                    # A gap of 2 or more (e.g. 4-8, Span 4) is EV negative vs holding 2 Deuces.
                    vals = sorted([self.get_rank_val(c) for c in combo])
                    span = vals[-1] - vals[0]
                    if span <= 2:
                        return deuces + list(combo)

            # 6. Default: Hold 2 Deuces
            return deuces

        # --- 1 DEUCE ---
        if len(deuces) == 1:
            if current_rank in ["Natural Royal", "Wild Royal", "5 of a Kind", "Straight Flush"]: 
                return hand
            
            # 4 to Wild Royal
            royals = {10,11,12,13,14}
            for combo in itertools.combinations(non_deuces, 3):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals):
                    return deuces + list(combo)
            
            if current_rank == "Full House": return hand
            
            # Made Flush Logic
            if current_rank == "Flush":
                if self.variant == "AIRPORT":
                    return hand
                else:
                    return hand # NSUD Keep Flush > 1 Deuce

            if current_rank == "Straight":
                 return hand
            
            if current_rank == "4 of a Kind": return hand

            # 4 to Wild SF
            for combo in itertools.combinations(non_deuces, 3):
                if self.check_straight_flush_draw(combo):
                    return deuces + list(combo)
            
            # Made 3 of a Kind
            pair_cards = self.get_repeated_cards(non_deuces, 2)
            if pair_cards: return deuces + pair_cards
            
            # 3 to Wild Royal
            for combo in itertools.combinations(non_deuces, 2):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals):
                     return deuces + list(combo)
                     
            return deuces

        # --- 0 DEUCES ---
        if len(deuces) == 0:
            if current_rank == "Natural Royal": return hand
            
            if current_rank in ["Straight Flush", "4 of a Kind", "Full House", "Flush", "Straight", "3 of a Kind"]: 
                return hand
                
            royals = {10,11,12,13,14}
            # 4 to Royal
            for combo in itertools.combinations(non_deuces, 4):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals): return list(combo)

            # 4 to SF - Simplified
            for combo in itertools.combinations(non_deuces, 4):
                if self.check_straight_flush_draw(combo): return list(combo)
            
            # 3 to Royal
            for combo in itertools.combinations(non_deuces, 3):
                vals = {self.get_rank_val(c) for c in combo}
                suits = {c[1] for c in combo}
                if len(suits) == 1 and vals.issubset(royals): return list(combo)

            # 4 to Flush
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

    def run_specific_hand(self, raw_hand_str):
        # 1. Parse Input
        hand = self.normalize_input(raw_hand_str)
        if len(hand) != 5:
            return {"Error": "Invalid Hand"}
            
        initial_hand_str = " ".join(hand)
        
        # 2. Build Stub (Remaining 47 cards)
        full_deck = self.get_deck()
        stub = []
        user_cards_set = set(hand)
        for c in full_deck:
            if c not in user_cards_set:
                stub.append(c)
        
        # 3. Strategy
        held_cards = self.pro_strategy(hand)
        
        if len(held_cards) == 5: action_str = "Held All"
        elif len(held_cards) == 0: action_str = "Redraw"
        else: action_str = f"Held {' '.join(held_cards)}"
        
        # 4. Draw from Stub
        final_hand = held_cards[:]
        draw_count = 5 - len(final_hand)
        drawn_cards = stub[:draw_count]
        final_hand.extend(drawn_cards)
        
        # 5. Evaluate
        rank_name, payout_mult = self.evaluate_hand(final_hand)
        winnings = payout_mult * self.bet_amount
        start_bank = self.bankroll
        self.bankroll = self.bankroll - self.bet_amount + winnings
        change = self.bankroll - start_bank
        self.deal_count += 1
        
        return {
            "Deal": self.deal_count,
            "Start": initial_hand_str,
            "Action": action_str,
            "Result": rank_name,
            "Change": change,
            "Bankroll": self.bankroll
        }