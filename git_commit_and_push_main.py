#!/usr/bin/env python3
"""
git_commit_and_push_main.py

Performs:
  1. git status (printed)
  2. git add .
  3. git commit with a message that lists changed files
  4. git push origin main

Run from the repository root:
  python git_commit_and_push_main.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

def run(cmd, capture=False, check=True):
    if capture:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check)
    else:
        return subprocess.run(cmd, check=check)

def in_git_repo():
    try:
        run(["git", "rev-parse", "--is-inside-work-tree"], capture=True)
        return True
    except subprocess.CalledProcessError:
        return False

def print_git_status():
    print("=== git status ===")
    try:
        res = run(["git", "status"], capture=True)
        print(res.stdout)
    except subprocess.CalledProcessError as e:
        print("Failed to run git status:", e, file=sys.stderr)

def stage_all():
    print("Staging all changes (git add .)...")
    try:
        run(["git", "add", "."])
    except subprocess.CalledProcessError as e:
        print("git add failed:", e, file=sys.stderr)
        sys.exit(1)

def get_staged_files():
    # Use diff --name-only --cached to list staged files
    try:
        res = run(["git", "diff", "--name-only", "--cached"], capture=True)
        files = [s for s in res.stdout.splitlines() if s.strip()]
        return files
    except subprocess.CalledProcessError:
        return []

def get_unstaged_or_untracked_files():
    # Fallback: parse porcelain to show any changes
    try:
        res = run(["git", "status", "--porcelain"], capture=True)
        lines = res.stdout.splitlines()
        files = []
        for line in lines:
            if not line:
                continue
            # porcelain format: XY <path> or XY <path> -> <path>
            path = line[3:].strip()
            files.append(path)
        return files
    except subprocess.CalledProcessError:
        return []

def commit_with_file_list(files):
    if not files:
        print("No files to commit.")
        return False

    # Build commit message listing files
    commit_lines = ["Files changed:"]
    for f in files:
        commit_lines.append(f"- " + f)
    commit_message = "\n".join(commit_lines)

    # Write message to temp file and commit with -F
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tf:
        tf.write(commit_message)
        tf_path = tf.name

    try:
        print("Committing with message that lists changed files...")
        run(["git", "commit", "-F", tf_path])
        print("Commit successful.")
        return True
    except subprocess.CalledProcessError as e:
        # If commit failed, show stderr if available
        print("git commit failed.", file=sys.stderr)
        try:
            # try to show git status to help diagnose
            res = run(["git", "status"], capture=True)
            print(res.stdout)
        except Exception:
            pass
        return False
    finally:
        try:
            Path(tf_path).unlink(missing_ok=True)
        except Exception:
            pass

def push_to_origin_main():
    branch = "main"
    print(f"Pushing to origin {branch}...")
    try:
        run(["git", "push", "origin", branch])
        print("Push complete.")
    except subprocess.CalledProcessError as e:
        print("git push failed:", e, file=sys.stderr)
        sys.exit(1)

def main():
    if not in_git_repo():
        print("Error: current directory is not inside a git repository.", file=sys.stderr)
        sys.exit(1)

    print_git_status()

    stage_all()

    # Prefer staged files list; if empty, fall back to porcelain
    staged = get_staged_files()
    if not staged:
        staged = get_unstaged_or_untracked_files()

    if not staged:
        print("No changes detected after staging. Nothing to commit.")
        sys.exit(0)

    committed = commit_with_file_list(staged)
    if not committed:
        print("Commit did not complete. Aborting push.", file=sys.stderr)
        sys.exit(1)

    push_to_origin_main()

if __name__ == "__main__":
    main()