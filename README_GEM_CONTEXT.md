# EV Navigator System Architecture (Gem Context Map)

## 1. Core Philosophy (THE LAW)
* **Physics Isolation:** `dw_core_engine.py` is the "Black Box." It handles RNG, dealing, and hand identification ONLY. It never knows about money or bets.
* **Single Source of Truth:** `dw_pay_constants.py` is the supreme authority for all paytables. Never hardcode payout values; import them.
* **Variant Awareness:** Always check the active variant (e.g., `NSUD`, `BONUS_DEUCES_10_4`) before optimizing strategy.

## 2. File Dependency Map

### A. Core Logic & Physics
* **`dw_core_engine.py`**: Handles deck generation, shuffling (Mersenne Twister), and hand rank identification.
* **`dw_sim_engine.py`**: The Game Manager. Connects Physics to Payouts. Handles betting, dealing, and evaluating the final score.
* **`dw_pay_constants.py`**: **CRITICAL.** Contains the dictionaries for all variants (`PAYTABLES`).

### B. Strategy Pipeline
* **`dw_strategy_definitions.py`**: The "Rulebook." Contains Python functions like `holds_natural_royal`.
* **`dw_exact_solver.py`**: The "Teacher" (Brute-force Math).
* **`dw_fast_solver.py`**: The "Student" (Heuristic/Tree-based, high speed).
* **`dw_verify_strategy.py`**: The Auditor. Compares "Student" vs "Teacher".

### C. Simulation & Behavior
* **`dw_bot_amy.py`**: The AI Player. Implements betting ladders and risk tolerance.
* **`dw_protocol_guardian.py`**: The Risk Manager (Stop-loss, Sniping).
* **`dw_multihand_sim.py`**: The CLI entry point for batch simulations.

### D. UI & Visualization
* **`dw_trainer.py`**: The Pygame GUI.
* **`dw_plot_tools.py`**: Generates "Mission Control" dashboards.
* **`dw_logger.py`**: Handles CSV logging.