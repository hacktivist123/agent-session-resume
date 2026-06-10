# Claude Code Adapter

Use this adapter when the prior session came from Claude Code or when the user points to a `.claude/` directory.

Packaged helper scripts live in the skill's `scripts/` directory, next to `SKILL.md`. Resolve them relative to the skill base directory and set `skill_dir` accordingly before using the commands below.

## Discovery

Start in the current workspace:

```bash
find .claude -type f 2>/dev/null
```

Treat workspace `.claude/` configuration as routing context, not as transcript evidence. Files such as `.claude/settings.local.json` can explain permissions or local setup, but they do not prove what happened in a prior session. If workspace `.claude/` contains only configuration, continue to the user-level transcript store.

If the current workspace path is known, derive the likely Claude project directory before broad scans. Claude Code commonly stores project transcripts under a path-encoded directory:

```bash
cwd="$(pwd)"
project_dir="$HOME/.claude/projects/${cwd//\//-}"
find "$project_dir" -maxdepth 2 -type f -name '*.jsonl' 2>/dev/null
```

If that directory does not exist and the user did not provide a path, check known user-level Claude Code history locations only if they are accessible. Prefer bounded transcript locations over `find ~/.claude -type f`:

```bash
find "$HOME/.claude/projects" -maxdepth 2 -type f -name '*.jsonl' 2>/dev/null
find "$HOME/.claude" -maxdepth 1 -type f -name 'history.jsonl' 2>/dev/null
```

Claude Code stores full transcripts, per-session sidecars, and prompt history in different places:

- `~/.claude/projects/<project>/<session>.jsonl`: full conversation transcript with messages, tool calls, and tool results.
- `~/.claude/projects/<project>/<sessionId>/subagents/agent-*.jsonl`: subagent transcripts. When the main transcript delegates work to agents, include these in the evidence set; the main transcript may show only the dispatch and a summary.
- `~/.claude/projects/<project>/<sessionId>/tool-results/*.txt`: large tool outputs spilled to disk. Read these targeted files instead of giant inline transcript lines.
- `~/.claude/history.jsonl`: prompt history used for up-arrow recall, containing prompts with timestamps and project paths.

Use `history.jsonl` as a locator and context supplement, not as a transcript replacement. It can reveal the project path, the user's exact prompts, and nearby session intent even when the matching transcript is hard to identify. When a relevant history entry is used, include the project path or prompt-history clue in the context summary.

Treat Claude Code project transcripts as append logs that may still be active. A recent transcript timestamp or file modification time proves transcript freshness only; it does not prove the repository, branch, dependencies, or generated files are fresh. Compare transcript freshness and repository freshness separately.

Do not treat a `history.jsonl` miss as evidence that no transcript exists. If prompt history does not contain the current cwd or session topic, inspect the cwd-derived `~/.claude/projects/<project>` directory before broadening discovery.

Common useful formats include JSONL transcripts, Markdown exports, text exports, and metadata files.

Raw-grep trap: do not grep `~/.claude/projects/` transcript bodies for a topic, skill name, or tool name as a discovery step. Every transcript embeds the available-skills list, plugin descriptions, and other boilerplate inside `system-reminder` blocks, so a topic-shaped `rg` produces mass false positives. Concrete failure shape: `rg -l "agent-session-resume" ~/.claude/projects/` matches roughly 20 unrelated sessions whose only "mention" of the skill is the skills list injected into every conversation. Project user messages first, then search the projected view:

```bash
python3 "$skill_dir/scripts/session-events.py" "$candidate" | rg "text/user" | rg -i "<session name or topic>"
```

For shortlisting candidates by cwd, topic, or time window without opening bodies, use the packaged lister. Time-bounded asks map to `--since` / `--until`, which accept relative windows (`7d`, `12h`) or ISO dates:

```bash
python3 "$skill_dir/scripts/session-candidates.py" --platform claude-code --cwd "$(pwd)" --topic "<session name>"
python3 "$skill_dir/scripts/session-candidates.py" --platform claude-code --cwd "$(pwd)" --since 7d --until 1d
```

To filter prompt history by the current workspace path:

```bash
rg -F "$(pwd)" ~/.claude/history.jsonl 2>/dev/null
```

Before reading candidate message bodies, project routing metadata from the JSONL:

```bash
jq -r '
  select(.type == "user")
  | [.timestamp, .cwd, .sessionId, .entrypoint, .gitBranch]
  | @tsv
' "$session" | head
```

When multiple Claude project directories or transcripts could match, rank candidates by the strongest signal:

1. Explicit transcript path or session ID supplied by the user.
2. Exact path-encoded project directory for the current cwd.
3. Exact transcript `cwd` match from user events.
4. Parent/child cwd match.
5. Session title, prompt history, or user prompt match.
6. Recency, used only as a tie-breaker.

Do not let prefix siblings outrank an exact cwd match. For example, `~/.claude/projects/-Users-ojima-Desktop-experiments` should outrank `~/.claude/projects/-Users-ojima-Desktop-experiments-trybreak-prototype` when the current cwd is `/Users/ojima/Desktop/experiments`.

If no title is provided, sort candidate files by modified time only after applying the stronger path and metadata signals.

