import multiprocessing
import os
import csv
import time
from datetime import datetime
import dw_sim_engine
import dw_fast_solver
import dw_exact_solver

# ==============================================================================
# 🕵️ STRATEGY AUDITOR (MULTICORE EDITION)
# ==============================================================================
# - Runs on all available CPU cores
# - Saves report to /strategy_reports/strategy_audit_YYYYMMDD_HHMMSS.csv
# ==============================================================================

# --- THE MASTER TEST SUITE ---
TEST_SUITE = [
    # ==============================================================================
    # 🦆 NSUD (NOT SO UGLY DEUCES)
    # ==============================================================================
    ("NSUD", "2s 2c 2h 2d As", "Natural Royal (Impossible check)"), 
    ("NSUD", "2s 2c 2h 2d 5s", "4 Deuces"),
    ("NSUD", "2s 2c 2h Ts Qs", "Wild Royal (Pat)"),
    ("NSUD", "2s 2c 2h 9s 9d", "5 of a Kind (6-K) -> Holds 3 Deuces"),
    ("NSUD", "2s 2c 2h 3s 3d", "5 of a Kind (3-5) -> Holds 3 Deuces"),
    ("NSUD", "2s 2c 2h 4s 7d", "3 Deuces (Generic)"),
    ("NSUD", "2s 2c Ts Qs Ks", "Wild Royal (Pat)"),
    ("NSUD", "2s 2c 6h 6d 6s", "5 of a Kind (Pat)"),
    ("NSUD", "2s 2c 7h 8h 9h", "Straight Flush (Pat)"),
    ("NSUD", "2s 2c 7h 8h 5d", "4 to Straight Flush (Conn)"),
    ("NSUD", "2s 2c 4h 8h 3s", "2 Deuces (Generic)"),
    ("NSUD", "2s Ts Js Qs Ks", "Wild Royal (Pat)"),
    ("NSUD", "2s 5h 5d 5s 5c", "5 of a Kind"),
    ("NSUD", "2s 5h 6h 7h 8h", "Straight Flush (Pat)"),
    ("NSUD", "2s 5h 6h 7h 9s", "4 to Straight Flush (Conn)"),
    ("NSUD", "2s 9h 4h Th 3h", "Flush (Pat)"),
    ("NSUD", "2s Ts Js Qs 4d", "3 to Royal (TJQ)"),
    ("NSUD", "2s 5h 6h 7d 8c", "Straight (Pat)"),
    ("NSUD", "2s 5h 6h 9s Td", "3 to Straight Flush (Conn 5,6)"),
    ("NSUD", "2s 5h 7h 9s Td", "3 to Straight Flush (Gap 5,7)"),
    ("NSUD", "2s 5h 5d 9s Ts", "3 of a Kind (Deuce + Pair)"),
    ("NSUD", "2s 3c 5d 7h 9s", "1 Deuce (Generic)"),
    ("NSUD", "As Ks Qs Js Ts", "Natural Royal"),
    ("NSUD", "As Ks Qs Js 9h", "4 to Royal"),
    ("NSUD", "9s 8s 7s 6s 5s", "Straight Flush (Pat)"),
    ("NSUD", "9s 8s 7s 6s 2h", "4 to Straight Flush (Conn)"),
    ("NSUD", "As Ks Qs 9d 8c", "3 to Royal"),
    ("NSUD", "8s 8c 8h 4d 4s", "Full House"),
    ("NSUD", "Ks 8s 4s 3s 2h", "Flush (Pat)"),
    ("NSUD", "4s 5d 6c 7h 8s", "Straight (Pat)"),
    ("NSUD", "8s 8c 8h 4d 5s", "3 of a Kind"),
    ("NSUD", "Qs Ks 4s 8s 9d", "4 to Flush"),
    ("NSUD", "8s 8c 4d 5s 6h", "Pair (Generic)"),
    ("NSUD", "4s 5c 6d 7h 9s", "4 to Straight (Open)"),
    ("NSUD", "As Ks 4d 5c 6h", "2 to Royal"),
    ("NSUD", "3s 5c 7d 9h Qh", "Discard All"),

    # ==============================================================================
    # 🎰 BONUS DEUCES (10/4/80/40/20)
    # ==============================================================================
    ("BONUS_DEUCES_10_4", "2s 2c 2h 2d As", "4 Deuces + Ace (Pays 400)"),
    ("BONUS_DEUCES_10_4", "2s 2c 2h 2d 5s", "4 Deuces (Pays 200)"),
    ("BONUS_DEUCES_10_4", "2s 2c 2h Ah As", "5 Aces (Pays 80)"),
    ("BONUS_DEUCES_10_4", "2s 2c 2h 4s 4d", "5 3s-5s (Pays 40)"),
    ("BONUS_DEUCES_10_4", "2s 2c 2h Ts Js", "Wild Royal (Pays 25) vs 3 Deuces"),
    ("BONUS_DEUCES_10_4", "2s 2c 2h 6s 6d", "5 6-K (Pays 20) vs 3 Deuces"),
    ("BONUS_DEUCES_10_4", "2s 2c 2h 4s 7d", "3 Deuces"),
    ("BONUS_DEUCES_10_4", "2s 2c As Ad Ah", "5 Aces (Pays 80)"),
    ("BONUS_DEUCES_10_4", "2s 2c 4s 4d 4h", "5 3s-5s (Pays 40)"),
    ("BONUS_DEUCES_10_4", "2s 2c Ts Qs Ks", "Wild Royal (Pays 25)"),
    ("BONUS_DEUCES_10_4", "2s 2c 6h 6d 6s", "5 6-K (Pays 20)"),
    ("BONUS_DEUCES_10_4", "2s 2c 7h 8h 9h", "Straight Flush (Pat)"),
    ("BONUS_DEUCES_10_4", "2s 2c 7h 8h 5d", "4 to Straight Flush (Conn)"),
    ("BONUS_DEUCES_10_4", "2s 2c 4h 8h 3s", "2 Deuces"),
    ("BONUS_DEUCES_10_4", "2s As Ac Ad Ah", "5 Aces (Pays 80)"),
    ("BONUS_DEUCES_10_4", "2s 4s 4c 4d 4h", "5 3s-5s (Pays 40)"),
    ("BONUS_DEUCES_10_4", "2s Ts Js Qs Ks", "Wild Royal"),
    ("BONUS_DEUCES_10_4", "2s 6h 6c 6d 6s", "5 6-K (Pays 20)"),
    ("BONUS_DEUCES_10_4", "2s 6h 7h 8h 9h", "Straight Flush"),
    ("BONUS_DEUCES_10_4", "2s 6h 7h 8h 4d", "4 to Straight Flush"),
    ("BONUS_DEUCES_10_4", "2s 8h 8c 8d 4s", "Full House"),
    ("BONUS_DEUCES_10_4", "2s 6h 7h 5d 4c", "4 to SF (Gap/Conn check)"),
    ("BONUS_DEUCES_10_4", "2s 8h 4h Th 3h", "Flush (Pays 3)"),
    ("BONUS_DEUCES_10_4", "2s 5h 6h 9d Td", "3 to SF (Conn)"),
    ("BONUS_DEUCES_10_4", "2s Kh Qh 4d 5c", "3 to Royal"),
    ("BONUS_DEUCES_10_4", "2s 8h 8d 4c 5c", "3 of a Kind (Pair + Deuce)"),
    ("BONUS_DEUCES_10_4", "2s 4h 5h 6h 8h", "Straight (Pat)"),
    ("BONUS_DEUCES_10_4", "2s 4h 8d Jc Ks", "1 Deuce (Generic)"),
    ("BONUS_DEUCES_10_4", "As Ks Qs Js Ts", "Natural Royal"),
    ("BONUS_DEUCES_10_4", "As Ks Qs Js 9h", "4 to Royal"),
    ("BONUS_DEUCES_10_4", "9s 8s 7s 6s 5s", "Straight Flush"),
    ("BONUS_DEUCES_10_4", "8s 8c 8h 4d 4s", "Full House"),
    ("BONUS_DEUCES_10_4", "Ks 8s 4s 3s 2h", "Flush"),
    ("BONUS_DEUCES_10_4", "4s 5d 6c 7h 8s", "Straight"),
    ("BONUS_DEUCES_10_4", "8s 8c 8h 4d 5s", "3 of a Kind"),
    ("BONUS_DEUCES_10_4", "9s 8s 7s 6s 4d", "4 to Straight Flush (Conn)"),
    ("BONUS_DEUCES_10_4", "Qs Js Ts 4d 5s", "3 to Royal"),
    ("BONUS_DEUCES_10_4", "Qs Ks 4s 8s 9d", "4 to Flush"),
    ("BONUS_DEUCES_10_4", "8s 8c 4d 5s 6h", "Pair"),
    ("BONUS_DEUCES_10_4", "As Ks 4d 5c 6h", "2 to Royal"),
    ("BONUS_DEUCES_10_4", "As 4d 5c 8h 9s", "Discard All (or Ace Sniper?)"),

    # ==============================================================================
    # ✈️ AIRPORT DEUCES
    # ==============================================================================
    ("AIRPORT", "2s 2c 2h 2d 5s", "4 Deuces"),
    ("AIRPORT", "2s 2c 2h Ts Qs", "Wild Royal"),
    ("AIRPORT", "2s 2c 2h 9s 9d", "3 Deuces (Holds over 5OAK)"),
    ("AIRPORT", "2s 2c 2h 4s 7d", "3 Deuces (Generic)"),
    ("AIRPORT", "2s 2c Ts Qs Ks", "Wild Royal"),
    ("AIRPORT", "2s 2c 6h 6d 6s", "5 of a Kind"),
    ("AIRPORT", "2s 2c 7h 8h 9h", "Straight Flush"),
    ("AIRPORT", "2s 2c 7h 8h 5d", "4 to Straight Flush (Conn)"),
    ("AIRPORT", "2s 2c 4h 8h 3s", "2 Deuces"),
    ("AIRPORT", "2s Ts Js Qs Ks", "Wild Royal"),
    ("AIRPORT", "2s 5h 5d 5s 5c", "5 of a Kind"),
    ("AIRPORT", "2s 5h 6h 7h 8h", "Straight Flush"),
    ("AIRPORT", "2s 5h 6h 7h 9s", "4 to Straight Flush (Conn)"),
    ("AIRPORT", "2s 9h 4h Th 3h", "Flush"),
    ("AIRPORT", "2s Ts Js Qs 4d", "3 to Royal"),
    ("AIRPORT", "2s 5h 6h 7d 8c", "Straight"),
    ("AIRPORT", "2s 5h 6h 9s Td", "3 to Straight Flush (Conn)"),
    ("AIRPORT", "2s 5h 5d 9s Ts", "3 of a Kind"),
    ("AIRPORT", "2s 3c 5d 7h 9s", "1 Deuce"),
    ("AIRPORT", "As Ks Qs Js Ts", "Natural Royal"),
    ("AIRPORT", "As Ks Qs Js 9h", "4 to Royal"),
    ("AIRPORT", "9s 8s 7s 6s 5s", "Straight Flush"),
    ("AIRPORT", "9s 8s 7s 6s 2h", "4 to Straight Flush (Conn)"),
    ("AIRPORT", "8s 8c 8h 4d 4s", "Full House"),
    ("AIRPORT", "Ks 8s 4s 3s 2h", "Flush"),
    ("AIRPORT", "4s 5d 6c 7h 8s", "Straight"),
    ("AIRPORT", "8s 8c 8h 4d 5s", "3 of a Kind"),
    ("AIRPORT", "Qs Js Ts 4d 5s", "3 to Royal"),
    ("AIRPORT", "Qs Ks 4s 8s 9d", "4 to Flush"),
    ("AIRPORT", "8s 8c 4d 5s 6h", "Pair"),
    ("AIRPORT", "4s 5c 6d 7h 9s", "4 to Straight"),
    ("AIRPORT", "As Ks 4d 5c 6h", "2 to Royal"),
    ("AIRPORT", "As 4d 5c 8h 9s", "Discard All"),

    # ==============================================================================
    # 🔓 LOOSE DEUCES
    # ==============================================================================
    ("LOOSE_DEUCES", "2s 2c 2h 2d 5s", "4 Deuces"),
    ("LOOSE_DEUCES", "2s 2c 2h Ts Qs", "Wild Royal"),
    ("LOOSE_DEUCES", "2s 2c 2h 9s 9d", "3 Deuces (Holds over 5OAK?)"),
    ("LOOSE_DEUCES", "2s 2c 2h 4s 7d", "3 Deuces"),
    ("LOOSE_DEUCES", "2s 2c Ts Qs Ks", "Wild Royal"),
    ("LOOSE_DEUCES", "2s 2c 6h 6d 6s", "5 of a Kind"),
    ("LOOSE_DEUCES", "2s 2c 7h 8h 9h", "Straight Flush"),
    ("LOOSE_DEUCES", "2s 2c 7h 8h 5d", "4 to Straight Flush"),
    ("LOOSE_DEUCES", "2s 2c 4h 8h 3s", "2 Deuces"),
    ("LOOSE_DEUCES", "2s Ts Js Qs Ks", "Wild Royal"),
    ("LOOSE_DEUCES", "2s 5h 5d 5s 5c", "5 of a Kind"),
    ("LOOSE_DEUCES", "2s 5h 6h 7h 8h", "Straight Flush"),
    ("LOOSE_DEUCES", "2s 5h 6h 7h 9s", "4 to Straight Flush"),
    ("LOOSE_DEUCES", "2s 9h 4h Th 3h", "Flush"),
    ("LOOSE_DEUCES", "2s Ts Js Qs 4d", "3 to Royal"),
    ("LOOSE_DEUCES", "2s 5h 6h 7d 8c", "Straight"),
    ("LOOSE_DEUCES", "2s 5h 6h 9s Td", "3 to Straight Flush"),
    ("LOOSE_DEUCES", "2s 5h 5d 9s Ts", "3 of a Kind"),
    ("LOOSE_DEUCES", "2s 3c 5d 7h 9s", "1 Deuce"),
    ("LOOSE_DEUCES", "As Ks Qs Js Ts", "Natural Royal"),
    ("LOOSE_DEUCES", "As Ks Qs Js 9h", "4 to Royal"),
    ("LOOSE_DEUCES", "9s 8s 7s 6s 5s", "Straight Flush"),
    ("LOOSE_DEUCES", "8s 8c 8h 4d 4s", "Full House"),
    ("LOOSE_DEUCES", "Ks 8s 4s 3s 2h", "Flush"),
    ("LOOSE_DEUCES", "4s 5d 6c 7h 8s", "Straight"),
    ("LOOSE_DEUCES", "8s 8c 8h 4d 5s", "3 of a Kind"),
    ("LOOSE_DEUCES", "Qs Js Ts 4d 5s", "3 to Royal"),
    ("LOOSE_DEUCES", "Qs Ks 4s 8s 9d", "4 to Flush"),
    ("LOOSE_DEUCES", "8s 8c 4d 5s 6h", "Pair"),
    ("LOOSE_DEUCES", "4s 5c 6d 7h 9s", "4 to Straight"),
    ("LOOSE_DEUCES", "As Ks 4d 5c 6h", "2 to Royal"),
    ("LOOSE_DEUCES", "As 4d 5c 8h 9s", "Discard All"),

    # ==============================================================================
    # 🤡 DBW (DEUCES BONUS WILD)
    # ==============================================================================
    ("DBW", "2s 2c 2h 2d 5s", "4 Deuces"),
    ("DBW", "2s 2c 2h Ah As", "5OAK (Aces) - Pays 80 -> Hold 5OAK"),
    ("DBW", "2s 2c 2h 9s 9d", "5OAK (6-K) - Pays 20 -> Hold 5OAK"),
    ("DBW", "2s 2c 2h Ts Qs", "Wild Royal"),
    ("DBW", "2s 2c 2h 4s 7d", "3 Deuces"),
    ("DBW", "2s 2c As Ad Ah", "5 Aces (Pays 80)"),
    ("DBW", "2s 2c Ts Qs Ks", "Wild Royal"),
    ("DBW", "2s 2c 6h 6d 6s", "5 of a Kind (Pays 20)"),
    ("DBW", "2s 2c 7h 8h 9h", "Straight Flush"),
    ("DBW", "2s 2c 7h 8h 5d", "4 to Straight Flush"),
    ("DBW", "2s 2c 4h 8h 3s", "2 Deuces"),
    ("DBW", "2s As Ac Ad Ah", "5 Aces (Pays 80)"),
    ("DBW", "2s Ts Js Qs Ks", "Wild Royal"),
    ("DBW", "2s 6h 6c 6d 6s", "5 of a Kind (Pays 20)"),
    ("DBW", "2s 6h 7h 8h 9h", "Straight Flush"),
    ("DBW", "2s 6h 7h 8h 4d", "4 to Straight Flush"),
    ("DBW", "2s 8h 8c 8d 4s", "Full House"),
    ("DBW", "2s 9h 4h Th 3h", "Flush"),
    ("DBW", "2s Ts Js Qs 4d", "3 to Royal"),
    ("DBW", "2s 5h 6h 9s Td", "3 to Straight Flush"),
    ("DBW", "2s 5h 5d 9s Ts", "3 of a Kind"),
    ("DBW", "2s 3c 5d 7h 9s", "1 Deuce"),
    ("DBW", "2s 4h 5h 6h 8h", "Straight (Pays 1) - **TRAP**: Likely Hold Deuce/Pair instead"),
    ("DBW", "As Ks Qs Js Ts", "Natural Royal"),
    ("DBW", "As Ks Qs Js 9h", "4 to Royal"),
    ("DBW", "9s 8s 7s 6s 5s", "Straight Flush"),
    ("DBW", "8s 8c 8h 4d 4s", "Full House"),
    ("DBW", "Ks 8s 4s 3s 2h", "Flush"),
    ("DBW", "4s 5d 6c 7h 8s", "Straight (Pays 1) - **TRAP**"),
    ("DBW", "8s 8c 8h 4d 5s", "3 of a Kind"),
    ("DBW", "Qs Js Ts 4d 5s", "3 to Royal"),
    ("DBW", "Qs Ks 4s 8s 9d", "4 to Flush"),
    ("DBW", "8s 8c 4d 5s 6h", "Pair"),
    ("DBW", "4s 5c 6d 7h 9s", "4 to Straight"),
    ("DBW", "As Ks 4d 5c 6h", "2 to Royal"),
    ("DBW", "As 4d 5c 8h 9s", "Discard All"),
]

