"""
dw_compliance_test.py
REGULATORY COMPLIANCE SUITE (Interactive CLI)
Tests 'dw_core_engine' for statistical uniformity.

Design matches 'dw_multihand_sim.py' for consistent UX.
"""

import sys
import time
from collections import Counter
from dw_core_engine import DeucesWildCore

# ==========================================
# ⚙️ CONFIGURATION & DEFAULTS
# ==========================================
DEFAULT_DEALS = 100_000
DEFAULT_RUNS = 5
CRITICAL_VALUE = 67.50    # Chi-Sq threshold for df=51, p=0.05

def perform_single_audit(run_id, num_deals):
    """
    Runs a single pass of the Chi-Square audit.
    Returns: (is_passing, p_score, outlier_card, outlier_dev)
    """
    engine = DeucesWildCore()
    card_counts = Counter()
    
    # --- 1. THE GRIND ---
    # Only show detailed progress bar if the run is huge
    show_progress = (num_deals >= 500_000)
    
    if show_progress:
        print(f"    Run #{run_id}: Dealing {num_deals:,} hands...")
        milestone = num_deals // 10
    
    for i in range(num_deals):
        if show_progress and i % milestone == 0:
            sys.stdout.write(f"\r    Progress: {i/num_deals:.0%}...")
            sys.stdout.flush()
        
        hand, stub = engine.deal_hand()
        card_counts.update(hand)
    
    if show_progress:
        sys.stdout.write(f"\r    Progress: 100%       \n")

    # --- 2. THE MATH (Pure Python Chi-Square) ---
    total_cards = num_deals * 5
    expected_freq = total_cards / 52
    chi_sq_stat = 0
    max_dev = 0
    worst_card = ""
    
    deck = engine.get_fresh_deck()
    
    # Sanity Check
    if len(card_counts) < 52:
        return False, 9999.0, "MISSING", 1.0

    for card in deck:
        observed = card_counts[card]
        diff = observed - expected_freq
        chi_sq_stat += (diff ** 2) / expected_freq
        
        dev_percent = abs(diff) / expected_freq
        if dev_percent > max_dev:
            max_dev = dev_percent
            worst_card = card

    # Score < 67.50 = PASS (Random)
    # Score > 67.50 = FAIL (Biased)
    is_passing = chi_sq_stat < CRITICAL_VALUE
    
    return is_passing, chi_sq_stat, worst_card, max_dev

def run_audit_suite(deals, runs):
    print(f"\n🕵️  RUNNING AUDIT SUITE")
    print(f"==================================================")
    print(f"    Target Engine:  dw_core_engine.py")
    print(f"    Hands per Run:  {deals:,}")
    print(f"    Total Runs:     {runs}")
    print(f"    Pass Threshold: Chi-Sq < {CRITICAL_VALUE}")
    print(f"==================================================")
    print(f"ID  | STATUS | CHI-SQ  | WORST CARD (DEV)")
    print(f"----|--------|---------|------------------")

    passed = 0
    failed = 0
    
    try:
        for i in range(1, runs + 1):
            is_pass, score, bad_card, bad_dev = perform_single_audit(i, deals)
            
            status = "✅ PASS" if is_pass else "❌ FAIL"
            if is_pass: passed += 1
            else: failed += 1
            
            # Formatted Output Row
            print(f"#{i:<2} | {status} | {score:>7.2f} | {bad_card} ({bad_dev:.2%})")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  AUDIT ABORTED BY USER.")
        return

    pass_rate = passed / runs if runs > 0 else 0
    
    print(f"==================================================")
    print(f"🏁 SUMMARY REPORT")
    print(f"    Passed: {passed}/{runs} ({pass_rate:.0%})")
    
    if pass_rate >= 0.90:
        print(f"✅ CERTIFICATION GRANTED")
    elif pass_rate >= 0.80:
        print(f"⚠️ PROVISIONAL PASS (High Variance)")
    else:
        print(f"❌ CERTIFICATION DENIED")
    print(f"==================================================")
    input("\nPress Enter to return to menu...")

# ==========================================
# 🎮 INTERACTIVE MAIN LOOP
# ==========================================

if __name__ == "__main__":
    # Session State
    current_deals = DEFAULT_DEALS
    current_runs = DEFAULT_RUNS

    while True:
        # Calculate Total Load for display
        total_hands = current_deals * current_runs
        est_time_sec = total_hands / 250_000 # Rough estimate based on Python speed
        
        print("\n==========================================")
        print("🕵️  REGULATORY COMPLIANCE LAB (v3.0)")
        print("==========================================")
        print(f"[Audit Config: {current_deals:,} Hands/Run | {current_runs} Runs]")
        print(f"[Total Load:   {total_hands:,} Hands | Est. Time: ~{est_time_sec:.1f}s]")
        print("------------------------------------------")
        print("Options: (R)un Audit | (S)ettings | (Q)uit")
        
        choice = input(">> ").strip().upper()
        
        if choice == 'Q':
            print("Exiting Compliance Lab.")
            break
            
        elif choice == 'R':
            run_audit_suite(current_deals, current_runs)
            
        elif choice == 'S':
            print("\n--- AUDIT SETTINGS ---")
            print(f"1. Quick Check      (100,000 Hands x 5 Runs)")
            print(f"2. Standard Cert    (1,000,000 Hands x 5 Runs)")
            print(f"3. Deep Stress Test (5,000,000 Hands x 10 Runs)")
            print(f"4. Custom Configuration")
            print(f"5. Back")
            
            sub = input("Select: ").strip()
            
            if sub == '1':
                current_deals = 100_000
                current_runs = 5
                print("✅ Set to Quick Check.")
            elif sub == '2':
                current_deals = 1_000_000
                current_runs = 5
                print("✅ Set to Standard Certification.")
            elif sub == '3':
                current_deals = 5_000_000
                current_runs = 10
                print("✅ Set to Deep Stress Test.")
            elif sub == '4':
                try:
                    d = input(f"Hands per Run [{current_deals}]: ")
                    if d.strip(): current_deals = int(d)
                    r = input(f"Total Runs [{current_runs}]: ")
                    if r.strip(): current_runs = int(r)
                except ValueError:
                    print("❌ Invalid input.")