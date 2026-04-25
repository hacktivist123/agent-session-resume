#!/usr/bin/env python3
"""Validate agent-session-resume fixture scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
MANIFEST = FIXTURES / "manifest.json"
SUPPORTED_PLATFORMS = {"claude-code", "codex", "antigravity", "opencode"}
REQUIRED_EXPECTED_SECTIONS = (
    "Brief context summary",
    "Task status breakdown",
    "Clear next action",
)
REQUIRED_STATUSES = ("DONE", "PARTIALLY DONE", "NOT DONE")


def fail(message: str) -> None:
    print(f"fixture validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_manifest() -> dict:
    if not MANIFEST.exists():
        fail(f"missing manifest: {MANIFEST.relative_to(ROOT)}")
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid manifest JSON: {exc}")


def read_fixture(path: Path) -> str:
    if not path.exists():
        fail(f"missing file: {path.relative_to(ROOT)}")
    if not path.is_file():
        fail(f"not a file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        fail(f"empty file: {path.relative_to(ROOT)}")
    return text


def validate_scenario(scenario: dict, seen_ids: set[str]) -> str:
    scenario_id = scenario.get("id")
    if not isinstance(scenario_id, str) or not scenario_id:
        fail("scenario missing non-empty id")
    if scenario_id in seen_ids:
        fail(f"duplicate scenario id: {scenario_id}")
    seen_ids.add(scenario_id)

    platform = scenario.get("platform")
    if platform not in SUPPORTED_PLATFORMS:
        fail(f"{scenario_id}: unsupported platform {platform!r}")

    source_files = scenario.get("source_files")
    if not isinstance(source_files, list) or not source_files:
        fail(f"{scenario_id}: source_files must be a non-empty list")
    for source_file in source_files:
        if not isinstance(source_file, str) or not source_file:
            fail(f"{scenario_id}: invalid source file entry")
        read_fixture(FIXTURES / source_file)

    expected_path_value = scenario.get("expected")
    if not isinstance(expected_path_value, str) or not expected_path_value:
        fail(f"{scenario_id}: missing expected path")
    expected_text = read_fixture(FIXTURES / expected_path_value)

    for section in REQUIRED_EXPECTED_SECTIONS:
        if section not in expected_text:
            fail(f"{scenario_id}: expected output missing section {section!r}")

    task_statuses = scenario.get("task_statuses")
    if not isinstance(task_statuses, dict):
        fail(f"{scenario_id}: missing task_statuses object")
    for status in REQUIRED_STATUSES:
        tasks = task_statuses.get(status)
        if not isinstance(tasks, list):
            fail(f"{scenario_id}: task_statuses.{status} must be a list")
        for task in tasks:
            if not isinstance(task, str) or not task.strip():
                fail(f"{scenario_id}: task_statuses.{status} contains invalid task")
            if task not in expected_text:
                fail(f"{scenario_id}: task {task!r} missing from expected output")

    return platform


def main() -> None:
    manifest = load_manifest()
    scenarios = manifest.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        fail("manifest.scenarios must be a non-empty list")

    seen_ids: set[str] = set()
    covered_platforms: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            fail("every scenario must be an object")
        covered_platforms.add(validate_scenario(scenario, seen_ids))

    missing = SUPPORTED_PLATFORMS - covered_platforms
    if missing:
        fail(f"missing platform coverage: {', '.join(sorted(missing))}")

    print(f"validated {len(scenarios)} fixture scenarios")


if __name__ == "__main__":
    main()
