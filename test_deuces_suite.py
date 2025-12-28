import unittest
import pandas as pd
import sys
import os

# Ensure we can import local modules
sys.path.append(os.getcwd())

from dw_sim_engine import DeucesWildSim
from dw_multihand_sim import run_multihand_session, ProtocolGuardian
# FIXED: Added PAYTABLES to the import list so tests can access it
from dw_exact_solver import calculate_exact_ev, evaluate_hand as solver_evaluate, PAYTABLES
from dw_pay_constants import PAYTABLES as MASTER_REGISTRY

# Optional Imports (Graceful degradation if files missing)
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

try:
    import dw_fast_solver
    FAST_SOLVER_AVAILABLE = True
except ImportError:
    FAST_SOLVER_AVAILABLE = False

# ==============================================================================
# 🧠 CORE ENGINE TESTS
# ==============================================================================
class TestHandEvaluator(unittest.TestCase):
    def setUp(self):
        self.sim = DeucesWildSim()

    def test_natural_royal(self):
        hand = ["Ad", "Kd", "Qd", "Jd", "Td"]
        rank, _ = self.sim.evaluate_hand_score(hand)
        self.assertEqual(rank, "NATURAL_ROYAL")

    def test_four_deuces(self):
        hand = ["2d", "2h", "2s", "2c", "5d"]
        rank, _ = self.sim.evaluate_hand_score(hand)
        self.assertEqual(rank, "FOUR_DEUCES")

    def test_wild_royal(self):
        hand = ["2d", "Kd", "Qd", "Jd", "Td"]
        rank, _ = self.sim.evaluate_hand_score(hand)
        self.assertEqual(rank, "WILD_ROYAL")

    def test_five_of_a_kind_nsud(self):
        hand = ["2d", "8h", "8s", "8c", "8d"]
        rank, _ = self.sim.evaluate_hand_score(hand)
        self.assertEqual(rank, "FIVE_OAK") 

    def test_wheel_straight_flush(self):
        hand = ["Ad", "2d", "3d", "4d", "5d"]
        rank, _ = self.sim.evaluate_hand_score(hand)
        self.assertEqual(rank, "STRAIGHT_FLUSH")

    def test_dirty_input_normalization(self):
        raw = "10h, 2s, 2C  5d AS" 
        clean = self.sim.normalize_input(raw)
        expected = ['Th', '2s', '2c', '5d', 'As'] 
        self.assertEqual(clean, expected)

    def test_dirty_flush_integration(self):
        hand = ["8h", "9h", "2d", "Qh", "6h"]
        rank, _ = self.sim.evaluate_hand_score(hand)
        self.assertEqual(rank, "FLUSH", "Sim Engine failed to identify Mixed-Suit Flush")

# ==============================================================================
# 🧩 BONUS DEUCES LOGIC TESTS
# ==============================================================================
class TestBonusDeucesLogic(unittest.TestCase):
    def setUp(self):
        self.sim_bonus = DeucesWildSim(variant="BONUS_DEUCES_10_4")
        self.sim_std = DeucesWildSim(variant="NSUD")

    def test_five_aces_detection(self):
        hand = ["2s", "Ah", "Ad", "Ac", "As"]
        rank_b, pay_b = self.sim_bonus.evaluate_hand_score(hand)
        self.assertEqual(rank_b, "FIVE_ACES")
        self.assertEqual(pay_b, 80)

        rank_s, pay_s = self.sim_std.evaluate_hand_score(hand)
        self.assertEqual(rank_s, "FIVE_OAK")
        self.assertEqual(pay_s, 16)

    def test_five_3_4_5_detection(self):
        hand = ["2s", "3h", "3d", "3c", "3s"]
        rank, pay = self.sim_bonus.evaluate_hand_score(hand)
        self.assertEqual(rank, "FIVE_3_4_5")
        self.assertEqual(pay, 40)

    def test_five_6_to_k_detection(self):
        hand = ["2s", "8h", "8d", "8c", "8s"]
        rank, pay = self.sim_bonus.evaluate_hand_score(hand)
        self.assertEqual(rank, "FIVE_6_TO_K")
        self.assertEqual(pay, 20)

    def test_four_deuces_with_ace(self):
        hand = ["2s", "2h", "2d", "2c", "As"]
        rank_b, pay_b = self.sim_bonus.evaluate_hand_score(hand)
        self.assertEqual(rank_b, "FOUR_DEUCES_ACE")
        self.assertEqual(pay_b, 400)
        
        rank_s, pay_s = self.sim_std.evaluate_hand_score(hand)
        self.assertEqual(rank_s, "FOUR_DEUCES")
        self.assertEqual(pay_s, 200)

    def test_four_deuces_no_kicker(self):
        hand = ["2s", "2h", "2d", "2c", "Ks"]
        rank_b, pay_b = self.sim_bonus.evaluate_hand_score(hand)
        self.assertEqual(rank_b, "FOUR_DEUCES")
        self.assertEqual(pay_b, 200)

