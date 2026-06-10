# Cursor Adapter

Use this adapter when resuming work from Cursor, a Cursor Agent chat export, a Cursor Background Agent handoff, or Cursor project-local artifacts.

If the prior work was GitHub Copilot Chat running in stock VS Code rather than Cursor's own Agent/Composer chat, use `references/github-copilot.md` instead. Cursor is a VS Code fork, so it shares the `workspaceStorage/<hash>/workspace.json` mapping, but it stores its native chat in `state.vscdb`, not in VS Code's `chatSessions/*.json`.

## Source Priority

Cursor has both documented handoff surfaces and local application state. Prefer stable, explicit sources before inspecting local internals:

1. User-provided Cursor Agent Markdown export.
2. Project-local handoff, transcript, summary, or artifact files.
3. Project-local Cursor context such as `.cursor/rules`, `.cursor/commands`, `AGENTS.md`, and `.cursorrules`.
4. Observed local project roots such as `~/.cursor/projects/<path-encoded-project>/`.
5. Workspace storage metadata under `~/Library/Application Support/Cursor/User/workspaceStorage/`.
6. Global Cursor app storage only as a last resort, and only when the user has made it accessible and explicitly wants local storage inspection.

Do not treat undocumented Cursor databases as the default transcript API. Cursor's documented preservation path is exporting chats as Markdown.

## Discovery

Inspect the current workspace for explicit exports and handoffs first:

```bash
find . -maxdepth 5 -type f \( \
  -iname '*cursor*' -o \
  -iname '*session*' -o \
  -iname '*transcript*' -o \
  -iname '*handoff*' -o \
  -iname '*summary*' \
\) 2>/dev/null
```

Cursor project context can explain the prior agent's behavior, but it does not prove task completion. Inventory it separately from transcript evidence:

```bash
find . -maxdepth 4 -type f \( \
  -path '*/.cursor/rules/*' -o \
  -path '*/.cursor/commands/*' -o \
  -name 'AGENTS.md' -o \
  -name '.cursorrules' \
\) 2>/dev/null
```

If no export is present and the user asks for a local Cursor session, inspect project-scoped Cursor roots before broad app storage. Cursor commonly uses path-encoded project directories under `~/.cursor/projects`:

```bash
cwd="$(pwd)"
encoded="${cwd#/}"
encoded="${encoded//\//-}"
project_dir="$HOME/.cursor/projects/$encoded"
find "$project_dir" -maxdepth 3 -type f 2>/dev/null
```

Observed project-scoped folders can include:

- `agent-transcripts/` - possible transcript artifacts when present.
- `terminals/` - terminal output artifacts; inspect only relevant bounded slices.
- `rules/` - project-specific Cursor rules.
- `mcps/` and `mcp-cache.json` - tool/server context, not task-completion evidence.
- `assets/` and `agent-tools/` - supporting artifacts.

If the path-encoded project directory is missing or inconclusive, map Cursor workspace storage back to the current project by reading only `workspace.json` files:

```bash
find "$HOME/Library/Application Support/Cursor/User/workspaceStorage" \
  -maxdepth 2 -name 'workspace.json' 2>/dev/null
```

Search these small mapping files for the current path, then consider the matching workspace folder. Do not scan every `state.vscdb` body.

## Official Export Reading

Cursor Agent exports are Markdown files. Treat an export as transcript evidence when it contains chronological user/assistant messages, file references, code blocks, commands, tool output, task summaries, or stopping-point instructions.

Read the export in order. Capture:

- original user request
- assistant plan and decisions
- files referenced or changed
- commands and results
- explicit TODOs, blockers, and "stop here" instructions
- final user prompt and final assistant response

Cursor export docs say exports include messages/responses, code blocks, file references/context, and chronological conversation flow. Still verify claims against current files and `git status` before editing.

## Safe Reading

Cursor exports and project-scoped artifacts can be large. Check size before reading any candidate body:

```bash
wc -lc path/to/export.md
```

Peek structure and evidence cues before reading bodies, then read only the slices that carry evidence:

```bash
rg -n "^#|^##|TODO|error|failed|stop here" path/to/export.md
sed -n '40,120p' path/to/export.md
```

