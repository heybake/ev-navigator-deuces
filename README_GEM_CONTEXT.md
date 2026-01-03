# EV Navigator System Architecture (Gem Context Map)
**Version:** 1.0 (Production Candidate)
**Last Updated:** 2026-01-02

## 1. Core Philosophy (THE LAW)
* **Physics Isolation:** `dw_core_engine.py` is the "Black Box." It handles RNG, dealing, and hand identification ONLY. It never knows about money or bets.
* **Single Source of Truth:** `dw_pay_constants.py` is the supreme authority for all paytables. Never hardcode payout values; import them.
* **Variant Awareness:** Always check the active variant (e.g., `NSUD`, `BONUS_DEUCES_10_4`) before optimizing strategy.

## 2. Active File Inventory ("The Golden Set")
The application has been pruned to **9 essential files**. All experimental scripts (bots, batch simulators, plotters) have been moved to `_RESEARCH_ARCHIVE`.

### A. Interface & Orchestration
* **`dw_main.py`** (formerly `dw_trainer_test.py`):
    * **Role:** The Application Entry Point.
    * **Function:** Orchestrates the Game Loop, renders the UI (Pygame), manages the State Machine, and handles User Input.
    * **Key Components:** `SessionLogger` (Internal), `StrategyPanel`, `LogPanel`.
* **`dw_universal_lib.py`**:
    * **Role:** Shared UI Utilities.
    * **Function:** Handles screen scaling (`s()`), color definitions, and the `AssetManager` (loading cards/sounds).

### B. Core Physics & Logic
* **`dw_core_engine.py`**:
    * **Role:** The Physics Engine.
    * **Function:** Deck generation, Fisher-Yates shuffling (Mersenne Twister), and hand rank evaluation. Zero dependencies.
* **`dw_sim_engine.py`**:
    * **Role:** The Game Manager.
    * **Function:** Connects Physics to Payouts. Handles betting logic, dealing flow, and scoring.
* **`dw_pay_constants.py`**:
    * **Role:** Data Source.
    * **Function:** Contains the `PAYTABLES` dictionaries for all game variants. The Single Source of Truth.

### C. Strategy Engine ("The Brain")
* **`dw_strategy_definitions.py`**:
    * **Role:** The Rulebook.
    * **Function:** Defines atomic decision rules (e.g., `holds_natural_royal`, `holds_4_to_straight_flush`).
* **`dw_fast_solver.py`**:
    * **Role:** The Real-Time Solver.
    * **Function:** Uses a heuristic tree to instantly find the Best Hold and Runner-Up. Used for "Trainer Mode" feedback.
* **`dw_exact_solver.py`**:
    * **Role:** The Verifier.
    * **Function:** Calculates exact Expected Value (EV) via brute force. Used to audit the Fast Solver.

### D. Analytics & Support
* **`dw_stats_helper.py`**:
    * **Role:** Statistics Engine.
    * **Function:** Calculates Volatility, Variance, Hit Frequencies, and formatted "Win Strings" for the UI.

## 3. System Architecture & Topology (Dependency Report)
*Based on Static Analysis of Release 1.0 Source Code.*

### Executive Summary
The EV Navigator utilizes a **"Star Topology"** (Hub-and-Spoke) architecture. The application is centralized around a single entry point that orchestrates seven specialized modules. This design ensures that the User Interface manages state while delegating complex logic (Physics, Strategy, Analytics) to isolated sub-systems.

### The Dependency Graph
* **Entry Point (The Hub):** `dw_main.py`
    * *Role:* Main Loop, UI Rendering, State Machine.
    * *Direct Dependencies:* `dw_sim_engine.py`, `dw_fast_solver.py`, `dw_exact_solver.py`, `dw_strategy_definitions.py`, `dw_pay_constants.py`, `dw_universal_lib.py`, `dw_stats_helper.py`.
    * *Coupling:* Moderate (Intentional "Switchboard" Design).
* **The "Physics" Layer (Isolated):** `dw_core_engine.py`
    * *Role:* RNG and Hand Evaluation.
    * *Constraints:* Zero dependencies. Does not know the Simulator exists.
* **The "Brain" Layer (Pure Logic):** `dw_strategy_definitions.py`
    * *Role:* Atomic decision rules.
    * *Constraints:* Zero dependencies. Pure Python functions.
* **The "Data" Layer (Truth):** `dw_pay_constants.py`
    * *Role:* Static dictionaries for Payouts.
    * *Constraints:* Zero dependencies. Imported by Solver, Sim, and Stats.

### Metric Summary
* **Total Production Files:** 9
* **Depth Level:** 2 (Flat Hierarchy)
* **Circular Dependencies:** 0 (Verified via AST Scan)

## 4. Deployment Topology
* **Entry Point:** Run `python dw_main.py` to launch.
* **Assets:** Requires `images/` (Cards/Icons) and `sounds/` folders in the root directory.
* **Archives:** All non-production research code is stored in `_RESEARCH_ARCHIVE/`.