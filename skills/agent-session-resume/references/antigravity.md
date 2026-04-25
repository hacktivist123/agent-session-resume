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

## Reading

Read artifacts in chronological order when possible. Prioritize files that explain:

- the user request
- the agent plan
- completed implementation steps
- verification evidence
- review comments or follow-up instructions

If only artifacts are available, state that no full transcript was found and reconstruct task status from the artifacts plus current repository state.

## Resume Notes

- Conversation transcript wins over artifacts when both are available.
- Artifacts are evidence, not proof of completion. Verify claimed changes in the actual files.
- If Antigravity history is inaccessible and no export exists, ask the user for an export or the relevant artifact only after workspace inspection fails.

Reference: Google describes Antigravity agents producing reviewable artifacts such as task lists, implementation plans, screenshots, and recordings in its launch post: https://developers.googleblog.com/en/build-with-google-antigravity-our-new-agentic-development-platform/
