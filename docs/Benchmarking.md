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
