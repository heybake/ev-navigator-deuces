"""
dw_plot_tools.py
CORE VISUALIZATION MODULE for Deuces Wild "Airport Protocol".

This module generates the "Mission Control" Dashboard.
It is designed to be imported by other tools or run standalone.

USAGE:
    1. Import: from dw_plot_tools import generate_mission_control_plot
    2. Standalone: python dw_plot_tools.py [filename or folder]
"""

import pandas as pd
import matplotlib.pyplot as plt
import sys
import argparse
import glob
import os

def classify_session(df, start_bank, floor, ceiling):
    """
    Analyzes the flight path to assign an Airport Protocol Classification.
    Returns: (Label, Color_Code)
    """
    max_bank = df['Bankroll'].max()
    # Check minimum of first 10 hands, or all hands if length < 10
    min_bank_first_10 = df['Bankroll'].iloc[:10].min() if len(df) >= 10 else df['Bankroll'].min()
    final_bank = df['Bankroll'].iloc[-1]
    total_hands = len(df)
    
    # 1. SNIPER CHECK (Priority #1: Did we hit the target?)
    if max_bank >= ceiling:
        return ("SNIPER (MISSION SUCCESS)", "#00CC00") # Green
        
    # 2. VACUUM CHECK (Did we crash immediately?)
    if min_bank_first_10 <= floor:
        return ("VACUUM (EARLY FAILURE)", "#8B0000") # Dark Red
        
    # 3. TEASE CHECK (Did we profit then die?)
    if max_bank > start_bank and final_bank < start_bank:
        return ("THE TEASE (PROFIT LOST)", "#FF8C00") # Orange
        
    # 4. HARD DECK CHECK (Did we stay too long?)
    if total_hands >= 35:
        return ("HARD DECK (MATH DEAD)", "#555555") # Grey
        
    # 5. ZOMBIE CHECK (Are we just surviving?)
    if total_hands >= 20 and final_bank < start_bank:
        return ("ZOMBIE (SLOW BLEED)", "#800080") # Purple

    # Default
    return ("GRIND (IN PROGRESS)", "#0000FF") # Blue

