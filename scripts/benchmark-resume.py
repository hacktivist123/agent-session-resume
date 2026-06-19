#!/usr/bin/env python3
"""Benchmark context-loading cost for session-resume reading strategies.

Measures, for each fixture transcript/artifact set under tests/fixtures/,
the bytes that would enter the model context under three strategies:

  raw        full file read (the naive baseline)
  projected  message-only projection with bounded tool summaries
  digest     keyword/evidence digest (todo|error|failed|next|done|partially
             lines plus first+last 5 messages, each truncated to 300 chars)

This script is intentionally self-contained (python3 stdlib only) and does
not import the other session scripts. The inline projection is a minimal
re-implementation used only for measurement, not for producing handoffs.

Usage:
  python3 scripts/benchmark-resume.py [--fixtures-dir DIR] [--json]

Token note: tokens are approximated as bytes / 4 (a common rough heuristic
for English/code text); the markdown output carries this as a footnote.
"""

import argparse
import json
import os
import re
import sys

TOOL_USE_LIMIT = 300          # Claude tool_use name+input
TOOL_RESULT_LIMIT = 500       # Claude tool_result
FUNCTION_CALL_LIMIT = 300     # Codex function_call name+args
FUNCTION_OUTPUT_LIMIT = 1000  # Codex function_call_output
DIGEST_LINE_LIMIT = 300
DIGEST_EDGE_MESSAGES = 5
KEYWORD_RE = re.compile(r"(todo|error|failed|next|done|partially)", re.IGNORECASE)

EXCLUDED_BASENAMES = {"expected.md"}


def truncate(text, limit):
    text = text or ""
    return text if len(text) <= limit else text[:limit]


