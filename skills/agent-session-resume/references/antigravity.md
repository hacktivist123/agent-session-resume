# Antigravity Adapter

Use this adapter when resuming work from Google Antigravity or an Antigravity-exported handoff.

## Discovery

Prefer explicit exports, workspace artifacts, and user-provided paths over private application storage. Antigravity emphasizes agent-visible artifacts such as task lists, implementation plans, screenshots, walkthroughs, and browser recordings, so these may be the best available substitute when a raw chat transcript is unavailable.

Inspect the workspace for likely handoff material:

```bash
find . -maxdepth 5 -type f \( \
  -iname '*artifact*' -o \
  -iname '*walkthrough*' -o \
  -iname '*plan*' -o \
  -iname '*task*' -o \
  -iname '*transcript*' -o \
  -iname '*summary*' \
\) 2>/dev/null
```

Also inspect any Antigravity-specific workspace folder if present, but do not rely on undocumented private storage as the only source.

## Artifact Ordering

When no full transcript is available, build an artifact inventory before reading deeply:

```bash
find . -maxdepth 5 -type f \( \
  -iname '*artifact*' -o \
  -iname '*walkthrough*' -o \
  -iname '*plan*' -o \
  -iname '*task*' -o \
  -iname '*transcript*' -o \
  -iname '*summary*' \
\) -print0 2>/dev/null | xargs -0 ls -lt 2>/dev/null
```

Prefer the strongest source for the question being resumed:

1. Explicit user-provided export, transcript, or artifact path.
2. Full transcript or conversation export.
3. Task list or implementation plan with timestamps.
4. Walkthrough, screenshot, browser recording, or verification artifact.
5. Generated summary or status note.
6. File modification times, used only as a tie-breaker.

If artifacts disagree, prefer the latest artifact that includes concrete verification evidence, then validate against current repository files and git state.

## Reading

Read artifacts in chronological order when possible. Prioritize files that explain:

- the user request
- the agent plan
- completed implementation steps
- verification evidence
- review comments or follow-up instructions

For screenshots and recordings, extract only the resume-relevant facts: visible state, tested flow, errors, and what the prior agent claimed was verified. Do not treat a visual artifact as proof that code is complete until the repository state confirms it.

If only artifacts are available, state that no full transcript was found and reconstruct task status from the artifacts plus current repository state.

## Resume Notes

- Conversation transcript wins over artifacts when both are available.
- Artifacts are evidence, not proof of completion. Verify claimed changes in the actual files.
- If Antigravity history is inaccessible and no export exists, ask the user for an export or the relevant artifact only after workspace inspection fails.

Reference: Google describes Antigravity agents producing reviewable artifacts such as task lists, implementation plans, screenshots, and recordings in its launch post: https://developers.googleblog.com/en/build-with-google-antigravity-our-new-agentic-development-platform/
