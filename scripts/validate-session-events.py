#!/usr/bin/env python3
"""Validate the session event projection helper against fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "session-events.py"
CODEX_FIXTURE = ROOT / "tests" / "fixtures" / "codex-noisy-jsonl" / "transcript.jsonl"
CLAUDE_FIXTURE = ROOT / "tests" / "fixtures" / "claude-noisy-jsonl" / "transcript.jsonl"


def fail(message: str) -> None:
    print(f"session event validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_projection(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def validate_text_projection() -> None:
    output = run_projection(str(CODEX_FIXTURE), str(CLAUDE_FIXTURE), "--limit", "20")
    required = (
        "platform=codex",
        "platform=claude-code",
        "user_message",
        "agent_message",
        "tool_use",
        "tool_result",
        ":L",
    )
    for snippet in required:
        if snippet not in output:
            fail(f"text projection missing {snippet!r}")

    forbidden = ("base_instructions", "signature", "thinking")
    for snippet in forbidden:
        if snippet in output:
            fail(f"text projection leaked opaque payload {snippet!r}")


def validate_json_projection() -> None:
    output = run_projection(str(CODEX_FIXTURE), str(CLAUDE_FIXTURE), "--format", "json")
    data = json.loads(output)
    if len(data) != 2:
        fail("expected two projected files")
    platforms = {item.get("platform") for item in data}
    if platforms != {"codex", "claude-code"}:
        fail(f"unexpected platforms: {platforms}")
    for item in data:
        metrics = item.get("metrics") or {}
        if metrics.get("raw_bytes", 0) <= 0:
            fail("missing raw byte metric")
        if metrics.get("projected_events", 0) <= 0:
            fail("missing projected event metric")
        if metrics.get("projected_chars", 0) >= metrics.get("raw_bytes", 0):
            fail("projection should be smaller than raw fixture bytes")
        events = item.get("events") or []
        if not all("ref" in event and ":L" in event["ref"] for event in events):
            fail("every event should include a line reference")


def main() -> None:
    validate_text_projection()
    validate_json_projection()
    print("validated session event projection")


if __name__ == "__main__":
    main()
