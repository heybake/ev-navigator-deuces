import shutil
import os
import datetime
import glob

# =========================================================
# ⚙️ CONFIGURATION
# =========================================================
# PASTE YOUR GOOGLE DRIVE FOLDER PATH HERE:
DRIVE_FOLDER = r"G:\My Drive\Temp\EV Navigator Deuces Wild\EV_Navigator_Gem_Context"

# 1. AUTO-DETECT: Grab all Python files (excluding this script)
SOURCE_FILES = [f for f in glob.glob("*.py") if "update_gem_context" not in f]

# 2. DOCUMENTATION: We grab the Map separately
DOC_FILES = ["README_GEM_CONTEXT.md"]

def create_monolith():
    print(f"🚀 Starting Context Sync...")
    
    if "PASTE_YOUR" in DRIVE_FOLDER:
        print("❌ ERROR: Please edit the 'DRIVE_FOLDER' path in this script!")
        return
    if not os.path.exists(DRIVE_FOLDER):
        print(f"❌ ERROR: Drive folder not found at: {DRIVE_FOLDER}")
        return

    # Build the Monolith (The Codebase)
    monolith_path = os.path.join(DRIVE_FOLDER, "EV_Navigator_FULL_CODE.txt")
    print(f"   🔨 Building Monolith: {monolith_path}...")
    
    try:
        with open(monolith_path, "w", encoding="utf-8") as outfile:
            outfile.write(f"EV NAVIGATOR CODEBASE SNAPSHOT\nGenerated: {datetime.datetime.now()}\n")
            outfile.write("="*60 + "\n\n")

            for filename in sorted(SOURCE_FILES):
                outfile.write(f"START_FILE: {filename}\n")
                outfile.write("-" * 40 + "\n")
                try:
                    with open(filename, "r", encoding="utf-8") as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    outfile.write(f"# Error reading file: {e}\n")
                outfile.write(f"\n\nEND_FILE: {filename}\n")
                outfile.write("="*60 + "\n\n")
                print(f"      + Added: {filename}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return

    # Copy Documentation
    for doc in DOC_FILES:
        if os.path.exists(doc):
            shutil.copy2(doc, os.path.join(DRIVE_FOLDER, doc))
            print(f"   📄 Copied Doc: {doc}")

    print(f"\n✨ Sync Complete! Files are ready in Google Drive.")

if __name__ == "__main__":
    create_monolith()