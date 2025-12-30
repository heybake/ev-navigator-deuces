import os
import csv
import glob
import sys

# ==============================================================================
# 📊 CONFIGURATION
# ==============================================================================
LOG_DIR = "logs"
REQUIRED_FIELDS = ["Variant", "Denom", "Wins", "EV", "Hand_ID"]
BET_PER_HAND = 5  # Standard Max Bet for Deuces Wild

def analyze_logs():
    print("=========================================================")
    print("   DEUCES WILD LOG VERIFIER (POST-MORTEM ANALYSIS)      ")
    print("=========================================================")

    # 1. Find all CSV logs
    pattern = os.path.join(LOG_DIR, "*.csv")
    files = glob.glob(pattern)
    
    if not files:
        print(f"[ERROR] No log files found in '{LOG_DIR}'")
        print("Run dw_multihand_sim.py first to generate data!")
        return

    print(f"📂 Found {len(files)} log files. Processing...\n")

    # 2. Data Containers (Grouped by Variant)
    # Structure: stats[variant] = {hands: 0, coin_in: 0, coin_out: 0, total_ev: 0.0}
    stats = {}

    total_files_processed = 0
    total_rows_processed = 0

    # 3. Process Files
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Validate headers
                if not reader.fieldnames: continue
                
                # Check for empty file
                rows = list(reader)
                if not rows: continue

                total_files_processed += 1
                
                for row in rows:
                    variant = row.get("Variant", "Unknown")
                    if variant not in stats:
                        stats[variant] = {
                            "hands": 0, 
                            "coin_in": 0, 
                            "coin_out": 0, 
                            "total_ev": 0.0,
                            "min_ev": 100.0,
                            "max_ev": 0.0
                        }

                    # Parse values
                    try:
                        # Wins = Credits Won (e.g., 5, 20, 4000)
                        wins = float(row.get("Wins", 0))
                        # EV = Expected Value of the hand held (e.g., 4.54)
                        ev = float(row.get("EV", 0))
                        
                        # Update Stats
                        stats[variant]["hands"] += 1
                        stats[variant]["coin_in"] += BET_PER_HAND
                        stats[variant]["coin_out"] += wins
                        stats[variant]["total_ev"] += ev
                        
                        total_rows_processed += 1
                        
                    except ValueError:
                        continue # Skip malformed rows

        except Exception as e:
            print(f"[WARN] Could not process {filepath}: {e}")

    # 4. Report Results
    if total_rows_processed == 0:
        print("[WARN] No valid data rows found.")
        return

    print("-" * 65)
    print(f"{'VARIANT':<20} | {'HANDS':<10} | {'THEORY RTP':<12} | {'REAL RTP':<10}")
    print("-" * 65)

    for variant, data in stats.items():
        hands = data["hands"]
        coin_in = data["coin_in"]
        coin_out = data["coin_out"]
        total_ev = data["total_ev"]
        
        # RTP Calculation
        # Theoretical = (Total EV Generated / Total Coin In)
        # Realized    = (Total Coin Won / Total Coin In)
        
        if coin_in > 0:
            rtp_theory = (total_ev / coin_in) * 100
            rtp_real = (coin_out / coin_in) * 100
            diff = rtp_real - rtp_theory
        else:
            rtp_theory = 0.0
            rtp_real = 0.0
            diff = 0.0

        # Formatting colors for the "Real" RTP
        # If within 0.5% of theory, it's green. If wildly off, red.
        pass_fail = "✅" if abs(diff) < 0.5 else "⚠️" 
        
        print(f"{variant:<20} | {hands:<10,} | {rtp_theory:>9.4f}%  | {rtp_real:>8.4f}% {pass_fail}")
        
    print("-" * 65)
    print(f"\n📊 SUMMARY: Processed {total_rows_processed:,} hands across {total_files_processed} files.")
    print("   (Note: Realized RTP requires ~1M+ hands to converge with Theory)")

if __name__ == "__main__":
    analyze_logs()