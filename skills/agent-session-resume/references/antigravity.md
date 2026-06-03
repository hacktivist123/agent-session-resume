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

When the user explicitly asks to use local Antigravity data, prefer the readable artifact store before application databases or binary conversation records. On macOS, useful local artifacts may exist under:

```bash
find "$HOME/.gemini/antigravity/brain" -maxdepth 2 -type f \( \
  -name '*.metadata.json' -o \
  -name 'task.md' -o \
  -name 'implementation_plan.md' -o \
  -name '*.resolved' -o \
  -name '*.resolved.*' \
\) 2>/dev/null
```

Read `*.metadata.json` first. Metadata commonly includes `artifactType`, `summary`, `updatedAt`, and sometimes `version`, which is enough to rank candidate conversations before loading larger task or plan artifacts.

Before reading large artifacts, count them:

```bash
find "$HOME/.gemini/antigravity/brain" -maxdepth 2 -type f \( \
  -name 'task.md' -o -name 'implementation_plan.md' -o -name '*.resolved*' \
\) -print0 2>/dev/null | xargs -0 wc -lc 2>/dev/null
```

## Local App Storage

Antigravity may also keep VS Code/Electron-style state under `~/Library/Application Support/Antigravity`. Use it as bounded discovery context, not as the first transcript source.

Workspace mappings can connect a repository path to a workspace storage hash:

```bash
find "$HOME/Library/Application Support/Antigravity/User/workspaceStorage" \
  -maxdepth 2 -name workspace.json -type f 2>/dev/null
```

For SQLite state databases, inspect keys and value sizes before reading values:

```bash
sqlite3 "$HOME/Library/Application Support/Antigravity/User/globalStorage/state.vscdb" \
  "select key, length(value) from ItemTable order by key;" 2>/dev/null
```

The global and workspace databases may contain useful routing keys such as `chat.ChatSessionStore.index`, `antigravityUnifiedStateSync.trajectorySummaries`, `antigravityUnifiedStateSync.artifactReview`, `history.entries`, and terminal state. They may also contain sensitive authentication or preference state such as OAuth tokens. Do not dump raw database values into the model; inventory keys first, then read only a specific safe value if it is necessary and clearly relevant.

Other local surfaces are lower priority:

- `~/Library/Application Support/Antigravity/User/History/*/entries.json` can show file edit-history clues, but it does not prove implementation or verification.
- `~/Library/Application Support/Antigravity/logs/*/*.log` can help explain errors, permission prompts, or crashes, but logs may be empty or noisy.
- `~/.gemini/antigravity/conversations/*.pb` is a binary conversation store. Treat it as a last resort after readable artifacts and exports fail.
- `~/.gemini/antigravity/browser_recordings/<conversation-id>/` may contain many screenshots. Inventory counts and timestamps first, then inspect only relevant frames.
- `~/.gemini/antigravity/code_tracker/` can contain copied source snapshots and secrets such as `.env` files. Use filenames and metadata for routing; read contents only when explicitly relevant and redact secrets.

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
3. Local Antigravity `brain/<conversation-id>/*.metadata.json` whose summary, type, and `updatedAt` match the current repo or user request.
4. Task list, implementation plan, or resolved artifact sidecar with concrete steps and verification notes.
5. Workspace storage mapping that exactly matches the current repository path.
6. Walkthrough, screenshot, browser recording, or verification artifact.
7. Generated summary or status note.
8. Logs, edit history, app database keys, and file modification times, used only as supporting clues or tie-breakers.

If artifacts disagree, prefer the latest artifact that includes concrete verification evidence, then validate against current repository files and git state.

## Reading

Read artifacts in chronological order when possible. For local Antigravity data, inspect metadata first, then the smallest task/plan artifacts that explain:

- the user request
- the agent plan
- completed implementation steps
- verification evidence
- review comments or follow-up instructions

For screenshots and recordings, extract only the resume-relevant facts: visible state, tested flow, errors, and what the prior agent claimed was verified. Do not treat a visual artifact as proof that code is complete until the repository state confirms it.

For `User/History` entries, record which files appear to have local history, then verify against the current repo. For app-state databases, cite the key that guided discovery rather than pasting the raw value. If only artifacts are available, state that no full transcript was found and reconstruct task status from the artifacts plus current repository state.

## Resume Notes

- Conversation transcript wins over artifacts when both are available.
- Artifacts are evidence, not proof of completion. Verify claimed changes in the actual files.
- If Antigravity history is inaccessible and no export exists, ask the user for an export or the relevant artifact only after workspace inspection fails.
- Local Antigravity storage can be private and sensitive. Prefer metadata inventory, explicit paths, and bounded reads over broad transcript or database dumps.

Reference: Google describes Antigravity agents producing reviewable artifacts such as task lists, implementation plans, screenshots, and recordings in its launch post: https://developers.googleblog.com/en/build-with-google-antigravity-our-new-agentic-development-platform/
