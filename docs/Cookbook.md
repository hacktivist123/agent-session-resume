# Cookbook

This cookbook shows practical ways to use `agent-session-resume` with Claude Code, Codex, Cursor, Antigravity, and OpenCode.

The skill's job is to make your prompt small. You name the prior agent/session source; the skill handles transcript discovery, full reading, task classification, and continuing from the true stopping point.

## Expected First Response

Every resume should begin with:

```text
Brief context summary
Loaded skill: path=<loaded SKILL.md path or unknown>; source/version=<marker or unknown>
Task status breakdown
User deferrals
Clear next action
```

Only after that checkpoint should the agent continue implementation.

## Resume Modes

Use report-only mode when the user asks for status, the latest stopping point, or a done/partial/not-done breakdown:

```text
Use agent-session-resume.

Check the last conversation in this folder and tell me where it left off.
```

Use continue-edit mode when the user asks the agent to act after the checkpoint:

```text
Use agent-session-resume.

Continue the previous session and finish the first unfinished task.
```

Use quick resume for a compact status report. Use deep resume when the agent will edit files, when the transcript source is ambiguous, or when the current repo may have drifted since the prior session.

### Deep Resume With Parallel Read-Only Workers

For large or possibly forked sessions, Deep resume may use a small read-only parallel strategy:

```text
Use agent-session-resume.

Deep resume this prior session. You may use up to 3 read-only workers to inspect transcript slices, sidecars, and current files. The coordinator owns the final report and task classification. Do not edit before the checkpoint.
```

Keep the coordinator responsible for candidate selection, source coverage, mismatch handling, and the final `DONE`/`PARTIALLY DONE`/`NOT DONE` classification. Workers should only gather evidence, use compact tables, and report exact source references. If worker setup is unavailable, noisy, or slower than direct inspection, fall back to sequential reading.

When transcript timestamps matter, compare UTC or epoch values and separate transcript freshness from repository freshness. Recheck the transcript tail and `git status --short --branch` before the checkpoint if the resume took long enough for upstream or append-log drift to matter.

## Claude Code

Recommended install is the Claude Code plugin:

```text
/plugin marketplace add hacktivist123/agent-session-resume
/plugin install agent-session-resume@hacktivist123
/reload-plugins
```

Use the namespaced plugin command:

```text
/agent-session-resume:agent-session-resume
```

### Continue The Most Recent Claude Code Session

```text
/agent-session-resume:agent-session-resume

Continue the most recent Claude Code session for this repository.
```

The skill should inspect project-local `.claude/` first, then user-level Claude Code history such as:

```text
~/.claude/projects/<project>/<session>.jsonl
~/.claude/history.jsonl
```

`history.jsonl` is useful as a locator and prompt-history clue, but the full transcript is the source of truth.

### Continue A Named Claude Code Session

```text
/agent-session-resume:agent-session-resume

Continue the Claude Code session titled "Fix checkout retry flow".
```

### Continue From A Specific Claude Transcript

```text
/agent-session-resume:agent-session-resume

Continue from ~/.claude/projects/<project>/<session>.jsonl.
```

## Codex

For Codex, the short prompt should be enough:

```text
Use $agent-session-resume.

Continue the most recent Codex session for this repository.
```

Codex transcripts are usually stored in the user-level Codex home, not in each repository:

```text
${CODEX_HOME:-$HOME/.codex}/session_index.jsonl
${CODEX_HOME:-$HOME/.codex}/sessions/YYYY/MM/DD/*.jsonl
${CODEX_HOME:-$HOME/.codex}/archived_sessions/*.jsonl
```

The agent should choose the most recent transcript whose cwd, workdir, repo path, thread name, or mentioned files match the current repository.

### Continue A Codex Session From Claude Code

Start Claude Code with access to Codex's user-level session store:

```bash
claude --add-dir ~/.codex
```

Then prompt:

```text
/agent-session-resume:agent-session-resume

Continue the most recent Codex session for this repository.
```

### Continue From A Codex Handoff File

```text
Use $agent-session-resume.

Continue from ./handoff.md.
```

Best practice: before switching agents, ask Codex to write a short handoff file into the repo.

## Antigravity

Use this when you have Antigravity artifacts such as task lists, plans, walkthroughs, screenshots, recordings, or exported summaries.

