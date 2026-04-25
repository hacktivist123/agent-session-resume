#!/usr/bin/env python3
"""Validate prompt coverage for agent-session-resume trigger testing."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "tests" / "trigger-matrix.json"

REQUIRED_TRIGGER_CATEGORIES = {
    "explicit-skill",
    "implicit-resume",
    "platform-specific",
    "handoff-artifact",
    "paraphrase",
}
REQUIRED_NEGATIVE_CATEGORIES = {
    "general-coding",
    "new-build",
    "review",
    "data-work",
    "general-qa",
}
REQUIRED_PLATFORMS = {"Claude Code", "Codex", "Antigravity", "OpenCode"}


def fail(message: str) -> None:
    print(f"trigger matrix validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_matrix() -> dict[str, object]:
    if not MATRIX.exists():
        fail(f"missing matrix: {MATRIX.relative_to(ROOT)}")
    try:
        data = json.loads(MATRIX.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid matrix JSON: {exc}")
    if not isinstance(data, dict):
        fail("trigger matrix must be a JSON object")
    return data


def validate_cases(name: str, minimum: int, seen_ids: set[str]) -> set[str]:
    data = load_matrix()
    cases = data.get(name)
    if not isinstance(cases, list) or len(cases) < minimum:
        fail(f"{name} must contain at least {minimum} cases")

    categories: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            fail(f"{name}[{index}] must be an object")

        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            fail(f"{name}[{index}] missing non-empty id")
        if case_id in seen_ids:
            fail(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)

        prompt = case.get("prompt")
        if not isinstance(prompt, str) or len(prompt.split()) < 5:
            fail(f"{case_id}: prompt must contain at least 5 words")

        category = case.get("category")
        if not isinstance(category, str) or not category.strip():
            fail(f"{case_id}: missing category")
        categories.add(category)

        rationale = case.get("rationale")
        if not isinstance(rationale, str) or len(rationale.split()) < 4:
            fail(f"{case_id}: rationale must explain the expected behavior")

    return categories


def main() -> None:
    data = load_matrix()
    if data.get("version") != 1:
        fail("trigger matrix version must be 1")

    seen_ids: set[str] = set()
    trigger_categories = validate_cases("should_trigger", 8, seen_ids)
    negative_categories = validate_cases("should_not_trigger", 5, seen_ids)

    missing_trigger_categories = REQUIRED_TRIGGER_CATEGORIES - trigger_categories
    if missing_trigger_categories:
        fail(f"missing trigger categories: {', '.join(sorted(missing_trigger_categories))}")

    missing_negative_categories = REQUIRED_NEGATIVE_CATEGORIES - negative_categories
    if missing_negative_categories:
        fail(f"missing negative categories: {', '.join(sorted(missing_negative_categories))}")

    trigger_text = " ".join(
        case["prompt"]
        for case in data["should_trigger"]
        if isinstance(case, dict) and isinstance(case.get("prompt"), str)
    )
    missing_platforms = {
        platform for platform in REQUIRED_PLATFORMS if platform not in trigger_text
    }
    if missing_platforms:
        fail(f"missing platform trigger coverage: {', '.join(sorted(missing_platforms))}")

    print(
        f"validated {len(data['should_trigger'])} trigger and "
        f"{len(data['should_not_trigger'])} non-trigger prompts"
    )


if __name__ == "__main__":
    main()