# --- WORKER FUNCTION (Must be top-level for multiprocessing) ---
def process_hand_task(task_data):
    """
    Worker function to process a single hand test case.
    Returns a result dictionary.
    """
    variant, hand_str, desc = task_data
    
    # Re-import inside worker to ensure clean state if needed (though global imports usually fine)
    # import dw_sim_engine, dw_fast_solver, dw_exact_solver
    
    result = {
        'variant': variant,
        'hand_str': hand_str,
        'description': desc,
        'strategy_hold': "",
        'rule_name': "N/A",
        'optimal_hold': "",
        'strategy_ev': 0.0,
        'optimal_ev': 0.0,
        'diff': 0.0,
        'status': "ERROR",
        'error_msg': ""
    }

    try:
        hand = hand_str.split()
        sim = dw_sim_engine.DeucesWildSim(variant=variant)
        paytable = sim.paytable

        # 1. STRATEGY SOLVE
        fast_res = dw_fast_solver.solve_hand(hand, paytable)
        
        # Handle 2 or 3 return values
        if len(fast_res) == 3:
            fast_held, _, meta = fast_res
            rule_name = meta.get('rule_name', 'Unknown')
        else:
            fast_held, _ = fast_res
            rule_name = "Legacy_Return"
            
        result['strategy_hold'] = " ".join(sorted(fast_held))
        result['rule_name'] = rule_name

        # 2. EXACT SOLVE (Strategy EV)
        fast_indices = [i for i, c in enumerate(hand) if c in fast_held]
        fast_ev = dw_exact_solver.calculate_exact_ev(hand, fast_indices, paytable)
        result['strategy_ev'] = fast_ev

        # 3. EXACT SOLVE (Optimal EV - Brute Force)
        # This is the heavy lifting part
        exact_held, max_ev = dw_exact_solver.get_best_hold(hand, paytable)
        result['optimal_hold'] = " ".join(sorted(exact_held))
        result['optimal_ev'] = max_ev

        # 4. COMPARE
        # Allow tiny float diff
        diff = max_ev - fast_ev
        result['diff'] = diff
        
        if diff < 0.001:
            result['status'] = "PASS"
        else:
            result['status'] = "FAIL"

    except Exception as e:
        result['error_msg'] = str(e)
        result['status'] = "CRASH"
    
    return result