# ==============================================================================
# 🔬 STRATEGY CLASSIFIER TESTS
# ==============================================================================
@unittest.skipUnless(GENERATOR_AVAILABLE, "Strategy Generator not importable")
class TestStrategyClassifier(unittest.TestCase):
    def test_classify_four_deuces_ace(self):
        hand = ['2s', '2c', '2h', '2d', 'As']
        label = classify_hold(hand)
        self.assertEqual(label, "4_DEUCES_ACE")

    def test_classify_generic_four_deuces(self):
        hand = ['2s', '2c', '2h', '2d', 'Ks']
        label = classify_hold(hand)
        self.assertEqual(label, "4_DEUCES")

    def test_classify_five_aces(self):
        hand = ['As', 'Ac', 'Ah', 'Ad', '2s']
        label = classify_hold(hand)
        self.assertEqual(label, "FIVE_ACES")

    def test_classify_five_3_4_5(self):
        hand = ['3s', '3c', '3h', '3d', '2s']
        label = classify_hold(hand)
        self.assertEqual(label, "FIVE_3_4_5")

    def test_classify_five_6_to_k(self):
        hand = ['Ks', 'Kc', 'Kh', 'Kd', '2s']
        label = classify_hold(hand)
        self.assertEqual(label, "FIVE_6_TO_K")

    def test_classify_natural_royal(self):
        hand = ['Ts', 'Js', 'Qs', 'Ks', 'As']
        label = classify_hold(hand)
        self.assertEqual(label, "NATURAL_ROYAL")

# ==============================================================================
# 🚀 FAST SOLVER & EV TESTS (UPDATED FOR v8.0)
# ==============================================================================
@unittest.skipUnless(FAST_SOLVER_AVAILABLE, "Fast Solver not importable")
class TestFastSolver(unittest.TestCase):
    def setUp(self):
        self.pt_bonus = MASTER_REGISTRY["BONUS_DEUCES_10_4"]

    def test_return_structure(self):
        """Verifies v8.0 returns (held, ev, metadata)"""
        hand = ['2s', '2h', '2c', '2d', '3s']
        result = dw_fast_solver.solve_hand(hand, self.pt_bonus)
        
        # --- FIXED ASSERTION FOR v8.0 ---
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3, "Failed v8.0 Signature Check: Expected 3 return values") 
        self.assertIsInstance(result[0], list)
        self.assertIsInstance(result[1], float)
        self.assertIsInstance(result[2], dict) # Metadata

    def test_fast_eval_bonus_math(self):
        """Verifies Fast Solver calculates correct EV for tiered hands."""
        # 5 Aces (Pay 80 * 5 = 400)
        hand_aces = ['As', 'Ac', 'Ah', 'Ad', '2s']
        
        # --- FIXED UNPACKING FOR v8.0 ---
        held, ev, meta = dw_fast_solver.solve_hand(hand_aces, self.pt_bonus)
        
        self.assertAlmostEqual(ev, 400.0, places=1)
        self.assertEqual(meta['rule_name'], 'FIVE ACES')

        # 5 Threes (Pay 40 * 5 = 200)
        hand_3s = ['3s', '3c', '3h', '3d', '2s']
        held, ev, meta = dw_fast_solver.solve_hand(hand_3s, self.pt_bonus)
        self.assertAlmostEqual(ev, 200.0, places=1)

        # 5 Eights (Pay 20 * 5 = 100)
        hand_8s = ['8s', '8c', '8h', '8d', '2s']
        held, ev, meta = dw_fast_solver.solve_hand(hand_8s, self.pt_bonus)
        self.assertAlmostEqual(ev, 100.0, places=1)

