"""
dw_strategy_generator.py
THE STRATEGY DISCOVERY ENGINE (v9.4 - Classifier Patch)

Features:
- "Golden Seed" Injection.
- "Microscope" Classifier:
    - FIXED: Distinguishes "Pat 4 Deuces + Ace" from "Pat 5 Aces".
    - Distinguishes Tiered 5-of-a-Kind (3s/4s/5s vs 6s-Ks).
- Resume Capability & Auto-Save.
"""

import multiprocessing
import time
import os
import glob
import csv
import datetime
from collections import defaultdict
from dw_sim_engine import DeucesWildSim
import dw_exact_solver
from dw_pay_constants import PAYTABLES

# --- GLOBAL DEFAULTS ---
CONFIG = {
    "SAMPLES": 200,          
    "VARIANT": "NSUD",       
    "CORES": max(1, min(6, multiprocessing.cpu_count() - 2)),
    "BASELINE_FILE": None    
}

# ==========================================
# 🧠 THE "MICROSCOPE" CLASSIFIER LOGIC
# ==========================================
def get_ranks_suits(cards):
    # Map: 2=0, 3=1, ... A=12
    rank_map = {r: i for i, r in enumerate("23456789TJQKA")}
    ranks = sorted([rank_map[c[0]] for c in cards])
    suits = [c[1] for c in cards]
    return ranks, suits

def is_royal_draw(ranks):
    royal_set = {8, 9, 10, 11, 12} 
    return set(ranks).issubset(royal_set)

def count_gaps(ranks):
    if not ranks: return 0
    span = ranks[-1] - ranks[0]
    return span - (len(ranks) - 1)

def classify_hold(held_cards):
    if not held_cards: return "DISCARD_ALL"
    
    ranks, suits = get_ranks_suits(held_cards)
    deuces = [c for c in held_cards if c[0] == '2']
    num_deuces = len(deuces)
    count = len(held_cards)
    
    # --- HELPER: Is this a Flush (ignoring Deuce suits)? ---
    non_deuce_suits = [c[1] for c in held_cards if c[0] != '2']
    is_wild_flush = len(set(non_deuce_suits)) <= 1
    
    non_deuce_ranks = [r for r in ranks if r != 0] # 0 is Deuce

    # ==================================================
    # 1. PAT HANDS (Held 5) - CHECK FIRST!
    # ==================================================
    if count == 5:
        # --- NEW: CRITICAL PATCH FOR 4 DEUCES + ACE ---
        # If we hold 5 cards and 4 are deuces, identifying the kicker is vital
        if num_deuces == 4:
            # Check for Ace Kicker
            if any(r == 12 for r in non_deuce_ranks): # 12 is Ace
                return "4_DEUCES_ACE"
            return "4_DEUCES" # Pat 4 Deuces (with junk kicker)

        # A. Natural Royal (Must be strict suits, no deuces)
        if num_deuces == 0 and len(set(suits)) == 1:
             if set(ranks) == {8, 9, 10, 11, 12}: return "NATURAL_ROYAL"
             
        # B. 5 OF A KIND LOGIC
        if num_deuces > 0 and len(set(non_deuce_ranks)) == 1:
            rank_val = non_deuce_ranks[0]
            if rank_val == 12: return "FIVE_ACES"
            if 1 <= rank_val <= 3: return "FIVE_3_4_5"
            return "FIVE_6_TO_K" 

        # C. WILD ROYAL vs STRAIGHT FLUSH
        if is_wild_flush:
            if all(r >= 8 for r in non_deuce_ranks):
                return "WILD_ROYAL"
            return "PAT_FLUSH_OR_STR_FLUSH"
        
        return "PAT_STRAIGHT_OR_FULL_HOUSE"

    # ==================================================
    # 2. DEUCE HEAVY (Partial Holds)
    # ==================================================
    if num_deuces == 4: 
        # Partial hold of 4 Deuces (dropped kicker)
        # Note: Logic usually holds 5 if kicker is Ace, drops if junk.
        # But if we dropped the kicker, we don't have the Ace anymore.
        return "4_DEUCES"
        
    if num_deuces == 3: return "3_DEUCES"
    if num_deuces == 2: return "2_DEUCES"

    # ==================================================
    # 3. ONE DEUCE
    # ==================================================
    if num_deuces == 1:
        non_deuce_cards = [c for c in held_cards if c[0] != '2']
        nd_ranks, nd_suits = get_ranks_suits(non_deuce_cards)
        
        is_suited_non_deuce = len(set(nd_suits)) <= 1
        
        if len(set(nd_ranks)) < len(nd_ranks): return "3_KIND" 
            
        if is_suited_non_deuce:
            if len(non_deuce_cards) == 3:
                if is_royal_draw(nd_ranks): return "1_DEUCE_3_ROYAL"
                gaps = count_gaps(nd_ranks)
                if gaps == 0: return "1_DEUCE_3_SF_CONN" 
                if gaps <= 2: return "1_DEUCE_3_SF_GAP"
                return "1_DEUCE_3_FLUSH"
            
            if len(non_deuce_cards) == 2:
                if is_royal_draw(nd_ranks): return "1_DEUCE_2_ROYAL"
                gaps = count_gaps(nd_ranks)
                if gaps == 0: return "1_DEUCE_2_SF_CONN"
                if gaps == 1: return "1_DEUCE_2_SF_GAP"
                return "1_DEUCE_2_FLUSH"
        return "1_DEUCE_GENERIC"

    # ==================================================
    # 4. NATURALS (No Deuces)
    # ==================================================
    if len(set(ranks)) == 1 and count > 1:
        rank_val = ranks[0]
        if count == 3:
            if rank_val == 12: return "3_ACES" 
            if 1 <= rank_val <= 3: return "3_3_4_5"
            return "3_KIND"
        if count == 2: return "1_PAIR"
        
    if count == 4 and len(set(ranks)) == 2: return "2_PAIR"

    is_suited = len(set(suits)) == 1
    if is_suited:
        if count == 4:
            if is_royal_draw(ranks): return "4_ROYAL"
            gaps = count_gaps(ranks)
            if gaps == 0: return "4_STR_FLUSH_CONN"
            if gaps <= 2: return "4_STR_FLUSH_GAP"
            return "4_FLUSH"
        if count == 3:
            if is_royal_draw(ranks): return "3_ROYAL"
            gaps = count_gaps(ranks)
            if gaps == 0: return "3_STR_FLUSH_CONN"
            if gaps <= 2: return "3_STR_FLUSH_GAP"
            return "3_FLUSH"
        if count == 2:
            if is_royal_draw(ranks): return "2_ROYAL"
    
    if count == 4:
        gaps = count_gaps(ranks)
        if gaps == 0: return "4_STRAIGHT_OPEN"
        
    return "JUNK_HIGH_CARDS" if max(ranks) >= 9 else "JUNK_LOW"

