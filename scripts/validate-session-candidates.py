#!/usr/bin/env python3
"""Validate the session candidates helper, including time-window and cwd filters."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-session-resume" / "scripts" / "session-candidates.py"

NOW = datetime.now(timezone.utc)
RECENT = (NOW - timedelta(days=1)).isoformat()
OLD = (NOW - timedelta(days=30)).isoformat()
OLD_EPOCH = (NOW - timedelta(days=30)).timestamp()

ISO_UTC_SECONDS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
ALLOWED_SOURCES = {"index", "mtime"}


def fail(message: str) -> None:
    print(f"session candidates validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_candidates(*args: str) -> list[dict]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def codex_session(session_id: str, cwd: str) -> list[dict]:
    return [
        {"type": "session_meta", "payload": {"id": session_id, "cwd": cwd, "timestamp": RECENT, "originator": "codex"}},
        {"type": "event_msg", "timestamp": RECENT, "payload": {"type": "user_message", "message": f"work in {cwd}"}},
    ]


def build_codex_home(home: Path, repo_cwd: str, other_cwd: str) -> None:
    write_jsonl(
        home / "session_index.jsonl",
        [
            {"id": "recent-repo", "thread_name": "checkout retry fix", "updated_at": RECENT},
            {"id": "old-repo", "thread_name": "stale repo thread", "updated_at": OLD},
            {"id": "recent-other", "thread_name": "other repo work", "updated_at": RECENT},
        ],
    )
    write_jsonl(home / "sessions" / "rollout-recent-repo.jsonl", codex_session("recent-repo", repo_cwd))
    write_jsonl(home / "sessions" / "rollout-old-repo.jsonl", codex_session("old-repo", repo_cwd))
    write_jsonl(home / "sessions" / "rollout-recent-other.jsonl", codex_session("recent-other", other_cwd))
    # Unindexed transcripts (e.g. Codex Desktop sub-threads) live only on disk,
    # under dated sessions/YYYY/MM/DD directories, and never get index entries.
    dated = home / "sessions" / "2026" / "06" / "09"
    write_jsonl(dated / "rollout-sub-recent.jsonl", codex_session("sub-recent", repo_cwd))
    write_jsonl(dated / "rollout-sub-old.jsonl", codex_session("sub-old", repo_cwd))
    os.utime(dated / "rollout-sub-old.jsonl", (OLD_EPOCH, OLD_EPOCH))


def check_normalized(candidates: list[dict], label: str) -> None:
    for candidate in candidates:
        updated_at = str(candidate.get("updated_at") or "")
        if not ISO_UTC_SECONDS_RE.fullmatch(updated_at):
            fail(f"{label}: updated_at must be ISO-8601 UTC seconds (e.g. 2026-06-10T00:15:30Z), got {updated_at!r}")
        if candidate.get("source") not in ALLOWED_SOURCES:
            fail(f"{label}: source must be one of {sorted(ALLOWED_SOURCES)}, got {candidate.get('source')!r}")


def claude_session(cwd: str, title: str) -> list[dict]:
    return [
        {"type": "ai-title", "aiTitle": title, "timestamp": RECENT},
        {"type": "user", "cwd": cwd, "timestamp": RECENT, "message": {"role": "user", "content": f"work in {cwd}"}},
    ]


def build_claude_home(home: Path, repo_cwd: str, other_cwd: str) -> None:
    repo_dir = home / "projects" / repo_cwd.replace("/", "-")
    other_dir = home / "projects" / other_cwd.replace("/", "-")
    write_jsonl(repo_dir / "recent-repo.jsonl", claude_session(repo_cwd, "checkout retry fix"))
    write_jsonl(other_dir / "recent-other.jsonl", claude_session(other_cwd, "other repo work"))
    write_jsonl(other_dir / "old-other.jsonl", claude_session(other_cwd, "stale other thread"))
    old_epoch = (NOW - timedelta(days=30)).timestamp()
    os.utime(other_dir / "old-other.jsonl", (old_epoch, old_epoch))


def ids(candidates: list[dict]) -> set[str]:
    return {candidate["id"] for candidate in candidates}


def validate_codex(tmp: Path) -> None:
    home = tmp / "codex-home"
    repo_cwd = str(tmp / "work" / "repo")
    other_cwd = str(tmp / "elsewhere" / "proj")
    build_codex_home(home, repo_cwd, other_cwd)
    base = ("--platform", "codex", "--codex-home", str(home))

    unfiltered = run_candidates(*base)
    if ids(unfiltered) != {"recent-repo", "old-repo", "recent-other", "rollout-sub-recent", "rollout-sub-old"}:
        fail("codex: unfiltered run should list indexed sessions plus unindexed mtime-fallback sessions")
    check_normalized(unfiltered, "codex")
    sources = {candidate["id"]: candidate.get("source") for candidate in unfiltered}
    for indexed_id in ("recent-repo", "old-repo", "recent-other"):
        if sources[indexed_id] != "index":
            fail(f"codex: indexed session {indexed_id} should carry source=index")
    for fallback_id in ("rollout-sub-recent", "rollout-sub-old"):
        if sources[fallback_id] != "mtime":
            fail(f"codex: unindexed session {fallback_id} should carry source=mtime")

    if ids(run_candidates(*base, "--since", "7d")) != {"recent-repo", "recent-other", "rollout-sub-recent"}:
        fail("codex: --since 7d should drop the 30-day-old sessions but keep the unindexed recent one")

    until = (NOW - timedelta(days=7)).date().isoformat()
    if ids(run_candidates(*base, "--until", until)) != {"old-repo", "rollout-sub-old"}:
        fail("codex: --until should keep only sessions before the cutoff, including unindexed ones")

    since_iso = (NOW - timedelta(days=7)).date().isoformat()
    if ids(run_candidates(*base, "--since", since_iso)) != {"recent-repo", "recent-other", "rollout-sub-recent"}:
        fail("codex: ISO --since should drop the 30-day-old sessions")

    if ids(run_candidates(*base, "--cwd", repo_cwd)) != {"recent-repo", "old-repo", "rollout-sub-recent", "rollout-sub-old"}:
        fail("codex: --cwd should keep only matching-workspace sessions (fallback cwd comes from the first-line peek)")

    child = str(Path(repo_cwd) / "packages" / "api")
    if ids(run_candidates(*base, "--cwd", child)) != {"recent-repo", "old-repo", "rollout-sub-recent", "rollout-sub-old"}:
        fail("codex: --cwd should match parent/child workspaces")

    if ids(run_candidates(*base, "--since", "7d", "--cwd", repo_cwd)) != {"recent-repo", "rollout-sub-recent"}:
        fail("codex: combined --since and --cwd should intersect")

    if ids(run_candidates(*base, "--topic", "checkout")) != {"recent-repo"}:
        fail("codex: --topic should match indexed titles only (untitled fallback rows cannot match)")


def validate_claude(tmp: Path) -> None:
    home = tmp / "claude-home"
    repo_cwd = str(tmp / "work" / "repo")
    other_cwd = str(tmp / "work" / "other")
    build_claude_home(home, repo_cwd, other_cwd)
    base = ("--platform", "claude-code", "--claude-home", str(home))

    unfiltered = run_candidates(*base)
    if ids(unfiltered) != {"recent-repo", "recent-other", "old-other"}:
        fail("claude: unfiltered run should list all sessions")
    check_normalized(unfiltered, "claude")
    if any(candidate.get("source") != "mtime" for candidate in unfiltered):
        fail("claude: updated_at is mtime-derived, so every row should carry source=mtime")

    if ids(run_candidates(*base, "--since", "7d")) != {"recent-repo", "recent-other"}:
        fail("claude: --since 7d should drop the 30-day-old session")

    if ids(run_candidates(*base, "--cwd", repo_cwd)) != {"recent-repo"}:
        fail("claude: --cwd should keep only matching-workspace sessions")

    parent = str(tmp / "work")
    if ids(run_candidates(*base, "--cwd", parent)) != {"recent-repo", "recent-other", "old-other"}:
        fail("claude: --cwd parent path should match child workspaces")

    if ids(run_candidates(*base, "--cwd", parent, "--until", "7d")) != {"old-other"}:
        fail("claude: combined --cwd and --until should intersect")


def validate_bad_value() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--platform", "codex", "--since", "lastweek"],
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        fail("invalid --since value should exit non-zero")
    if "invalid --since/--until value" not in result.stderr:
        fail("invalid --since value should explain the accepted formats")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="asr-candidates-") as tmp:
        validate_codex(Path(tmp))
        validate_claude(Path(tmp))
    validate_bad_value()
    print("validated session candidate filters")


if __name__ == "__main__":
    main()
