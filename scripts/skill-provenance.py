#!/usr/bin/env python3
"""Compare repo, Codex, and Claude installed skill artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_SKILL = "agent-session-resume"


def file_stats(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {
            "path": str(path),
            "exists": False,
            "bytes": 0,
            "lines": 0,
            "sha256": "",
        }
    data = path.read_bytes()
    return {
        "path": str(path),
        "exists": True,
        "bytes": len(data),
        "lines": len(data.decode("utf-8", errors="replace").splitlines()),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def annotate_status(records: dict[str, dict[str, Any]]) -> None:
    repo_hash = records.get("repo", {}).get("sha256") or ""
    for name, record in records.items():
        if not record.get("exists"):
            record["status"] = "missing"
        elif name == "repo":
            record["status"] = "reference"
        elif repo_hash and record.get("sha256") == repo_hash:
            record["status"] = "matches-repo"
        elif repo_hash:
            record["status"] = "differs-from-repo"
        else:
            record["status"] = "unknown"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    codex_home = Path(args.codex_home).expanduser()
    claude_home = Path(args.claude_home).expanduser()
    skill = args.skill

    records = {
        "repo": file_stats(repo_root / "skills" / skill / "SKILL.md"),
        "codex": file_stats(codex_home / "skills" / skill / "SKILL.md"),
        "claude": file_stats(claude_home / "skills" / skill / "SKILL.md"),
    }
    annotate_status(records)

    plugin_manifest = read_json(repo_root / ".claude-plugin" / "plugin.json")
    openai_yaml = repo_root / "skills" / skill / "agents" / "openai.yaml"

    return {
        "skill": skill,
        "repo_root": str(repo_root),
        "version": plugin_manifest.get("version") or "",
        "repository": plugin_manifest.get("repository") or "",
        "openai_yaml": file_stats(openai_yaml),
        "artifacts": records,
        "reload_note": "If installed artifacts differ from the repo, restart or reload the receiving agent before assuming the update is active.",
    }


def print_text(report: dict[str, Any]) -> None:
    print("# Skill Provenance")
    print(f"- Skill: {report['skill']}")
    print(f"- Repo root: {report['repo_root']}")
    print(f"- Version: {report['version'] or 'unknown'}")
    print(f"- Repository: {report['repository'] or 'unknown'}")
    print("")
    print("| Surface | Status | Lines | Bytes | SHA-256 | Path |")
    print("| --- | --- | ---: | ---: | --- | --- |")
    for surface in ("repo", "codex", "claude"):
        record = report["artifacts"][surface]
        digest = record["sha256"][:12] if record["sha256"] else ""
        print(
            f"| {surface} | {record['status']} | {record['lines']} | {record['bytes']} | "
            f"{digest or 'unknown'} | {record['path']} |"
        )
    print("")
    print(report["reload_note"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", default=DEFAULT_SKILL)
    parser.add_argument("--repo-root", default=os.getcwd())
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--claude-home", default=str(Path.home() / ".claude"))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
