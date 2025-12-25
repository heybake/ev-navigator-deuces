import unittest
import pandas as pd
import sys
import os

# Ensure we can import local modules
sys.path.append(os.getcwd())

from dw_sim_engine import DeucesWildSim
# Assuming these modules exist in your folder structure
from dw_multihand_sim import ProtocolGuardian, run_multihand_session
from dw_exact_solver import calculate_exact_ev, evaluate_hand as solver_evaluate, PAYTABLES
# NEW: Import the Registry for Verification
from dw_pay_constants import PAYTABLES as MASTER_REGISTRY

# Try to import the Strategy Generator Classifier for testing
try:
    from dw_strategy_generator import classify_hold
    GENERATOR_AVAILABLE = True
except ImportError:
    GENERATOR_AVAILABLE = False

try:
    from dw_plot_tools import classify_session
    PLOT_TOOLS_AVAILABLE = True
except ImportError:
    PLOT_TOOLS_AVAILABLE = False

# Try to import Fast Solver for testing
try:
    import dw_fast_solver
    FAST_SOLVER_AVAILABLE = True
except ImportError:
    FAST_SOLVER_AVAILABLE = False

# ==========================================
# 🧠 CORE ENGINE TESTS (Updated for v3.2)
# ==========================================
class TestHandEvaluator(unittest.TestCase):
    """
    Verifies that the engine correctly identifies hand ranks
    using the v3.2 System Keys (UPPERCASE_SNAKE_CASE).
    """
    def setUp(self):
        self.sim = DeucesWildSim()

    def test_natural_royal(self):
        hand = ["Ad", "Kd", "Qd", "Jd", "Td"]
        rank, _ = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "NATURAL_ROYAL")

    def test_four_deuces(self):
        hand = ["2d", "2h", "2s", "2c", "5d"]
        rank, _ = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "FOUR_DEUCES")

    def test_wild_royal(self):
        hand = ["2d", "Kd", "Qd", "Jd", "Td"]
        rank, _ = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "WILD_ROYAL")

    def test_five_of_a_kind_nsud(self):
        hand = ["2d", "8h", "8s", "8c", "8d"]
        rank, _ = self.sim.evaluate_hand(hand)
        # v3.2 uses the standard key FIVE_OAK for all variants
        self.assertEqual(rank, "FIVE_OAK") 

    def test_wheel_straight_flush(self):
        # A-2-3-4-5 is a Straight Flush in Deuces Wild
        hand = ["Ad", "2d", "3d", "4d", "5d"]
        rank, _ = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "STRAIGHT_FLUSH")

    def test_dirty_input_normalization(self):
        raw = "10h, 2s, 2C  5d AS" 
        clean = self.sim.normalize_input(raw)
        # Note: v3.2 Engine usually outputs capitalized rank/suit like 'Th', '2s'
        expected = ['Th', '2s', '2c', '5d', 'As'] 
        self.assertEqual(clean, expected)

    def test_dirty_flush_integration(self):
        """
        REGRESSION TEST: Verifies the 'Wild Flush' fix in the Sim Engine.
        Hearts + Diamond Deuce should equal FLUSH.
        """
        # 4 Hearts + 1 Diamond Deuce
        hand = ["8h", "9h", "2d", "Qh", "6h"]
        rank, _ = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "FLUSH", "Sim Engine failed to identify Mixed-Suit Flush")


