# Fixture Tests

These fixtures are small pressure scenarios for `agent-session-resume`.

Run structural validation:

```bash
python3 scripts/validate-fixtures.py
```

The validator checks that every supported platform has a scenario, that each source and expected-output file exists, and that expected outputs include the required resume sections and task classifications.

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
- it proposes the same next action class

## Scenarios

- `claude-code-jsonl`: full JSONL-style transcript with unfinished docs and unrun integration tests
- `codex-compacted-handoff`: compacted handoff with a failing reload persistence test
- `antigravity-artifacts`: artifact-only handoff with missing mobile verification
- `opencode-session-export`: session export with leftover cleanup and leak check work
