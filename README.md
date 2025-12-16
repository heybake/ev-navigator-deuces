@"
# EV Navigator: Deuces Wild (Dual-Core Engine)

## 🧬 Overview
This is a **Variance Lab** and **Strategy Engine** for Deuces Wild Video Poker. It features a "Dual-Core" architecture that automatically pivots strategy between the two most common casino variants:
* **NSUD (Not So Ugly Ducks):** Aggressive Strategy (5OAK pays 16).
* **Airport / Illinois:** Defensive Strategy (5OAK pays 12).

## 📂 Architecture
* **\`dw_sim_engine.py\`**: The strategic brain. Handles hand evaluation, logic pivoting, and edge cases (e.g., Wheel Straights).
* **\`dw_multihand_sim.py\`**: The session controller. Runs batch simulations, generates variance plots, and enforces the "Protocol Guardian" safeguards.
* **\`dw_exact_solver.py\`**: The mathematical core. Calculates the exact Combinatorial EV (Expected Value) for any given hand.
* **\`test_deuces_suite.py\`**: A complete unit test suite verifying the math and strategy logic.

## 🚀 Usage

### 1. Run the Simulator
\`\`\`bash
python dw_multihand_sim.py
\`\`\`
*Follow the on-screen prompts to run a single hand or a batch simulation (e.g., 50 sessions).*

### 2. Run the Integrity Check
\`\`\`bash
python test_deuces_suite.py
\`\`\`
*Verifies the logic against known edge cases (e.g., the "Flush Trap").*

## 🛡️ The Protocol Guardian
The simulator includes a \`ProtocolGuardian\` class that mimics professional bankroll management:
* **Vacuum Stop:** Aborts if bankroll drops 25% in the first 15 hands.
* **Sniper Win:** Locks in profit at +20% gain.
* **Hard Deck:** Forces a stop at Hand 66 to prevent statistical drift.

## 📊 Outputs
* **logs/**: CSV files detailing every hand, action, and EV decision.
* **plots/**: PNG scatter plots visualizing the bankroll variance and "Amy Bot" betting levels.
"@ | Out-File -Encoding utf8 README.md