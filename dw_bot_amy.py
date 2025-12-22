"""
dw_bot_amy.py
THE ARTIFICIAL PLAYER (AMY)
Algorithmic Betting Agent.
Logic: Scales denomination based on "Window Ratio" (Recent Win Rate).
"""

from collections import deque

class AmyBot:
    def __init__(self, ladder, lines):
        self.ladder = ladder  # e.g., [0.05, 0.10, 0.25]
        self.lines = lines
        self.win_history = deque(maxlen=20) # Memory of recent results
        self.note = "" # Log output (e.g., "UP_10")

    def record_result(self, wins):
        """Adds the result of the last hand (lines won) to memory."""
        self.win_history.append(wins)

    def decide_denom(self, current_denom, current_bankroll, floor):
        """
        Decides the denomination for the NEXT hand.
        Returns: (new_denom, note_string)
        """
        self.note = ""
        
        # Ensure we have enough data to make a decision
        if len(self.ladder) < 3: 
            return current_denom, ""

        try: 
            level_idx = self.ladder.index(current_denom)
        except: 
            level_idx = 0
            current_denom = self.ladder[0]

        # Dynamic Window Size based on Aggression Level
        # Level 0 (Base): Needs 10 hands of proof to move up
        # Level 1 (Mid):  Needs 5 hands to move up
        # Level 2 (High): Needs only 3 bad hands to drop down
        window_size = 10 if level_idx == 0 else (5 if level_idx == 1 else 3)

        if len(self.win_history) < window_size:
            return current_denom, ""

        # Calculate "Window Ratio" (Win Rate over recent history)
        recent_wins = list(self.win_history)[-window_size:]
        win_sum = sum(recent_wins)
        ratio = win_sum / (self.lines * window_size)
        
        # Liquidity Check (Can we afford the next level?)
        liquidity = current_bankroll - floor
        cost_at_mid = self.ladder[1] * 5 * self.lines
        cost_at_high = self.ladder[2] * 5 * self.lines
        
        # LOGIC TREE
        
        # Case A: Climbing from Base (0.05 -> 0.10)
        if level_idx == 0:
            # Rule: 50% Win Rate + 10x Buy-in liquidity
            if ratio >= 0.5 and liquidity >= (cost_at_mid * 10):
                self.note = "UP_10"
                self.win_history.clear() # Reset memory on switch
                return self.ladder[1], self.note

        # Case B: Climbing from Mid (0.10 -> 0.25)
        elif level_idx == 1:
            if ratio >= 0.5 and liquidity >= (cost_at_high * 10):
                self.note = "UP_25"
                self.win_history.clear()
                return self.ladder[2], self.note
            # Rule: Retreat if cold
            elif ratio < 0.5:
                self.note = "DOWN_05"
                self.win_history.clear()
                return self.ladder[0], self.note

        # Case C: Defending High (0.25)
        elif level_idx >= 2:
            # Rule: Strict Retreat. Any weakness -> Drop.
            if ratio <= 0.5:
                self.note = "DOWN_05"
                self.win_history.clear()
                return self.ladder[0], self.note

        return current_denom, ""