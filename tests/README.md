# Fixture Tests

These fixtures are small pressure scenarios for `agent-session-resume`.

Run structural validation:

```bash
python3 scripts/validate-skill-package.py
python3 scripts/validate-fixtures.py
python3 scripts/validate-trigger-matrix.py
claude plugin validate .
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json
```

The package validator checks the installable skill shape and the optional Claude plugin wrapper that points at the same canonical skill folder. The fixture validator checks that every supported platform has a scenario, that each source and expected-output file exists, that expected outputs include the required resume sections, task classifications, and fixture evidence references, and that optional source/expected cues are present. The trigger matrix validator checks prompt coverage for should-trigger and should-not-trigger cases.

For benchmark areas and issue/PR evaluation fields, see [`docs/Benchmarking.md`](../docs/Benchmarking.md).

Validate compact handoff files with:

```bash
python3 scripts/validate-handoff.py tests/fixtures/redacted-handoff/handoff.md
```

## Manual Skill Pressure Test

To test behavior with an agent, give it the skill plus one fixture source and ask:

```text
Use agent-session-resume on this fixture. Read the full source, reconstruct context, classify tasks as DONE, PARTIALLY DONE, or NOT DONE, then state the next action. Do not edit files.
```

Compare the result with that scenario's `expected.md`. The goal is not exact wording; the important checks are:

- it reads all provided source files before deciding
- it does not repeat completed work
- it identifies the true stopping point
- it preserves the expected task classifications
- it cites concrete evidence for each task status
- it treats prior resume reports and handoff summaries as claims until verified by primary evidence
- it proposes the same next action class

For static fixtures and saved transcripts, rerunning the same unchanged source should converge on the same task status breakdown and next-action class. Wording may vary, but classifications, evidence anchors, and blocked/actionable state should remain stable. Do not apply this expectation to live or active transcripts, changing workspaces, remote GitHub state, or commands that can produce new output.

## Manual Trigger Test

Use `tests/trigger-matrix.json` to check whether the skill activates at the right times:

- `should_trigger`: obvious, paraphrased, platform-specific, and artifact-based resume requests
- `should_not_trigger`: unrelated build, coding, review, data, and general question prompts

The validator checks matrix structure and coverage. It does not prove model behavior by itself; run the prompts manually or through an agent evaluation harness when changing the skill description.

## Scenarios

- `claude-code-jsonl`: prompt history plus full JSONL-style transcript with unfinished docs and unrun integration tests
- `codex-compacted-handoff`: compacted handoff with a failing reload persistence test
- `antigravity-artifacts`: artifact-only handoff with missing mobile verification
- `antigravity-local-store`: local Antigravity `brain` artifacts plus workspace/history clues, with metadata-first ranking and bounded reads
- `opencode-session-export`: session export with leftover cleanup and leak check work
- `cursor-agent-export`: Markdown export with Cursor rule context and unfinished preview wiring
- `codex-noisy-jsonl`: noisy Codex JSONL with telemetry, reasoning, tool calls, and bounded resume evidence
- `codex-wrong-newest`: candidate-selection pressure case where a newer unrelated session must lose to the cwd match
- `claude-noisy-jsonl`: Claude JSONL with duplicate titles, queue metadata, opaque thinking/signature payloads, and a persisted-output sidecar
- `large-transcript`: large-transcript pressure case that should be inventoried and searched before deep reading
