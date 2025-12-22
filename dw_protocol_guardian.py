"""
dw_protocol_guardian.py
THE COMPLIANCE OFFICER
Enforces Bankroll Management Rules (Stop Loss / Take Profit).
"""

class ProtocolGuardian:
    def __init__(self, start_bankroll):
        self.start = start_bankroll
        self.spike_hand_idx = -1
        self.triggered = False
        self.trigger_reason = None
        
    def check(self, hands_played, current_bankroll):
        """
        Evaluates the session health against the Airport Protocol rules.
        Returns the trigger name (str) if a stop is required, else None.
        """
        if self.triggered: return self.trigger_reason
        
        # 1. SNIPER EXCEPTION (Win Limit: +20%)
        # Logic: If we hit a quick profit, leave before the house edge eats it.
        if current_bankroll >= (self.start * 1.20):
            self.triggered = True
            self.trigger_reason = "SNIPER_WIN"
            return "SNIPER_WIN"

        # 2. VACUUM CHECK (First 15 Hands: -25%)
        # Logic: If the machine is "cold" immediately, do not chase.
        if hands_played <= 15 and current_bankroll <= (self.start * 0.75):
            self.triggered = True
            self.trigger_reason = "VACUUM_STOP"
            return "VACUUM_STOP"

        # 3. THE TEASE (Sub-Surface Check)
        # Logic: We recovered to break-even, but immediately dipped again.
        if current_bankroll > self.start:
            self.spike_hand_idx = hands_played
            
        if self.spike_hand_idx != -1: # We surfaced once
            if current_bankroll < self.start: # Now underwater
                if (hands_played - self.spike_hand_idx) <= 5:
                    self.triggered = True
                    self.trigger_reason = "TEASE_EXIT"
                    return "TEASE_EXIT"

        # 4. ZOMBIE THRESHOLD (Hand 40)
        # Logic: If we are losing at Hand 40, we are "Walking Dead."
        if hands_played == 40 and current_bankroll < self.start:
            self.triggered = True
            self.trigger_reason = "ZOMBIE_LIMIT"
            return "ZOMBIE_LIMIT"

        # 5. HARD DECK (Hand 66)
        # Logic: Absolute session limit to prevent fatigue/grind.
        if hands_played >= 66:
            self.triggered = True
            self.trigger_reason = "HARD_DECK"
            return "HARD_DECK"
            
        return None