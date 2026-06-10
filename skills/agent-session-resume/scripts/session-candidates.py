#!/usr/bin/env python3
"""List likely agent-session transcripts without dumping transcript bodies.

Supports time-window filters (`--since`, `--until`, ISO dates or relative
values such as `7d`) and a `--cwd` filter that keeps only sessions whose
workspace matches the given path exactly or as a parent/child directory.

Every row's `updated_at` is normalized to ISO-8601 UTC with seconds precision
(e.g. 2026-06-10T00:15:30Z) on both platforms, and carries a `source` marker:
`index` (platform session index) or `mtime` (transcript file mtime). For codex,
an mtime fallback sweep surfaces in-window transcripts the session index never
recorded (e.g. Codex Desktop sub-threads).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


RELATIVE_RE = re.compile(r"^(?P<value>\d+)(?P<unit>[smhdw])$")
RELATIVE_UNITS = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
    "w": "weeks",
}

# Where a candidate's updated_at came from: a platform session index ("index")
# or the transcript file's mtime ("mtime").
SOURCE_INDEX = "index"
SOURCE_MTIME = "mtime"

# Cap for the optional first-line cwd peek on unindexed codex transcripts, so
# the mtime fallback never reads more than this many bytes per file.
MAX_CWD_PEEK_BYTES = 65536


def parse_when(raw: str) -> float:
    """Parse an ISO date/datetime or a relative window like 7d into epoch seconds."""
    value = raw.strip()
    match = RELATIVE_RE.match(value)
    if match:
        delta = timedelta(**{RELATIVE_UNITS[match.group("unit")]: int(match.group("value"))})
        return (datetime.now(timezone.utc) - delta).timestamp()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SystemExit(f"invalid --since/--until value: {raw!r} (use ISO date/datetime or relative like 7d, 12h)")
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.timestamp()


def parse_iso_epoch(raw: str) -> float | None:
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed.timestamp()


def iso_utc(epoch: float) -> str:
    """Render an epoch as ISO-8601 UTC with seconds precision (the one updated_at format both platforms emit)."""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_updated_at(raw: str, path: Path | None) -> str:
    """Normalize index timestamps (fractional ISO, plain ISO, or epoch nanoseconds) to iso_utc; fall back to file mtime."""
    value = str(raw or "").strip()
    if value.isdigit():
        return iso_utc(int(value) / 1_000_000_000)
    if value:
        epoch = parse_iso_epoch(value)
        if epoch is not None:
            return iso_utc(epoch)
    if path is not None:
        try:
            return iso_utc(path.stat().st_mtime)
        except OSError:
            return ""
    return ""


def candidate_epoch(candidate: dict[str, Any]) -> float | None:
    updated_at = str(candidate.get("updated_at") or "")
    if updated_at.isdigit():
        return int(updated_at) / 1_000_000_000
    epoch = parse_iso_epoch(updated_at) if updated_at else None
    if epoch is not None:
        return epoch
    path = candidate.get("path") or ""
    if path:
        try:
            return Path(path).stat().st_mtime
        except OSError:
            return None
    return None


def cwd_related(candidate_cwd: str, filter_cwd: str) -> bool:
    if not candidate_cwd:
        return False
    candidate_norm = os.path.normpath(candidate_cwd)
    filter_norm = os.path.normpath(filter_cwd)
    return (
        candidate_norm == filter_norm
        or candidate_norm.startswith(filter_norm + os.sep)
        or filter_norm.startswith(candidate_norm + os.sep)
    )


def apply_filters(
    candidates: list[dict[str, Any]],
    since_epoch: float | None,
    until_epoch: float | None,
    filter_cwd: str | None,
) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for candidate in candidates:
        if filter_cwd is not None and not cwd_related(candidate.get("cwd") or "", filter_cwd):
            continue
        if since_epoch is not None or until_epoch is not None:
            epoch = candidate_epoch(candidate)
            if epoch is None:
                continue
            if since_epoch is not None and epoch < since_epoch:
                continue
            if until_epoch is not None and epoch > until_epoch:
                continue
        kept.append(candidate)
    return kept


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


def peek_codex_cwd(path: Path) -> str:
    """Read at most MAX_CWD_PEEK_BYTES of the first line to recover session_meta cwd; empty string when not cheap/parseable."""
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            line = handle.readline(MAX_CWD_PEEK_BYTES).strip()
    except OSError:
        return ""
    if not line or not line.endswith("}"):
        return ""
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        return ""
    if row.get("type") != "session_meta":
        return ""
    payload = row.get("payload") or {}
    return str(payload.get("cwd") or "")


def codex_mtime_fallback(
    codex_home: Path,
    known_paths: set[str],
    target_cwd: str,
    since_epoch: float | None,
    until_epoch: float | None,
) -> list[dict[str, Any]]:
    """Surface in-window transcripts the session index never recorded (e.g. Codex Desktop sub-threads).

    Cost is bounded: os.walk + stat per file, plus a size-capped first-line cwd
    peek for files that pass the time window.
    """
    sessions_dir = codex_home / "sessions"
    if not sessions_dir.exists():
        return []
    fallback: list[dict[str, Any]] = []
    for dirpath, _dirnames, filenames in os.walk(sessions_dir):
        for name in sorted(filenames):
            if not name.endswith(".jsonl"):
                continue
            path = Path(dirpath) / name
            if str(path) in known_paths:
                continue
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            if since_epoch is not None and mtime < since_epoch:
                continue
            if until_epoch is not None and mtime > until_epoch:
                continue
            cwd = peek_codex_cwd(path)
            score, signals = score_candidate(cwd, "", target_cwd, "")
            fallback.append(
                {
                    "platform": "codex",
                    "id": path.stem,
                    "title": "",
                    "updated_at": iso_utc(mtime),
                    "cwd": cwd,
                    "path": str(path),
                    "score": score,
                    "signals": signals,
                    "source": SOURCE_MTIME,
                }
            )
    return fallback


def codex_candidates(
    codex_home: Path,
    target_cwd: str,
    topic: str,
    since_epoch: float | None,
    until_epoch: float | None,
) -> list[dict[str, Any]]:
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
                "updated_at": normalize_updated_at(str(row.get("updated_at") or ""), path),
                "cwd": cwd,
                "path": str(path) if path else "",
                "score": score,
                "signals": signals,
                "source": SOURCE_INDEX,
            }
        )
    # The index silently omits unindexed transcripts (Codex Desktop sub-threads
    # with parent_thread_id never get index entries); sweep sessions/ by mtime so
    # those still surface. Skipped under --topic: unindexed files have no title
    # to match, so the topic filter would drop every fallback row anyway.
    if not topic:
        known_paths = {candidate["path"] for candidate in candidates if candidate["path"]}
        candidates.extend(codex_mtime_fallback(codex_home, known_paths, target_cwd, since_epoch, until_epoch))
    return candidates


def encode_claude_project_path(cwd: str) -> str:
    return cwd.replace("/", "-")


def claude_candidates(claude_home: Path, target_cwd: str, topic: str, scan_all_projects: bool) -> list[dict[str, Any]]:
    projects = claude_home / "projects"
    project_dirs: list[Path] = []
    if target_cwd and not scan_all_projects:
        derived = projects / encode_claude_project_path(target_cwd)
        if derived.exists():
            project_dirs.append(derived)
    if not project_dirs and projects.exists():
        project_dirs = sorted(projects.iterdir())

    candidates: list[dict[str, Any]] = []
    for project_dir in project_dirs:
        if not project_dir.is_dir():
            continue
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
                    "updated_at": iso_utc(path.stat().st_mtime),
                    "cwd": cwd,
                    "path": str(path),
                    "score": score,
                    "signals": signals,
                    "source": SOURCE_MTIME,
                }
            )
    return candidates


def print_tsv(candidates: list[dict[str, Any]]) -> None:
    print("score\tplatform\tupdated_at\tsource\tcwd\ttitle\tpath")
    for candidate in candidates:
        print(
            "\t".join(
                [
                    str(candidate["score"]),
                    candidate["platform"],
                    str(candidate["updated_at"]),
                    str(candidate.get("source") or ""),
                    candidate["cwd"],
                    candidate["title"],
                    candidate["path"],
                ]
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", choices=["codex", "claude-code"], required=True)
    parser.add_argument(
        "--cwd",
        default=None,
        help=(
            "Workspace path filter; keeps sessions whose cwd matches exactly or as a parent/child path "
            "and boosts ranking. When omitted, the current directory is used for ranking only."
        ),
    )
    parser.add_argument("--topic", default="", help="Optional title/topic filter.")
    parser.add_argument(
        "--since",
        default=None,
        help="Keep sessions updated at/after this ISO date/datetime or relative window (e.g. 7d, 12h).",
    )
    parser.add_argument(
        "--until",
        default=None,
        help="Keep sessions updated at/before this ISO date/datetime or relative window (e.g. 1d).",
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--format", choices=["json", "tsv"], default="json")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--claude-home", default=str(Path.home() / ".claude"))
    args = parser.parse_args()

    filter_cwd = os.path.abspath(args.cwd) if args.cwd is not None else None
    target_cwd = filter_cwd or os.getcwd()
    since_epoch = parse_when(args.since) if args.since else None
    until_epoch = parse_when(args.until) if args.until else None
    if since_epoch is not None and until_epoch is not None and since_epoch > until_epoch:
        print("session-candidates: --since is later than --until; no sessions can match", file=sys.stderr)

    if args.platform == "codex":
        candidates = codex_candidates(Path(args.codex_home), target_cwd, args.topic, since_epoch, until_epoch)
    else:
        # A --cwd filter accepts parent/child workspaces, so the single derived
        # project directory is too narrow; scan all project directories instead.
        scan_all_projects = filter_cwd is not None
        candidates = claude_candidates(Path(args.claude_home), target_cwd, args.topic, scan_all_projects)

    candidates = apply_filters(candidates, since_epoch, until_epoch, filter_cwd)
    candidates.sort(key=lambda item: (item["score"], item.get("updated_at", ""), item.get("path", "")), reverse=True)
    candidates = candidates[: args.limit]

    if args.format == "tsv":
        print_tsv(candidates)
    else:
        print(json.dumps(candidates, indent=2))


if __name__ == "__main__":
    main()
