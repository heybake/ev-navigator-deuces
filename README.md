# 🧬 EV Navigator: Deuces Wild (Dual-Core Engine)

## Overview
**EV Navigator** is a specialized Variance Lab and Strategy Engine for Deuces Wild Video Poker. Unlike generic solvers, this engine operates on a "Dual-Core" architecture that automatically pivots strategy based on the specific Pay Table volatility:

* **NSUD (Not So Ugly Ducks):** Aggressive Strategy (5OAK pays 16). [cite_start]We break made hands to hunt for Quads[cite: 6].
* **Airport / Illinois:** Defensive Strategy (5OAK pays 12). [cite_start]We hold made hands (like Flushes) to reduce variance[cite: 7].

The core philosophy is defined by **The Deuce Event Horizon**: The "2" is not a card; it is a multiplier. [cite_start]Hand value is determined strictly by the count of Deuces[cite: 3].

---

## 🚀 Key Features: DBW & Plotting

The repository focuses on two main pillars of analysis: **DBW (Deuces Wild Logic)** and **Variance Plotting (Simulation)**.

### 1. DBW (The Logic Core)
The analytical engine (`dw_exact_solver.py`) calculates Expected Value (EV) by analyzing "Deuce Density." It implements the mathematical axioms:
* [cite_start]**Axiom 1:** The "2" is a multiplier, not a high card[cite: 3].
* **Axiom 2:** The 5-of-a-Kind Payout is the fulcrum. [cite_start]If 5OAK > 15, we play aggressively; if < 13, we play defensively[cite: 5, 20, 21].
* [cite_start]**Penalty Card Theory:** In 0-Deuce hands, we discard cards (like Aces) that reduce outs to 5OAK[cite: 8, 9].

### 2. Plotting & Simulation (The Variance Lab)
The simulation engine (`dw_sim_engine.py`) is designed to generate data points for **Bankroll Variance Plotting**. It runs automated sessions to demonstrate the volatility of the strategy:
* [cite_start]**Tracks:** Deal, Hand, Action, Result, and Bankroll fluctuation[cite: 64].
* [cite_start]**Controls:** Includes Floor (Stop Loss) and Ceiling (Take Profit) parameters to mimic real session constraints[cite: 93].
* [cite_start]**Output:** Generates a structured log suitable for graphing variance over time[cite: 98].

---

## 📂 Repository Architecture

### 🧠 The Engines
* **`dw_exact_solver.py` (v3.1):** The mathematical heart. [cite_start]Uses multiprocessing to calculate the exact Combinatorial EV for any given hand against specific pay tables[cite: 64].
* **`dw_sim_engine.py`:** The "Variance Lab." [cite_start]Runs automated sessions (e.g., 50 deals) to demonstrate bankroll volatility and the reality of RNG[cite: 91].
* **`navigator_dealer.py`:** A strict RNG tool used for the **"EV Intuition Game"**. [cite_start]It ensures hands are dealt fairly using a Fisher-Yates shuffle for training purposes[cite: 78].

### 📜 The Protocols (Strategy Files)
* **`NSUD_Core_Strategy.txt`:** The "Golden Master" for 16/10 pay tables. [cite_start]Prioritizes "Deuce Density" over made hands[cite: 23].
* **`Airport_Deuces_Strategy.txt`:** The Defensive Protocol for 12/9 pay tables. Prioritizes "Variance Damping" (keeping Made Flushes)[cite: 103].
* [cite_start]**`dw_general_theory.txt`:** The Axioms of Deuces Wild (e.g., "Pairs are Trash," "The Penalty Card Theory")[cite: 1].

---

## 📉 The "Dual-Core" Pivot (Common Traps)
The engine handles specific "Traps" where the correct move flips 180° depending on the casino structure.

| Scenario | NSUD (Aggressive) | Airport (Defensive) | Logic |
| :--- | :--- | :--- | :--- |
| **2 Deuces + Made Flush** | **BREAK IT** | **HOLD IT** | NSUD breaks for Quads (EV ~16.37). [cite_start]Airport holds for safety (EV 15.00 > 14.79)[cite: 153, 154]. |
| **2 Deuces + Made Straight** | **BREAK IT** | **BREAK IT** | [cite_start]In both variants, 2 Deuces (EV ~15-16) crushes a Made Straight (EV 10)[cite: 155]. |
| **Suited Connectors (1 Deuce)** | **DRAW** | **DRAW** | Connectors (6-7) are valuable; [cite_start]Gapped (6-8) are weak[cite: 12]. |

---

## ⚙️ Usage & Modes

### 1. Mode A: Strategic Analysis (Solver)
Input a hand to receive the optimal hold based on the specific variant.
```python
# Run the solver script to access the specific solver functions
import dw_exact_solver
# Input hand to get EV and Best Hold
dw_exact_solver.solve_hand_silent(["2h", "2s", "5c", "9d", "Js"], pt=PAYTABLES["NSUD"])