def run_multicore_audit():
    start_time = time.time()
    
    # 1. Setup Output Directory
    report_dir = "strategy_reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(report_dir, f"strategy_audit_{timestamp}.csv")

    print(f"\n🚀 STARTING MULTICORE STRATEGY AUDIT")
    print(f"   Test Cases: {len(TEST_SUITE)}")
    print(f"   CPU Cores:  {multiprocessing.cpu_count()}")
    print("-" * 60)

    # 2. Run Pool
    # We use a Pool to process hands in parallel
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    
    results = []
    
    # Use imap_unordered for a progress bar feel if we iterated, but map is simple
    # Wrapping in try/finally to ensure pool closes
    try:
        # Map the worker function to the test suite
        results_iterator = pool.map(process_hand_task, TEST_SUITE)
        results = list(results_iterator)
    finally:
        pool.close()
        pool.join()

    # 3. Write Report to CSV
    headers = ["Variant", "Status", "Hand", "Strategy Hold", "Rule Hit", "Optimal Hold", "Strategy EV", "Optimal EV", "Diff", "Description"]
    
    pass_count = 0
    fail_count = 0
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for res in results:
            if res['status'] == "PASS": pass_count += 1
            if res['status'] == "FAIL": fail_count += 1
            
            # Console Output for Failures
            if res['status'] == "FAIL":
                print(f"🔴 FAIL: {res['variant']} | {res['hand_str']} | {res['description']}")
                print(f"         Held: {res['strategy_hold']} (Rule: {res['rule_name']})")
                print(f"         Best: {res['optimal_hold']}")
                print(f"         EV Diff: {res['diff']:.4f}\n")

            writer.writerow([
                res['variant'],
                res['status'],
                res['hand_str'],
                res['strategy_hold'],
                res['rule_name'],
                res['optimal_hold'],
                f"{res['strategy_ev']:.4f}",
                f"{res['optimal_ev']:.4f}",
                f"{res['diff']:.4f}",
                res['description']
            ])

    elapsed = time.time() - start_time
    print("-" * 60)
    print(f"🏁 AUDIT COMPLETE in {elapsed:.2f} seconds")
    print(f"   ✅ PASSED: {pass_count}")
    print(f"   ❌ FAILED: {fail_count}")
    print(f"   📂 Report saved to: {filename}")
    print("-" * 60)

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    run_multicore_audit()