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

## Candidate Ranking

When multiple Codex transcripts could match, rank candidates by the strongest matching signal. Do not let several weaker signals outrank a stronger one:

1. Explicit path or session ID supplied by the user.
2. Exact `cwd`, `workdir`, or repo path match with the current repository.
3. Parent/child cwd match, where the transcript cwd contains the repo or is inside it.
4. Thread name, title, or session name match.
5. Mentioned files, package names, repository names, or branch names from the current work.
6. Recency, used only as a tie-breaker among otherwise equal candidates.

If candidates are still tied after recency, choose the stable lexical order of transcript path or session ID and mention the ambiguity in the context summary. Do not pick the newest global Codex session if it appears to belong to a different project.

Use `git status --short --branch` early to understand what already changed. If the active folder is not a git repository, locate the relevant repo from the transcript or user-provided path.

## Reading

Read the current conversation summary, local handoff files, and changed files referenced by the prior session. When a full transcript is unavailable, explicitly distinguish:

- facts from the transcript or summary
- facts verified from files
- inferences from current repository state

## Resume Notes

- If the user says the prior session was from Claude Code and Codex is only the current runtime, use the Claude Code adapter for transcript discovery.
- Codex work often includes compacted context. Treat summaries as useful but incomplete until checked against changed files, tests, and git state.
- Do not overwrite user edits in a dirty worktree while trying to recreate prior work.
