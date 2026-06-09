# Cross-Platform Resume

Use this workflow when one ask spans multiple agent platforms: "review my threads across Claude and Codex", "what did my agents do on this repo last week", or any resume/audit naming more than one runtime.

## Detect the Span

Treat the ask as cross-platform when the user names two or more runtimes, says "all my agents/sessions/threads", or when discovery for one named platform surfaces a matching session on another runtime for the same repo and time window. State the platform set you are covering in the context summary before reading transcripts.

## Discover Per Platform

Run each platform adapter's discovery independently and completely. Do not let one runtime's results stop or narrow discovery on another.

- Claude Code: `references/claude-code.md`
- Codex: `references/codex.md`
- Cursor: `references/cursor.md`
- Antigravity: `references/antigravity.md`
- OpenCode: `references/opencode.md`

Keep one candidate list per runtime, each entry carrying session ID, transcript path, cwd, title, and updated time.

## Normalize Timestamps

Runtimes mix ISO-8601 strings, local times, and file mtimes. Convert every candidate's time to UTC epoch seconds before comparing across runtimes:

```bash
# ISO-8601 -> epoch (BSD date first, GNU date fallback)
date -j -u -f '%Y-%m-%dT%H:%M:%S' '2026-06-09T14:03:11' +%s 2>/dev/null \
  || date -u -d '2026-06-09T14:03:11' +%s
# file mtime -> epoch
stat -f '%m' "$transcript" 2>/dev/null || stat -c '%Y' "$transcript"
```

Never rank candidates from mixed-format timestamp strings.

## Build One Merged Timeline

Merge the per-runtime candidate lists into a single timeline keyed by (cwd match, time window). One TSV line per session, sorted by epoch:

```bash
# epoch <TAB> runtime <TAB> cwd <TAB> transcript path <TAB> title
sort -n /tmp/merged-sessions.tsv | column -t -s $'\t'
```

Group sessions that share a cwd (or parent/child cwd) into per-repo lanes, then read them in time order. The merged timeline decides reading order; the per-runtime adapters decide how to read each transcript safely.

## Attribute Evidence

Every evidence item names its runtime and transcript path, not just a line number:

- `codex: ~/.codex/sessions/2026/06/09/rollout-<id>.jsonl:L42`
- `claude-code: ~/.claude/projects/<project-slug>/<uuid>.jsonl:L17`

Never cite "the transcript" when more than one runtime is in play.

## Dedupe Overlapping Work

Same repo, overlapping time window, and same files touched usually means one task seen from two runtimes (for example, work started in Claude Code and reviewed or continued in Codex). For each suspected overlap:

1. Compare the touched-file sets and the commands run in both transcripts.
2. If they describe the same task, merge into one task entry, keep both runtimes' evidence refs, and note which runtime carried it furthest.
3. If you cannot confirm they are the same task, keep them as separate entries and flag the possible overlap in the context summary.

Do not double-count merged work in the task status breakdown, and do not let a stale transcript from one runtime downgrade work a later session completed.

## Report

Produce one task-status breakdown (the Required Response Shape in SKILL.md) covering all runtimes:

- `Source reviewed` lists each runtime with its transcript paths.
- Each `DONE` / `PARTIALLY DONE` / `NOT DONE` line cites per-runtime evidence refs.
- Mismatch and deferral lines name the runtime whose transcript carries the evidence.
- The clear next action is a single step, even when the prior work spans runtimes; name the runtime context only if it changes what to do.