```text
Use agent-session-resume.

Continue the Antigravity task from the saved artifacts in this repository.
```

If you know the artifact path:

```text
Use agent-session-resume.

Continue from ./artifacts/antigravity-walkthrough.md and ./artifacts/task-list.md.
```

If the user asks to use local Antigravity data on macOS, inspect readable artifacts before private application state:

```bash
find "$HOME/.gemini/antigravity/brain" -maxdepth 2 -type f \( \
  -name '*.metadata.json' -o \
  -name 'task.md' -o \
  -name 'implementation_plan.md' -o \
  -name '*.resolved*' \
\) 2>/dev/null
```

Use metadata summaries and `updatedAt` values to rank candidate conversations, then read the smallest task or implementation-plan artifacts that explain the work. `~/Library/Application Support/Antigravity/User/workspaceStorage/*/workspace.json` can map storage hashes back to project paths. Treat `User/History`, logs, app database keys, browser recordings, binary conversation files, and code tracker snapshots as supporting clues unless the user explicitly points at them.

The agent should prefer an exported transcript when present, but artifact evidence is often enough to reconstruct:

- original user request
- plan
- completed implementation steps
- verification evidence
- review comments
- next unfinished task

## OpenCode

Use exported sessions, share links, summaries, or project-local OpenCode configuration.

```text
Use agent-session-resume.

Continue from this OpenCode session export.
```

If the repo has OpenCode configuration:

```text
Use agent-session-resume.

Continue the most recent OpenCode session for this repository.
```

The agent should inspect:

```text
opencode.json
.opencode/
```

When the `opencode` CLI or SDK is available, the agent should prefer supported session access over scraping private storage.

## Cursor

Prefer Cursor Agent Markdown exports when moving work from Cursor into another agent:

```text
Use agent-session-resume.

Continue from this Cursor Agent chat export.
```

Cursor documents chat export as Markdown with messages, responses, code blocks, file references, and chronological flow. Treat that export as the transcript source, then verify claims against current files, `git status`, commands, and tests before editing.

If no export is present, inspect project-local context before app internals:

```text
.cursor/rules/
.cursor/commands/
AGENTS.md
.cursorrules
```

These files can explain style, workflow, or constraints, but they do not prove task completion.

### Local Cursor Storage

On macOS, Cursor may keep project-scoped and app-scoped state in locations like:

```text
~/.cursor/projects/<path-encoded-project>/
~/Library/Application Support/Cursor/User/workspaceStorage/<hash>/
~/Library/Application Support/Cursor/User/globalStorage/
```

Use these as bounded discovery clues, not as the default transcript source. A safe local traversal is:

1. Check for explicit exports or handoff files in the workspace.
2. Inspect `~/.cursor/projects/<path-encoded-current-cwd>/` for project-scoped artifacts such as `agent-transcripts/`, `terminals/`, `rules/`, `mcp-cache.json`, and assets.
3. Map `workspaceStorage/*/workspace.json` back to the current `file://` project path before considering any `state.vscdb`.
4. If inspecting `state.vscdb`, list table names, keys, and value sizes before reading values.
5. Avoid giant global storage DBs unless the user explicitly asks and there is no better export.

For Cursor Background Agents, normal chat history may not contain the conversation. Prefer the produced branch or PR, changed files, and an exported Background Agent conversation when available.

## Cross-Agent Handoffs

The main pattern is:

1. Install the skill in the receiving agent.
2. Give the receiving agent access to the prior transcript, handoff file, or artifact folder.
3. Use a short resume prompt.
4. Require the checkpoint before edits.

Before switching agents, ask the current agent for a compact handoff instead of pasting a full transcript:

```text
Create a compact handoff for the next coding agent. Include only the goal, completed work, in-progress work, deferred or parked scope, not-done work, changed files, commands run, verification, exact stopping point, and next action. Redact secrets and customer data.
```

### Prove Which Skill Ran

When comparing behavior between Codex and Claude Code, first prove which installed skill each runtime loaded. Ask each agent to report:

- loaded `SKILL.md` path, or `unknown` if the runtime does not expose it
- source/version marker such as plugin manifest version, marketplace version, git commit, tag, package source, or checksum
- candidate install paths checked, clearly labeled as candidates when they are not proven loaded

Common standalone install paths to compare:

