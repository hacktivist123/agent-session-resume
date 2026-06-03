# Implementation Plan

## Current State

- Implemented `src/imports/ProgressBanner.tsx` for import progress states.
- Connected the banner in `src/imports/ImportScreen.tsx`.
- Ran `npm test -- imports/progress-banner.test.ts`; focused progress test passed.

## Remaining Work

- Add retry copy to the zero-row import empty state.
- Run `npm test -- imports` after the retry copy is wired.

## Verification Notes

Treat `User/History` snapshots as edit clues only; verify current repo files before editing.
