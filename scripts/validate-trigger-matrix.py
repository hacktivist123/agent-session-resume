#!/usr/bin/env python3
"""Validate prompt coverage for agent-session-resume trigger testing."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "tests" / "trigger-matrix.json"
SKILL_MD = ROOT / "skills" / "agent-session-resume" / "SKILL.md"

REQUIRED_TRIGGER_CATEGORIES = {
    "explicit-skill",
    "implicit-resume",
    "platform-specific",
    "handoff-artifact",
    "paraphrase",
    "locate",
    "audit",
    "cross-platform",
}

# Verb stems the SKILL.md description must keep so locate/audit/review asks
# still trigger ("locat" covers locating/locate, and so on).
REQUIRED_DESCRIPTION_VERBS = {
    "locat": "locating",
    "audit": "auditing",
    "review": "reviewing",
}
REQUIRED_NEGATIVE_CATEGORIES = {
    "general-coding",
    "new-build",
    "review",
    "data-work",
    "general-qa",
}
REQUIRED_PLATFORMS = {"Claude Code", "Codex", "Cursor", "Antigravity", "OpenCode"}


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


def validate_skill_description() -> None:
    if not SKILL_MD.exists():
        fail(f"missing skill file: {SKILL_MD.relative_to(ROOT)}")
    text = SKILL_MD.read_text(encoding="utf-8")
    match = re.search(r"^description:\s*(\S.*)$", text, flags=re.MULTILINE)
    if not match:
        fail("SKILL.md frontmatter must define a description")
    description = match.group(1).strip().lower()

    missing_verbs = sorted(
        label for stem, label in REQUIRED_DESCRIPTION_VERBS.items() if stem not in description
    )
    if missing_verbs:
        fail(f"SKILL.md description must keep trigger verbs: {', '.join(missing_verbs)}")

    has_cross_platform_clause = "across" in description and (
        "platforms" in description or ("claude" in description and "codex" in description)
    )
    if not has_cross_platform_clause:
        fail("SKILL.md description must keep a cross-platform clause (e.g. across several platforms)")


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

    validate_skill_description()

    print(
        f"validated {len(data['should_trigger'])} trigger and "
        f"{len(data['should_not_trigger'])} non-trigger prompts "
        "plus SKILL.md description coverage"
    )


if __name__ == "__main__":
    main()