```text
${CODEX_HOME:-$HOME/.codex}/skills/agent-session-resume/SKILL.md
$HOME/.claude/skills/agent-session-resume/SKILL.md
```

Claude Code plugin installs may report a plugin-managed loaded path or only the plugin manifest/version. If the path or version cannot be proven, the resume report should say `unknown` instead of inferring from a nearby checkout.

After updating an installed skill, restart the app/CLI or reload the plugin before expecting active sessions to use the new instructions. A running Codex or Claude Code session may keep the previously loaded skill text.

Useful checks when the files are accessible:

```bash
shasum -a 256 "${CODEX_HOME:-$HOME/.codex}/skills/agent-session-resume/SKILL.md"
shasum -a 256 "$HOME/.claude/skills/agent-session-resume/SKILL.md"
```

If a repository checkout is being used as the package source, record its commit too:

```bash
git -C /path/to/agent-session-resume rev-parse HEAD
```

### Preserve Parked Scope

Explicit user deferrals are part of the handoff. Words such as "skip", "park", "leave out", "not now", "later", "hold", or "out of scope" should be carried forward with evidence and an explicit reopen rule.

If the next prompt is vague, such as:

```text
Proceed.
```

the agent should continue only the unparked next action. It should ask before reviving deferred scope unless the user clearly names that scope or the recorded reopen condition has been met.

### Claude Code Continuing Codex

```bash
cd /path/to/project
claude --add-dir ~/.codex
```

```text
/agent-session-resume:agent-session-resume

Continue the most recent Codex session for this repository.
```

### Codex Continuing Claude Code

```text
Use $agent-session-resume.

Continue the most recent Claude Code session for this repository.
```

If Codex cannot access `~/.claude`, provide a project-local handoff or add the Claude history directory to the allowed workspace.

### Any Agent Continuing From A Handoff File

```text
Use agent-session-resume.

Continue from ./handoff.md.
```

## Helper Scripts

The skill package ships small local helpers for discovery and digesting in `skills/agent-session-resume/scripts/`. Because they live inside the skill folder, they are installed alongside `SKILL.md` (for example under `~/.claude/skills/agent-session-resume/scripts/` or `~/.codex/skills/agent-session-resume/scripts/`), so an installed skill can run them instead of re-deriving long jq pipelines. They are python3-stdlib-only, take absolute or relative paths as arguments, and can run from any working directory. They are optional: use them when a transcript store is noisy or a source file is too large to read directly.

In the examples below, `$SKILL_SCRIPTS` is wherever the scripts live: `skills/agent-session-resume/scripts` in this repo, or `<install dir>/agent-session-resume/scripts` for an installed skill.

### Find Candidate Sessions

Use `session-candidates.py` to shortlist likely transcripts before opening transcript bodies.

```bash
python3 "$SKILL_SCRIPTS/session-candidates.py" --platform codex --cwd "$PWD" --format tsv
python3 "$SKILL_SCRIPTS/session-candidates.py" --platform claude-code --cwd "$PWD" --format tsv
```

For Codex, the helper reads `session_index.jsonl` first and resolves candidate IDs to transcript files. For Claude Code, it derives the likely `~/.claude/projects/<project>` directory from the current cwd before falling back to broader project scans.

Use `--topic` when the user gave a title or theme:

```bash
python3 "$SKILL_SCRIPTS/session-candidates.py" --platform codex --cwd "$PWD" --topic "checkout retry"
```

Use `--since` / `--until` to answer time-window asks such as "my Codex threads from the past week" without hand-rolling date enumeration. Both accept an ISO date or datetime (`2026-06-01`, `2026-06-01T12:00:00Z`) or a relative window (`7d`, `12h`, `30m`, `2w`):

```bash
python3 "$SKILL_SCRIPTS/session-candidates.py" --platform codex --since 7d --format tsv
python3 "$SKILL_SCRIPTS/session-candidates.py" --platform claude-code --since 2026-06-01 --until 2026-06-08
```

`--cwd <path>` filters as well as ranks: only sessions whose recorded workspace matches the given path exactly, or as a parent/child directory, are kept. Omit `--cwd` to rank by the current directory without filtering. Filters compose, so "this repo, past week" is:

```bash
python3 "$SKILL_SCRIPTS/session-candidates.py" --platform codex --cwd "$PWD" --since 7d
```

