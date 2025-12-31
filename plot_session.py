import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import io

# ==============================================================================
# 1. DATA LOADING (Embedded Sample from your Log)
# ==============================================================================
csv_raw = """HandID,Time,Variant,Bankroll_Start,Denom,Coins,Bet_Cost,Result_Rank,Win_Amt,Profit
1,12:00:03,NSUD,100.00,0.25,5,1.25,LOSER,0.00,-1.25
11,12:00:12,NSUD,92.50,0.25,5,1.25,FULL_HOUSE,5.00,3.75
29,12:00:27,NSUD,90.00,0.25,5,1.25,FOUR_OAK,5.00,3.75
34,12:00:31,NSUD,90.00,0.25,5,1.25,FLUSH,3.75,2.50
59,12:00:51,NSUD,80.00,0.25,5,1.25,STRAIGHT,2.50,1.25
127,12:01:47,NSUD,67.50,0.25,5,1.25,FLUSH,3.75,2.50
136,12:01:54,NSUD,62.50,0.25,5,1.25,FULL_HOUSE,5.00,3.75
144,12:02:01,NSUD,67.50,0.25,5,1.25,FULL_HOUSE,5.00,3.75
197,12:02:44,NSUD,51.25,0.25,5,1.25,LOSER,0.00,-1.25
"""

# TO USE REAL FILE, UNCOMMENT BELOW:
# df = pd.read_csv("logs/your_session_file.csv")
# For now, we use the reconstruction:
df = pd.read_csv(io.StringIO(csv_raw))

# ==============================================================================
# 2. DATA RECONSTRUCTION (Filling the gaps for the curve)
# ==============================================================================
# Since the sample log only had key events, we linearly interpolate 
# to create the "Grind" look of a real session.
full_hands = np.arange(1, 198)
bankroll_curve = np.interp(full_hands, df['HandID'], df['Bankroll_Start'])

# Create a clean DataFrame for plotting
plot_df = pd.DataFrame({'Hand': full_hands, 'Bankroll': bankroll_curve})

# Calculate a Rolling Average (Trend)
plot_df['Trend'] = plot_df['Bankroll'].rolling(window=20).mean()

# ==============================================================================
# 3. PLOTTING ENGINE (The "Mathematica" Style)
# ==============================================================================
# Set font to something professional (serif/sans-serif math style)
plt.rcParams['font.family'] = 'DejaVu Sans' 
plt.style.use('dark_background')

fig, ax = plt.subplots(figsize=(14, 8), dpi=100)

# Colors
C_LINE = '#00f2ff'    # Cyan Neon
C_TREND = '#ffffff'   # White
C_FILL = '#00f2ff'
C_GRID = '#333333'
C_TEXT = '#e0e0e0'

# A. Main Data Line
ax.plot(plot_df['Hand'], plot_df['Bankroll'], color=C_LINE, linewidth=1.5, label='Actual Balance', alpha=0.9)

# B. Gradient Fill (Simulated with alpha layers)
ax.fill_between(plot_df['Hand'], plot_df['Bankroll'], 50, color=C_FILL, alpha=0.1)
ax.fill_between(plot_df['Hand'], plot_df['Bankroll'], 50, color=C_FILL, alpha=0.05)

# C. Trend Line (The "Signal" amidst the "Noise")
ax.plot(plot_df['Hand'], plot_df['Trend'], color=C_TREND, linewidth=2, linestyle='--', alpha=0.6, label='20-Hand Trend')

# D. Reference Lines
ax.axhline(y=100, color='#888888', linestyle=':', linewidth=1, label='Start ($100)')
ax.axhline(y=50, color='#ff4444', linestyle='-', linewidth=2, label='Floor Limit ($50)')

# E. Annotations (Key Hands)
major_wins = df[df['Win_Amt'] >= 3.00] # Filter for big wins
for _, row in major_wins.iterrows():
    h = row['HandID']
    b = row['Bankroll_Start']
    label = row['Result_Rank'].replace('_', ' ').title()
    
    # Draw arrow and label
    ax.annotate(
        f"{label}\n(${row['Win_Amt']:.2f})", 
        xy=(h, b), 
        xytext=(h, b + 8),
        arrowprops=dict(arrowstyle='->', color='yellow', lw=1.5),
        color='yellow', fontsize=9, ha='center', weight='bold',
        bbox=dict(boxstyle="round,pad=0.3", fc="#222222", ec="yellow", alpha=0.8)
    )
    # Draw point on line
    ax.plot(h, b, 'o', color='white', markersize=5, markeredgecolor='yellow')

# ==============================================================================
# 4. AXIS & GRID STYLING (Fixing the "No Numbers" Bug)
# ==============================================================================
# Grid - Subtle but precise
ax.grid(which='major', color=C_GRID, linestyle='-', linewidth=0.8)
ax.grid(which='minor', color=C_GRID, linestyle=':', linewidth=0.5, alpha=0.5)
ax.minorticks_on()

# Spines - Make them visible
for spine in ax.spines.values():
    spine.set_edgecolor('#666666')
    spine.set_linewidth(1.5)

# Ticks - THE CRITICAL FIX
ax.tick_params(axis='both', colors=C_TEXT, which='major', labelsize=11, length=6, width=1.5)
ax.tick_params(axis='both', colors=C_TEXT, which='minor', length=3, width=1)

# Labels
ax.set_title("Deuces Wild Session Analysis: The 'Slow Bleed'", fontsize=18, color='white', pad=20, weight='bold')
ax.set_xlabel("Hands Played", fontsize=14, color=C_TEXT, labelpad=10)
ax.set_ylabel("Bankroll ($)", fontsize=14, color=C_TEXT, labelpad=10)

# Legend
ax.legend(loc='upper right', frameon=True, facecolor='#222222', edgecolor='#666666', fontsize=10)

# Stats Box
stats_text = (
    f"Hands: {197}\n"
    f"Start: $100.00\n"
    f"End:   $51.25\n"
    f"Net:   -$48.75"
)
props = dict(boxstyle='round', facecolor='#222222', alpha=0.9, edgecolor='#666666')
ax.text(0.02, 0.05, stats_text, transform=ax.transAxes, fontsize=12,
        verticalalignment='bottom', color='white', bbox=props, family='monospace')

# Final Polish
plt.tight_layout()
plt.show()