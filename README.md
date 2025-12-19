﻿# EV Navigator: Deuces Wild (Hybrid v3.2)

## 🔭 Overview
This is a **Variance Lab** and **Strategy Engine** for Deuces Wild Video Poker. It features a "Hybrid" architecture that automatically pivots strategy between three distinct casino variants based on the pay table structure.

## 🏗️ Architecture
* `dw_pay_constants.py`: **The Registry.** (New v3.2). The immutable "Single Source of Truth" for all pay table data. Separation of concerns (Data vs. Logic).
* `dw_sim_engine.py`: **The Strategic Brain.** (v3.2 User Verified). Handles hand evaluation, logic pivoting, and specific math for "Feature" games (e.g., Wheel costs, Split Pay Tables). Imports strictly from the Registry.
* `dw_multihand_sim.py`: **The Session Controller.** Runs batch simulations (e.g., 100 sessions) and enforces "Protocol Guardian" safeguards.
* `navigator_dealer.py`: **The Dealer.** A cryptographically secure RNG that generates hands for the simulation and training modes.
* `dw_exact_solver.py`: **The Math Core.** Calculates the exact Combinatorial EV (Expected Value) for any given hand using parallel processing. Imports strictly from the Registry.
* `dw_plot_tools.py`: **The Visualizer.** Generates variance scatter plots and performance graphs for post-session analysis.
* `test_deuces_suite.py`: **The Auditor.** A unit test suite verifying logic against known edge cases (e.g., The Flush Trap) and Registry integrity.

## 🎰 Supported Variants (Auto-Pivoting)

| Variant | 5 of a Kind | Straight Flush | Flush | Strategy Profile |
| :--- | :---: | :---: | :---: | :--- |
| **NSUD** | 16 | 10 | 3 | **Aggressive:** Break made hands to hunt for Quads. |
| **AIRPORT** | 12 | 9 | 3 | **Defensive:** Hold made Flushes to survive the grind. |
| **DBW** | 16 | 13 | 2 | **Hyper-Aggressive:** Treat Flushes as "Trash" (Pay 2) and hunt the 13x SF. |

## 🚀 Usage

### 1. Run the Simulator
```bash
python dw_multihand_sim.py