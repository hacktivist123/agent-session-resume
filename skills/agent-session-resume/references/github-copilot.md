# GitHub Copilot Adapter

Use this adapter when the prior session came from GitHub Copilot Chat in VS Code (or VS Code Insiders), or when the user points to Copilot chat history or an exported Copilot chat.

## Discovery

GitHub Copilot Chat stores conversations per workspace inside the VS Code user-data directory, not in the project tree. Each workspace maps to a hash-named folder under `workspaceStorage`:

- macOS: `~/Library/Application Support/Code/User/workspaceStorage/<hash>/`
- Linux: `~/.config/Code/User/workspaceStorage/<hash>/`
- Windows: `%APPDATA%\Code\User\workspaceStorage\<hash>\`

For VS Code Insiders, replace `Code` with `Code - Insiders`. Forks such as Cursor or VSCodium use their own product directory (for example `~/Library/Application Support/Cursor/User/...`); only treat those as GitHub Copilot sources when the user confirms Copilot Chat ran there. For Cursor's own Agent/Composer chat, use `references/cursor.md` instead — Cursor stores that in `state.vscdb`, not in VS Code's `chatSessions/`.

Inside each `<hash>` folder, the relevant entries are:

- `workspace.json` — records the project this hash represents, as a `folder` URI such as `file:///Users/you/project`. Use it to find the hash that matches the current workspace before reading any chat file.
- `GitHub.copilot-chat/transcripts/<session-id>.jsonl` — the Copilot Chat extension's own transcript: a line-delimited event stream. This is the most readable source; prefer it when present.
- `chatSessions/<session-id>.jsonl` — VS Code's core chat-model serialization for the same sessions. Useful as a session-id locator; the body is a versioned `{kind, v}` record stream that is harder to parse (see Reading).
- `chatEditingSessions/<session-id>/` — edit-mode (Edits/agent) working state per session.
- `state.vscdb` (plus `state.vscdb.backup`) — SQLite metadata and the session index.

Note these are `.jsonl` files, not `.json`.

Match the workspace by path, not by recency. The hash is derived from the folder path and its creation time, so one project can map to several hashes and old chats can be orphaned in a stale hash. Check `workspace.json` in each candidate before trusting a recent modification time.

Find the hash for the current workspace:

```bash
storage="$HOME/Library/Application Support/Code/User/workspaceStorage"   # macOS
# Linux:    storage="$HOME/.config/Code/User/workspaceStorage"
# Insiders: replace "Code" with "Code - Insiders"
grep -rl "$(pwd)" "$storage"/*/workspace.json 2>/dev/null
```

List the transcripts for the matching hash, newest first:

```bash
ls -t "$storage/<hash>/GitHub.copilot-chat/transcripts/"*.jsonl 2>/dev/null
# VS Code core chat-model copies (same session ids):
ls -t "$storage/<hash>/chatSessions/"*.jsonl 2>/dev/null
```

If `workspace.json` does not point at the current cwd, do not assume there is no prior session; the project may have been re-hashed. Fall back to searching transcript contents for the project path or topic:

```bash
grep -rl "<file-or-topic-pattern>" \
  "$storage"/*/GitHub.copilot-chat/transcripts/*.jsonl \
  "$storage"/*/chatSessions/*.jsonl 2>/dev/null
```

Treat `workspace.json` and `state.vscdb` as routing context, not as transcript evidence. Do not dump `state.vscdb`; read a single key or fall back to the JSONL transcripts for task state.

## Reading

Prefer the extension transcript `GitHub.copilot-chat/transcripts/<id>.jsonl`. It is true JSON Lines — one event object per line, each shaped like `{type, data, id, parentId, timestamp}`. Read events in order and key off `type`:

- `session.start` — `data` carries provenance: `copilotVersion`, `vscodeVersion`, `sessionId`, `startTime`. Useful as source/version markers in the checkpoint.
- `user.message` — `data.content` is the user prompt; `data.attachments` lists referenced files/context.
- `assistant.message` — `data.content` is the assistant reply; `data.toolRequests` lists tool calls; `data.reasoningText` is optional thinking.
- `assistant.turn_start` / `assistant.turn_end` — turn boundaries.
- `tool.execution_start` — `data.toolName`, `data.arguments`, `data.toolCallId`; `tool.execution_complete` carries the result.

Skim the conversation without dumping tool noise:

```bash
jq -r '
  select(.type == "user.message" or .type == "assistant.message")
  | (.type | ascii_upcase) + ": " + ((.data.content // "") | tostring | .[0:800])
' "$transcript"
```

List the tools the session ran (names only):

```bash
jq -r 'select(.type == "tool.execution_start") | .data.toolName' "$transcript" | sort | uniq -c
```

Capture the user requests, assistant responses, referenced files (`user.message` attachments), tool executions, and the final turn. Do not stop at the first plan or TODO list; continue to the last event so later corrections and completed work are not missed.

If only the core `chatSessions/<id>.jsonl` file exists (no extension transcript), it is a stream of `{kind, v}` records, not a flat array. The full session object lives in the `kind == 0` record under `.v`, with fields such as `requests`, `responderUsername`, and `sessionId`:

```bash
jq -r 'select(.kind == 0) | .v
  | (.requests // [])[]
  | "USER: " + ((.message.text // "") | tostring),
    "ASSISTANT: " + ([.response[]? | .value? // empty] | map(select(type == "string")) | join(" ") | .[0:800])
' "$session"
```

This core format changes between VS Code versions and some records are placeholders, so treat it as a fallback to the extension transcript.

Copilot Chat can also be exported through the built-in `Chat: Export Chat...` command. When the user supplies an exported chat file or pasted transcript, treat that as the session source and skip the `workspaceStorage` discovery.

The stopping point should come from the final meaningful turn, not the first plan. Capture:

- the last `user.message` instruction
- the last `assistant.message` after it
- any final `tool.execution_complete`, applied edit, or error that explains a blocker
- whether the session ends in a completed answer, an unanswered question, a failed command, or a pending next step

## Resume Notes

- Prefer `GitHub.copilot-chat/transcripts/<id>.jsonl` (clean event stream) over the `chatSessions/<id>.jsonl` core serialization; not every session has an extension transcript, so fall back when it is absent.
- A recent transcript timestamp proves chat freshness only, not repository freshness. Compare chat freshness and repo freshness separately, and confirm task state against current files and `git status`.
- A single project can own several hashes; reconcile them as one evidence set but keep source references (hash plus session id) separate in the report.
- `workspace.json` and `state.vscdb` are routing/config context, not proof that implementation or verification happened.
- Copilot inline-completion history (ghost text) is not stored as chat; only Copilot Chat and Edits sessions are recoverable here. Classify task status from the transcript plus the current workspace.

Reference: VS Code stores GitHub Copilot Chat under `User/workspaceStorage/<hash>/`, with `workspace.json` mapping the hash to a project folder, the Copilot extension transcript at `GitHub.copilot-chat/transcripts/<id>.jsonl`, and VS Code's core chat model at `chatSessions/<id>.jsonl`: https://github.com/orgs/community/discussions/129888