# ==============================================================================
# ⚖️ STRATEGY LOGIC TESTS
# ==============================================================================
class TestDualCoreStrategy(unittest.TestCase):
    def test_the_flush_trap(self):
        """
        The Famous Trap: 2 Deuces + Made Flush.
        Mathematically, you should BREAK the flush (Hold < 5 cards).
        """
        hand = ["2h", "2s", "4h", "Th", "Kh"] 
        
        # Test AIRPORT: Should Break
        sim_air = DeucesWildSim(variant="AIRPORT")
        held_air = sim_air.pro_strategy(hand)
        self.assertNotEqual(len(held_air), 5, "Airport: Should BREAK the flush")

        # Test NSUD: Should Break
        sim_nsud = DeucesWildSim(variant="NSUD")
        held_nsud = sim_nsud.pro_strategy(hand)
        self.assertNotEqual(len(held_nsud), 5, "NSUD: Should BREAK the flush")

        # Test DBW: Should Break
        sim_dbw = DeucesWildSim(variant="DBW")
        held_dbw = sim_dbw.pro_strategy(hand)
        self.assertNotEqual(len(held_dbw), 5, "DBW: Should BREAK the flush")

    def test_five_oak_payouts(self):
        nsud = DeucesWildSim(variant="NSUD")
        air = DeucesWildSim(variant="AIRPORT")
        dbw = DeucesWildSim(variant="DBW")
        self.assertEqual(nsud.paytable['FIVE_OAK'], 16)
        self.assertEqual(air.paytable['FIVE_OAK'], 12)
        self.assertEqual(dbw.paytable['FIVE_OAK'], 16)

    def test_straight_flush_payouts(self):
        nsud = DeucesWildSim(variant="NSUD")
        air = DeucesWildSim(variant="AIRPORT")
        dbw = DeucesWildSim(variant="DBW")
        self.assertEqual(nsud.paytable['STRAIGHT_FLUSH'], 10)
        self.assertEqual(air.paytable['STRAIGHT_FLUSH'], 9)
        self.assertEqual(dbw.paytable['STRAIGHT_FLUSH'], 13)

# ==============================================================================
# 🎮 SIMULATION CONTROLLER TESTS
# ==============================================================================
class TestSimController(unittest.TestCase):
    def test_session_execution_structure(self):
        hand_str = "2s 2h 5d 6c 9s"
        # Note: run_multihand_session now handles the v8.0 unpacking internally
        net, log_data = run_multihand_session(hand_str, 1, "NSUD", 0.25)
        
        self.assertIsInstance(net, float)
        self.assertIsInstance(log_data, dict)
        required_keys = ["Variant", "Action", "EV", "Net_Result", "Hit_Summary"]
        for k in required_keys: self.assertIn(k, log_data)
        self.assertIn("2s", log_data["Hand_Dealt"])

    def test_dbw_wheel_costs(self):
        sim_std = DeucesWildSim(variant="NSUD", denom=1.0)
        sim_dbw = DeucesWildSim(variant="DBW", denom=1.0)
        self.assertEqual(sim_std.variant, "NSUD")
        self.assertEqual(sim_dbw.variant, "DBW")
        self.assertEqual(sim_std.paytable["FLUSH"], 3)
        self.assertEqual(sim_dbw.paytable["FLUSH"], 2)

# ==============================================================================
# 🛡️ PROTOCOL GUARDIAN TESTS
# ==============================================================================
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

