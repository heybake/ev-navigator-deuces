import dw_exact_solver
import dw_pay_constants

# Config
VARIANT = "BONUS_DEUCES_10_4"
PAYTABLE = dw_pay_constants.PAYTABLES[VARIANT]

# The Problem Hand (Pair of Jacks)
HAND = ["Jh", "Jd", "5c", "9s", "4h"]
HELD_INDICES = [0, 1] # Hold J-J

print(f"🕵️ DEBUGGING EV FOR: {HAND}")
print(f"   Held Indices: {HELD_INDICES} ({[HAND[i] for i in HELD_INDICES]})")
print(f"   Variant: {VARIANT}")
print("-" * 40)

# 1. Run Calculation
ev = dw_exact_solver.calculate_exact_ev(HAND, HELD_INDICES, PAYTABLE)
print(f"📊 CALCULATED EV: {ev}")

# 2. Check "Ghost" Payouts
# We will simulate a few draws to see what 'evaluate_hand' returns
print("\n🧪 SAMPLING OUTCOMES:")
import random
deck = [r+s for r in "23456789TJQKA" for s in "shdc"]
norm_hand = [c[0].upper() + c[1].lower() for c in HAND]
stub = [c for c in deck if c not in norm_hand]

for _ in range(5):
    drawn = random.sample(stub, 3)
    final = [norm_hand[i] for i in HELD_INDICES] + drawn
    payout = dw_exact_solver.evaluate_hand(final, PAYTABLE)
    print(f"   Draw {drawn} -> Payout: {payout}")