Rank candidates by strongest signal before opening anything: explicit user-supplied path first, then exact cwd/workspace match, then title match, with recency only as a tie-breaker (see Candidate Ranking below). Do not read whole files to decide between candidates.

If a JSONL transcript surfaces (for example under `~/.cursor/projects/<project>/agent-transcripts/`, or a handoff produced by another agent), project it with the packaged scripts from the skill's `scripts/` directory (next to `SKILL.md`) instead of dumping raw lines:

```bash
python3 "$skill_dir/scripts/session-events.py" path/to/transcript.jsonl --limit 200
python3 "$skill_dir/scripts/session-digest.py" path/to/transcript.jsonl
```

For `terminals/` and other artifact folders, slice bounded ranges with `rg -n` plus `sed -n` rather than reading entire outputs.

## Local Storage Safety

Cursor chat history may be stored locally in SQLite, while Background Agent chats are not part of normal history and may be remote. Local storage formats can be large and unstable.

If the user explicitly asks to inspect local storage:

1. Count candidate files before opening them.
2. Prefer `workspace.json` mappings and directory inventories.
3. For SQLite files such as `state.vscdb`, inspect table names, key names, and value sizes before reading values.
4. Read values only after narrowing to a likely session and only when the user has requested local-storage inspection.
5. Treat database-derived content as sensitive. Redact secrets and private data in reports and fixtures.

Useful metadata-only checks:

```bash
sqlite3 path/to/state.vscdb '.tables'
sqlite3 path/to/state.vscdb 'select key, length(value) from ItemTable order by key limit 80;'
```

Keys such as `composer.composerData`, `aiService.prompts`, `aiService.generations`, `workbench.backgroundComposer.workspacePersistentData`, `interactive.sessions`, and terminal buffer state are routing clues, not guaranteed transcript schema.

Avoid global storage by default. It can be very large, noisy, locked, or unavailable, and it is more likely to include unrelated projects.

## Background Agents

If the prior work came from Cursor Background Agents, do not expect it in normal Cursor chat history. Prefer:

- the branch or PR produced by the Background Agent
- the changed files and git history
- exported Background Agent conversation when the user provides it
- project-local artifacts written by the agent

Report when Background Agent chat history is unavailable and ask for an export or explicit path if the transcript is needed.

## Candidate Ranking

When multiple Cursor sources could match, rank by:

1. Explicit export path, handoff path, branch, PR, or Background Agent link supplied by the user.
2. Workspace-local export or handoff whose path/title matches the requested session.
3. Exact current cwd match from a path-encoded `~/.cursor/projects/<project>` directory.
4. Exact `workspace.json` `file://` folder match in Cursor `workspaceStorage`.
5. Title, file, branch, command, or task references inside bounded exports/artifacts.
6. Recency, used only as a tie-breaker among otherwise equal candidates.

Do not let a newer unrelated Cursor workspace outrank an exact cwd or explicit export match.

## Reading

Read the full available Cursor export before continuing. If only local storage clues are available, clearly distinguish:

- facts from a Cursor export or handoff
- facts from current repository files, git history, commands, or tests
- context from Cursor rules, commands, memories, MCP metadata, or terminal artifacts
- inferences from local storage metadata

Do not mark tasks `DONE` from Cursor rules, commands, memories, or MCP metadata. Those are context. Task status requires transcript/export evidence, file evidence, git evidence, command output, test output, or an explicit missing-evidence note.

## Resume Notes

- Prefer Cursor Markdown exports over local database scraping.
- Project rules, commands, memories, and `AGENTS.md` shape behavior but are not task-completion evidence.
- Background Agent evidence may be in a remote UI, branch, PR, or export rather than normal local history.
- If no transcript/export is available, produce a report saying what was inspected and what explicit export/path is needed before classifying task state.

References:

- Cursor chat export: https://docs.cursor.com/agent/chat/export
- Cursor chat history: https://docs.cursor.com/agent/chat/history
- Cursor rules and `AGENTS.md`: https://docs.cursor.com/en/context
- Cursor commands: https://docs.cursor.com/en/agent/chat/commands
- Cursor memories: https://docs.cursor.com/context/memories
- Cursor Background Agents: https://docs.cursor.com/background-agent
