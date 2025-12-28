"""
dw_strategy_compiler.py
THE BRIDGE: Converts Strategy CSVs into Python Code. (v2.2 - Name Fix)

1. Scans 'strategy/' folder for strategy_*.csv files.
2. Lets user select a Variant and a specific File.
3. Translates labels -> Python functions.
4. Injects them into dw_strategy_definitions.py in the root folder.
"""

import csv
import os
import re
import glob
import datetime

# ==============================================================================
# ⚙️ CONFIGURATION
# ==============================================================================
STRATEGY_DIR = "strategy"  # The folder where CSVs are stored
TARGET_DEF_FILE = "dw_strategy_definitions.py" # The root definition file

# ==============================================================================
# 🔤 THE ROSETTA STONE (CSV Label -> Python Function)
# ==============================================================================
TRANSLATION_MAP = {
    # --- NATURALS ---
    "NATURAL_ROYAL":            ["holds_natural_royal"],
    "STRAIGHT_FLUSH":           ["holds_straight_flush"],
    "4_ROYAL":                  ["holds_4_to_royal"],
    "FULL_HOUSE":               ["holds_full_house"],
    "FLUSH":                    ["holds_flush"],
    "STRAIGHT":                 ["holds_straight"],
    "3_KIND":                   ["holds_3_of_a_kind"],
    "3_ACES":                   ["holds_3_of_a_kind"], 
    "3_3_4_5":                  ["holds_3_of_a_kind"], 
    "3_6_TO_K":                 ["holds_3_of_a_kind"],
    "4_STR_FLUSH_CONN":         ["holds_4_to_straight_flush_conn"],
    "4_STR_FLUSH_GAP":          ["holds_4_to_straight_flush_conn"], 
    "3_ROYAL":                  ["holds_3_to_royal"],
    "2_ROYAL":                  ["holds_2_to_royal"],
    
    # --- NEW MAPPINGS FOR AIRPORT/GENERIC ---
    "4_FLUSH":                  ["holds_4_to_flush"], 
    "4_STRAIGHT_OPEN":          ["holds_4_to_straight"], 
    "3_STR_FLUSH_CONN":         ["holds_3_to_straight_flush_conn"],
    "3_STR_FLUSH_GAP":          ["holds_3_to_straight_flush_conn"],
    "3_FLUSH":                  ["discard_all"], 
    "1_PAIR":                   ["holds_any_pair"],
    "2_PAIR":                   ["holds_any_pair"], 
    "JUNK_HIGH_CARDS":          ["discard_all"],
    "JUNK_LOW":                 ["discard_all"],
    
    # --- WILDS (1 DEUCE) ---
    "1_DEUCE_3_ROYAL":          ["holds_3_to_royal"], 
    "1_DEUCE_3_SF_CONN":        ["holds_4_to_straight_flush_conn"],
    "1_DEUCE_3_SF_GAP":         ["holds_4_to_straight_flush_conn"],
    "1_DEUCE_2_SF_CONN":        ["holds_3_to_straight_flush_conn"],
    "1_DEUCE_2_SF_GAP":         ["holds_3_to_straight_flush_conn"],
    "1_DEUCE_3_FLUSH":          ["holds_flush"], 
    "1_DEUCE_2_ROYAL":          ["holds_2_to_royal"],
    "1_DEUCE_2_FLUSH":          ["discard_all"],
    "1_DEUCE_GENERIC":          ["holds_1_deuce"],
    "1_DEUCE":                  ["holds_1_deuce"],
    
    # --- WILDS (2-4 DEUCES) ---
    "2_DEUCES":                 ["holds_2_deuces"],
    "3_DEUCES":                 ["holds_3_deuces"],
    "4_DEUCES":                 ["holds_4_deuces"],
    "4_DEUCES_ACE":             ["holds_4_deuces_ace"],
    
    # --- UNIVERSALS ---
    "WILD_ROYAL":               ["holds_wild_royal"],
    "5_OF_A_KIND":              ["holds_5_of_a_kind"],
    "FIVE_ACES":                ["holds_five_aces"],
    "FIVE_3_4_5":               ["holds_five_3_4_5"],
    "FIVE_6_TO_K":              ["holds_five_6_to_k"],
    
    # --- SPECIAL CASES ---
    "PAT_FLUSH_OR_STR_FLUSH":   ["holds_straight_flush", "holds_flush"], 
    "PAT_STRAIGHT_OR_FULL_HOUSE": ["holds_full_house", "holds_straight"],
    
    "DISCARD_ALL":              ["discard_all"]
}

# ==============================================================================
# ⚙️ COMPILER LOGIC
# ==============================================================================
def parse_csv(filepath):
    """Reads CSV and returns a list of rules sorted by Rank."""
    rules = []
    print(f"📂 Reading: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rules.append({
                    "rank": int(row['Rank']),
                    "label": row['Category Label'],
                    "ev": float(row['Avg EV'])
                })
            except Exception as e:
                pass 
            
    rules.sort(key=lambda x: x['rank'])
    return rules

def classify_bucket(label):
    if "4_DEUCES" in label: return [4]
    if "3_DEUCES" in label: return [3]
    if "2_DEUCES" in label: return [2]
    if "1_DEUCE" in label: return [1]
    if label == "NATURAL_ROYAL": return [0, 1, 2, 3, 4] 
    if "WILD_ROYAL" in label: return [1, 2, 3]
    if "5_OF_A_KIND" in label or "FIVE_" in label: return [1, 2, 3] 
    if "STR_FLUSH" in label or "STRAIGHT_FLUSH" in label: return [0, 1, 2]
    return [0]

