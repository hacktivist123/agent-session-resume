#!/usr/bin/env python3
"""Create a compact evidence digest from agent-session files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MAX_PREVIEW = 500
KEYWORDS = ("todo", "not done", "partially done", "failed", "error", "next", "pause", "stop here")


def preview(text: Any, limit: int = MAX_PREVIEW) -> str:
    value = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def is_codex(rows: list[dict[str, Any]]) -> bool:
    return any(row.get("type") == "session_meta" for row in rows)


def is_claude(rows: list[dict[str, Any]]) -> bool:
    return any(row.get("type") in {"ai-title", "queue-operation"} for row in rows) or any(
        row.get("type") in {"user", "assistant", "tool_result"} and "message" in row for row in rows
    )


def text_from_claude_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return preview(content)
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "text":
            parts.append(str(item.get("text") or ""))
        elif item_type == "tool_use":
            parts.append(f"[tool_use {item.get('name')}] {preview(item.get('input') or '')}")
        elif item_type == "tool_result":
            parts.append(f"[tool_result] {preview(item.get('content') or '')}")
    return "\n".join(part for part in parts if part)


def digest_codex(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    timeline: list[str] = []
    tool_calls: list[str] = []
    evidence: list[str] = []
    for row in rows:
        row_type = row.get("type")
        payload = row.get("payload") or {}
        if row_type == "session_meta":
            meta = {
                "id": payload.get("id"),
                "cwd": payload.get("cwd"),
                "timestamp": payload.get("timestamp"),
                "originator": payload.get("originator"),
            }
        if row_type not in {"event_msg", "response_item"}:
            continue
        payload_type = payload.get("type")
        timestamp = row.get("timestamp") or ""
        if payload_type in {"user_message", "agent_message"}:
            message = preview(payload.get("message") or payload.get("text") or "")
            timeline.append(f"{timestamp} {payload_type}: {message}")
            if any(keyword in message.lower() for keyword in KEYWORDS):
                evidence.append(f"{timestamp} {message}")
        elif payload_type == "function_call":
            tool_calls.append(f"{timestamp} {payload.get('name') or 'tool'}: {preview(payload.get('arguments') or payload)}")
        elif payload_type == "function_call_output":
            output = preview(payload.get("output") or payload)
            if any(keyword in output.lower() for keyword in KEYWORDS):
                evidence.append(f"{timestamp} tool_output: {output}")
    return {"platform": "codex", "path": str(path), "meta": meta, "timeline": timeline, "tool_calls": tool_calls, "evidence": evidence}


def digest_claude(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    meta: dict[str, Any] = {"titles": []}
    timeline: list[str] = []
    tool_calls: list[str] = []
    evidence: list[str] = []
    seen_titles: set[str] = set()
    for row in rows:
        row_type = row.get("type")
        timestamp = row.get("timestamp") or ""
        if row_type == "ai-title":
            title = str(row.get("aiTitle") or "")
            if title and title not in seen_titles:
                meta["titles"].append(title)
                seen_titles.add(title)
            continue
        if row_type not in {"user", "assistant", "system", "tool_result"}:
            continue
        if row.get("cwd") and "cwd" not in meta:
            meta["cwd"] = row.get("cwd")
        if row.get("sessionId") and "id" not in meta:
            meta["id"] = row.get("sessionId")
        if row_type == "tool_result":
            role = "tool_result"
            content = {
                "command": row.get("command"),
                "output": row.get("output"),
            }
        else:
            message = row.get("message") or {}
            role = message.get("role") or row_type if isinstance(message, dict) else row_type
            content = message.get("content") if isinstance(message, dict) else message
        text = text_from_claude_content(content)
        if not text:
            continue
        line = f"{timestamp} {role}: {preview(text)}"
        timeline.append(line)
        if "[tool_use" in text:
            tool_calls.append(line)
        if any(keyword in text.lower() for keyword in KEYWORDS):
            evidence.append(line)
    return {"platform": "claude-code", "path": str(path), "meta": meta, "timeline": timeline, "tool_calls": tool_calls, "evidence": evidence}


def digest_text(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    evidence = [line for line in lines if any(keyword in line.lower() for keyword in KEYWORDS)]
    return {"platform": "text", "path": str(path), "meta": {}, "timeline": lines[:20], "tool_calls": [], "evidence": evidence[:20]}


def digest_file(path: Path) -> dict[str, Any]:
    if path.suffix == ".jsonl":
        rows = read_jsonl(path)
        if is_codex(rows):
            return digest_codex(path, rows)
        if is_claude(rows):
            return digest_claude(path, rows)
    return digest_text(path)


def print_digest(digests: list[dict[str, Any]]) -> None:
    print("# Session Digest")
    for digest in digests:
        print(f"\n## {digest['path']}")
        print(f"- Platform: {digest['platform']}")
        if digest["meta"]:
            print(f"- Metadata: `{json.dumps(digest['meta'], ensure_ascii=False)}`")
        print("\n### Timeline Preview")
        for line in digest["timeline"][:12]:
            print(f"- {line}")
        if digest["tool_calls"]:
            print("\n### Tool Calls")
            for line in digest["tool_calls"][:8]:
                print(f"- {line}")
        if digest["evidence"]:
            print("\n### Evidence Cues")
            for line in digest["evidence"][:12]:
                print(f"- {line}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    print_digest([digest_file(path) for path in args.files])


if __name__ == "__main__":
    main()
