import unittest
import pandas as pd
from dw_sim_engine import DeucesWildSim
from dw_multihand_sim import ProtocolGuardian, run_multihand_session
from dw_exact_solver import normalize_hand, evaluate_hand, calculate_exact_ev, PAYTABLES
from dw_exact_solver import evaluate_hand as solver_evaluate

try:
    from dw_plot_tools import classify_session
    PLOT_TOOLS_AVAILABLE = True
except ImportError:
    PLOT_TOOLS_AVAILABLE = False

class TestHandEvaluator(unittest.TestCase):
    def setUp(self):
        self.sim = DeucesWildSim(variant="NSUD")

    def test_natural_royal(self):
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
        hand = ['2s', 'Ts', 'Js', 'Ks', 'As']
        rank, pay = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "Wild Royal")
        self.assertEqual(pay, 25)

    def test_five_of_a_kind_nsud(self):
        hand = ['2s', '2h', '5s', '5d', '5c']
        rank, pay = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "5 of a Kind")
        self.assertEqual(pay, 16)

    def test_wheel_straight_flush(self):
        hand = ['As', '3s', '4s', '5s', '2h'] 
        rank, pay = self.sim.evaluate_hand(hand)
        self.assertEqual(rank, "Straight Flush")

    def test_dirty_input_normalization(self):
        raw = "10h, 2s, 2C  5d AS" 
        clean = self.sim.normalize_input(raw)
        expected = ['Th', '2s', '2c', '5d', 'As']
        self.assertEqual(clean, expected)


class TestDualCoreStrategy(unittest.TestCase):
    def test_the_flush_trap(self):
        hand = ['2s', '2h', '4s', '8s', 'Js']
        nsud = DeucesWildSim(variant="NSUD")
        hold_nsud = nsud.pro_strategy(hand)
        self.assertEqual(len(hold_nsud), 2, f"NSUD should break this flush. Held: {hold_nsud}")
        
        airport = DeucesWildSim(variant="AIRPORT")
        hold_air = airport.pro_strategy(hand)
        self.assertEqual(len(hold_air), 5, "Airport should keep the flush")

    def test_five_oak_payouts(self):
        nsud = DeucesWildSim(variant="NSUD")
        air = DeucesWildSim(variant="AIRPORT")
        self.assertEqual(nsud.paytable['FIVE_OAK'], 16)
        self.assertEqual(air.paytable['FIVE_OAK'], 12)
        
    def test_straight_flush_payouts(self):
        nsud = DeucesWildSim(variant="NSUD")
        air = DeucesWildSim(variant="AIRPORT")
        self.assertEqual(nsud.paytable['STRAIGHT_FLUSH'], 10)
        self.assertEqual(air.paytable['STRAIGHT_FLUSH'], 9)


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

    def test_solver_royal_flush_ev(self):
        hand = ['ts', 'js', 'qs', 'ks', 'as']
        hold_indices = [0, 1, 2, 3, 4]
        ev = calculate_exact_ev(hand, hold_indices, self.pt)
        self.assertEqual(ev, 4000.0)

    def test_solver_dead_hand_ev(self):
        hand = ['2s', '2h', '2c', '2d', '3s']
        hold_indices = [0, 1, 2, 3] 
        ev = calculate_exact_ev(hand, hold_indices, self.pt)
        self.assertEqual(ev, 1000.0)

    def test_solver_evaluator_consistency(self):
        hand = ['2s', 'ts', 'js', 'ks', 'as'] 
        payout = solver_evaluate(hand, self.pt)
        self.assertEqual(payout, 25)


class TestSimController(unittest.TestCase):
    def test_session_execution_structure(self):
        hand_str = "2s 2h 5d 6c 9s"
        net, log_data = run_multihand_session(hand_str, 1, "NSUD", 0.25)
        
        self.assertIsInstance(net, float)
        self.assertIsInstance(log_data, dict)
        
        required_keys = ["Variant", "Action", "EV", "Net_Result", "Hit_Summary"]
        for k in required_keys:
            self.assertIn(k, log_data)
        self.assertEqual(log_data["Held_Cards"], "2s 2h")

    def test_dbw_wheel_costs(self):
        """
        [NEW] Verifies that enabling the Wheel correctly doubles the bet cost.
        """
        # FIX: Ensure hand is truly junk (High Card only)
        # 3s 5h 7d 9c Jk -> No pair, no straight, no flush
        hand_str = "3s 5h 7d 9c Js" 
        lines = 1
        denom = 1.00
        
        # 1. Standard Mode (5 coins cost)
        net_std, _ = run_multihand_session(hand_str, lines, "NSUD", denom, wheel_active=False)
        self.assertEqual(net_std, -5.0, "Standard bet should cost 5 coins")
        
        # 2. Wheel Mode (10 coins cost)
        net_wheel, _ = run_multihand_session(hand_str, lines, "DBW", denom, wheel_active=True)
        self.assertEqual(net_wheel, -10.0, "Wheel bet should cost 10 coins")


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


if __name__ == '__main__':
    print("========================================")
    print("🧬 DEUCES WILD INTEGRITY CHECK (v2.1)")
    print("========================================")
    unittest.main(verbosity=2)