# ==========================================
# 🌟 THE GOLDEN SEED
# ==========================================
def get_golden_hands(variant):
    """Returns list of rare hands to inject."""
    # Base Seeds
    hands = [
        ['Ts', 'Js', 'Qs', 'Ks', 'As'],  # NATURAL_ROYAL
        ['2s', '2h', '2c', '2d', '3h'],  # 4_DEUCES
        ['2s', 'Js', 'Qs', 'Ks', 'As'],  # Wild Royal (Pat)
        ['8s', '8c', '8h', '8d', '2s'],  # FIVE_6_TO_K
        ['9s', 'Ts', 'Js', 'Qs', 'Ks'],  # PAT_STR_FLUSH
        ['3s', '3h', '3c', '3d', '5h'],  # 4 of a Kind (Pat)
        ['3s', '3h', '3c', '4d', '4h'],  # Full House (Pat)
        ['3s', '5s', '7s', '9s', 'Js'],  # Flush (Pat)
        ['3s', '4h', '5c', '6d', '7s'],  # Straight (Pat)
    ]
    # Variant Seeds (Bonus Deuces logic)
    if "BONUS" in variant or "DBW" in variant:
        hands.append(['2s', '2h', '2c', '2d', 'As']) # 4_DEUCES_ACE
        hands.append(['As', 'Ac', 'Ah', 'Ad', '2s']) # FIVE_ACES
        hands.append(['3s', '3c', '3h', '3d', '2s']) # FIVE_3_4_5 (New!)
        
    return hands

