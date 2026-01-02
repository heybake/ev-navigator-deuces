import dw_core_engine
import dw_pay_constants
import dw_fast_solver

# 1. SETUP
VARIANT = "SUPER_DEUCES"
print(f"🕵️ TESTING VARIANT: {VARIANT}")

# Check if data exists
if VARIANT not in dw_pay_constants.PAYTABLES:
    print("❌ CRITICAL ERROR: Variant not found in Pay Constants!")
    exit()

paytable = dw_pay_constants.PAYTABLES[VARIANT]

# 2. CREATE THE JACKPOT HAND (4 Queens + 1 Deuce)
# Physics Engine expects strings like 'Qh', '2d'
hand = ['Qh', 'Qd', 'Qs', 'Qc', '2h']

# 3. ASK THE SIMULATION: "What is this hand?"
sim = dw_core_engine.DeucesWildCore()
rank = sim.identify_hand(hand)
payout = paytable.get(rank, 0)

print("-" * 30)
print(f"HAND: {hand}")
print(f"RANK DETECTED: {rank}")
print(f"PAYOUT (1 Coin): {payout}")
print("-" * 30)

if rank == "FIVE_OAK_1_DEUCE" and payout == 160:
    print("✅ SUCCESS: The Engine recognizes the Super Deuces Jackpot!")
else:
    print("❌ FAILURE: Engine logic is missing.")