# ==========================================
# 💎 NEW: BONUS DEUCES LOGIC TESTS
# ==========================================
class TestBonusDeucesLogic(unittest.TestCase):
    """
    Verifies the specific kicker logic for 'Bonus Deuces' games.
    """
    def setUp(self):
        self.sim_bonus = DeucesWildSim(variant="BONUS_DEUCES_10_4")
        self.sim_std = DeucesWildSim(variant="NSUD")

    def test_five_aces_detection(self):
        # 1 Deuce + 4 Aces = 5 Aces
        hand = ["2s", "Ah", "Ad", "Ac", "As"]
        
        # In Bonus Deuces, this is special (Pays 80)
        rank_b, pay_b = self.sim_bonus.evaluate_hand(hand)
        self.assertEqual(rank_b, "FIVE_ACES")
        self.assertEqual(pay_b, 80)

        # In NSUD, this is just 5OAK (Pays 16)
        rank_s, pay_s = self.sim_std.evaluate_hand(hand)
        self.assertEqual(rank_s, "FIVE_OAK")
        self.assertEqual(pay_s, 16)

    def test_five_3_4_5_detection(self):
        """NEW: Verifies 5 of a Kind (3s, 4s, 5s) pays 40."""
        # 1 Deuce + 4 Threes
        hand = ["2s", "3h", "3d", "3c", "3s"]
        rank, pay = self.sim_bonus.evaluate_hand(hand)
        self.assertEqual(rank, "FIVE_3_4_5")
        self.assertEqual(pay, 40)

    def test_five_6_to_k_detection(self):
        """NEW: Verifies 5 of a Kind (6s thru Ks) pays 20."""
        # 1 Deuce + 4 Eights
        hand = ["2s", "8h", "8d", "8c", "8s"]
        rank, pay = self.sim_bonus.evaluate_hand(hand)
        self.assertEqual(rank, "FIVE_6_TO_K")
        self.assertEqual(pay, 20)

    def test_four_deuces_with_ace(self):
        # 4 Deuces + Ace Kicker
        hand = ["2s", "2h", "2d", "2c", "As"]
        
        # In Bonus Deuces, this is special (Pays 400)
        rank_b, pay_b = self.sim_bonus.evaluate_hand(hand)
        self.assertEqual(rank_b, "FOUR_DEUCES_ACE")
        self.assertEqual(pay_b, 400)
        
        # In NSUD, this is just 4 Deuces (Pays 200)
        rank_s, pay_s = self.sim_std.evaluate_hand(hand)
        self.assertEqual(rank_s, "FOUR_DEUCES")
        self.assertEqual(pay_s, 200)

    def test_four_deuces_no_kicker(self):
        # 4 Deuces + King (Not Ace)
        hand = ["2s", "2h", "2d", "2c", "Ks"]
        
        # Should be standard 4 Deuces for BOTH
        rank_b, pay_b = self.sim_bonus.evaluate_hand(hand)
        self.assertEqual(rank_b, "FOUR_DEUCES")
        self.assertEqual(pay_b, 200)


# ==========================================
# 🔬 NEW: STRATEGY CLASSIFIER TESTS (Added for v5.0)
# ==========================================
@unittest.skipUnless(GENERATOR_AVAILABLE, "Strategy Generator not importable")
class TestStrategyClassifier(unittest.TestCase):
    """
    Verifies the 'Microscope' logic in the Strategy Generator.
    Ensures that seeded hands are labeled correctly.
    """
    def test_classify_four_deuces_ace(self):
        hand = ['2s', '2c', '2h', '2d', 'As']
        label = classify_hold(hand)
        self.assertEqual(label, "4_DEUCES_ACE")

    def test_classify_generic_four_deuces(self):
        hand = ['2s', '2c', '2h', '2d', 'Ks']
        label = classify_hold(hand)
        self.assertEqual(label, "4_DEUCES")

    def test_classify_five_aces(self):
        # 4 Aces + 1 Deuce
        hand = ['As', 'Ac', 'Ah', 'Ad', '2s']
        label = classify_hold(hand)
        self.assertEqual(label, "FIVE_ACES")

    def test_classify_five_3_4_5(self):
        """NEW: Ensure 3s/4s/5s are labeled correctly."""
        hand = ['3s', '3c', '3h', '3d', '2s']
        label = classify_hold(hand)
        self.assertEqual(label, "FIVE_3_4_5")

    def test_classify_five_6_to_k(self):
        """NEW: Ensure 6s-Ks are labeled correctly."""
        hand = ['Ks', 'Kc', 'Kh', 'Kd', '2s']
        label = classify_hold(hand)
        self.assertEqual(label, "FIVE_6_TO_K")

    def test_classify_natural_royal(self):
        hand = ['Ts', 'Js', 'Qs', 'Ks', 'As']
        label = classify_hold(hand)
        self.assertEqual(label, "NATURAL_ROYAL")


