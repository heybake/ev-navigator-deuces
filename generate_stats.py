"""
generate_stats.py
Theoretical Frequency Generator for Deuces Wild Trainer.

This script runs a Monte Carlo simulation (playing thousands of hands)
using the 'dw_fast_solver' strategy engine to determine the Expected Hit Frequencies
for variants that don't have published tables (Loose Deuces, Airport, etc.).
"""

import time
import sys
import random
from collections import Counter

# --- IMPORT YOUR PROJECT MODULES ---
# (Ensure these are in the same folder)
try:
    import dw_sim_engine
    import dw_fast_solver
    import dw_strategy_definitions
except ImportError as e:
    print("❌ ERROR: Could not import game modules.")
    print(f"Details: {e}")
    print("Make sure this script is in the same folder as 'dw_sim_engine.py' and 'dw_fast_solver.py'.")
    sys.exit(1)

# ==============================================================================
# ⚙️ CONFIGURATION
# ==============================================================================
# 1 Million hands gives ~3 decimal precision (Good enough for UI).
# 100,000 is faster for testing (approx 1 minute).
SIMULATION_SIZE = 100000 

VARIANTS_TO_PROCESS = [
    "LOOSE_DEUCES",
    "AIRPORT",
    "BONUS_DEUCES_10_4",
    "DBW"
]

# Keys must match dw_stats_helper.HAND_TYPES
HAND_KEYS = [
    "NATURAL_ROYAL", "FOUR_DEUCES", "WILD_ROYAL", 
    "FIVE_ACES", "FIVE_3_4_5", "FIVE_6_TO_K", "FIVE_OF_A_KIND",
    "STRAIGHT_FLUSH", "FOUR_OF_A_KIND", "FULL_HOUSE", 
    "FLUSH", "STRAIGHT", "THREE_OF_A_KIND", "LOSER"
]

# ==============================================================================
# 🚀 SIMULATION ENGINE
# ==============================================================================
def run_variant_sim(variant_name, num_hands):
    print(f"\n🚀 STARTING SIMULATION: {variant_name}")
    print(f"   Target: {num_hands:,} hands")
    
    # Initialize Game Engine
    sim = dw_sim_engine.DeucesWildSim(variant=variant_name)
    paytable = sim.paytable
    
    # Trackers
    counts = Counter()
    start_time = time.time()
    
    for i in range(1, num_hands + 1):
        # 1. Deal
        hand, stub = sim.core.deal_hand()
        
        # 2. Solver (Get Best Hold)
        # Note: We trust the Fast Solver matches the Strategy Definitions
        solutions = dw_fast_solver.solve_hand(hand, paytable)
        
        if solutions:
            best_hold = solutions[0]['held'] # List of card strings
        else:
            best_hold = []
            
        # 3. Draw (Fill the hand)
        # Reconstruct the hand: Keep held cards, replace others from stub
        final_hand = []
        
        # We need to map held cards back to indices to preserve order or just append?
        # Sim engine usually keeps indices. Let's do it manually for speed.
        # dw_fast_solver returns actual card strings (e.g. ['2h', 'Ad']).
        
        # Helper: pull cards from stub to fill gaps
        stub_idx = 0
        current_stub = list(stub) # Copy stub
        
        # Simple Draw Logic:
        # If we held 5, we keep 5. If we held 0, we draw 5.
        # We don't care about position for evaluation, just the set of cards.
        draw_count = 5 - len(best_hold)
        drawn_cards = current_stub[:draw_count]
        final_hand = best_hold + drawn_cards
        
        # 4. Evaluate
        # We need the Rank Key (e.g. "FOUR_DEUCES")
        # sim.evaluate_hand_score returns (rank_key, multiplier)
        rank_key, _ = sim.evaluate_hand_score(final_hand)
        
        # Normalize keys if needed (Sim engine output should match HAND_KEYS mostly)
        # Bonus Deuces might output specific keys like "FIVE_ACES".
        # We count exactly what the sim returns.
        counts[rank_key] += 1
        
        # Progress Bar
        if i % (num_hands // 10) == 0:
            pct = (i / num_hands) * 100
            elapsed = time.time() - start_time
            print(f"   ... {int(pct)}% complete ({elapsed:.1f}s)")

    return counts

# ==============================================================================
# 🖨️ OUTPUT GENERATOR
# ==============================================================================
def generate_python_dict(variant_results, num_hands):
    print("\n" + "="*60)
    print("✅ GENERATION COMPLETE! COPY THE BLOCK BELOW:")
    print("="*60 + "\n")
    
    print("THEORETICAL_PROBS = {")
    print('    "NSUD": { ... }, # (Keep existing NSUD data)')
    
    for variant, counts in variant_results.items():
        print(f'\n    "{variant}": {{')
        
        # Sort by standard hierarchy for readability
        # But we must include keys that appeared in the sim
        
        # Calculate prob for each key in HAND_KEYS
        # (And any extras the sim might produce)
        all_found_keys = set(counts.keys())
        sorted_keys = [k for k in HAND_KEYS if k in all_found_keys]
        
        # Add any unexpected keys found by sim
        extras = all_found_keys - set(HAND_KEYS)
        for e in extras: sorted_keys.append(e)
        
        for key in sorted_keys:
            count = counts.get(key, 0)
            prob = count / num_hands
            # Format to 6 decimal places
            print(f'        "{key}": {prob:.6f},')
            
        print("    },")
        
    print("}")
    print("\n" + "="*60)

# ==============================================================================
# 🏁 MAIN
# ==============================================================================
if __name__ == "__main__":
    results = {}
    
    print(f"🎰 DEUCES WILD STATS GENERATOR")
    print(f"   Simulation Size: {SIMULATION_SIZE} hands per variant")
    
    try:
        for variant in VARIANTS_TO_PROCESS:
            counts = run_variant_sim(variant, SIMULATION_SIZE)
            results[variant] = counts
            
        generate_python_dict(results, SIMULATION_SIZE)
        
    except KeyboardInterrupt:
        print("\n⚠️ Simulation cancelled by user.")