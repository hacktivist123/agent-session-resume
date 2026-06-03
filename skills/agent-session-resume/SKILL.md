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
   - For large transcripts, first build an inventory of files, event types, timestamps, sidecars, and candidate evidence; then read the evidence-bearing slices until the complete record has been accounted for.
   - Include user messages, assistant messages, tool calls, tool outputs, summaries, plans, and artifacts that explain decisions.
   - Full coverage means no relevant evidence was skipped. It does not require pasting giant transcript records, raw metadata, or entire tool-output files into context when a bounded search or slice captures the evidence.
   - If a large output is summarized instead of fully loaded, say so in the resume report and identify the file/event searched.
   - Do not edit files, run fix commands, or repeat prior work before this pass is complete.

4. Record skill provenance.
   - Name the loaded skill file path in the checkpoint when the runtime exposes it, for example a `skills/agent-session-resume/SKILL.md` path. If the runtime does not expose the loaded path, write `unknown`.
   - Name a source/version marker when available: plugin manifest version, marketplace package version, git tag or commit, package source, or checksum from the loaded skill file. If none is available, write `unknown`.
   - Do not infer the active skill version from an unrelated repository checkout, local clone, docs page, or install command. Label those as candidate sources unless you can prove they are the loaded artifact.
   - When comparing Codex and Claude behavior, compare the known install paths and reported source/version markers from each runtime. Common standalone paths are `${CODEX_HOME:-$HOME/.codex}/skills/agent-session-resume/SKILL.md` for Codex and `$HOME/.claude/skills/agent-session-resume/SKILL.md` for Claude Code. Claude Code plugin installs may expose a plugin-managed path or only the plugin manifest/version.
   - After updating installed skill files, assume an already-running agent may still be using the previous loaded instructions until the app, CLI, plugin, or session is restarted or reloaded.

5. Reconstruct context.
   - Summarize the session goal.
   - List important decisions, constraints, style choices, and user preferences.
   - Identify completed work, changed files, commands run, tests run, and verification results.
   - Identify the exact stopping point, including the last command, edit, failure, or pending instruction.
   - Attach evidence references to claims about work state. Prefer `path/to/file.ext:L10-L20` for files, transcript line numbers for session records, command names plus transcript/tool-output lines for verification, and explicit "not found" or "not checked yet" notes when evidence is missing.
   - Treat prior resume reports, summaries, and handoffs as orientation aids and claims, not primary evidence. Re-verify their task status claims against transcript events, repo files, git status, GitHub state, command output, fixtures, or other primary sources before relying on them.
   - If a prior-report claim cannot be checked against a primary source, label it as unverified instead of presenting it as fact.
   - Preserve explicit user deferrals such as "skip", "park", "leave out", "not now", "later", "hold", or "out of scope" with evidence, the deferred scope, and any condition for reopening it.

6. Extract tasks.
   - Capture explicit TODOs, checklists, plans, and open questions.
   - Infer implicit tasks from failing tests, unfinished edits, "next step" language, and partially applied changes.
   - Classify concrete action items separately; do not replace a specific unfinished task with a broad category.
   - Track explicitly deferred or parked work separately from ordinary `NOT DONE` work. Do not reintroduce deferred scope just because the user says "proceed", "continue", or another vague go-ahead; ask for confirmation unless the user clearly names the parked scope or its reopening condition has been met.
   - Classify each item as:
     - `DONE`: completed and verified, or clearly no longer needed.
     - `PARTIALLY DONE`: started but missing implementation, tests, review, commit, push, or user confirmation.
     - `NOT DONE`: not started or only discussed.

7. Validate against the workspace.
   - Inspect git status before editing and mention the result in the checkpoint.
   - Read files touched or discussed in the prior session.
   - Preserve unrelated user changes.
   - If the worktree is dirty before you start, identify likely pre-existing changes, keep them out of unrelated commits, and do not overwrite, reset, revert, or stage them unless the user explicitly asks. If checkout, merge, or branch work would collide with dirty files, use a separate worktree or ask before proceeding.
   - If transcript claims conflict with the current files, trust current files for implementation state and report the discrepancy in the mismatch format below.

8. Continue from the first unfinished step.
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
- Cursor: read `references/cursor.md`.
- Antigravity: read `references/antigravity.md`.
- OpenCode: read `references/opencode.md`.

## Required Response Shape

Before continuing execution, report:

```markdown
## Brief context summary

- Goal: <prior session goal>
- Loaded skill: path=<loaded SKILL.md path or "unknown">; source/version=<plugin version, package source, git commit/tag/checksum, or "unknown">
- Source reviewed: <transcript/export/artifact refs>
- Current workspace check: <git status summary and touched-file refs, or why not checked>
- Transcript/current repo mismatches: none found
  - Or: <claim> - transcript: <ref>; current repo: <ref>; action: <trust current repo / ask / inspect next>
- User deferrals: none found
  - Or: <deferred scope> - user said <skip/park/leave out/not now/etc.>; evidence: <ref>; reopen condition: <explicit condition or "requires confirmation">
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
- The loaded skill path and source/version marker may be `unknown`, but must not be guessed. If only a candidate install path is known, say `unknown` for the loaded path and mention the candidate path separately.
- User deferrals require evidence from the transcript, handoff, or active prompt. Preserve the deferred scope even when the rest of the work is ready to continue.
- Use compact, stable references so a person or script can trace the claim: `session.jsonl:L4`, `handoff.md:L7-L10`, `src/file.ts:L20-L35`, or `git status --short --branch`.
- Prior resume reports can help route the investigation, but they do not prove task state by themselves. Cite the primary evidence that verifies the claim, or mark the claim unverified when primary evidence is unavailable.

## Static Idempotency Contract

- For static sources, repeated resumes over the same unchanged transcript, artifacts, and workspace should converge on the same task status breakdown and next-action class.
- Exact wording may vary, but evidence references, task classifications, mismatch handling, and whether the next action is blocked or actionable should remain stable.
- Static idempotency does not apply to live or active transcripts, changing repositories, remote GitHub state, running commands, or other sources that may drift between runs.

## Guardrails

- Never assume the newest file is the right transcript if the user supplied a title or path.
- Never summarize from filenames alone.
- Never reset, revert, or discard existing changes unless the user explicitly asks.
- Never treat a compact summary as equivalent to the full transcript when a full transcript is available.
- Never mark a task `DONE` only because it was planned.
- Never mark a task `PARTIALLY DONE` only because it appeared in a plan; there must be evidence work started.
- Never omit transcript/current-repo mismatches when the transcript and checked files disagree.
- Never unpark explicitly deferred scope from a vague prompt such as "Proceed" or "continue"; confirm the user wants that parked work reopened.
