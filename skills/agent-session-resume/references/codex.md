# Codex Adapter

Use this adapter when resuming a Codex session, continuing from a Codex desktop or CLI handoff, or when a Codex conversation summary is present.

## Discovery

Codex may provide prior context directly in the active conversation, through a compaction summary, or through files in the workspace. Treat injected conversation context as a session record, then validate it against the repository before editing.

Inspect the workspace for:

```bash
find . -maxdepth 4 -type f \( -name '*session*' -o -name '*transcript*' -o -name '*handoff*' -o -name '*summary*' \) 2>/dev/null
find .codex .agents -type f 2>/dev/null
```

Codex normally stores conversation transcripts in the user-level Codex home, not inside each repository. If the user asks for the "most recent Codex session" and no project-local handoff is present, inspect the user-level index before broad transcript scans:

```bash
tail -n 40 "${CODEX_HOME:-$HOME/.codex}/session_index.jsonl" 2>/dev/null
```

Use `session_index.jsonl` to shortlist candidate session IDs by thread name, session name, and update time. If a title or topic is known, filter the index before opening transcripts:

```bash
jq -r 'select((.thread_name // "") | test("<session name or topic>"; "i")) | [.updated_at, .id, .thread_name] | @tsv' "${CODEX_HOME:-$HOME/.codex}/session_index.jsonl"
```

After choosing a candidate ID, resolve it to the transcript file:

```bash
session_id="<candidate id>"
find "${CODEX_HOME:-$HOME/.codex}/sessions" "${CODEX_HOME:-$HOME/.codex}/archived_sessions" -type f -name "*${session_id}*.jsonl" 2>/dev/null
```

If the index is missing or inconclusive, then broaden discovery:

```bash
find "${CODEX_HOME:-$HOME/.codex}" -maxdepth 5 -type f -name '*.jsonl' 2>/dev/null
```

Common locations:

- `${CODEX_HOME:-$HOME/.codex}/session_index.jsonl` - session IDs, names, and update times.
- `${CODEX_HOME:-$HOME/.codex}/sessions/YYYY/MM/DD/*.jsonl` - active or recent session transcripts.
- `${CODEX_HOME:-$HOME/.codex}/archived_sessions/*.jsonl` - archived transcripts.

Before reading a transcript body, confirm that its `session_meta` `cwd` matches the current repository. Project only the field you need instead of dumping the raw record, because Codex `session_meta` can include large base instructions and tool metadata:

```bash
session="<candidate transcript>"
jq -r 'select(.type == "session_meta") | .payload.cwd // empty' "$session" | head -n 1
```

When checking several candidate transcripts, print a compact `cwd<TAB>file` inventory before ranking:

```bash
for session in path/to/candidates/*.jsonl; do
  jq -r --arg file "$session" 'select(.type == "session_meta") | [(.payload.cwd // ""), $file] | @tsv' "$session" | head -n 1
done
```

## Candidate Ranking

When multiple Codex transcripts could match, rank candidates by the strongest matching signal. Do not let several weaker signals outrank a stronger one:

1. Explicit path or session ID supplied by the user.
2. Exact `cwd`, `workdir`, or repo path match with the current repository.
3. Parent/child cwd match, where the transcript cwd contains the repo or is inside it.
4. Thread name, title, or session name match from the index or transcript metadata.
5. Mentioned files, package names, repository names, or branch names from the current work.
6. Recency, used only as a tie-breaker among otherwise equal candidates.

Only inspect transcript bodies for mentioned files or symbols when candidates are still tied after stronger metadata signals. If candidates are still tied after recency, choose the stable lexical order of transcript path or session ID and mention the ambiguity in the context summary. Do not pick the newest global Codex session if it appears to belong to a different project.

Example:

| Candidate | Signal | Result |
|---|---|---|
| `A`, updated today | thread name matches, cwd is another repo | skip |
| `B`, updated yesterday | exact cwd match | choose |
| `C`, updated today | mentions a package name, no cwd match | inspect only if no stronger match exists |

Use `git status --short --branch` early to understand what already changed. If the active folder is not a git repository, locate the relevant repo from the transcript or user-provided path.

## Safe Reading

Codex session files can contain raw metadata and very large tool results. Do not load or paste entire `session_meta` records, full session indexes, or giant tool outputs when only routing fields or a small evidence slice is needed.

Before reading a candidate transcript, check its size and line count:

```bash
wc -lc "$session_file"
```

Project metadata with `jq` instead of dumping raw JSONL:

```bash
jq -c 'select(.type == "session_meta") | {id: .payload.id, timestamp: .payload.timestamp, cwd: .payload.cwd, originator: .payload.originator, cli_version: .payload.cli_version}' "$session_file" | head -n 1
```

Use event types to decide what to inspect next:

| Event shape | Resume use |
|---|---|
| `session_meta` | Session ID, cwd, originator, CLI version |
| `event_msg` with `user_message` or `agent_message` | Human-readable conversation timeline |
| `event_msg` with `reasoning` | Optional decision context when user/agent messages are not enough |
| `response_item` with `function_call` | Commands or tools the agent ran |
| `response_item` with `function_call_output` | Tool output; inspect selectively when relevant |
| token counts, web-search status, and other telemetry | Usually skip unless debugging the resume process itself |

For large tool outputs, first identify the relevant event, command, file, or error text. Then slice by line range or search for matching terms instead of loading the whole output:

```bash
rg -n "error|failed|TODO|<file-or-symbol-pattern>" "$session_file"
sed -n '120,220p' "$session_file"
```

## Reading

Read the current conversation summary, local handoff files, and changed files referenced by the prior session. When a full transcript is unavailable, explicitly distinguish:

- facts from the transcript or summary
- facts verified from files
- inferences from current repository state

For large Codex JSONL transcripts, start with a message-only skim to orient yourself before deeper review:

```bash
jq -r '
  select(.type == "event_msg" or .type == "response_item")
  | select(.payload.type == "user_message" or .payload.type == "agent_message")
  | "\n=== \(.timestamp) [\(.payload.type)] ===\n\(.payload.message // .payload.text // "")"
' "$session_file"
```

This intentionally keeps only user and agent messages with timestamps, skipping session metadata, tool calls, tool output, and other large event payloads. Use it as an orientation step, not as a replacement for evidence review: still inspect relevant tool outputs, changed files, git state, tests, and artifacts before continuing work.

## Resume Notes

- If the user says the prior session was from Claude Code and Codex is only the current runtime, use the Claude Code adapter for transcript discovery.
- Codex work often includes compacted context. Treat summaries as useful but incomplete until checked against changed files, tests, and git state.
- Do not overwrite user edits in a dirty worktree while trying to recreate prior work.