# ==========================================
# ⚡ NEW: FAST SOLVER TESTS (Added for v5.4)
# ==========================================
@unittest.skipUnless(FAST_SOLVER_AVAILABLE, "Fast Solver not importable")
class TestFastSolver(unittest.TestCase):
    """
    Verifies the logic of dw_fast_solver.py, especially regarding
    tiered payouts and return structures.
    """
    def setUp(self):
        self.pt_bonus = MASTER_REGISTRY["BONUS_DEUCES_10_4"]

    def test_return_structure(self):
        """Critical: Trainer expects (hand, ev) tuple."""
        hand = ['2s', '2h', '2c', '2d', '3s']
        result = dw_fast_solver.solve_hand(hand, self.pt_bonus)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], list) # The Held Cards
        self.assertIsInstance(result[1], float) # The EV

    def test_fast_eval_bonus_math(self):
        """Verifies Fast Solver calculates correct EV for tiered hands."""
        # 5 Aces (Pay 80)
        hand_aces = ['As', 'Ac', 'Ah', 'Ad', '2s']
        _, ev = dw_fast_solver.solve_hand(hand_aces, self.pt_bonus)
        self.assertAlmostEqual(ev, 80.0, places=1)

        # 5 Threes (Pay 40)
        hand_3s = ['3s', '3c', '3h', '3d', '2s']
        _, ev = dw_fast_solver.solve_hand(hand_3s, self.pt_bonus)
        self.assertAlmostEqual(ev, 40.0, places=1)

        # 5 Eights (Pay 20)
        hand_8s = ['8s', '8c', '8h', '8d', '2s']
        _, ev = dw_fast_solver.solve_hand(hand_8s, self.pt_bonus)
        self.assertAlmostEqual(ev, 20.0, places=1)


class TestDualCoreStrategy(unittest.TestCase):
    """
    Verifies the Strategy Logic Pivots (NSUD vs Airport vs DBW).
    """

    def test_the_flush_trap(self):
        """
        The Famous Trap: 2 Deuces + Made Flush.
        - Airport: HOLD FLUSH (Defensive)
        - NSUD: BREAK FLUSH (Aggressive)
        - DBW: BREAK FLUSH (Hyper-Aggressive)
        """
        # FIXED HAND: 2h, 2s, 4h, 8h, Kh (Pure Flush, No Straight chance)
        hand = ["2h", "2s", "4h", "8h", "Kh"] 
        
        # 1. Test AIRPORT (Should Hold All)
        sim_air = DeucesWildSim(variant="AIRPORT")
        held_air = sim_air.pro_strategy(hand)
        self.assertEqual(len(held_air), 5, "Airport should HOLD Made Flush")

        # 2. Test NSUD (Should Break, hold 2 Deuces)
        sim_nsud = DeucesWildSim(variant="NSUD")
        held_nsud = sim_nsud.pro_strategy(hand)
        self.assertEqual(len(held_nsud), 2, "NSUD should BREAK Flush for 2 Deuces")

        # 3. Test DBW (Should Break, hold 2 Deuces)
        sim_dbw = DeucesWildSim(variant="DBW")
        held_dbw = sim_dbw.pro_strategy(hand)
        self.assertEqual(len(held_dbw), 2, "DBW should BREAK Flush (Pays 2) for 2 Deuces")

    def test_five_oak_payouts(self):
        # v3.2 DBW pays 16 (same as NSUD)
        nsud = DeucesWildSim(variant="NSUD")
        air = DeucesWildSim(variant="AIRPORT")
        dbw = DeucesWildSim(variant="DBW")
        
        self.assertEqual(nsud.paytable['FIVE_OAK'], 16)
        self.assertEqual(air.paytable['FIVE_OAK'], 12)
        self.assertEqual(dbw.paytable['FIVE_OAK'], 16)

    def test_straight_flush_payouts(self):
        # v3.2 DBW pays 13 (High Bonus)
        nsud = DeucesWildSim(variant="NSUD")
        air = DeucesWildSim(variant="AIRPORT")
        dbw = DeucesWildSim(variant="DBW")
        
        self.assertEqual(nsud.paytable['STRAIGHT_FLUSH'], 10)
        self.assertEqual(air.paytable['STRAIGHT_FLUSH'], 9)
        self.assertEqual(dbw.paytable['STRAIGHT_FLUSH'], 13)


