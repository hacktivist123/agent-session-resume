# Cookbook

This cookbook shows practical ways to use `agent-session-resume` with Claude Code, Codex, Antigravity, and OpenCode.

The skill's job is to make your prompt small. You name the prior agent/session source; the skill handles transcript discovery, full reading, task classification, and continuing from the true stopping point.

## Expected First Response

Every resume should begin with:

```text
Brief context summary
Task status breakdown
Clear next action
```

Only after that checkpoint should the agent continue implementation.

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

## Cross-Agent Handoffs

The main pattern is:

1. Install the skill in the receiving agent.
2. Give the receiving agent access to the prior transcript, handoff file, or artifact folder.
3. Use a short resume prompt.
4. Require the checkpoint before edits.

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

## Good Handoff File Template

When leaving one agent and moving to another, ask the first agent to create:

```text
# Handoff

## Goal

## Completed

## In Progress

## Not Done

## Files Changed

## Commands Run

## Verification

## Exact Stopping Point

## Next Action
```

## Common Pitfalls

- Do not resume from a summary when a full transcript is available.
- Do not pick the newest global session if it belongs to another repo.
- Do not mark planned work as `DONE`.
- Do not edit before the checkpoint.
- Do not reinstall both Claude plugin and standalone Claude skill unless you intentionally want duplicate command suggestions.

