# Expected Resume Output

## Brief context summary

The source represents a large transcript that should be inventoried and searched before reading deeply. The relevant evidence is a failing `tests/payment-retry.test.ts` result found in the large build log.

## Task status breakdown

- DONE: Add payment retry helper.
- PARTIALLY DONE: Wire retry helper into checkout flow.
- NOT DONE: Fix failing payment retry test.

## Clear next action

Open the checkout retry flow and reproduce `FAIL tests/payment-retry.test.ts` before changing unrelated payment code.
