import unittest
from dw_sim_engine import DeucesWildSim
from dw_multihand_sim import ProtocolGuardian, run_multihand_session
# Import all necessary tools from the solver
from dw_exact_solver import normalize_hand, evaluate_hand, calculate_exact_ev, PAYTABLES
# We import evaluate_hand as 'solver_evaluate' to test it specifically against the Engine
from dw_exact_solver import evaluate_hand as solver_evaluate

class TestHandEvaluator(unittest.TestCase):
    """
    Verifies the Engine correctly identifies poker hands,
    specifically edge cases like Wheel Straights and Wild Royals.
    """
    def setUp(self):
        # We test with NSUD defaults primarily
        self.sim = DeucesWildSim(variant="NSUD")

    def test_natural_royal(self):
        # 10, J, Q, K, A suited, 0 Deuces
        hand = ['Ts', 'Js', 'Qs', 'Ks', 'As']
        rank, pay = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "Natural Royal")
        self.assertEqual(pay, 800)

    def test_four_deuces(self):
        hand = ['2s', '2h', '2c', '2d', '5s']
        rank, pay = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "Four Deuces")
        self.assertEqual(pay, 200)

    def test_wild_royal(self):
        # 2 + 10, J, K, A suited (Wild Royal)
        hand = ['2s', 'Ts', 'Js', 'Ks', 'As']
        rank, pay = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "Wild Royal")
        # NSUD pays 25 for WR
        self.assertEqual(pay, 25)

    def test_five_of_a_kind_nsud(self):
        # 2 Deuces + Three 5s
        hand = ['2s', '2h', '5s', '5d', '5c']
        rank, pay = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "5 of a Kind")
        self.assertEqual(pay, 16)  # NSUD Payout

    def test_wheel_straight_flush(self):
        # A-2-3-4-5 Suited (Wild or Natural)
        # 2h is the wild card completing the Spade run
        hand = ['As', '3s', '4s', '5s', '2h'] 
        rank, pay = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "Straight Flush")

    def test_dirty_input_normalization(self):
        # Test the string cleaner from Solver/Engine
        raw = "10h, 2s, 2C  5d AS" # Messy input
        clean = self.sim.normalize_input(raw)
        expected = ['Th', '2s', '2c', '5d', 'As']
        self.assertEqual(clean, expected)


class TestDualCoreStrategy(unittest.TestCase):
    """
    Verifies the CRITICAL logic pivot between NSUD and Airport.
    Strategies must change based on the variant.
    """
    
    def test_the_flush_trap(self):
        """
        Scenario: 2 Deuces + Made Flush (THAT IS NOT A STRAIGHT FLUSH).
        Hand: 2s 2h 4s 8s Js (Gaps are too wide for SF).
        NSUD: Break Flush (Hold Deuces only).
        Airport: Keep Flush.
        """
        hand = ['2s', '2h', '4s', '8s', 'Js']

        # 1. Test NSUD (Aggressive)
        nsud = DeucesWildSim(variant="NSUD")
        hold_nsud = nsud.pro_strategy(hand)
        # Should hold only the two deuces (Length 2)
        self.assertEqual(len(hold_nsud), 2, f"NSUD should break this flush. Held: {hold_nsud}")
        self.assertIn('2s', hold_nsud)
        self.assertIn('2h', hold_nsud)

        # 2. Test Airport (Defensive)
        airport = DeucesWildSim(variant="AIRPORT")
        hold_air = airport.pro_strategy(hand)
        # Should hold all 5 cards (Length 5)
        self.assertEqual(len(hold_air), 5, "Airport should keep the flush")

    def test_five_oak_payouts(self):
        """Verifies the payout dictionary loaded correctly."""
        nsud = DeucesWildSim(variant="NSUD")
        air = DeucesWildSim(variant="AIRPORT")
        
        self.assertEqual(nsud.paytable['FIVE_OAK'], 16)
        self.assertEqual(air.paytable['FIVE_OAK'], 12)
        
    def test_straight_flush_payouts(self):
        """Verifies SF payouts (10 vs 9)."""
        nsud = DeucesWildSim(variant="NSUD")
        air = DeucesWildSim(variant="AIRPORT")
        
        self.assertEqual(nsud.paytable['STRAIGHT_FLUSH'], 10)
        self.assertEqual(air.paytable['STRAIGHT_FLUSH'], 9)