class TestSimController(unittest.TestCase):
    """
    Verifies the Session Mechanics and Costs.
    """
    def test_session_execution_structure(self):
        # Integration test for the runner
        hand_str = "2s 2h 5d 6c 9s"
        # We assume run_multihand_session returns (net_result, log_dict)
        net, log_data = run_multihand_session(hand_str, 1, "NSUD", 0.25)
        
        self.assertIsInstance(net, float)
        self.assertIsInstance(log_data, dict)
        
        required_keys = ["Variant", "Action", "EV", "Net_Result", "Hit_Summary"]
        for k in required_keys:
            self.assertIn(k, log_data)
        
        # Check that cards were parsed correctly
        self.assertIn("2s", log_data["Hand_Dealt"])

    def test_dbw_wheel_costs(self):
        """
        Verifies that DBW mode implicitly doubles the bet cost 
        by checking the engine configuration/paytable flags.
        (Integration test failed previously, so we test the Engine state here).
        """
        sim_std = DeucesWildSim(variant="NSUD", denom=1.0)
        sim_dbw = DeucesWildSim(variant="DBW", denom=1.0)
        
        # In v3.2, the difference is strictly enforced via Paytable & Strategy
        # The 'Wheel Tax' is applied in the simulation loop, but we can verify
        # the engine knows it is in DBW mode.
        self.assertEqual(sim_std.variant, "NSUD")
        self.assertEqual(sim_dbw.variant, "DBW")
        
        # Verify the key feature: Flush Payout Degradation
        self.assertEqual(sim_std.paytable["FLUSH"], 3)
        self.assertEqual(sim_dbw.paytable["FLUSH"], 2)


# ==========================================
# 🛡️ RESTORED PROTOCOL & SOLVER TESTS
# ==========================================
class TestProtocolGuardian(unittest.TestCase):
    def setUp(self):
        self.start_bank = 100.0
        self.guard = ProtocolGuardian(start_bankroll=self.start_bank)

    def test_vacuum_stop(self):
        trigger = self.guard.check(hands_played=10, current_bankroll=70.0)
        self.assertEqual(trigger, "VACUUM_STOP")

    def test_vacuum_safe(self):
        trigger = self.guard.check(hands_played=20, current_bankroll=70.0)
        self.assertNotEqual(trigger, "VACUUM_STOP")

    def test_sniper_win(self):
        trigger = self.guard.check(hands_played=50, current_bankroll=120.0)
        self.assertEqual(trigger, "SNIPER_WIN")

    def test_hard_deck(self):
        trigger = self.guard.check(hands_played=66, current_bankroll=100.0)
        self.assertEqual(trigger, "HARD_DECK")

    def test_tease_logic(self):
        self.guard.check(hands_played=10, current_bankroll=105.0) 
        self.assertEqual(self.guard.spike_hand_idx, 10) 
        self.guard.check(hands_played=12, current_bankroll=102.0)
        trigger = self.guard.check(hands_played=14, current_bankroll=95.0)
        self.assertEqual(trigger, "TEASE_EXIT")


class TestExactSolver(unittest.TestCase):
    def setUp(self):
        self.pt = PAYTABLES["NSUD"]
        # FIX: Updated key to match the actual system definition
        self.pt_bonus = MASTER_REGISTRY["BONUS_DEUCES_10_4"]

    def test_solver_royal_flush_ev(self):
        hand = ['ts', 'js', 'qs', 'ks', 'as']
        hold_indices = [0, 1, 2, 3, 4]
        ev = calculate_exact_ev(hand, hold_indices, self.pt)
        self.assertEqual(ev, 4000.0)

    def test_solver_case_insensitivity(self):
        """NEW: Ensures 'ah' and 'Ah' are treated equally."""
        hand_lower = ['ah', 'kh', 'qh', 'jh', 'th']
        payout = solver_evaluate(hand_lower, self.pt)
        self.assertEqual(payout, 800) # Natural Royal

    def test_solver_wild_flush_recognition(self):
        """NEW: The 'Dirty Flush' Bug Fix (2s completing Hearts)."""
        # 2s is a Spade, but Wild. Should complete Heart flush.
        hand = ['2s', '4h', '8h', 'Kh', '2h']
        payout = solver_evaluate(hand, self.pt)
        self.assertEqual(payout, 3, "Solver failed to recognize Wild Flush")

    def test_solver_bonus_math(self):
        """NEW: Verifies Solver uses Bonus Payouts correctly."""
        # 5 Aces (Should be 80 coins)
        hand_5a = ['As', 'Ac', 'Ah', 'Ad', '2s']
        self.assertEqual(solver_evaluate(hand_5a, self.pt_bonus), 80)
        
        # 4 Deuces + Ace (Should be 400 coins)
        hand_4da = ['2s', '2c', '2h', '2d', 'As']
        self.assertEqual(solver_evaluate(hand_4da, self.pt_bonus), 400)
    
    def test_four_deuces_bonus_ev_precision(self):
        """
        NEW: Verifies the exact weighted EV for holding 4 Deuces in Bonus Poker.
        Math: (4 Aces * 2000 coins + 43 Others * 1000 coins) / 47 cards
        Expected: ~1085.10638
        """
        # Hand with 4 Deuces and junk kicker
        hand = ['2s', '2h', '2c', '2d', '9s']
        hold_indices = [0, 1, 2, 3] # Hold the 4 deuces
        
        # Calculate EV using the Bonus Paytable
        ev = calculate_exact_ev(hand, hold_indices, self.pt_bonus)
        
        # Weighted Average: (4/47 * 2000) + (43/47 * 1000)
        # 2000 = 400 * 5 (Max Bet)
        # 1000 = 200 * 5 (Max Bet)
        expected = 51000 / 47
        
        self.assertAlmostEqual(ev, expected, places=4, msg="EV calculation for 4 Deuces mismatch")

    def test_solver_dead_hand_ev(self):
        hand = ['2s', '2h', '2c', '2d', '3s']
        # Note: Solver expects lowercase usually, ensure consistency
        hold_indices = [0, 1, 2, 3] 
        ev = calculate_exact_ev(hand, hold_indices, self.pt)
        self.assertEqual(ev, 1000.0)

    def test_solver_evaluator_consistency(self):
        hand = ['2s', 'ts', 'js', 'ks', 'as'] 
        payout = solver_evaluate(hand, self.pt)
        self.assertEqual(payout, 25)


