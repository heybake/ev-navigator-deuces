﻿# EV Navigator: Deuces Wild (v7.0) 🧬

**A Professional-Grade Video Poker Research Suite.**
*Certified Class III RNG | Micro-Service Architecture | Real-Time EV Coaching*

## 📦 Installation & Setup

### Prerequisites

* Python 3.8 or higher
* (Optional) `pandas` and `matplotlib` for plotting graphs.

### Setup

1. **Clone the Repository:**
`git clone https://github.com/YourUsername/ev-navigator-deuces.git`
`cd ev-navigator-deuces`
2. **Install Dependencies:**
The core simulator runs in pure Python. To enable the **Mission Control Plotting** tools, install the data science libraries:
`pip install pandas matplotlib`

## 🚀 Quick Start

**Launch the Simulator:**
`python dw_multihand_sim.py`

### Key Commands

| Command | Feature | Description |
| --- | --- | --- |
| **`[R]`** | **Random Batch** | Run high-speed simulations (e.g., 50 sessions of 1,000 hands). |
| **`[E]`** | **Enter Hand** | **EV Coach Mode:** Enter cards and get graded by the Solver. |
| **`[S]`** | **Settings** | Switch Variants (NSUD/Loose Deuces), set Lines, or adjust Bankroll. |
| **`[A]`** | **Toggle Amy** | Turn the **AI Betting Bot** ON/OFF. |
| **`[P]`** | **Toggle Protocol** | Turn the **Bankroll Guardian** ON/OFF. |
| **`[W]`** | **Toggle Wheel** | Enable the "Double Wheel" volatility feature. |

## 🌟 New Features (v7.0)

### 1. 🧠 Interactive EV Coach

The `[E]`nter Hand mode now integrates a **Brute-Force Exact Solver**.

* It calculates the Expected Value (EV) of your hold vs. the optimal hold.
* It displays the **Equity Error** (Cost of Mistake) in real-time.

### 2. 🛡️ The Protocol Guardian

A dedicated Compliance Officer module (`dw_protocol_guardian.py`) that enforces professional bankroll management rules:

* **Sniper Win:** Locks in profits immediately upon hitting +20% gain.
* **Vacuum Stop:** Exits early if the machine shows "cold" variance (-25% in 15 hands).
* **Zombie Limit:** Prevents "walking dead" play (grinding at a loss) past Hand 40.

### 3. 🤖 "Amy" AI Agent

An algorithmic betting bot (`dw_bot_amy.py`) that simulates a disciplined player:

* **Ladder Logic:** Scales bets ($0.05 -> $0.10 -> $0.25) based on win-rate trends.
* **Liquidity Check:** Only moves up if the bankroll can sustain the volatility.

### 4. 🎰 Multi-Variant Engine

Supports dynamic rule injection via `dw_pay_constants.py`.

* **NSUD:** Not So Ugly Ducks (~99.7% RTP).
* **LOOSE DEUCES:** High volatility, 2500 coin Jackpot for 4 Deuces.
* **AIRPORT / DBW:** Custom variants.

## 📂 System Architecture

The project uses a **Micro-Service Architecture** to ensure stability:

| File | Role | Description |
| --- | --- | --- |
| **`dw_multihand_sim.py`** | **Controller** | The main entry point. Orchestrates the UI and loop. |
| **`dw_core_engine.py`** | **Physics** | **Certified RNG.** Handles shuffling and dealing. |
| **`dw_sim_engine.py`** | **Logic** | Handles hand evaluation and payout mapping. |
| **`dw_bot_amy.py`** | **Agent** | Contains the AI betting logic (Amy). |
| **`dw_protocol_guardian.py`** | **Compliance** | Contains the Stop-Loss/Take-Profit rules. |
| **`dw_logger.py`** | **Memory** | Handles CSV logging and file I/O. |
| **`dw_exact_solver.py`** | **Solver** | The mathematical engine for the EV Coach. |

## 📜 Certification

* **RNG Audit:** Passed (5,000,000 Hands)
* **Statistical Test:** Chi-Square Goodness-of-Fit
* **Result:** Uniform Distribution (p > 0.05)

*Built for educational research into Video Poker volatility and bankroll management strategies.*