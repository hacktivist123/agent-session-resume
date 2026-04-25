---
name: agent-session-resume
description: Use when continuing work from a previous AI coding-agent session, handoff transcript, chat log, exported conversation, saved artifact set, or session summary.
---

# Agent Session Resume

## Purpose

Resume prior coding-agent work with continuity. The agent must reconstruct what happened before acting, then continue from the real stopping point.

## Core Workflow

1. Identify the source.
   - If the user names a platform, read the matching file in `references/`.
   - If no platform is named, inspect the workspace for session folders, exports, summaries, and artifacts.
   - If a session title or name is provided, prefer exact or fuzzy title matches over recency.

2. Locate the transcript or best available substitute.
   - Prefer a full transcript over summaries.
   - Prefer workspace-local session data over global history when both are plausible.
   - Prefer explicit user-provided paths over discovered paths.

3. Read the full available session record before taking action.
   - For large transcripts, read in chunks until the complete record has been reviewed.
   - Include user messages, assistant messages, tool calls, tool outputs, summaries, plans, and artifacts that explain decisions.
   - Do not edit files, run fix commands, or repeat prior work before this pass is complete.

4. Reconstruct context.
   - Summarize the session goal.
   - List important decisions, constraints, style choices, and user preferences.
   - Identify completed work, changed files, commands run, tests run, and verification results.
   - Identify the exact stopping point, including the last command, edit, failure, or pending instruction.

5. Extract tasks.
   - Capture explicit TODOs, checklists, plans, and open questions.
   - Infer implicit tasks from failing tests, unfinished edits, "next step" language, and partially applied changes.
   - Classify concrete action items separately; do not replace a specific unfinished task with a broad category.
   - Classify each item as:
     - `DONE`: completed and verified, or clearly no longer needed.
     - `PARTIALLY DONE`: started but missing implementation, tests, review, commit, push, or user confirmation.
     - `NOT DONE`: not started or only discussed.

6. Validate against the workspace.
   - Inspect git status before editing.
   - Read files touched or discussed in the prior session.
   - Preserve unrelated user changes.
   - If transcript claims conflict with the current files, trust current files for implementation state and note the discrepancy.

7. Continue from the first unfinished step.
   - Do not repeat completed work.
   - Follow the established approach, style, naming, and decisions unless they are clearly broken.
   - If context is missing, inspect related files and logs.
   - Ask the user only when progress is blocked by missing information or an unsafe choice.

## Platform References

- Claude Code: read `references/claude-code.md`.
- Codex: read `references/codex.md`.
- Antigravity: read `references/antigravity.md`.
- OpenCode: read `references/opencode.md`.

## Required Response Shape

Before continuing execution, report:

```text
Brief context summary
Task status breakdown
Clear next action
```

Then continue immediately unless blocked.

## Guardrails

- Never assume the newest file is the right transcript if the user supplied a title or path.
- Never summarize from filenames alone.
- Never reset, revert, or discard existing changes unless the user explicitly asks.
- Never treat a compact summary as equivalent to the full transcript when a full transcript is available.
- Never mark a task `DONE` only because it was planned.
- Never mark a task `PARTIALLY DONE` only because it appeared in a plan; there must be evidence work started.
