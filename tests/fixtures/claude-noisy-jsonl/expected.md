# Expected Resume Output

## Brief context summary

The Claude Code transcript has duplicate title events, queue metadata, user/assistant messages, and a persisted-output sidecar. The useful evidence is that checkout retry focused tests passed and the full integration suite remains unrun.

## Task status breakdown

- DONE: Run focused checkout retry tests - evidence: `tests/fixtures/claude-noisy-jsonl/tool-results/checkout.txt:L3`.
- NOT DONE: Run full integration suite - evidence: `tests/fixtures/claude-noisy-jsonl/transcript.jsonl:L7`.

## Clear next action

Inspect the persisted `tool-results/checkout.txt` evidence, then run the full integration suite from `/workspace/shop`.
