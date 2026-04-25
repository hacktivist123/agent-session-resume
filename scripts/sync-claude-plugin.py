#!/usr/bin/env python3
"""Refresh the optional Claude plugin skill from the canonical skill package."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "agent-session-resume"
TARGET = ROOT / "plugins" / "agent-session-resume" / "skills" / "agent-session-resume"


def main() -> None:
    if not SOURCE.is_dir():
        raise SystemExit(f"missing canonical skill directory: {SOURCE.relative_to(ROOT)}")

    if TARGET.exists():
        shutil.rmtree(TARGET)

    shutil.copytree(SOURCE, TARGET)
    print(f"synced {TARGET.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