def process_golden_seeds(variant):
    """Solves the golden hands to inject into the dataset."""
    seeds = get_golden_hands(variant)
    results = []
    if variant not in PAYTABLES:
        print(f"⚠️ Warning: Variant {variant} not found in PAYTABLES. Using defaults.")
        paytable = list(PAYTABLES.values())[0]
    else:
        paytable = PAYTABLES[variant]
    
    print(f"🌟 Seeding {len(seeds)} 'Golden Hands' (Jackpots & Rare Events)...")
    
    for hand in seeds:
        best_hold, max_ev = dw_exact_solver.solve_hand_silent(hand, paytable)
        label = classify_hold(best_hold)
        results.append((label, max_ev))
        
    return results

# ==========================================
# ⚡ WORKER & UI (Standard)
# ==========================================
def worker_task(params):
    variant_name = params
    sim = DeucesWildSim(variant=variant_name)
    paytable = PAYTABLES[variant_name]
    hand, _ = sim.core.deal_hand()
    best_hold, max_ev = dw_exact_solver.solve_hand_silent(hand, paytable)
    label = classify_hold(best_hold)
    return (label, max_ev)

def load_baseline_data(filepath):
    baseline = {}
    variant_found = None
    total_loaded_samples = 0
    print(f"\n📂 Loading baseline: {os.path.basename(filepath)}...")
    try:
        with open(filepath, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                label = row['Category Label']
                avg = float(row['Avg EV'])
                count = int(row['Samples'])
                min_v = float(row['Min EV'])
                max_v = float(row['Max EV'])
                row_var = row.get('Variant', 'Unknown')
                if variant_found is None: variant_found = row_var
                
                sum_ev = avg * count
                baseline[label] = {
                    'count': count, 'sum_ev': sum_ev, 'min': min_v, 'max': max_v
                }
                total_loaded_samples += count
        print(f"✅ Baseline Loaded: {total_loaded_samples} hands | Variant: {variant_found}")
        return baseline, variant_found, total_loaded_samples
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return {}, None, 0

def save_results_to_csv(variant, samples_run, duration, aggregated_data, total_history_samples):
    folder_name = "strategy"
    if not os.path.exists(folder_name): os.makedirs(folder_name)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "cumulative_" if total_history_samples > samples_run else "strategy_"
    filename = f"{folder_name}/{prefix}{variant}_{timestamp}.csv"
    try:
        with open(filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Category Label", "Avg EV", "Samples", "Min EV", "Max EV", "Variant", "Total_Cumulative_Samples"])
            for rank, (label, avg, count, min_v, max_v) in enumerate(aggregated_data, 1):
                writer.writerow([rank, label, round(avg, 5), count, round(min_v, 5), round(max_v, 5), variant, total_history_samples])
        print(f"\n💾 Report saved: {filename}")
    except Exception as e:
        print(f"\n❌ Error saving CSV: {e}")

def run_generator_session():
    variant = CONFIG["VARIANT"]
    new_samples = CONFIG["SAMPLES"]
    cores = CONFIG["CORES"]
    baseline_file = CONFIG["BASELINE_FILE"]
    
    baseline_data = {}
    history_samples = 0
    
    if baseline_file:
        baseline_data, loaded_variant, history_samples = load_baseline_data(baseline_file)
        if loaded_variant and loaded_variant != variant:
            print(f"⚠️ Switching Target to: {loaded_variant}")
            variant = loaded_variant
            CONFIG["VARIANT"] = loaded_variant

    print(f"\n🚀 LAUNCHING SOLVER SESSION")
    print(f"   Target:  {variant}")
    print(f"   New Run: {new_samples} Hands")
    print(f"   Workers: {cores}")
    print("-" * 50)
    
    start_time = time.time()
    results = []
    
    # 1. INJECT SEEDS
    seed_results = process_golden_seeds(variant)
    results.extend(seed_results)
    
    # 2. RUN WORKERS
    completed = 0
    worker_args = [variant for _ in range(new_samples)]
    try:
        with multiprocessing.Pool(processes=cores) as pool:
            for res in pool.imap_unordered(worker_task, worker_args):
                results.append(res)
                completed += 1
                if completed % 10 == 0 or completed == new_samples:
                    percent = (completed / new_samples) * 100
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    print(f"   [Progress] {completed}/{new_samples} ({percent:.0f}%) | {rate:.1f} hands/sec...", end='\r')
    except KeyboardInterrupt:
        print("\n⚠️ Aborted.")
        return

    duration = time.time() - start_time
    print(f"\n✅ Finished in {duration:.2f} seconds")

    # 3. AGGREGATE
    current_buckets = defaultdict(list)
    for label, ev in results:
        current_buckets[label].append(ev)

    final_stats = {}
    all_labels = set(current_buckets.keys()) | set(baseline_data.keys())
    
    for label in all_labels:
        old = baseline_data.get(label, {'count': 0, 'sum_ev': 0.0, 'min': 9999.0, 'max': -9999.0})
        new_list = current_buckets.get(label, [])
        new_count = len(new_list)
        new_sum = sum(new_list)
        new_min = min(new_list) if new_list else 9999.0
        new_max = max(new_list) if new_list else -9999.0
        
        total_count = old['count'] + new_count
        total_sum = old['sum_ev'] + new_sum
        
        if old['count'] == 0:
            final_min, final_max = new_min, new_max
        elif new_count == 0:
            final_min, final_max = old['min'], old['max']
        else:
            final_min = min(old['min'], new_min)
            final_max = max(old['max'], new_max)
            
        final_stats[label] = {
            'avg': total_sum / total_count if total_count > 0 else 0,
            'count': total_count, 'min': final_min, 'max': final_max
        }

    # 4. DISPLAY
    total_run_samples = history_samples + new_samples 
    
    print("-" * 65)
    print(f"🏆 STRATEGY CHART: {variant}")
    print(f"{'RANK':<5} | {'CATEGORY LABEL':<25} | {'AVG EV':<10} | {'SAMPLES':<5}")
    print("-" * 65)
    
    export_list = []
    for label, stats in final_stats.items():
        export_list.append((label, stats['avg'], stats['count'], stats['min'], stats['max']))
    
    export_list.sort(key=lambda x: x[1], reverse=True)
    
    for rank, (label, avg, count, _, _) in enumerate(export_list, 1):
        if rank <= 25: # Show top 25
            print(f"{rank:<5} | {label:<25} | {avg:<10.4f} | {count:<5}")
    
    save_results_to_csv(variant, new_samples, duration, export_list, total_run_samples)
    input("\nPress Enter...")

def file_selection_menu():
    files = glob.glob("strategy/*.csv")
    if not files: return
    files.sort(key=os.path.getmtime, reverse=True)
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("📂 SELECT BASELINE")
        for i, f in enumerate(files, 1): print(f"{i}. {os.path.basename(f)}")
        print(f"{len(files)+1}. Cancel")
        choice = input("Select: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                CONFIG["BASELINE_FILE"] = files[idx]
                break
            elif idx == len(files):
                CONFIG["BASELINE_FILE"] = None
                break
        except: pass

def settings_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        b_file = os.path.basename(CONFIG['BASELINE_FILE']) if CONFIG['BASELINE_FILE'] else "None"
        print("==========================================")
        print("⚙️  GENERATOR SETTINGS")
        print("==========================================")
        print(f"1. Target Variant    [{CONFIG['VARIANT']}]")
        print(f"2. Sample Size       [{CONFIG['SAMPLES']}]")
        print(f"3. CPU Cores         [{CONFIG['CORES']}]")
        print(f"4. Baseline File     [{b_file}]")
        print("5. Back")
        choice = input(">> ").strip()
        if choice == '1':
            keys = list(PAYTABLES.keys())
            for i, k in enumerate(keys, 1): print(f"{i}. {k}")
            try: CONFIG["VARIANT"] = keys[int(input("Select: ")) - 1]
            except: pass
        elif choice == '2':
            try: CONFIG["SAMPLES"] = int(input("Samples: "))
            except: pass
        elif choice == '3':
            try: CONFIG["CORES"] = int(input("Cores: "))
            except: pass
        elif choice == '4': file_selection_menu()
        elif choice == '5': break

def main_menu():
    multiprocessing.freeze_support()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("==========================================")
        print("🧬 STRATEGY DISCOVERY ENGINE (v9.4)")
        print("==========================================")
        print(f"[Config: {CONFIG['VARIANT']} | {CONFIG['SAMPLES']} Hands | {CONFIG['CORES']} Cores]")
        print("1. 🚀 Run Generation")
        print("2. ⚙️  Settings")
        print("3. 🚪 Quit")
        choice = input(">> ").strip()
        if choice == '1': run_generator_session()
        elif choice == '2': settings_menu()
        elif choice == '3': break

if __name__ == "__main__":
    main_menu()