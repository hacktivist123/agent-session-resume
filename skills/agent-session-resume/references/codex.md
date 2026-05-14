# Codex Adapter

Use this adapter when resuming a Codex session, continuing from a Codex desktop or CLI handoff, or when a Codex conversation summary is present.

## Discovery

Codex may provide prior context directly in the active conversation, through a compaction summary, or through files in the workspace. Treat injected conversation context as a session record, then validate it against the repository before editing.

Inspect the workspace for:

```bash
find . -maxdepth 4 -type f \( -name '*session*' -o -name '*transcript*' -o -name '*handoff*' -o -name '*summary*' \) 2>/dev/null
find .codex .agents -type f 2>/dev/null
```

Codex normally stores conversation transcripts in the user-level Codex home, not inside each repository. If the user asks for the "most recent Codex session" and no project-local handoff is present, inspect:

```bash
find "${CODEX_HOME:-$HOME/.codex}" -maxdepth 5 -type f \( -name 'session_index.jsonl' -o -name '*.jsonl' \) 2>/dev/null
```

Common locations:

- `${CODEX_HOME:-$HOME/.codex}/session_index.jsonl` - session IDs, names, and update times.
- `${CODEX_HOME:-$HOME/.codex}/sessions/YYYY/MM/DD/*.jsonl` - active or recent session transcripts.
- `${CODEX_HOME:-$HOME/.codex}/archived_sessions/*.jsonl` - archived transcripts.

When choosing a session, prefer the most recent transcript whose cwd, workdir, repo path, thread name, or mentioned files match the current repository. Do not pick the newest global Codex session if it appears to belong to a different project.

Use `git status --short --branch` early to understand what already changed. If the active folder is not a git repository, locate the relevant repo from the transcript or user-provided path.

## Safe Reading

Codex session files can contain raw metadata and very large tool results. Do not load or paste entire `session_meta` records, full session indexes, or giant tool outputs when only routing fields or a small evidence slice is needed.

Before reading a candidate transcript, check its size and line count:

```bash
wc -lc "$session_file"
```

Project metadata with `jq` instead of dumping raw JSONL:

```bash
jq -c 'select(.type == "session_meta") | {id: .payload.id, timestamp: .payload.timestamp, cwd: .payload.cwd, originator: .payload.originator, cli_version: .payload.cli_version}' "$session_file"
```

For large tool outputs, first identify the relevant event, command, file, or error text. Then slice by line range or search for matching terms instead of loading the whole output:

```bash
rg -n "error|failed|TODO|src/theme/useThemePreference" "$session_file"
sed -n '120,220p' "$session_file"
```

## Reading

Read the current conversation summary, local handoff files, and changed files referenced by the prior session. When a full transcript is unavailable, explicitly distinguish:

- facts from the transcript or summary
- facts verified from files
- inferences from current repository state

## Resume Notes

- If the user says the prior session was from Claude Code and Codex is only the current runtime, use the Claude Code adapter for transcript discovery.
- Codex work often includes compacted context. Treat summaries as useful but incomplete until checked against changed files, tests, and git state.
- Do not overwrite user edits in a dirty worktree while trying to recreate prior work.
