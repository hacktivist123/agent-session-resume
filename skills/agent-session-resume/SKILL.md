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
   - Attach evidence references to claims about work state. Prefer `path/to/file.ext:L10-L20` for files, transcript line numbers for session records, command names plus transcript/tool-output lines for verification, and explicit "not found" or "not checked yet" notes when evidence is missing.

5. Extract tasks.
   - Capture explicit TODOs, checklists, plans, and open questions.
   - Infer implicit tasks from failing tests, unfinished edits, "next step" language, and partially applied changes.
   - Classify concrete action items separately; do not replace a specific unfinished task with a broad category.
   - Classify each item as:
     - `DONE`: completed and verified, or clearly no longer needed.
     - `PARTIALLY DONE`: started but missing implementation, tests, review, commit, push, or user confirmation.
     - `NOT DONE`: not started or only discussed.

6. Validate against the workspace.
   - Inspect git status before editing and mention the result in the checkpoint.
   - Read files touched or discussed in the prior session.
   - Preserve unrelated user changes.
   - If the worktree is dirty before you start, identify likely pre-existing changes, keep them out of unrelated commits, and do not overwrite, reset, revert, or stage them unless the user explicitly asks. If checkout, merge, or branch work would collide with dirty files, use a separate worktree or ask before proceeding.
   - If transcript claims conflict with the current files, trust current files for implementation state and report the discrepancy in the mismatch format below.

7. Continue from the first unfinished step.
   - Do not repeat completed work.
   - Follow the established approach, style, naming, and decisions unless they are clearly broken.
   - If context is missing, inspect related files and logs.
   - Ask the user only when progress is blocked by missing information or an unsafe choice.

## Resume Modes

Use the user's prompt to decide how far to go after the checkpoint:

- `Report-only`: If the user asks what happened, where the prior session left off, what is done versus pending, or asks to check a previous session without asking for edits, stop after the required resume report and clear next action.
- `Continue-edit`: If the user asks to continue, resume, fix, implement, open a PR, run tests, or otherwise act on the unfinished work, provide the required resume report first, then continue from the first unfinished safe step.
- `Quick resume`: Use when the user asks for a status report, latest stopping point, or task breakdown. Prefer a compact source inventory, task classification, and next action.
- `Deep resume`: Use when the user asks to continue implementation, when the source is ambiguous, or when current files may have drifted. Read the full available record, inspect current git state and relevant files, then continue.

## Platform References

- Claude Code: read `references/claude-code.md`.
- Codex: read `references/codex.md`.
- Antigravity: read `references/antigravity.md`.
- OpenCode: read `references/opencode.md`.

## Required Response Shape

Before continuing execution, report:

```markdown
## Brief context summary

- Goal: <prior session goal>
- Source reviewed: <transcript/export/artifact refs>
- Current workspace check: <git status summary and touched-file refs, or why not checked>
- Transcript/current repo mismatches: none found
  - Or: <claim> - transcript: <ref>; current repo: <ref>; action: <trust current repo / ask / inspect next>
- Stopping point: <last command, edit, failure, or user pause instruction with evidence>

## Task status breakdown

- DONE: <specific completed task> - evidence: <implementation refs>; verification: <test/tool refs or "not recorded">.
- PARTIALLY DONE: <specific started task> - evidence: <started-work refs>; missing: <remaining gap refs>.
- NOT DONE: <specific unstarted task> - evidence: <TODO, failing test, absent artifact, or transcript gap refs>.

## Clear next action

- Next: <first unfinished step to take now>
- Blocked: <no | yes - reason and evidence>
```

Then continue immediately unless blocked.

## Evidence Rules

- Every task status line must include `evidence:` with at least one concrete source reference.
- `DONE` requires evidence of completion, not just a plan or intention.
- `PARTIALLY DONE` requires evidence that work started plus the missing completion or verification.
- `NOT DONE` requires evidence from an explicit TODO, failing command, missing artifact, or transcript gap.
- If current-repo verification has not happened yet, say so plainly instead of implying the transcript is current.
- Use compact, stable references so a person or script can trace the claim: `session.jsonl:L4`, `handoff.md:L7-L10`, `src/file.ts:L20-L35`, or `git status --short --branch`.

## Guardrails

- Never assume the newest file is the right transcript if the user supplied a title or path.
- Never summarize from filenames alone.
- Never reset, revert, or discard existing changes unless the user explicitly asks.
- Never treat a compact summary as equivalent to the full transcript when a full transcript is available.
- Never mark a task `DONE` only because it was planned.
- Never mark a task `PARTIALLY DONE` only because it appeared in a plan; there must be evidence work started.
- Never omit transcript/current-repo mismatches when the transcript and checked files disagree.
