# Codex Adapter

Use this adapter when resuming a Codex session, continuing from a Codex desktop or CLI handoff, or when a Codex conversation summary is present.

Packaged helper scripts live in the skill's `scripts/` directory, next to `SKILL.md`. Resolve them relative to the skill base directory and set `skill_dir` accordingly before using the commands below.

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

Use `session_index.jsonl` to shortlist candidate session IDs by thread name, session name, and update time. Use the packaged candidate lister, which ranks candidates without dumping transcript bodies and accepts `--cwd`, `--topic`, `--since`, and `--until` filters:

```bash
python3 "$skill_dir/scripts/session-candidates.py" --platform codex --cwd "$(pwd)" --topic "<session name or topic>"
```

Warning: `session_index.jsonl` does not cover every transcript. Codex Desktop sub-threads (transcripts with a `parent_thread_id`) never get index entries, so any index-only listing silently omits them. The packaged lister compensates with an mtime fallback sweep over `sessions/YYYY/MM/DD` that surfaces unindexed in-window transcripts as `source=mtime` rows (untitled, so `--topic` cannot match them). On windowed asks where completeness matters, also broaden directly on disk:

```bash
find "${CODEX_HOME:-$HOME/.codex}/sessions" -name '*.jsonl' -newermt '<date, e.g. 2026-06-03>' 2>/dev/null
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

Treat Codex transcripts as append logs that may still be active. A recent `updated_at` or file modification time proves transcript freshness only; it does not prove the repository is fresh. Compare transcript timestamps, file mtimes, and `git status`/remote refs separately.

Before reading a transcript body, confirm that its `session_meta` `cwd` matches the current repository. Project only the field you need instead of dumping the raw record, because Codex `session_meta` can include large base instructions and tool metadata:

```bash
session="<candidate transcript>"
jq -r 'select(.type == "session_meta") | .payload.cwd // empty' "$session" | head -n 1
```

When checking several candidate transcripts, use `session-candidates.py` (above) to print a compact ranked inventory instead of looping `jq` over every file.

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

When comparing candidate times, normalize to UTC or epoch seconds before deciding which record is newer. `session-candidates.py` prints every row's `updated_at` normalized to ISO-8601 UTC with seconds precision (e.g. `2026-06-10T00:15:30Z`) on both platforms; cross-check against file and repo time:

```bash
stat -f '%m %N' "$session_file" 2>/dev/null
git log -1 --format='%ct %h %s'
```

If a Deep resume may run for a long time, recheck the chosen transcript tail and `git status --short --branch` before the checkpoint report. If the tail changed while reading, account for the appended events before classifying tasks.

## Safe Reading

Codex session files can contain raw metadata and very large tool results. Do not load or paste entire `session_meta` records, full session indexes, or giant tool outputs when only routing fields or a small evidence slice is needed.

Before reading a candidate transcript, check its size and line count:

```bash
wc -lc "$session_file"
```

Project metadata and the bounded event stream with the packaged projector instead of dumping raw JSONL. Its first projected event is the `session_meta` routing record (id, cwd, originator, CLI version), followed by previewed user/agent messages, tool calls, and truncated tool output:

```bash
python3 "$skill_dir/scripts/session-events.py" "$session_file" --limit 200
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

For large tool outputs, first identify the relevant event, command, file, or error text. Then search a sidecar or narrowed output source, or slice the specific transcript line range, instead of loading the whole output:

```bash
rg -n "error|failed|TODO|<file-or-symbol-pattern>" path/to/tool-output-or-sidecar.txt
sed -n '120,220p' "$session_file"
```

Do not use broad raw JSONL regex scans as the first evidence pass for Codex transcripts. Matches inside `session_meta`, embedded developer/system instructions, tool schemas, or serialized prompts can look like user-visible TODOs or errors even when they are only context. Project the event stream first, then apply targeted `rg` to that projected view or to a narrowed line range:

```bash
python3 "$skill_dir/scripts/session-events.py" "$session_file" | rg -n "error|failed|TODO|<file-or-symbol-pattern>"
```

For a compact reusable summary with evidence cues, build a digest. It writes a persistent `<transcript>.digest.json` sidecar cache and processes only the appended tail on later runs, so rechecks of an active transcript stay cheap:

```bash
python3 "$skill_dir/scripts/session-digest.py" "$session_file"
```

Use raw `rg` only after the projection reveals a specific event, file path, command, or line range worth inspecting.

## Reading

Read the current conversation summary, local handoff files, and changed files referenced by the prior session. When a full transcript is unavailable, explicitly distinguish:

- facts from the transcript or summary
- facts verified from files
- inferences from current repository state

For large Codex JSONL transcripts, start with a bounded skim to orient yourself before deeper review:

```bash
python3 "$skill_dir/scripts/session-events.py" "$session_file" | rg "user_message|agent_message"
```

This keeps only previewed user and agent messages with timestamps and transcript line references, skipping session metadata and large event payloads. Use it as an orientation step, not as a replacement for evidence review: still inspect relevant tool outputs, changed files, git state, tests, and artifacts before continuing work.

## Resume Notes

- If the user says the prior session was from Claude Code and Codex is only the current runtime, use the Claude Code adapter for transcript discovery.
- Codex work often includes compacted context. Treat summaries as useful but incomplete until checked against changed files, tests, and git state.
- Codex work can fork into worker or sub-agent sessions. Detect child sessions by `parent_session_id`, shared thread IDs, worker metadata, nearby timestamps, matching cwd, or messages that mention delegated/background work. Review the parent and relevant child transcripts as one evidence set, but keep their source references separate.
- Do not overwrite user edits in a dirty worktree while trying to recreate prior work.
