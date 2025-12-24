from dw_sim_engine import DeucesWildSim

def verify_fix():
    print("🧪 Verifying Flush Logic Fix (Wild Suit Independence)...")
    print("=" * 60)
    
    # We use BONUS_DEUCES to match your screenshot, but this logic is core to all.
    sim = DeucesWildSim(variant="BONUS_DEUCES")

    # --- TEST CASE 1 (From Image 1) ---
    # Scenario: 4 Hearts + 1 Diamond Deuce.
    # The Bug: Engine saw {Hearts, Diamonds} -> Count 2 -> Not Flush.
    # The Fix: Engine sees {Hearts} (Non-Deuces) -> Count 1 -> Flush.
    hand1 = ["8h", "9h", "2d", "Qh", "6h"]
    rank1, pay1 = sim.evaluate_hand_score(hand1)
    
    print(f"🃏 Hand 1: {hand1}")
    print(f"   expecting: FLUSH (Pays 3)")
    print(f"   actual:    {rank1} (Pays {pay1})")
    
    if rank1 == "FLUSH":
        print("   ✅ PASS: Diamond Deuce did not break the Heart Flush.")
    else:
        print("   ❌ FAIL: Still detecting mixed suits.")

    print("-" * 60)

    # --- TEST CASE 2 (From Image 2) ---
    # Scenario: 3 Clubs + 2 Wilds (Heart, Spade).
    # The Bug: Engine saw {Clubs, Hearts, Spades} -> Count 3 -> Not Flush.
    # The Fix: Engine sees {Clubs} (Non-Deuces) -> Count 1 -> Flush.
    hand2 = ["9c", "Ac", "2h", "Tc", "2s"]
    rank2, pay2 = sim.evaluate_hand_score(hand2)
    
    print(f"🃏 Hand 2: {hand2}")
    print(f"   expecting: FLUSH (Pays 3)")
    print(f"   actual:    {rank2} (Pays {pay2})")
    
    if rank2 == "FLUSH":
        print("   ✅ PASS: Multiple Wild suits ignored.")
    else:
        print("   ❌ FAIL: Still detecting mixed suits.")

    print("=" * 60)

if __name__ == "__main__":
    verify_fix()