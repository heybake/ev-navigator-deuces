﻿# 🧬 EV Navigator: Deuces Wild Suite (v3.2)
  
**A Professional-Grade Stochastic Simulation Lab for Video Poker.**
  
> "Pairs are trash. The 2 is the Sun."
  
## 🔭 Overview
**EV Navigator** is a Python-based research suite designed to solve, simulate, and visualize **Deuces Wild** video poker. Unlike standard trainers, it features a **Hybrid Architecture** that decouples "Card Physics" from "Economic Strategy," allowing for:
  
1.  **Dynamic Pivoting:** Automatically switches strategy logic between **NSUD** (Aggressive), **Airport** (Defensive), and **DBW** (Hybrid) based on pay table math.
2.  **Variance Visualization:** Generates "Mission Control" flight paths to visualize volatility and bankroll swings.
3.  **Protocol Enforcement:** Automates bankroll management using "Sniper" (Win) and "Vacuum" (Loss) triggers.
  
---
  
## 🏗️ Architecture
  
| Module | Role | Description |
| :--- | :--- | :--- |
| **`dw_core_engine.py`** | 🃏 Physics | The "Black Box." Handles RNG, shuffling, and hand ranking. Strictly immutable. |
| **`dw_sim_engine.py`** | 🧠 Strategy | The "Brain." Applies EV logic, manages the "Double Wheel," and executes strategy holds. |
| **`dw_exact_solver.py`** | 🔢 Math | A parallel-processing brute force solver that calculates exact EV for any 5 cards. |
| **`dw_multihand_sim.py`** | 🎮 Controller | The main CLI for running sessions, batch simulations, and managing the "Amy" bot. |
| **`dw_plot_tools.py`** | 📊 Visuals | Generates the "Mission Control" dashboard plots using Matplotlib/Pandas. |
| **`dw_compliance_test.py`** | ⚖️ Audit | Regulatory compliance suite to verify RNG statistical uniformity (Chi-Square). |
  
---
  
## 🚀 Usage Guide
  
### 1. The Simulator (Session Mode)
Run a multi-hand session with the "Protocol Guardian" active. This simulates the casino experience with automated safeguards.
  
```bash
python dw_multihand_sim.py
  
```
  
**Key Commands:**
  
* **[R]andom Batch:** Run automated sessions (e.g., 100 runs) to generate variance data.
* **[P]rotocol:** Toggle the "Guardian" (Hard Deck/Sniper limits).
* **[A]my:** Activate the auto-denomination stepping bot (see below).
* **[W]heel:** Toggle the "Double Wheel" feature (extra volatility).
  
### 2. The Exact Solver (Analysis Mode)
  
Calculate the mathematical truth of a hand using all CPU cores. Ideal for settling debates on close calls (e.g., "Do I keep the pair of 4s?").
  
```bash
python dw_exact_solver.py
  
```
  
* **Input:** `2h 2s 5c 6d 7s`
* **Output:** `Best Hold: 2h 2s (EV: 15.35)`
  
### 3. The Auditor (Compliance Mode)
  
Verify the statistical uniformity of the RNG. This runs a Chi-Square test on millions of hands to ensure the deck is not rigged.
  
```bash
python dw_compliance_test.py
  
```
  
---
  
## 🧠 Supported Variants & Strategies
  
The engine automatically adjusts its strategy matrix based on the selected variant:
  
| Variant | 5-of-a-Kind | Strategy Profile | Key Difference |
| --- | --- | --- | --- |
| **NSUD** | 16 | **Aggressive** | Breaks Made Flushes/Straights to hunt for Quads. |
| **Airport** | 12 | **Defensive** | Holds Made Flushes/Straights to survive the low volatility. |
| **DBW** | 16 | **Hybrid** | Hunts the specific 13x Straight Flush payout; treats Flushes as trash. |
  
---
  
## 🤖 The "Amy" Bot & Protocol Guardian
  
This suite includes automated agents to simulate disciplined play:
  
### The Protocol Guardian
  
A rules-based bankroll manager that enforces "Stop Loss" and "Take Profit" rules:
  
* **Sniper Win:** Stops immediately if Bankroll hits +20%.
* **Vacuum Stop:** Aborts if Bankroll drops -25% in the first 15 hands (bad start).
* **Hard Deck:** Forced exit after 66 hands to prevent grinding into a loss.
  
### Amy Mode
  
An algorithmic betting agent that scales denomination based on bankroll health:
  
* **Ladder:** Steps up denomination (e.g., <img src="https://latex.codecogs.com/gif.latex?0.05%20-&gt;"/>0.10 -> $0.25) when winning.
* **Retreat:** Steps down immediately when the "Window Ratio" (recent win rate) drops below 50%.
  
---
  
## 📊 "Mission Control" Visualization
  
When running batch simulations, the suite generates `_mission_control.png` dashboards via `dw_plot_tools.py`. These visualize:
  
* **The Flight Path:** Your bankroll over time.
* **The Zones:** "Sniper Targets" (Green) and "Vacuum Limits" (Red).
* **The Events:** Highlights big wins and "Wheel Triggers" on the chart.
  
---
  
## 🛠️ Installation
  
Requires **Python 3.8+**.
Dependencies are minimal, used primarily for the visualization engine.
  
```bash
pip install pandas matplotlib
  
```
  
---
  
## 📜 Disclaimer
  
*This software is for educational and mathematical research purposes only. It is a simulation tool designed to demonstrate the effects of variance and Expected Value (EV). It does not offer real-money gambling.*
  
  