When comparing candidate times, normalize to UTC or epoch seconds before deciding which record is newer. `session-candidates.py` prints every row's `updated_at` normalized to ISO-8601 UTC with seconds precision (e.g. `2026-06-10T00:15:30Z`) on both platforms, so its rows sort chronologically as plain strings, and `session-events.py` prints normalized event timestamps; cross-check against file and repo time:

```bash
stat -f '%m %N' "$session" 2>/dev/null
git log -1 --format='%ct %h %s'
```

If a Deep resume may run for a long time, recheck the chosen transcript tail and `git status --short --branch` before the checkpoint report. If the tail changed while reading, account for the appended events before classifying tasks.

## Reading

For JSONL transcripts, read entries in order. Capture user messages, assistant responses, tool calls, tool results, system reminders, compaction summaries, and any error output that explains the stopping point.

Do not stop at the first TODO list. Continue through the end of the transcript so later changes, corrections, or completed tasks are not missed.

When using `history.jsonl`, read it near the relevant timestamp or project path to recover user intent, but classify task status from the full transcript and current workspace whenever possible.

Use event types to skim before deep reading:

| Event type | Resume use |
|---|---|
| `user` | User prompts, tool results, cwd/session metadata |
| `assistant` | Assistant text responses and tool-use requests |
| `system` | System reminders and compaction context |
| `attachment` | Attached context or artifacts; inspect when relevant |
| `ai-title` | Session title metadata; deduplicate repeated values |
| `queue-operation` | Prompt queue boundaries; usually routing metadata |
| `last-prompt` | Latest prompt/stopping-point clue |

Repeated `ai-title` events should be treated as one title signal per `(sessionId, aiTitle)` pair. Do not count duplicate title rows as progress, task evidence, or user/assistant turns.

For a message-only skim, extract visible user and assistant text plus bounded tool summaries with the packaged projector. It emits one previewed event per line with transcript line references and skips opaque thinking/signature payloads, which add noise and do not normally change task status:

```bash
python3 "$skill_dir/scripts/session-events.py" "$session" --limit 200
```

For a compact reusable summary with evidence cues, build a digest. It writes a persistent `<transcript>.digest.json` sidecar cache and processes only the appended tail on later runs:

```bash
python3 "$skill_dir/scripts/session-digest.py" "$session"
```

Claude Code persists oversized tool results outside the JSONL transcript, under the per-session sidecar directory `~/.claude/projects/<project>/<sessionId>/tool-results/*.txt`. If a tool result contains a placeholder such as `<persisted-output>` or says the full output was saved to `tool-results/<id>.txt`, treat that sidecar as part of the session record. Likewise check `~/.claude/projects/<project>/<sessionId>/subagents/agent-*.jsonl` whenever the main transcript dispatches subagents; project them with `session-events.py` like any other transcript.

Inspect sidecars safely:

```bash
wc -lc path/to/tool-results/<id>.txt
rg -n "error|failed|TODO|not done|next|<file-or-symbol-pattern>" path/to/tool-results/<id>.txt
sed -n '120,180p' path/to/tool-results/<id>.txt
```

Do not read a large sidecar from beginning to end unless it is small enough for the active context. Search for the command, error text, file path, task label, or final summary that explains the resume state. In the resume report, state that the evidence came from a sidecar file when it did.

For large transcript or tool-output files, use an evidence inventory before deep reading:

1. Count lines and bytes.
2. List JSONL event types or artifact names.
3. Identify user prompts, assistant summaries, tool calls, tool failures, and persisted-output pointers.
4. Search/slice the relevant evidence.
5. Continue to the final transcript event so late corrections or appended turns are not missed.

If the transcript may still be active or was modified during resume, recheck the tail before reporting. Use a bounded projected tail instead of dumping raw JSONL, so the final scan keeps visible messages, tool-use summaries, and tool-result previews while skipping opaque `thinking` or `signature` payloads:

```bash
python3 "$skill_dir/scripts/session-events.py" "$session" | tail -n 40
```

Re-running `session-digest.py` is also cheap here: its `<transcript>.digest.json` sidecar cache means only the appended tail is processed.

The exact stopping point should come from the final meaningful events, not from the first TODO list. Capture:

- the last user prompt or instruction
- the last assistant response after that prompt
- any final tool call or tool result that explains a blocker
- whether the last state is a completed report, an unanswered question, a failed command, or a pending next step

Claude Code work can fork into parallel terminals, sidecar tool outputs, or handoffs to another agent. Detect these by shared session IDs, worker labels in messages, sidecar paths, matching cwd, nearby timestamps, or explicit delegation language. Review the parent transcript and relevant forked streams as one evidence set, but keep source references separate in the report.

## Resume Notes

- Prefer `.claude/` inside the current project over global Claude history.
- If both a transcript and `.meta.json` exist, use metadata for title and timing, but use the transcript for task state.
- Use `~/.claude/history.jsonl` to find prompts, project paths, and likely sessions; do not treat it as evidence that implementation or verification happened.
- Claude Code sessions often include plans and tool output; classify task status from what actually happened, not from the plan text alone.

Reference: Claude Code documents `history.jsonl` as prompt history and `projects/<project>/<session>.jsonl` as full transcripts: https://code.claude.com/docs/en/claude-directory
