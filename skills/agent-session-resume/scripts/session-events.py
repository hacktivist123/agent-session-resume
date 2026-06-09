#!/usr/bin/env python3
"""Project agent-session JSONL files into bounded evidence events."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_PREVIEW_CHARS = 300


@dataclass
class Event:
    file: str
    line: int
    platform: str
    timestamp: str
    kind: str
    role: str
    text: str

    @property
    def ref(self) -> str:
        return f"{self.file}:L{self.line}"


def compact(value: Any, limit: int) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "..."


def read_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield index, json.loads(stripped)
            except json.JSONDecodeError:
                yield index, {"type": "invalid-json", "raw": stripped}


def detect_platform(rows: list[tuple[int, dict[str, Any]]]) -> str:
    if any(row.get("type") == "session_meta" for _, row in rows):
        return "codex"
    if any(row.get("type") in {"ai-title", "queue-operation"} for _, row in rows):
        return "claude-code"
    if any(row.get("type") in {"user", "assistant", "system"} and "message" in row for _, row in rows):
        return "claude-code"
    return "unknown"


def project_codex(path: Path, rows: list[tuple[int, dict[str, Any]]], preview_chars: int) -> list[Event]:
    events: list[Event] = []
    for line, row in rows:
        row_type = row.get("type")
        timestamp = str(row.get("timestamp") or "")
        payload = row.get("payload") or {}

        if row_type == "session_meta":
            text = compact(
                {
                    "id": payload.get("id"),
                    "cwd": payload.get("cwd"),
                    "originator": payload.get("originator"),
                    "cli_version": payload.get("cli_version"),
                },
                preview_chars,
            )
            events.append(Event(str(path), line, "codex", timestamp, "session_meta", "metadata", text))
            continue

        if row_type not in {"event_msg", "response_item"}:
            continue

        payload_type = str(payload.get("type") or "")
        if payload_type in {"user_message", "agent_message"}:
            text = compact(payload.get("message") or payload.get("text") or "", preview_chars)
            events.append(Event(str(path), line, "codex", timestamp, payload_type, payload_type, text))
        elif payload_type == "function_call":
            name = str(payload.get("name") or "tool")
            text = compact(payload.get("arguments") or payload, preview_chars)
            events.append(Event(str(path), line, "codex", timestamp, "function_call", name, text))
        elif payload_type == "function_call_output":
            text = compact(payload.get("output") or payload, preview_chars)
            events.append(Event(str(path), line, "codex", timestamp, "function_call_output", "tool", text))
    return events


def claude_content_items(content: Any) -> Iterable[tuple[str, str, Any]]:
    if isinstance(content, str):
        yield "text", "assistant", content
        return
    if not isinstance(content, list):
        yield "text", "assistant", content
        return
    for item in content:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type") or "")
        if item_type == "text":
            yield "text", "assistant", item.get("text") or ""
        elif item_type == "tool_use":
            yield "tool_use", str(item.get("name") or "tool"), item.get("input") or {}
        elif item_type == "tool_result":
            yield "tool_result", "tool", item.get("content") or ""


def project_claude(path: Path, rows: list[tuple[int, dict[str, Any]]], preview_chars: int) -> list[Event]:
    events: list[Event] = []
    seen_titles: set[str] = set()
    for line, row in rows:
        row_type = str(row.get("type") or "")
        timestamp = str(row.get("timestamp") or "")

        if row_type == "ai-title":
            title = str(row.get("aiTitle") or "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                events.append(Event(str(path), line, "claude-code", timestamp, "ai-title", "metadata", compact(title, preview_chars)))
            continue

        if row_type == "tool_result":
            text = compact({"command": row.get("command"), "output": row.get("output")}, preview_chars)
            events.append(Event(str(path), line, "claude-code", timestamp, "tool_result", "tool", text))
            continue

        if row_type not in {"user", "assistant", "system"}:
            continue

        message = row.get("message") or {}
        if isinstance(message, dict):
            role = str(message.get("role") or row_type)
            content = message.get("content")
        else:
            role = row_type
            content = message

        for kind, item_role, text_value in claude_content_items(content):
            event_role = role if kind == "text" else item_role
            text = compact(text_value, preview_chars)
            if text:
                events.append(Event(str(path), line, "claude-code", timestamp, kind, event_role, text))
    return events


def project_file(path: Path, preview_chars: int) -> tuple[str, list[Event], dict[str, int]]:
    rows = list(read_jsonl(path))
    platform = detect_platform(rows)
    if platform == "codex":
        events = project_codex(path, rows, preview_chars)
    elif platform == "claude-code":
        events = project_claude(path, rows, preview_chars)
    else:
        events = []
    projected_chars = sum(len(event.text) for event in events)
    metrics = {
        "raw_bytes": path.stat().st_size,
        "raw_lines": sum(1 for _ in path.open(encoding="utf-8")),
        "projected_events": len(events),
        "projected_chars": projected_chars,
    }
    return platform, events, metrics


def print_text(path: Path, platform: str, events: list[Event], metrics: dict[str, int]) -> None:
    print(f"## {path}")
    print(
        "metrics "
        f"platform={platform} raw_bytes={metrics['raw_bytes']} raw_lines={metrics['raw_lines']} "
        f"projected_events={metrics['projected_events']} projected_chars={metrics['projected_chars']}"
    )
    for event in events:
        stamp = f"{event.timestamp} " if event.timestamp else ""
        print(f"{event.ref}\t{stamp}{event.platform}/{event.kind}/{event.role}\t{event.text}")


def print_tsv(path: Path, platform: str, events: list[Event], metrics: dict[str, int]) -> None:
    print("file\tline\tplatform\ttimestamp\tkind\trole\ttext")
    for event in events:
        print(
            "\t".join(
                [
                    event.file,
                    str(event.line),
                    event.platform,
                    event.timestamp,
                    event.kind,
                    event.role,
                    event.text.replace("\t", " "),
                ]
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--format", choices=["text", "json", "tsv"], default="text")
    parser.add_argument("--limit", type=int, default=0, help="Maximum events per file; 0 means no limit.")
    parser.add_argument("--preview-chars", type=int, default=DEFAULT_PREVIEW_CHARS)
    args = parser.parse_args()

    all_json: list[dict[str, Any]] = []
    for path in args.files:
        platform, events, metrics = project_file(path, args.preview_chars)
        if args.limit:
            events = events[: args.limit]
        if args.format == "json":
            all_json.append(
                {
                    "file": str(path),
                    "platform": platform,
                    "metrics": metrics,
                    "events": [event_json(event) for event in events],
                }
            )
        elif args.format == "tsv":
            print_tsv(path, platform, events, metrics)
        else:
            print_text(path, platform, events, metrics)

    if args.format == "json":
        print(json.dumps(all_json, indent=2, ensure_ascii=False))


def event_json(event: Event) -> dict[str, Any]:
    value = asdict(event)
    value["ref"] = event.ref
    return value


if __name__ == "__main__":
    main()
