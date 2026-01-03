import os
import datetime
import shutil

# =========================================================
# ⚙️ CONFIGURATION
# =========================================================
# PASTE YOUR GOOGLE DRIVE FOLDER PATH HERE:
DRIVE_FOLDER = r"G:\My Drive\Temp\EV Navigator Deuces Wild\EV_Navigator_Gem_Context"

# =========================================================
# 📂 FILE CATEGORIZATION MAP
# =========================================================
FILE_MAP = {
    "EV_NAV_1_CORE.txt": [
        "dw_core_engine.py",
        "dw_sim_engine.py",
        "dw_pay_constants.py"
    ],
    "EV_NAV_2_STRATEGY.txt": [
        "dw_fast_solver.py",
        "dw_exact_solver.py",
        "dw_strategy_definitions.py"
    ],
    "EV_NAV_3_INTERFACE.txt": [
        "dw_main.py",
        "dw_stats_helper.py",
        "dw_universal_lib.py"  # Ensure this is captured this time!
    ]
}

# Documentation to include with every update (Optional)
DOC_FILES = ["README_GEM_CONTEXT.md", "README_MOBILE_DEVICES.md"]

def get_file_timestamp(filepath):
    """Gets the formatted last modification time of a file."""
    try:
        ts = os.path.getmtime(filepath)
        return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return "MISSING_FILE"

def create_bundles():
    print(f"🚀 Starting Split-Context Sync...")
    print(f"   Target: {DRIVE_FOLDER}\n")
    
    if "PASTE_YOUR" in DRIVE_FOLDER:
        print("❌ ERROR: Please edit the 'DRIVE_FOLDER' path in this script!")
        return
    if not os.path.exists(DRIVE_FOLDER):
        print(f"❌ ERROR: Drive folder not found.")
        return

    # 1. Process Code Bundles
    for bundle_name, file_list in FILE_MAP.items():
        output_path = os.path.join(DRIVE_FOLDER, bundle_name)
        print(f"📦 Building Bundle: {bundle_name}...")
        
        try:
            with open(output_path, "w", encoding="utf-8") as outfile:
                outfile.write(f"EV NAVIGATOR CONTEXT: {bundle_name}\n")
                outfile.write(f"Generated: {datetime.datetime.now()}\n")
                outfile.write("="*60 + "\n\n")

                for filename in file_list:
                    if not os.path.exists(filename):
                        print(f"   ⚠️ WARNING: {filename} not found in root!")
                        outfile.write(f"!!! MISSING FILE: {filename} !!!\n\n")
                        continue

                    timestamp = get_file_timestamp(filename)
                    outfile.write(f"START_FILE: {filename}\n")
                    outfile.write(f"LAST_MODIFIED: {timestamp}\n")
                    outfile.write("-" * 40 + "\n")
                    
                    try:
                        with open(filename, "r", encoding="utf-8") as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"# Error reading file: {e}\n")
                    
                    outfile.write(f"\n\nEND_FILE: {filename}\n")
                    outfile.write("="*60 + "\n\n")
                    print(f"   + Packed: {filename}")

        except Exception as e:
            print(f"   ❌ Failed to write bundle: {e}")

    # 2. Copy Documentation
    print("\n📄 Syncing Documentation...")
    for doc in DOC_FILES:
        if os.path.exists(doc):
            try:
                shutil.copy2(doc, os.path.join(DRIVE_FOLDER, doc))
                print(f"   + Copied: {doc}")
            except Exception as e:
                print(f"   ⚠️ Error copying {doc}: {e}")

    print(f"\n✅ SYSTEM READY. Upload the files from Drive to Gemini.")

if __name__ == "__main__":
    create_bundles()