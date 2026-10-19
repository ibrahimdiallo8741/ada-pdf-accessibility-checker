#!/usr/bin/env python3
"""Syncs .mmd diagram source files into docs/diagrams/README.md between marker tags.

Ensures .mmd files remain the single source of truth without manual copy-pasting.

Usage:
    python3 scripts/sync_diagrams.py
"""

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
DIAGRAMS_DIR = REPO_ROOT / "docs" / "diagrams"
README_PATH = DIAGRAMS_DIR / "README.md"


def sync_diagrams():
    if not README_PATH.exists():
        print(f"Error: {README_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    content = README_PATH.read_text(encoding="utf-8")
    synced_count = 0

    for mmd_file in sorted(DIAGRAMS_DIR.glob("*.mmd")):
        stem = mmd_file.stem
        code = mmd_file.read_text(encoding="utf-8").strip()

        pattern = re.compile(
            rf"<!-- BEGIN:{re.escape(stem)} -->[\s\S]*?<!-- END:{re.escape(stem)} -->"
        )
        replacement = f"<!-- BEGIN:{stem} -->\n```mermaid\n{code}\n```\n<!-- END:{stem} -->"

        if pattern.search(content):
            content = pattern.sub(replacement, content)
            synced_count += 1
            print(f"  [SYNCED] {mmd_file.name} -> {README_PATH.name}")
        else:
            print(f"  [SKIPPED] No <!-- BEGIN:{stem} --> marker found in {README_PATH.name}")

    README_PATH.write_text(content, encoding="utf-8")
    print(f"\nSuccessfully synchronized {synced_count} diagram(s) into {README_PATH.relative_to(REPO_ROOT)}.")


if __name__ == "__main__":
    print("Synchronizing Mermaid diagrams...")
    sync_diagrams()