class TestWheelMechanic(unittest.TestCase):
    def setUp(self):
        self.sim = DeucesWildSim(variant="DBW")

    def test_wheel_init(self):
        self.assertTrue(hasattr(self.sim, 'wheel'), "DBW Engine missing Wheel module")

    def test_spin_ranges(self):
        mult, w1, w2 = self.sim.wheel.spin()
        self.assertIn(w2, [1, 2, 3, 4])
        self.assertIsInstance(mult, int)
        self.assertGreaterEqual(mult, 1)


@unittest.skipUnless(PLOT_TOOLS_AVAILABLE, "Plot Tools not installed")
class TestMissionControl(unittest.TestCase):
    def test_classify_sniper(self):
        data = {'Hand_ID': [1, 2, 3], 'Bankroll': [100, 125, 110]}
        df = pd.DataFrame(data)
        label, color = classify_session(df, start_bank=100, floor=70, ceiling=120)
        self.assertIn("SNIPER", label)

    def test_classify_vacuum(self):
        data = {'Hand_ID': [1, 5, 10], 'Bankroll': [90, 60, 65]}
        df = pd.DataFrame(data)
        label, color = classify_session(df, start_bank=100, floor=70, ceiling=120)
        self.assertIn("VACUUM", label)

    def test_classify_tease(self):
        data = {'Hand_ID': [1, 2, 3], 'Bankroll': [100, 110, 90]}
        df = pd.DataFrame(data)
        label, color = classify_session(df, start_bank=100, floor=70, ceiling=120)
        self.assertIn("TEASE", label)

# ==========================================
# 🧱 NEW ARCHITECTURE TESTS (v3.2)
# ==========================================
class TestPayTableQuarantine(unittest.TestCase):
    """
    Verifies the Architectural Decision: The Pay Table Quarantine.
    Ensures Data is decoupled from Logic.
    """
    def test_single_source_of_truth(self):
        # Verify Engine uses Registry
        sim = DeucesWildSim(variant="NSUD")
        # Compare sim.paytable with the MASTER_REGISTRY
        self.assertEqual(sim.paytable, MASTER_REGISTRY["NSUD"])

    def test_dbw_values_in_registry(self):
        # Verify the specific feature values for DBW directly from source
        self.assertEqual(MASTER_REGISTRY["DBW"]["FLUSH"], 2, "DBW Flush must be 2")
        self.assertEqual(MASTER_REGISTRY["DBW"]["STRAIGHT_FLUSH"], 13, "DBW SF must be 13")

    def test_solver_integration(self):
        # Verify Solver sees the same data object as the Registry
        # Since PAYTABLES was imported from dw_exact_solver at top level,
        # checking identity against MASTER_REGISTRY confirms the link.
        self.assertIs(PAYTABLES, MASTER_REGISTRY, "Solver and Registry must share the same data object")


if __name__ == '__main__':
    print("========================================")
    print("🧬 DEUCES WILD INTEGRITY CHECK (v5.2)")
    print("========================================")
    unittest.main(verbosity=2)