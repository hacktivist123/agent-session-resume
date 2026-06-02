# Expected Resume Output

## Brief context summary

The source represents a large transcript that should be inventoried and searched before reading deeply. The relevant evidence is a failing `tests/payment-retry.test.ts` result found in the large build log.

## Task status breakdown

- DONE: Add payment retry helper - evidence: `tests/fixtures/large-transcript/handoff.md:L13`.
- PARTIALLY DONE: Wire retry helper into checkout flow - evidence: `tests/fixtures/large-transcript/handoff.md:L14`.
- NOT DONE: Fix failing payment retry test - evidence: `tests/fixtures/large-transcript/handoff.md:L15`.

## Clear next action

Open the checkout retry flow and reproduce `FAIL tests/payment-retry.test.ts` before changing unrelated payment code.
