#!/usr/bin/env python3
"""Validate the installable agent-session-resume skill package."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "agent-session-resume"
SKILL_MD = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
REFERENCES = SKILL_DIR / "references"
REQUIRED_REFERENCES = {
    "claude-code.md": "Claude Code",
    "codex.md": "Codex",
    "antigravity.md": "Antigravity",
    "opencode.md": "OpenCode",
}


def fail(message: str) -> None:
    print(f"skill package validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_required(path: Path) -> str:
    if not path.exists():
        fail(f"missing file: {path.relative_to(ROOT)}")
    if not path.is_file():
        fail(f"not a file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        fail(f"empty file: {path.relative_to(ROOT)}")
    return text


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        fail("SKILL.md missing opening YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        fail("SKILL.md missing closing YAML frontmatter")

    fields: dict[str, str] = {}
    for line in parts[1].splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not match:
            fail(f"unsupported frontmatter line: {line}")
        key, value = match.groups()
        fields[key] = value.strip().strip('"')
    return fields


def validate_skill_md() -> None:
    text = read_required(SKILL_MD)
    fields = parse_frontmatter(text)
    if fields.get("name") != "agent-session-resume":
        fail("SKILL.md frontmatter name must be agent-session-resume")

    description = fields.get("description", "")
    if not description.startswith("Use when "):
        fail("SKILL.md description must start with 'Use when '")
    if len(description) > 500:
        fail("SKILL.md description should stay under 500 characters")

    for section in ("## Core Workflow", "## Platform References", "## Required Response Shape", "## Guardrails"):
        if section not in text:
            fail(f"SKILL.md missing section: {section}")


def validate_references() -> None:
    if not REFERENCES.is_dir():
        fail(f"missing directory: {REFERENCES.relative_to(ROOT)}")

    for filename, platform_name in REQUIRED_REFERENCES.items():
        text = read_required(REFERENCES / filename)
        if platform_name not in text:
            fail(f"{filename} should mention {platform_name}")

    skill_text = read_required(SKILL_MD)
    for filename in REQUIRED_REFERENCES:
        if f"references/{filename}" not in skill_text:
            fail(f"SKILL.md does not link {filename}")


def validate_openai_yaml() -> None:
    text = read_required(OPENAI_YAML)
    required_snippets = (
        'display_name: "Agent Session Resume"',
        'short_description: "Resume prior AI coding sessions"',
        "Use $agent-session-resume",
    )
    for snippet in required_snippets:
        if snippet not in text:
            fail(f"agents/openai.yaml missing {snippet!r}")


def main() -> None:
    if not SKILL_DIR.is_dir():
        fail(f"missing directory: {SKILL_DIR.relative_to(ROOT)}")

    validate_skill_md()
    validate_references()
    validate_openai_yaml()

    print("validated agent-session-resume skill package")


if __name__ == "__main__":
    main()