# ==============================================================================
# 🎯 EXACT SOLVER TESTS
# ==============================================================================
class TestExactSolver(unittest.TestCase):
    def setUp(self):
        self.pt = PAYTABLES["NSUD"]
        self.pt_bonus = MASTER_REGISTRY["BONUS_DEUCES_10_4"]

    def test_solver_royal_flush_ev(self):
        hand = ['ts', 'js', 'qs', 'ks', 'as']
        hold_indices = [0, 1, 2, 3, 4]
        ev = calculate_exact_ev(hand, hold_indices, self.pt)
        self.assertEqual(ev, 4000.0)

    def test_solver_case_insensitivity(self):
        hand_lower = ['ah', 'kh', 'qh', 'jh', 'th']
        payout = solver_evaluate(hand_lower, self.pt)
        self.assertEqual(payout, 4000)

    def test_solver_wild_flush_recognition(self):
        hand = ['2s', '4h', '8h', 'Kh', '2h']
        payout = solver_evaluate(hand, self.pt)
        self.assertEqual(payout, 15) 

    def test_solver_bonus_math(self):
        hand_5a = ['As', 'Ac', 'Ah', 'Ad', '2s']
        self.assertEqual(solver_evaluate(hand_5a, self.pt_bonus), 400)
        hand_4da = ['2s', '2c', '2h', '2d', 'As']
        self.assertEqual(solver_evaluate(hand_4da, self.pt_bonus), 2000)
    
    def test_four_deuces_bonus_ev_precision(self):
        hand = ['2s', '2h', '2c', '2d', '9s']
        hold_indices = [0, 1, 2, 3] 
        ev = calculate_exact_ev(hand, hold_indices, self.pt_bonus)
        expected = 51000 / 47
        self.assertAlmostEqual(ev, expected, places=4)

    def test_solver_dead_hand_ev(self):
        hand = ['2s', '2h', '2c', '2d', '3s']
        hold_indices = [0, 1, 2, 3] 
        ev = calculate_exact_ev(hand, hold_indices, self.pt)
        self.assertEqual(ev, 1000.0)

    def test_solver_evaluator_consistency(self):
        hand = ['2s', 'ts', 'js', 'ks', 'as'] 
        payout = solver_evaluate(hand, self.pt)
        self.assertEqual(payout, 125)

# ==============================================================================
# 🎡 WHEEL MECHANIC TESTS
# ==============================================================================
class TestWheelMechanic(unittest.TestCase):
    def setUp(self):
        self.sim = DeucesWildSim(variant="DBW")

    def test_wheel_init(self):
        self.assertTrue(hasattr(self.sim, 'wheel'))

    def test_spin_ranges(self):
        mult, w1, w2 = self.sim.wheel.spin()
        self.assertIn(w2, [1, 2, 3, 4])
        self.assertIsInstance(mult, int)
        self.assertGreaterEqual(mult, 1)

# ==============================================================================
# 📊 MISSION CONTROL TESTS
# ==============================================================================
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

# ==============================================================================
# 🧪 PAYTABLE INTEGRITY TESTS
# ==============================================================================
class TestPayTableQuarantine(unittest.TestCase):
    def test_single_source_of_truth(self):
        sim = DeucesWildSim(variant="NSUD")
        self.assertEqual(sim.paytable, MASTER_REGISTRY["NSUD"])

    def test_dbw_values_in_registry(self):
        self.assertEqual(MASTER_REGISTRY["DBW"]["FLUSH"], 2)
        self.assertEqual(MASTER_REGISTRY["DBW"]["STRAIGHT_FLUSH"], 13)

    def test_solver_integration(self):
        # We imported PAYTABLES from dw_exact_solver and MASTER from dw_pay_constants
        # They should match (dw_exact_solver usually imports from dw_pay_constants)
        self.assertEqual(PAYTABLES["NSUD"], MASTER_REGISTRY["NSUD"])

if __name__ == '__main__':
    print("========================================")
    print("🧬 DEUCES WILD INTEGRITY CHECK (v8.0)")
    print("========================================")
    unittest.main(verbosity=3)