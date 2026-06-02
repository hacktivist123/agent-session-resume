#!/usr/bin/env python3
"""Validate a compact agent handoff file."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = (
    "Goal",
    "Completed",
    "In Progress",
    "Not Done",
    "Files Changed",
    "Commands Run",
    "Verification",
    "Exact Stopping Point",
    "Next Action",
)

SECRET_PATTERNS = (
    re.compile(r"\b[A-Za-z0-9_]*API[_-]?KEY[A-Za-z0-9_]*\s*[:=]\s*[^<\s][^\s]+", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_]*TOKEN[A-Za-z0-9_]*\s*[:=]\s*[^<\s][^\s]+", re.IGNORECASE),
    re.compile(r"\bPASSWORD\s*[:=]\s*[^<\s][^\s]+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)


def fail(path: Path, message: str) -> None:
    print(f"{path}: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        fail(path, "empty handoff")

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.MULTILINE):
            fail(path, f"missing heading: ## {heading}")

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            fail(path, "contains an unredacted secret-looking value")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: validate-handoff.py path/to/handoff.md [...]", file=sys.stderr)
        raise SystemExit(2)
    for value in sys.argv[1:]:
        validate(Path(value))
    print(f"validated {len(sys.argv) - 1} handoff file(s)")


if __name__ == "__main__":
    main()