def generate_python_dict(rules, variant_name):
    bucket_map = {0: [], 1: [], 2: [], 3: [], 4: []}
    for r in rules:
        label = r['label']
        funcs = TRANSLATION_MAP.get(label)
        if not funcs:
            print(f"   ⚠️ Warning: No translation for '{label}'. Skipping.")
            continue
        target_buckets = classify_bucket(label)
        for b in target_buckets:
            for f in funcs:
                if f not in bucket_map[b]: bucket_map[b].append(f)

    if "discard_all" not in bucket_map[0]: bucket_map[0].append("discard_all")

    out = f"STRATEGY_{variant_name} = {{\n"
    for b in [4, 3, 2, 1, 0]:
        out += f"    {b}: [\n"
        for func in bucket_map[b]: out += f"        {func},\n"
        out += "    ],\n"
    out += "}"
    return out

def inject_code(variant_name, new_code):
    target_file = TARGET_DEF_FILE
    start_tag = f"# >>>> STRATEGY_{variant_name}_START"
    end_tag = f"# <<<< STRATEGY_{variant_name}_END"
    
    try:
        with open(target_file, 'r', encoding='utf-8') as f: content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: {target_file} not found.")
        return

    if start_tag not in content or end_tag not in content:
        print(f"❌ Error: Anchor tags for {variant_name} not found.")
        return

    pattern_str = f"({re.escape(start_tag)})(.*?)({re.escape(end_tag)})"
    replacement = f"\\1\n{new_code}\n\\3"
    new_content = re.sub(pattern_str, replacement, content, flags=re.DOTALL)
    
    if new_content == content:
        print(f"   ⚠️ No changes made to {variant_name}.")
    else:
        with open(target_file, 'w', encoding='utf-8') as f: f.write(new_content)
        print(f"✅ Successfully injected strategy for {variant_name}")

# ==============================================================================
# 🎮 INTERACTIVE FILE SELECTION
# ==============================================================================
def get_file_timestamp(filepath):
    ts = os.path.getmtime(filepath)
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')

def scan_files():
    """
    Finds all strategy_*.csv files in STRATEGY_DIR and groups by variant.
    Improved Parser: Uses slicing to handle variants with numbers (e.g. 10_4).
    """
    search_path = os.path.join(STRATEGY_DIR, "strategy_*.csv")
    files = glob.glob(search_path)
    
    if not files: files = glob.glob("strategy_*.csv")
    
    grouped = {}
    
    for f in files:
        basename = os.path.basename(f)
        # Format: strategy_NAME_DATE_TIME.csv
        # We strip "strategy_" prefix and ".csv" suffix
        # Then we assume the LAST TWO parts are Date and Time
        
        core_name = basename.replace("strategy_", "").replace(".csv", "")
        parts = core_name.split("_")
        
        if len(parts) >= 3:
            # Reassemble everything EXCEPT the last two tokens
            variant_name = "_".join(parts[:-2])
        else:
            # Fallback for weird filenames
            variant_name = core_name
            
        if variant_name not in grouped: grouped[variant_name] = []
        grouped[variant_name].append(f)
        
    for k in grouped:
        grouped[k].sort(key=os.path.getmtime, reverse=True)
        
    return grouped

def main_menu():
    while True:
        print("\n" + "="*50)
        print("🏗️  STRATEGY COMPILER (v2.2 - Name Fix)")
        print("="*50)
        
        groups = scan_files()
        if not groups:
            print(f"❌ No 'strategy_*.csv' files found.")
            return

        sorted_variants = sorted(groups.keys())
        
        print(f"Found {sum(len(v) for v in groups.values())} strategy files for {len(groups)} variants.\n")
        
        for i, var in enumerate(sorted_variants, 1):
            count = len(groups[var])
            latest = groups[var][0]
            ts = get_file_timestamp(latest)
            print(f"{i}. {var:<20} ({count} files) - Latest: {ts}")
            
        print("\nQ. Quit")
        choice = input("\nSelect Variant to Update: ").strip().upper()
        
        if choice == 'Q': break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(sorted_variants):
                selected_variant = sorted_variants[idx]
                select_file_menu(selected_variant, groups[selected_variant])
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Invalid input.")

def select_file_menu(variant, files):
    print(f"\n--- Select File for {variant} ---")
    for i, f in enumerate(files, 1):
        ts = get_file_timestamp(f)
        print(f"{i}. {os.path.basename(f)}  ({ts})")
    print("0. Cancel")
    
    choice = input("\nFile #: ").strip()
    if choice == '0': return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(files):
            target_file = files[idx]
            print(f"\n🚀 Compiling {target_file}...")
            rules = parse_csv(target_file)
            if rules:
                py_code = generate_python_dict(rules, variant)
                inject_code(variant, py_code)
                input("\n(Press Enter to continue)")
            else:
                print("❌ Failed to parse rules.")
                input("\n(Press Enter to continue)")
        else:
            print("❌ Invalid selection.")
    except ValueError:
        print("❌ Invalid input.")

if __name__ == "__main__":
    main_menu()