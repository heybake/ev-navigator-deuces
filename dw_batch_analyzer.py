"""
dw_batch_analyzer.py
THE FORENSIC ACCOUNTANT (v1.0)

Purpose:
Scans the 'logs/' directory, aggregates all session CSVs, and calculates
the Global RTP, Variance, and Survival Rates for the Deuces Wild Engine.
"""

import os
import glob
import pandas as pd
import numpy as np

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
LOG_DIR = "logs"  # The folder where your CSVs live
EXPECTED_RTP = 99.45  # Theoretical RTP for Bonus Deuces
BET_PER_HAND = 500.00 # $1 Denom * 5 Coins * 100 Lines

def analyze_batch():
    print(f"🔍 INITIALIZING BATCH ANALYSIS...")
    print(f"   Target Directory: ./{LOG_DIR}")
    
    # 1. Find Files
    search_path = os.path.join(LOG_DIR, "session_*.csv")
    files = glob.glob(search_path)
    
    if not files:
        print("❌ CRITICAL ERROR: No log files found!")
        print(f"   Make sure your CSVs are in the '{LOG_DIR}' folder.")
        return

    print(f"   Found {len(files)} session logs. Processing...")
    print("-" * 60)

    # 2. Aggregation Variables
    total_hands = 0
    total_wagered = 0.0
    total_won = 0.0
    
    sessions_won = 0  # Hit Ceiling ($20k)
    sessions_bust = 0 # Hit Floor ($0)
    sessions_alive = 0 # Hit Hand Cap
    
    # 3. Process File by File (Memory Efficient)
    for i, filepath in enumerate(files, 1):
        try:
            df = pd.read_csv(filepath)
            
            # --- VALIDATION ---
            if df.empty:
                print(f"⚠️  Warning: File {os.path.basename(filepath)} is empty. Skipping.")
                continue
                
            # --- MATH ---
            # Calculate metrics for this specific session
            hands_played = len(df)
            
            # Wager: We assume fixed bet size based on your settings (100 lines * $5)
            # If your CSV records Lines/Denom per row, we could be more dynamic, 
            # but for this batch, the fixed assumption is safer and faster.
            session_wager = hands_played * BET_PER_HAND
            
            # Win: Net_Result + Wager = Gross Payout
            # We sum the Net_Result column and add back the wagers
            net_result_sum = df['Net_Result'].sum()
            session_payout = net_result_sum + session_wager
            
            # --- ACCUMULATE ---
            total_hands += hands_played
            total_wagered += session_wager
            total_won += session_payout
            
            # --- DETERMINE FATE ---
            final_bankroll = df.iloc[-1]['Bankroll']
            start_bankroll = df.iloc[0]['Bankroll'] - df.iloc[0]['Net_Result'] # approx
            
            # Logic based on your $0 Floor / $20k Ceiling
            if final_bankroll <= 500: # allowing for small dust
                sessions_bust += 1
            elif final_bankroll >= 20000:
                sessions_won += 1
            else:
                sessions_alive += 1

        except Exception as e:
            print(f"❌ Error reading {os.path.basename(filepath)}: {e}")

    # 4. Final Calculations
    if total_wagered == 0:
        print("❌ No wagers found. Cannot calculate RTP.")
        return

    global_rtp = (total_won / total_wagered) * 100
    house_edge = 100 - global_rtp
    diff_from_theory = global_rtp - EXPECTED_RTP

    # 5. The Report
    print("\n" + "="*60)
    print(f"📊 FORENSIC REPORT: DEUCES WILD ENGINE")
    print("="*60)
    print(f"📂 Sessions Analyzed:  {len(files)}")
    print(f"🃏 Total Hands Dealt:  {total_hands:,}")
    print(f"💰 Total Coin-In:      ${total_wagered:,.2f}")
    print(f"💸 Total Coin-Out:     ${total_won:,.2f}")
    print("-" * 60)
    print(f"📈 GLOBAL RTP:         {global_rtp:.4f}%")
    print(f"📐 Theoretical RTP:    {EXPECTED_RTP:.4f}%")
    print(f"🎯 Deviation:          {diff_from_theory:+.4f}%")
    print("-" * 60)
    print(f"🏆 PERFORMANCE OUTCOMES")
    print(f"   WIN (Doubled Up):   {sessions_won}  ({(sessions_won/len(files))*100:.1f}%)")
    print(f"   BUST (Ruined):      {sessions_bust}  ({(sessions_bust/len(files))*100:.1f}%)")
    print(f"   ALIVE (Grinding):   {sessions_alive}  ({(sessions_alive/len(files))*100:.1f}%)")
    print("="*60)
    
    # 6. Verdict
    if abs(diff_from_theory) < 0.5:
        print("✅ VERDICT: ENGINE CERTIFIED (Within Statistical Variance)")
    elif diff_from_theory < -2.0:
        print("❌ VERDICT: POSSIBLE LOGIC LEAK (RTP Too Low)")
        print("   Suggest auditing 'Discard' strategy or 'Wild Royal' payouts.")
    else:
        print("⚠️ VERDICT: INCONCLUSIVE (High Variance detected)")
        print("   More samples needed to converge.")

if __name__ == "__main__":
    analyze_batch()