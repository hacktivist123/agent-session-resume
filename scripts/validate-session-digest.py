#!/usr/bin/env python3
"""Validate the session digest helper, including sidecar cache behavior."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "agent-session-resume" / "scripts" / "session-digest.py"
CODEX_FIXTURE = ROOT / "tests" / "fixtures" / "codex-noisy-jsonl" / "transcript.jsonl"
CLAUDE_FIXTURE = ROOT / "tests" / "fixtures" / "claude-noisy-jsonl" / "transcript.jsonl"

APPENDED_ROW = {
    "timestamp": "2030-01-01T00:00:00Z",
    "type": "event_msg",
    "payload": {"type": "agent_message", "message": "appended-tail-marker next step pending"},
}


def fail(message: str) -> None:
    print(f"session digest validation failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_digest(*args: str) -> tuple[str, str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout, result.stderr


def sidecar_for(path: Path) -> Path:
    return path.with_name(path.name + ".digest.json")


def read_sidecar(path: Path) -> dict:
    sidecar = sidecar_for(path)
    if not sidecar.exists():
        fail(f"expected sidecar at {sidecar}")
    return json.loads(sidecar.read_text(encoding="utf-8"))


def validate_cache_hit(workdir: Path) -> None:
    transcript = workdir / "transcript.jsonl"
    shutil.copyfile(CODEX_FIXTURE, transcript)

    first_out, first_err = run_digest(str(transcript))
    if "cache hit" in first_err:
        fail("first run should not report a cache hit")
    record = read_sidecar(transcript)
    for key in ("cache_version", "source", "size", "sha256", "offset", "digest"):
        if key not in record:
            fail(f"sidecar missing key {key!r}")
    if record["size"] != transcript.stat().st_size or record["offset"] != record["size"]:
        fail("sidecar size/offset should match the transcript size")

    second_out, second_err = run_digest(str(transcript))
    if "cache hit" not in second_err:
        fail("second run on unchanged file should report a cache hit")
    if second_out != first_out:
        fail("cache-hit output should match the fresh digest output")


def validate_append_only_tail(workdir: Path) -> None:
    transcript = workdir / "transcript.jsonl"
    shutil.copyfile(CODEX_FIXTURE, transcript)
    run_digest(str(transcript))
    old_offset = read_sidecar(transcript)["offset"]

    with transcript.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(APPENDED_ROW) + "\n")

    out, err = run_digest(str(transcript))
    if "incremental update" not in err:
        fail("appended file should trigger incremental update")
    if "appended-tail-marker" not in out:
        fail("incremental digest should include the appended event")

    record = read_sidecar(transcript)
    if record["offset"] <= old_offset:
        fail("sidecar offset should advance after incremental update")

    # Incremental output must match a full recompute of the grown file.
    fresh_dir = workdir / "fresh"
    fresh_dir.mkdir()
    fresh = fresh_dir / "transcript.jsonl"
    shutil.copyfile(transcript, fresh)
    fresh_out, _ = run_digest(str(fresh))
    if out.replace(str(transcript), "X") != fresh_out.replace(str(fresh), "X"):
        fail("incremental digest output should match full recompute")


def validate_prefix_change_invalidation(workdir: Path) -> None:
    transcript = workdir / "transcript.jsonl"
    shutil.copyfile(CODEX_FIXTURE, transcript)
    run_digest(str(transcript))

    data = transcript.read_bytes()
    transcript.write_bytes(data.replace(b"session_meta", b"session_munge", 1))
    _, err = run_digest(str(transcript))
    if "cache invalidated" not in err and "recomputing" not in err:
        fail("changed prefix should invalidate the cache")
    if "cache hit" in err or "incremental update" in err:
        fail("changed prefix must not reuse the cache")


def validate_no_sidecar(workdir: Path) -> None:
    transcript = workdir / "transcript.jsonl"
    shutil.copyfile(CLAUDE_FIXTURE, transcript)
    run_digest(str(transcript), "--no-sidecar")
    if sidecar_for(transcript).exists():
        fail("--no-sidecar should not write a sidecar")


def validate_sidecar_dir(workdir: Path) -> None:
    transcript = workdir / "transcript.jsonl"
    shutil.copyfile(CLAUDE_FIXTURE, transcript)
    cache_dir = workdir / "cache"
    run_digest(str(transcript), "--sidecar-dir", str(cache_dir))
    if sidecar_for(transcript).exists():
        fail("--sidecar-dir should not write next to the transcript")
    if not (cache_dir / "transcript.jsonl.digest.json").exists():
        fail("--sidecar-dir should hold the sidecar")
    _, err = run_digest(str(transcript), "--sidecar-dir", str(cache_dir))
    if "cache hit" not in err:
        fail("--sidecar-dir rerun should report a cache hit")


def validate_unwritable_dir(workdir: Path) -> None:
    if os.name != "posix" or os.geteuid() == 0:
        return
    locked = workdir / "locked"
    locked.mkdir()
    transcript = locked / "transcript.jsonl"
    shutil.copyfile(CODEX_FIXTURE, transcript)
    locked.chmod(0o555)
    try:
        out, err = run_digest(str(transcript))
        if "skipping sidecar" not in err:
            fail("read-only directory should skip the sidecar with a notice")
        if "# Session Digest" not in out:
            fail("digest should still print when the sidecar is skipped")
    finally:
        locked.chmod(0o755)


def main() -> None:
    for check in (
        validate_cache_hit,
        validate_append_only_tail,
        validate_prefix_change_invalidation,
        validate_no_sidecar,
        validate_sidecar_dir,
        validate_unwritable_dir,
    ):
        with tempfile.TemporaryDirectory(prefix="asr-digest-") as tmp:
            check(Path(tmp))
    print("validated session digest caching")


if __name__ == "__main__":
    main()
