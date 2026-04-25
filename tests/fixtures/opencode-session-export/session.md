# OpenCode Session Export

## User

The activity feed is wasting CPU by polling every five seconds. Replace that with the existing event stream and clean up any old timer code.

## Assistant

Plan:

1. Find the polling loop.
2. Subscribe to `activityEvents`.
3. Remove interval cleanup if no longer needed.
4. Run the focused feed tests.
5. Run a leak check.

## Tool Output

`rg "setInterval|activityEvents" src` found `src/feed/activity.ts`.

## Assistant

Changed `src/feed/activity.ts` so feed updates subscribe to `activityEvents` instead of starting a polling interval.

## Tool Output

`npm test -- tests/activity-feed.test.ts`

Result: PASS, 5 tests.

## Assistant

I still see an old `clearInterval(feedTimer)` branch in the teardown path. It may now be dead code, but I did not remove it yet. Leak check has not been run.

## User

Stop here. Next time, start with the leftover cleanup.
