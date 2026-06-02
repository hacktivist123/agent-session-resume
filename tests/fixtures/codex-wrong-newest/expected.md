# Expected Resume Output

## Brief context summary

The newest indexed Codex session belongs to `/workspace/profile` and should be skipped. The older matching session has `cwd` `/workspace/shop` and contains the checkout retry banner work.

## Task status breakdown

- DONE: Add checkout retry banner - evidence: `tests/fixtures/codex-wrong-newest/older-matching.jsonl:L3`.
- NOT DONE: Run full checkout suite - evidence: `tests/fixtures/codex-wrong-newest/older-matching.jsonl:L3`.

## Clear next action

Choose `older-matching.jsonl` despite its older timestamp, inspect the checkout files, and run the full checkout suite.