def generate_mission_control_plot(csv_filename, floor=None, ceiling=None, spike_threshold=5.0, show_plot=False):
    """
    Generates the Dashboard Plot.
    
    Args:
        csv_filename (str): Path to the log file.
        floor (float): Stop loss level (optional, auto-calc if None).
        ceiling (float): Profit target (optional, auto-calc if None).
        spike_threshold (float): Dollar amount to qualify as a "Big Win" (default $5).
        show_plot (bool): If True, opens the window. If False, just saves file.
    """
    # 1. Load Data
    try:
        df = pd.read_csv(csv_filename)
        if 'Bankroll' not in df.columns or 'Hand_ID' not in df.columns:
            print(f"⚠️ Skipping {csv_filename}: Missing columns.")
            return
        print(f"✅ Generating Plot for {csv_filename}...")
    except Exception as e:
        print(f"❌ Error reading {csv_filename}: {e}")
        return

    # Data Prep
    x_vals = df['Hand_ID']
    y_vals = df['Bankroll']
    start_bank = df['Bankroll'].iloc[0]
    
    # --- 🧠 DYNAMIC PROTOCOL ---
    ceiling_is_auto = False
    if ceiling is None:
        ceiling = start_bank * 1.20
        ceiling_is_auto = True

    floor_is_auto = False
    if floor is None:
        floor = start_bank * 0.75
        floor_is_auto = True
    
    # --- 🏷️ CLASSIFY SESSION ---
    mission_type, mission_color = classify_session(df, start_bank, floor, ceiling)

    # 2. Setup Style
    try:
        plt.style.use('seaborn-v0_8-darkgrid') 
    except:
        plt.style.use('ggplot') 
        
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # 3. ZONES (Legend)
    ax.fill_between(x_vals, y_vals, start_bank, where=(y_vals >= start_bank), 
                    interpolate=True, color='green', alpha=0.1, label='Profit Zone')
    ax.fill_between(x_vals, y_vals, start_bank, where=(y_vals < start_bank), 
                    interpolate=True, color='red', alpha=0.1, label='Danger Zone')

    # 4. FLOOR & CEILING
    # Floor
    plt.axhspan(0, floor, color='#8B0000', alpha=0.15, zorder=0)
    plt.axhline(y=floor, color='red', linestyle='--', linewidth=2, alpha=0.8, label='Hard Deck')
    floor_label = "[AUTO] VACUUM LIMIT (-25%)" if floor_is_auto else "[USER] HARD DECK"
    plt.text(x_vals.iloc[0], floor - (floor*0.02), floor_label, 
             color='red', fontsize=10, fontweight='bold', va='top')

    # Ceiling
    plt.axhline(y=ceiling, color='#00CC00', linestyle='--', linewidth=2, alpha=0.8, label='Target')
    ceil_label = "[AUTO] SNIPER TARGET (+20%)" if ceiling_is_auto else "[USER] TARGET"
    plt.text(x_vals.iloc[0], ceiling + (ceiling*0.02), ceil_label, 
             color='#00CC00', fontsize=10, fontweight='bold', va='bottom')

    # 5. MAIN LINE
    ax.plot(x_vals, y_vals, color='#2c3e50', linewidth=2, zorder=2, label='Bankroll')
    ax.axhline(y=start_bank, color='black', linestyle='-', linewidth=1, alpha=0.3)

    # 6. PLOT MARKERS
    if 'Wheel_Mult' in df.columns and 'Net_Result' in df.columns:
        wheel_triggers = df[df['Wheel_Mult'] > 1]
        if not wheel_triggers.empty:
            ax.scatter(wheel_triggers['Hand_ID'], wheel_triggers['Bankroll'], 
                       color='gold', s=300, alpha=0.2, zorder=3, marker='o') 
            ax.scatter(wheel_triggers['Hand_ID'], wheel_triggers['Bankroll'], 
                       color='#FFD700', edgecolors='black', marker='*', s=150, zorder=4, label='Wheel Trigger')

        natural_wins = df[(df['Net_Result'] >= spike_threshold) & (df['Wheel_Mult'] <= 1)]
        if not natural_wins.empty:
            ax.scatter(natural_wins['Hand_ID'], natural_wins['Bankroll'], 
                       color='#00BFFF', edgecolors='black', marker='D', s=100, zorder=5, label='Big Win (Natural)')

    # 7. ANNOTATIONS
    if 'Wheel_Mult' in df.columns and 'Net_Result' in df.columns:
        high_mult_mask = (df['Wheel_Mult'] >= 4)
        big_win_mask = (df['Net_Result'] >= spike_threshold)
        spike_hands = df[high_mult_mask | big_win_mask]
        
        for _, row in spike_hands.iterrows():
            hand_id = row['Hand_ID']
            bankroll = row['Bankroll']
            mult = int(row['Wheel_Mult']) if row['Wheel_Mult'] > 1 else 1
            raw_summary = str(row['Hit_Summary'])
            
            if "No Jackpots" in raw_summary:
                short_summary = "(Dead)"
            else:
                short_summary = raw_summary.split('(')[0].split(',')[0].strip()
                if len(short_summary) > 15: short_summary = short_summary[:12] + "..."

            if mult > 1:
                label_text = f"{mult}x\n{short_summary}"
                box_color = "#b30000"
                offset = 25
            else:
                label_text = f"WIN\n{short_summary}"
                box_color = "#0047AB"
                offset = 35 

            ax.annotate(
                label_text, 
                xy=(hand_id, bankroll), 
                xytext=(0, offset), textcoords='offset points', ha='center', 
                fontsize=9, fontweight='bold', color='white',
                bbox=dict(boxstyle="round,pad=0.3", fc=box_color, ec="black", alpha=0.9),
                arrowprops=dict(arrowstyle='-', color='black', lw=0.5)
            )

    # 8. HIGH WATER MARK
    max_idx = df['Bankroll'].idxmax()
    max_hand = df.loc[max_idx, 'Hand_ID']
    max_val = df.loc[max_idx, 'Bankroll']
    
    ax.scatter(max_hand, max_val, color='#00FF00', edgecolors='black', marker='^', s=180, zorder=6, label='High Water Mark')
    
    is_spike = False
    if 'spike_hands' in locals() and not spike_hands.empty:
        if max_hand in spike_hands['Hand_ID'].values: is_spike = True
    hw_offset = 65 if is_spike else 35 
    
    ax.annotate(f"PEAK\n${max_val:.2f}", xy=(max_hand, max_val), xytext=(0, hw_offset), 
                textcoords='offset points', ha='center', fontsize=10, fontweight='bold', color='green',
                arrowprops=dict(arrowstyle='->', color='green', lw=2))

    # 9. HUD with CLASSIFICATION
    final_bank = df['Bankroll'].iloc[-1]
    net_result = final_bank - start_bank
    
    hud_text = (
        f"MISSION TYPE: {mission_type}\n"
        f"──────────────────────────\n"
        f"Hands Played:  {len(df)}\n"
        f"Start Bank:    ${start_bank:.2f}\n"
        f"Final Bank:    ${final_bank:.2f}\n"
        f"Net Result:    {'+' if net_result > 0 else ''}${net_result:.2f}\n"
        f"High Water:    ${max_val:.2f}"
    )
    
    props = dict(boxstyle='round', facecolor='white', alpha=0.95, edgecolor=mission_color, linewidth=3)
    ax.text(0.02, 0.95, hud_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props, fontfamily='monospace', fontweight='bold')

    # 10. SCALING & TITLE
    data_min = y_vals.min()
    data_max = y_vals.max()
    view_min = min(floor, data_min)
    view_max = max(ceiling, data_max)
    padding = (view_max - view_min) * 0.1
    ax.set_ylim(view_min - padding, view_max + padding)

    variant_name = df['Variant'].iloc[0] if 'Variant' in df.columns else "Unknown"
    ax.set_title(f"MISSION TELEMETRY: {variant_name} VARIANT", fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel("HAND NUMBER (DURATION)", fontsize=12, fontweight='bold')
    ax.set_ylabel("BANKROLL ($)", fontsize=12, fontweight='bold')

    # 11. LEGEND
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10),
              fancybox=True, shadow=True, ncol=5, fontsize=10)
    
    # Save
    output_filename = csv_filename.replace('.csv', '_mission_control.png')
    plt.savefig(output_filename, dpi=120)
    
    if show_plot:
        plt.show()
    
    plt.close(fig)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch Generate Mission Control Dashboards")
    parser.add_argument("path", nargs='?', default=".", help="File or Directory to process")
    parser.add_argument("--floor", type=float, default=None, help="Stop Loss Level")
    parser.add_argument("--ceiling", type=float, default=None, help="Profit Target")
    parser.add_argument("--spike", type=float, default=5.0, help="Min $ Win to Annotate")
    args = parser.parse_args()

    target_files = []
    if os.path.isfile(args.path):
        target_files.append(args.path)
    elif os.path.isdir(args.path):
        target_files = glob.glob(os.path.join(args.path, "*.csv"))
        print(f"📂 Scanning directory '{args.path}'...")
    else:
        target_files = glob.glob(args.path)

    if not target_files:
        print("❌ No CSV files found.")
    else:
        print(f"🚀 Found {len(target_files)} CSV files. Generating plots...")
        for csv_file in target_files:
            generate_mission_control_plot(csv_file, floor=args.floor, ceiling=args.ceiling, spike_threshold=args.spike)
        print(f"🏁 Batch Complete.")