# Fixture Tests

These fixtures are small pressure scenarios for `agent-session-resume`.

Run structural validation:

```bash
python3 scripts/sync-claude-plugin.py
python3 scripts/validate-skill-package.py
python3 scripts/validate-fixtures.py
python3 scripts/validate-trigger-matrix.py
claude plugin validate .
claude plugin validate plugins/agent-session-resume
```

The package validator checks the installable skill shape, the optional Claude plugin wrapper, and that the plugin copy matches the canonical standalone skill. The fixture validator checks that every supported platform has a scenario, that each source and expected-output file exists, and that expected outputs include the required resume sections and task classifications. The trigger matrix validator checks prompt coverage for should-trigger and should-not-trigger cases.

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

## Manual Trigger Test

Use `tests/trigger-matrix.json` to check whether the skill activates at the right times:

- `should_trigger`: obvious, paraphrased, platform-specific, and artifact-based resume requests
- `should_not_trigger`: unrelated build, coding, review, data, and general question prompts

The validator checks matrix structure and coverage. It does not prove model behavior by itself; run the prompts manually or through an agent evaluation harness when changing the skill description.

## Scenarios

- `claude-code-jsonl`: prompt history plus full JSONL-style transcript with unfinished docs and unrun integration tests
- `codex-compacted-handoff`: compacted handoff with a failing reload persistence test
- `antigravity-artifacts`: artifact-only handoff with missing mobile verification
- `opencode-session-export`: session export with leftover cleanup and leak check work