### Create A Compact Evidence Digest

Use `session-digest.py` to produce a bounded orientation digest from transcript, export, handoff, or artifact files:

```bash
python3 "$SKILL_SCRIPTS/session-digest.py" path/to/session.jsonl path/to/handoff.md
```

The digest is an orientation aid, not a replacement for evidence review. After digesting, still inspect the relevant transcript slices, tool outputs, changed files, git state, and verification results before continuing work.

#### Digest Caching

`session-digest.py` caches each digest in a sidecar file named `<transcript>.digest.json` written next to the source file. The sidecar stores the file size, a SHA-256 of the digested bytes, and the last processed byte offset. On rerun:

- unchanged file (size and hash match) - the sidecar is reused wholesale and nothing is re-read beyond the hash check;
- append-only growth (the previously digested prefix is unchanged) - only the appended tail is processed and merged into the cached digest; this incremental behavior is the default for Codex and Claude Code JSONL transcripts;
- prefix changed (rewritten, truncated, or compacted file) - the digest is recomputed from scratch.

Flags:

- `--sidecar-dir <dir>` writes sidecars into a separate directory instead of next to the transcript (useful for read-only stores).
- `--no-sidecar` disables cache reads and writes entirely.
- `--no-incremental` disables append-only tail processing; unchanged files still get whole-sidecar cache hits.

If the transcript directory is not writable, the digest still prints and the sidecar is skipped with a notice on stderr. Cache notices (`cache hit`, `incremental update`, `cache invalidated`) go to stderr so stdout stays a clean digest.

## Benchmarking Improvements

When proposing changes to the skill, adapters, fixtures, or helper scripts, describe the behavior being improved and the benchmark target. Use the standard areas in [Benchmarking](Benchmarking.md), especially session selection, discovery effort, token usage proxy, resume accuracy, evidence quality, safety/redaction, robustness, trigger behavior, and reviewer clarity.

Recommended PR sections:

```markdown
## What this improves

## Benchmark target

| Benchmark area | What we measure | Good result |
| --- | --- | --- |
```

Use deterministic fixture checks for repository consistency, then add agent-in-the-loop notes when a change affects realistic discovery or resume behavior.

## Good Handoff File Template

When leaving one agent and moving to another, ask the first agent to create:

```text
# Handoff

## Goal

## Completed

## In Progress

## Deferred / Parked

## Not Done

## Files Changed

## Commands Run

## Verification

## Exact Stopping Point

## Next Action
```

Keep the headings stable so another agent or validator can check the handoff shape. The repo includes a lightweight validator for this template:

```bash
python3 scripts/validate-handoff.py path/to/handoff.md
```

### Redaction Rules

Cross-agent handoffs should carry task evidence, not private data. Before sharing a handoff or turning it into a fixture:

- Replace API keys, tokens, passwords, cookies, and bearer values with `<redacted>`.
- Replace customer names, emails, IDs, and private URLs with placeholders unless they are essential to the bug.
- Summarize large logs instead of pasting full output.
- For Claude Code sidecars or Codex tool outputs, include the command, result, and relevant error lines rather than raw files.
- Add a short redaction note when sensitive values were removed.

### Minimal Handoff Example

```text
# Handoff

## Goal

Finish checkout retry handling.

## Completed

- Added retry helper in `src/checkout/retry.ts`.
- Focused retry tests pass.

## In Progress

- Webhook replay path still needs inspection.

## Deferred / Parked

- Loyalty discount handling was explicitly parked until the retry bug is fixed.

## Not Done

- Full checkout integration suite has not been run.

## Files Changed

- `src/checkout/retry.ts`
- `tests/checkout-retry.test.ts`

## Commands Run

- `npm test -- tests/checkout-retry.test.ts` passed.

## Verification

- Focused tests passed; integration coverage is still missing.

## Exact Stopping Point

Stopped before checking whether webhook replay should reuse the retry helper.

## Next Action

Inspect webhook replay, reuse the helper if needed, then run the full checkout integration suite.
```

## Common Pitfalls

- Do not resume from a summary when a full transcript is available.
- Do not pick the newest global session if it belongs to another repo.
- Do not mark planned work as `DONE`.
- Do not edit before the checkpoint.
- Do not reinstall both Claude plugin and standalone Claude skill unless you intentionally want duplicate command suggestions.
