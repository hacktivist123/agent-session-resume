#!/usr/bin/env python3
"""List likely agent-session transcripts without dumping transcript bodies."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows


def first_codex_cwd(path: Path) -> str:
    for row in read_jsonl(path):
        if row.get("type") == "session_meta":
            payload = row.get("payload") or {}
            return str(payload.get("cwd") or "")
    return ""


def first_claude_cwd(path: Path) -> str:
    for row in read_jsonl(path):
        cwd = row.get("cwd")
        if row.get("type") == "user" and cwd:
            return str(cwd)
    return ""


def first_claude_title(path: Path) -> str:
    seen: set[str] = set()
    for row in read_jsonl(path):
        if row.get("type") != "ai-title":
            continue
        title = str(row.get("aiTitle") or "")
        if title and title not in seen:
            return title
        seen.add(title)
    return ""


def score_candidate(cwd: str, title: str, target_cwd: str, topic: str) -> tuple[int, list[str]]:
    score = 0
    signals: list[str] = []
    if target_cwd and cwd == target_cwd:
        score += 100
        signals.append("exact-cwd")
    elif target_cwd and (cwd.startswith(target_cwd + os.sep) or target_cwd.startswith(cwd + os.sep)):
        score += 60
        signals.append("parent-child-cwd")
    if topic and topic.lower() in title.lower():
        score += 30
        signals.append("title-match")
    return score, signals


def find_codex_transcript(codex_home: Path, session_id: str) -> Path | None:
    for directory in (codex_home / "sessions", codex_home / "archived_sessions"):
        if not directory.exists():
            continue
        matches = sorted(directory.rglob(f"*{session_id}*.jsonl"))
        if matches:
            return matches[-1]
    return None


def codex_candidates(codex_home: Path, target_cwd: str, topic: str, limit: int) -> list[dict[str, Any]]:
    index = codex_home / "session_index.jsonl"
    candidates: list[dict[str, Any]] = []
    rows = read_jsonl(index) if index.exists() else []
    for row in rows:
        session_id = str(row.get("id") or "")
        title = str(row.get("thread_name") or "")
        if topic and topic.lower() not in title.lower():
            continue
        path = find_codex_transcript(codex_home, session_id) if session_id else None
        cwd = first_codex_cwd(path) if path else ""
        score, signals = score_candidate(cwd, title, target_cwd, topic)
        candidates.append(
            {
                "platform": "codex",
                "id": session_id,
                "title": title,
                "updated_at": row.get("updated_at") or "",
                "cwd": cwd,
                "path": str(path) if path else "",
                "score": score,
                "signals": signals,
            }
        )
    candidates.sort(key=lambda item: (item["score"], item.get("updated_at", ""), item.get("path", "")), reverse=True)
    return candidates[:limit]


def encode_claude_project_path(cwd: str) -> str:
    return cwd.replace("/", "-")


def claude_candidates(claude_home: Path, target_cwd: str, topic: str, limit: int) -> list[dict[str, Any]]:
    projects = claude_home / "projects"
    project_dirs: list[Path] = []
    if target_cwd:
        derived = projects / encode_claude_project_path(target_cwd)
        if derived.exists():
            project_dirs.append(derived)
    if not project_dirs and projects.exists():
        project_dirs = sorted(projects.iterdir())

    candidates: list[dict[str, Any]] = []
    for project_dir in project_dirs:
        for path in sorted(project_dir.glob("*.jsonl")):
            title = first_claude_title(path)
            if topic and topic.lower() not in title.lower():
                continue
            cwd = first_claude_cwd(path)
            score, signals = score_candidate(cwd, title, target_cwd, topic)
            candidates.append(
                {
                    "platform": "claude-code",
                    "id": path.stem,
                    "title": title,
                    "updated_at": str(path.stat().st_mtime_ns),
                    "cwd": cwd,
                    "path": str(path),
                    "score": score,
                    "signals": signals,
                }
            )
    candidates.sort(key=lambda item: (item["score"], item.get("updated_at", ""), item.get("path", "")), reverse=True)
    return candidates[:limit]


def print_tsv(candidates: list[dict[str, Any]]) -> None:
    print("score\tplatform\tupdated_at\tcwd\ttitle\tpath")
    for candidate in candidates:
        print(
            "\t".join(
                [
                    str(candidate["score"]),
                    candidate["platform"],
                    str(candidate["updated_at"]),
                    candidate["cwd"],
                    candidate["title"],
                    candidate["path"],
                ]
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["codex", "claude-code"], required=True)
    parser.add_argument("--cwd", default=os.getcwd(), help="Workspace path to match; defaults to the current directory.")
    parser.add_argument("--topic", default="", help="Optional title/topic filter.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--format", choices=["json", "tsv"], default="json")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--claude-home", default=str(Path.home() / ".claude"))
    args = parser.parse_args()

    if args.platform == "codex":
        candidates = codex_candidates(Path(args.codex_home), args.cwd, args.topic, args.limit)
    else:
        candidates = claude_candidates(Path(args.claude_home), args.cwd, args.topic, args.limit)

    if args.format == "tsv":
        print_tsv(candidates)
    else:
        print(json.dumps(candidates, indent=2))


if __name__ == "__main__":
    main()
