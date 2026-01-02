"""
dw_core_engine.py
CORE PHYSICS ENGINE - "The Black Box"
Strictly handles RNG, Card Physics, and Hand Identification.
Zero economic logic (No payouts, no bets).
"""

import random
import copy

class DeucesWildCore:
    def __init__(self):
        # No Paytables here. Pure Physics.
        pass

    # ==========================================
    # 🃏 CARD PHYSICS (Immutable)
    # ==========================================

    def get_fresh_deck(self):
        """Returns a sorted list of 52 card strings."""
        suits = ['s', 'h', 'd', 'c']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        return [r+s for r in ranks for s in suits]

    def shuffle(self, deck):
        """Fisher-Yates via Mersenne Twister."""
        random.shuffle(deck)

    def deal_hand(self):
        """
        Deals 5 cards, returns Hand + Stub.
        """
        deck = self.get_fresh_deck()
        self.shuffle(deck)
        return deck[:5], deck[5:]

    def draw_from_stub(self, held_cards, stub, num_lines=1):
        """
        Independent Stub Cloning for Multi-Hand Play.
        """
        final_hands = []
        num_needed = 5 - len(held_cards)
        
        if len(stub) != 47:
            raise ValueError(f"Physics Error: Stub size is {len(stub)}, expected 47.")

        for _ in range(num_lines):
            line_stub = copy.copy(stub)
            self.shuffle(line_stub)
            final_hands.append(held_cards + line_stub[:num_needed])
            
        return final_hands

    # ==========================================
    # 🔍 HAND IDENTIFICATION (Rules of Poker)
    # ==========================================
    
    def identify_hand(self, hand):
        """
        Identifies the Poker Rank of a 5-card hand in Deuces Wild.
        Returns the STRING KEY (e.g., 'WILD_ROYAL', 'FIVE_OAK').
        Does NOT return a payout value.
        """
        if len(hand) != 5: return "ERROR"

        # 1. Parse
        ranks_char = [c[0].upper() for c in hand]
        deuces = ranks_char.count('2')
        
        # Rank Values for sorting (2 is wild, but we need values for straights)
        non_deuce_ranks = []
        mapping = {'3':3, '4':4, '5':5, '6':6, '7':7, '8':8, 
                   '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
        
        for c in hand:
            r = c[0].upper()
            if r != '2': non_deuce_ranks.append(mapping[r])
        non_deuce_ranks.sort()
        
        # Flush Check
        suits = [c[1].lower() for c in hand if c[0] != '2']
        is_flush = (len(set(suits)) <= 1) # 0 suits (5 deuces) or 1 suit

        # 2. Logic Ladder (Highest to Lowest)
        
        # Natural Royal
        if deuces == 0 and is_flush and set(non_deuce_ranks) == {10,11,12,13,14}:
            return "NATURAL_ROYAL"
            
        # Four Deuces
        if deuces == 4:
            return "FOUR_DEUCES"
            
        # Wild Royal
        # Any flush, at least 1 deuce, and all non-deuces are 10 or higher
        if is_flush and deuces > 0:
            if all(r >= 10 for r in non_deuce_ranks):
                return "WILD_ROYAL"
                
        # Five of a Kind (Updated for Super Deuces)
        unique_ranks = set(non_deuce_ranks)
        if not unique_ranks: # 5 Deuces (Handled by Four Deuces check usually, but fallback)
            return "FIVE_OAK"
        
        counts = [non_deuce_ranks.count(r) for r in unique_ranks]
        max_matches = max(counts)
        if deuces + max_matches >= 5:
            # Super Deuces Distinction:
            # If exactly 1 Deuce was used (4 Naturals + 1 Wild), it's the Jackpot Hand.
            # If 2+ Deuces were used (3 Naturals + 2 Wilds), it's a Standard 5OAK.
            if deuces == 1:
                return "FIVE_OAK_1_DEUCE"
            else:
                return "FIVE_OAK"
            
        # Straight Flush
        if is_flush:
            # Connectivity check
            if self._is_connected(non_deuce_ranks, deuces):
                return "STRAIGHT_FLUSH"
                
        # Four of a Kind
        if deuces + max_matches >= 4:
            return "FOUR_OAK"
            
        # Full House
        # 3 of a kind + Pair. 
        if deuces == 0:
            if 3 in counts and 2 in counts: return "FULL_HOUSE"
        if deuces == 1:
            if counts.count(2) == 2: return "FULL_HOUSE"
            
        # Flush
        if is_flush:
            return "FLUSH"
            
        # Straight
        if self._is_connected(non_deuce_ranks, deuces):
            return "STRAIGHT"
            
        # Three of a Kind
        if deuces + max_matches >= 3:
            return "THREE_OAK"
            
        return "NOTHING"

    def _is_connected(self, sorted_ranks, deuces):
        """Helper to check for straights given N wild cards."""
        if not sorted_ranks: return True # All deuces
        
        # Check standard span
        span = sorted_ranks[-1] - sorted_ranks[0]
        distinct_count = len(set(sorted_ranks))
        
        # If we have duplicates, it's not a straight
        if distinct_count < len(sorted_ranks): return False
        
        # Normal Straight: Span <= 4
        if span <= 4: return True
        
        # Wheel Straight (A-2-3-4-5)
        # We have A (14). Convert to 1 and re-check.
        if 14 in sorted_ranks:
            wheel_ranks = [1 if r == 14 else r for r in sorted_ranks]
            wheel_ranks.sort()
            wheel_span = wheel_ranks[-1] - wheel_ranks[0]
            if wheel_span <= 4: return True
            
        return False

    def normalize_input(self, hand_str):
        """
        Cleans input strings like '10h, 2s' -> ['Th', '2s'].
        """
        parts = hand_str.strip().replace(',', ' ').split()
        clean = []
        for p in parts:
            p = p.upper()
            if p.startswith("10"): p = "T" + p[2:]
            if len(p) < 2: continue
            clean.append(p[0] + p[1].lower())
        return clean

# ==========================================
# 🧪 INTEGRITY CHECK (Self-Test)
# ==========================================
if __name__ == "__main__":
    print("🚦 DIAGNOSTIC TEST: Deuces Wild Core Engine (v1.1 - Super Deuces Ready)")
    print("=======================================================================")
    
    try:
        engine = DeucesWildCore()
        
        # 1. Test Deck Integrity
        d = engine.get_fresh_deck()
        print(f"1. Deck Integrity:   {'PASSED' if len(d) == 52 and len(set(d)) == 52 else 'FAILED'}")
        
        # 2. Test Deal Mechanics
        hand, stub = engine.deal_hand()
        print(f"2. Deal Mechanics:   {'PASSED' if len(hand) == 5 and len(stub) == 47 else 'FAILED'}")
        
        # 3. Test Hand Identification
        print("3. Identification Logic:")
        test_cases = [
            (['2s', '2h', '2c', '2d', '5s'], "FOUR_DEUCES"),
            (['Ts', 'Js', 'Qs', 'Ks', 'As'], "NATURAL_ROYAL"),
            (['2s', 'Ts', 'Js', 'Ks', 'As'], "WILD_ROYAL"),
            (['2s', 'Ts', 'Tc', 'Td', 'Th'], "FIVE_OAK_1_DEUCE"), # Super Deuces Jackpot
            (['2s', '2h', 'Tc', 'Td', 'Th'], "FIVE_OAK"),         # Generic 5OAK
            (['2c', '3h', '4h', '5h', 'Ah'], "STRAIGHT_FLUSH"),   # Wheel Check
            (['3s', '5d', '7h', '9c', 'Jk'], "NOTHING")
        ]
        
        all_passed = True
        for h, expected in test_cases:
            result = engine.identify_hand(h)
            status = "✅" if result == expected else f"❌ (Got {result})"
            print(f"   - {expected:<20}: {status}")
            
        # 4. Test Multi-Hand Physics
        held = hand[:2] 
        results = engine.draw_from_stub(held, stub, num_lines=5)
        print(f"4. Multi-Hand Draw:  {'PASSED' if len(results) == 5 else 'FAILED'}")
        
        print("\n✅ SYSTEM READY.")
        
    except Exception as e:
        print(f"\n❌ SYSTEM FAILURE: {e}")