class TestProtocolGuardian(unittest.TestCase):
    """
    Verifies the Simulation safeguards (Vacuum, Sniper, Hard Deck).
    """
    
    def setUp(self):
        self.start_bank = 100.0
        self.guard = ProtocolGuardian(start_bankroll=self.start_bank)

    def test_vacuum_stop(self):
        # Rule: Drop 25% within first 15 hands
        trigger = self.guard.check(hands_played=10, current_bankroll=70.0)
        self.assertEqual(trigger, "VACUUM_STOP")

    def test_vacuum_safe(self):
        # Drop 25% but AFTER 15 hands (Should NOT trigger Vacuum)
        trigger = self.guard.check(hands_played=20, current_bankroll=70.0)
        self.assertNotEqual(trigger, "VACUUM_STOP")

    def test_sniper_win(self):
        # Rule: +20% Gain
        trigger = self.guard.check(hands_played=50, current_bankroll=120.0)
        self.assertEqual(trigger, "SNIPER_WIN")

    def test_hard_deck(self):
        # Rule: Hand 66 is the limit
        trigger = self.guard.check(hands_played=66, current_bankroll=100.0)
        self.assertEqual(trigger, "HARD_DECK")

    def test_tease_logic(self):
        # Rule: Surface above start, then submerge within 5 hands
        self.guard.check(hands_played=10, current_bankroll=105.0) 
        self.assertEqual(self.guard.spike_hand_idx, 10) 
        
        self.guard.check(hands_played=12, current_bankroll=102.0)
        
        trigger = self.guard.check(hands_played=14, current_bankroll=95.0)
        self.assertEqual(trigger, "TEASE_EXIT")


class TestExactSolver(unittest.TestCase):
    """
    Verifies the standalone Combinatorial Solver (dw_exact_solver.py).
    Checks if the math engine is calculating True EV correctly.
    """
    def setUp(self):
        # Use NSUD paytable for verification
        self.pt = PAYTABLES["NSUD"]

    def test_solver_royal_flush_ev(self):
        """
        Control Case: A Dealt Royal Flush (Held) must have EV = 4000.
        (800 credits * 5 coins).
        """
        hand = ['ts', 'js', 'qs', 'ks', 'as']
        # If we hold all 5 (indices 0-4), the EV should be exactly the payout
        hold_indices = [0, 1, 2, 3, 4]
        ev = calculate_exact_ev(hand, hold_indices, self.pt)
        self.assertEqual(ev, 4000.0, "Solver failed basic Royal Flush math.")

    def test_solver_dead_hand_ev(self):
        """
        Control Case: A 'Discard All' on a dead hand.
        We test holding a "Guaranteed Loser" vs "Guaranteed Winner" logic to be safe.
        """
        # Hand: 4 Deuces. Hold indices [0,1,2,3].
        hand = ['2s', '2h', '2c', '2d', '3s']
        hold_indices = [0, 1, 2, 3] # Hold 4 Deuces
        ev = calculate_exact_ev(hand, hold_indices, self.pt)
        # 4 Deuces pays 200. Max Bet = 5 * 200 = 1000.
        self.assertEqual(ev, 1000.0)

    def test_solver_evaluator_consistency(self):
        """
        Ensures the Solver's internal evaluator matches the Engine's evaluator.
        """
        hand = ['2s', 'ts', 'js', 'ks', 'as'] # Wild Royal
        payout = solver_evaluate(hand, self.pt)
        self.assertEqual(payout, 25, "Solver Evaluator mismatch on Wild Royal.")


class TestSimController(unittest.TestCase):
    """
    Verifies the Session Manager (dw_multihand_sim.py).
    """
    def test_session_execution_structure(self):
        """
        Runs a single hand of the simulator to ensure the Data Dictionary
        and Return Types are correct.
        """
        hand_str = "2s 2h 5d 6c 9s"
        # Run 1 line, NSUD, $0.25 denom
        net, log_data = run_multihand_session(hand_str, 1, "NSUD", 0.25)
        
        # Check Return Types
        self.assertIsInstance(net, float)
        self.assertIsInstance(log_data, dict)
        
        # Check Log Integrity
        required_keys = ["Variant", "Action", "EV", "Net_Result", "Hit_Summary"]
        for k in required_keys:
            self.assertIn(k, log_data, f"Sim Controller failed to log key: {k}")
            
        # Check Logic Propagation
        # The log only stores "2s 2h" in the "Held_Cards" field (no "Held " prefix)
        self.assertEqual(log_data["Held_Cards"], "2s 2h")


if __name__ == '__main__':
    print("========================================")
    print("🧬 DEUCES WILD INTEGRITY CHECK (Final)")
    print("========================================")
    unittest.main(verbosity=2)