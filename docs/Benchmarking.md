# Benchmarking

Use this guide when proposing or reviewing changes to `agent-session-resume`.

Session-resume improvements are often documentation, fixture, or workflow changes. A useful PR should explain what behavior improves, how the improvement can be checked, and what a good result looks like.

## Standard Benchmark Areas

| Benchmark area | What we measure | Good result |
| --- | --- | --- |
| Session selection | Whether the agent chooses the right transcript, export, handoff, or artifact set among plausible candidates | Exact user-provided paths win; exact or near cwd matches beat newer unrelated global sessions; title/topic matches beat raw recency |
| Discovery effort | How much work the agent does before finding the right source | Uses indexes, metadata, project-local folders, and candidate shortlists before broad transcript scans |
| Token usage proxy | Bytes, characters, lines, or event counts loaded into the model context before the checkpoint | Reads projected fields, inventories, searches, and evidence slices instead of dumping huge JSONL records or tool-output files |
| Resume accuracy | Whether the report reconstructs the prior goal, task states, stopping point, and next action correctly | Matches the fixture expected output or an explicit review rubric for goal, `DONE` / `PARTIALLY DONE` / `NOT DONE`, and next action |
| Evidence quality | Whether task statuses and verification claims cite traceable evidence | Each status points to transcript lines, artifact files, command output, changed files, or an honest "not checked" gap |
| Safety and redaction | Whether sensitive-looking values leak into handoffs, fixtures, or digests | Fake secrets, customer data, bearer tokens, cookies, private URLs, and credentials are redacted or omitted |
| Robustness | Behavior with noisy, incomplete, huge, or partially inaccessible session records | Uses inventories and bounded searches; reports missing evidence honestly; avoids pretending a summary is a full transcript |
| Trigger behavior | Whether the skill activates for resume-like prompts and avoids unrelated prompts | Trigger fixtures gain useful true positives without broad over-triggering |
| Reviewer clarity | Whether an issue or PR explains the operational improvement, not just the text or files changed | Includes `What this improves` and `Benchmark target` sections with concrete measurements and good-result criteria |

## Issue And PR Fields

Use these sections for benchmarkable issues and PRs:

```markdown
## What this improves

Describe the behavior, safety property, token-efficiency goal, or reviewer decision that should improve.

## Benchmark target

| Benchmark area | What we measure | Good result |
| --- | --- | --- |
| <area> | <specific measurement or review check> | <observable passing behavior> |
```

The benchmark target does not need to be numeric for every documentation change. It does need to be specific enough that a maintainer can tell whether the PR did the intended job.

## Deterministic Checks

Deterministic checks are repo-local validations that should run before opening a PR:

```bash
python3 scripts/validate-skill-package.py
python3 scripts/validate-fixtures.py
python3 scripts/validate-trigger-matrix.py
```

Use deterministic checks for:

- package and plugin shape
- fixture manifest coverage
- required expected-output sections
- expected evidence references
- trigger and non-trigger prompt coverage
- handoff heading shape with `scripts/validate-handoff.py`

These checks prove the repository artifacts are internally consistent. They do not prove a live model will always follow the skill correctly.

## Agent-In-The-Loop Evaluations

Agent-in-the-loop evaluations ask a real agent to use the skill against one or more fixtures, then compare the checkpoint with the fixture's `expected.md`.

Use these evaluations when a change affects:

- platform-specific discovery instructions
- large transcript reading strategy
- tool-output sidecar handling
- resume report structure
- task classification rules
- trigger behavior in realistic prompts

Record the result as a short review note:

```text
Fixture: tests/fixtures/codex-wrong-newest
Agent: Codex
Prompt: Use agent-session-resume on this fixture. Do not edit files.
Result: picked older cwd-matching transcript over newer unrelated transcript.
Gaps: none / <gap found>
```

## First Benchmark Fixtures

The first benchmark set should stay small and representative:

| Fixture | Benchmark focus | Good result |
| --- | --- | --- |
| `codex-wrong-newest` | Session selection | The cwd-matching Codex transcript beats the newer unrelated session |
| `large-transcript` | Token usage proxy and robustness | The agent inventories/searches before deep reading and reports bounded evidence |
| `claude-noisy-jsonl` | Claude discovery and sidecar handling | The agent finds the right Claude session and uses persisted tool-output evidence when needed |
| `codex-noisy-jsonl` | Noisy Codex event streams | The agent extracts user-visible work state without relying on irrelevant telemetry |
| `redacted-handoff` | Safety and redaction | The handoff validates and avoids leaking fake secrets or private values |

Add new fixtures only when they cover a distinct failure mode. Prefer a small scenario with crisp expected output over a huge transcript that is hard to review.

## Baseline measurements (2026-06-10)

The token-usage-proxy area above previously had no recorded numbers. This baseline was produced with the self-contained harness in `scripts/benchmark-resume.py`, which measures the bytes that would enter the model context for each fixture source set under three reading strategies: `raw` (full file read), `projected` (message-only projection with bounded tool summaries), and `digest` (keyword/evidence lines plus first and last five messages).

Command:

```bash
python3 scripts/benchmark-resume.py
```

(Add `--json` for machine-readable output.)

| Fixture | Raw bytes | Projected bytes (% of raw) | Digest bytes (% of raw) |
| --- | ---: | ---: | ---: |
| antigravity-artifacts | 1017 | 1016 (99.9%) | 296 (29.1%) |
| antigravity-local-store | 1417 | 1416 (99.9%) | 261 (18.4%) |
| claude-code-jsonl | 1464 | 667 (45.6%) | 667 (45.6%) |
| claude-noisy-jsonl | 1651 | 432 (26.2%) | 432 (26.2%) |
| codex-compacted-handoff | 841 | 840 (99.9%) | 243 (28.9%) |
| codex-noisy-jsonl | 1397 | 346 (24.8%) | 346 (24.8%) |
| codex-wrong-newest | 922 | 116 (12.6%) | 116 (12.6%) |
| cursor-agent-export | 1425 | 1424 (99.9%) | 504 (35.4%) |
| large-transcript | 529 | 528 (99.8%) | 377 (71.3%) |
| opencode-session-export | 897 | 896 (99.9%) | 387 (43.1%) |
| redacted-handoff | 933 | 932 (99.9%) | 232 (24.9%) |
| **Total** | 12493 | 8613 (68.9%) | 3861 (30.9%) |

Token approximation: tokens ~= bytes / 4 (rough heuristic for English/code text). Totals: raw ~3123 tokens, projected ~2153 tokens, digest ~965 tokens.

Interpretation: on JSONL transcript fixtures, projection alone removes 54-87% of the bytes a naive full read would load, because telemetry, reasoning payloads, signatures, and unbounded tool output dominate the raw stream; on markdown handoffs and exports projection is a no-op by design and the digest does the work, cutting context to roughly 18-45% of raw. Across the whole fixture set, the digest strategy loads about 31% of the raw bytes. These fixtures are intentionally tiny (around 0.5-1.7 KB each); real transcripts observed in the wild run 1-70 MB, where the raw-read denominator grows far faster than the bounded projection and digest outputs, so the ratios here understate the real-world reduction substantially.