def coerce_text(value):
    """Best-effort plain text from a JSON value (str, list of blocks, dict)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = []
        for item in value:
            part = coerce_text(item)
            if part:
                parts.append(part)
        return "\n".join(parts)
    if isinstance(value, dict):
        for key in ("text", "content", "message", "output"):
            if key in value:
                return coerce_text(value[key])
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def project_claude_record(record):
    """Project one Claude Code JSONL record into message strings.

    Keeps user/assistant visible text, tool_use name+input (truncated),
    tool_result (truncated). Drops titles, queue ops, thinking blocks,
    signatures, and other telemetry.
    """
    messages = []
    rtype = record.get("type")

    # Flat tool_result records (e.g. {"type":"tool_result","command":...,"output":...})
    if rtype == "tool_result":
        text = coerce_text(record.get("output") or record.get("content") or record)
        command = record.get("command")
        if command:
            text = "%s\n%s" % (command, text)
        messages.append(truncate(text, TOOL_RESULT_LIMIT))
        return messages

    if rtype not in ("user", "assistant"):
        return messages

    payload = record.get("message")
    if isinstance(payload, str):
        messages.append(payload)
        return messages
    if not isinstance(payload, dict):
        return messages

    content = payload.get("content")
    if isinstance(content, str):
        messages.append(content)
        return messages
    if not isinstance(content, list):
        return messages

    for block in content:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text":
            text = block.get("text") or ""
            if text:
                messages.append(text)
        elif btype == "tool_use":
            summary = "%s %s" % (
                block.get("name") or "",
                json.dumps(block.get("input", {}), ensure_ascii=False),
            )
            messages.append(truncate(summary.strip(), TOOL_USE_LIMIT))
        elif btype == "tool_result":
            messages.append(truncate(coerce_text(block.get("content")), TOOL_RESULT_LIMIT))
        # thinking / signature / other block types are dropped on purpose
    return messages


def project_codex_record(record):
    """Project one Codex JSONL record into message strings.

    Keeps user_message/agent_message payloads, function_call name+args
    (truncated), function_call_output (truncated). Drops session_meta,
    token_count, reasoning, and other telemetry.
    """
    messages = []
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return messages
    ptype = payload.get("type")
    if ptype in ("user_message", "agent_message"):
        text = coerce_text(payload.get("message"))
        if text:
            messages.append(text)
    elif ptype == "function_call":
        summary = "%s %s" % (
            payload.get("name") or "",
            coerce_text(payload.get("arguments")),
        )
        messages.append(truncate(summary.strip(), FUNCTION_CALL_LIMIT))
    elif ptype == "function_call_output":
        messages.append(truncate(coerce_text(payload.get("output")), FUNCTION_OUTPUT_LIMIT))
    return messages


def project_jsonl_file(path):
    """Return (message_list, skipped_line_count) for a JSONL transcript."""
    messages = []
    skipped = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    skipped += 1
                    continue
                if not isinstance(record, dict):
                    skipped += 1
                    continue
                if "payload" in record:
                    messages.extend(project_codex_record(record))
                else:
                    messages.extend(project_claude_record(record))
    except OSError as exc:
        print("warning: cannot read %s: %s" % (path, exc), file=sys.stderr)
        skipped += 1
    return messages, skipped


def read_file_bytes(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def read_file_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return [line.rstrip("\n") for line in handle]
    except OSError as exc:
        print("warning: cannot read %s: %s" % (path, exc), file=sys.stderr)
        return []


def digest_from_messages(messages):
    """Keyword lines + first/last N messages, each truncated, de-duplicated."""
    selected = []
    seen = set()

    def add(text):
        text = truncate(text.strip(), DIGEST_LINE_LIMIT)
        if text and text not in seen:
            seen.add(text)
            selected.append(text)

    for msg in messages[:DIGEST_EDGE_MESSAGES]:
        add(msg)
    for msg in messages[-DIGEST_EDGE_MESSAGES:]:
        add(msg)
    for msg in messages:
        for line in msg.splitlines():
            if KEYWORD_RE.search(line):
                add(line)
    return selected


def measure_fixture(fixture_dir):
    """Measure raw/projected/digest byte counts for one fixture directory."""
    source_files = []
    for root, _dirs, files in os.walk(fixture_dir):
        for name in sorted(files):
            if name in EXCLUDED_BASENAMES:
                continue
            source_files.append(os.path.join(root, name))
    source_files.sort()

    raw_bytes = 0
    projected_parts = []
    all_messages = []
    skipped = 0

    for path in source_files:
        raw_bytes += read_file_bytes(path)
        if path.endswith(".jsonl"):
            messages, file_skipped = project_jsonl_file(path)
            skipped += file_skipped
            projected_parts.extend(messages)
            all_messages.extend(messages)
        else:
            # Non-JSONL artifacts (markdown handoffs, metadata JSON, sidecars)
            # enter the projection as-is; digest still works on their lines.
            lines = read_file_lines(path)
            text = "\n".join(lines)
            if text:
                projected_parts.append(text)
            all_messages.extend(lines)

    projected_bytes = len("\n".join(projected_parts).encode("utf-8"))
    digest_lines = digest_from_messages(all_messages)
    digest_bytes = len("\n".join(digest_lines).encode("utf-8"))

    return {
        "fixture": os.path.basename(fixture_dir),
        "source_files": len(source_files),
        "raw_bytes": raw_bytes,
        "projected_bytes": projected_bytes,
        "digest_bytes": digest_bytes,
        "skipped_lines": skipped,
        "raw_tokens_approx": raw_bytes // 4,
        "projected_tokens_approx": projected_bytes // 4,
        "digest_tokens_approx": digest_bytes // 4,
    }


def pct(part, whole):
    if whole <= 0:
        return "n/a"
    return "%.1f%%" % (100.0 * part / whole)


def render_markdown(results):
    lines = []
    lines.append("| Fixture | Raw bytes | Projected bytes (% of raw) | Digest bytes (% of raw) |")
    lines.append("| --- | ---: | ---: | ---: |")
    total_raw = total_proj = total_digest = 0
    for row in results:
        total_raw += row["raw_bytes"]
        total_proj += row["projected_bytes"]
        total_digest += row["digest_bytes"]
        lines.append(
            "| %s | %d | %d (%s) | %d (%s) |"
            % (
                row["fixture"],
                row["raw_bytes"],
                row["projected_bytes"],
                pct(row["projected_bytes"], row["raw_bytes"]),
                row["digest_bytes"],
                pct(row["digest_bytes"], row["raw_bytes"]),
            )
        )
    lines.append(
        "| **Total** | %d | %d (%s) | %d (%s) |"
        % (
            total_raw,
            total_proj,
            pct(total_proj, total_raw),
            total_digest,
            pct(total_digest, total_raw),
        )
    )
    lines.append("")
    lines.append(
        "Token approximation: tokens ~= bytes / 4. Total: raw ~%d tokens, "
        "projected ~%d tokens, digest ~%d tokens."
        % (total_raw // 4, total_proj // 4, total_digest // 4)
    )
    skipped_total = sum(row["skipped_lines"] for row in results)
    if skipped_total:
        lines.append("")
        lines.append("Skipped %d unparseable JSONL line(s) across all fixtures." % skipped_total)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Measure context bytes for raw vs projected vs digest reading strategies."
    )
    default_fixtures = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "fixtures")
    )
    parser.add_argument(
        "--fixtures-dir",
        default=default_fixtures,
        help="Directory containing fixture subdirectories (default: tests/fixtures)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of markdown")
    args = parser.parse_args()

    fixtures_dir = args.fixtures_dir
    if not os.path.isdir(fixtures_dir):
        print("error: fixtures directory not found: %s" % fixtures_dir, file=sys.stderr)
        return 1

    fixture_dirs = sorted(
        os.path.join(fixtures_dir, name)
        for name in os.listdir(fixtures_dir)
        if os.path.isdir(os.path.join(fixtures_dir, name))
    )
    if not fixture_dirs:
        print(
            "error: no fixture directories found under %s (expected one subdirectory per scenario)"
            % fixtures_dir,
            file=sys.stderr,
        )
        return 1

    results = [measure_fixture(path) for path in fixture_dirs]
    results = [row for row in results if row["source_files"] > 0]
    if not results:
        print("error: fixture directories contain no measurable source files", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"token_approximation": "bytes/4", "results": results}, indent=2))
    else:
        print(render_markdown(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
