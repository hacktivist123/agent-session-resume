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

## Window the Ask

Time-bounded asks ("past week", "since Monday", "before yesterday") map to the lister's `--since` / `--until` flags, which accept relative windows (`7d`, `12h`) or ISO dates/datetimes. Pass the same window to every runtime so the merged timeline covers one consistent span:

```bash
python3 scripts/session-candidates.py --platform claude-code --since 7d --until 1d --format tsv
python3 scripts/session-candidates.py --platform codex --since 7d --until 1d --format tsv
```

## Normalize Timestamps

Runtimes mix ISO-8601 strings (often with fractional seconds), local times, and file mtimes. Convert every candidate's time to UTC epoch seconds before comparing across runtimes. Do not reach for BSD `date -j -f`: on real Codex index timestamps such as `2026-06-09T14:03:11.482931Z` it emits "Ignoring 8 extraneous characters" and parses the wrong instant. Use a python3 one-liner that handles fractional-ISO and plain-ISO alike:

```bash
# ISO-8601 (fractional or plain, Z or numeric offset) -> epoch seconds
python3 -c 'import sys,datetime as dt; print(int(dt.datetime.fromisoformat(sys.argv[1].replace("Z","+00:00")).timestamp()))' '2026-06-09T14:03:11.482931Z'
# file mtime -> epoch
stat -f '%m' "$transcript" 2>/dev/null || stat -c '%Y' "$transcript"
```

The same one-liner accepts both platforms' lister output: `session-candidates.py` emits `updated_at` normalized to ISO-8601 UTC with seconds precision (e.g. `2026-06-10T00:15:30Z`) for claude-code and codex alike, so lister rows can also be compared or sorted as plain strings.

Never rank candidates from mixed-format timestamp strings.

## Build One Merged Timeline

Merge the per-runtime candidate lists into a single timeline keyed by (cwd match, time window). Concretely, with two lister TSVs:

```bash
python3 scripts/session-candidates.py --platform claude-code --since 7d --format tsv > /tmp/claude.tsv
python3 scripts/session-candidates.py --platform codex --since 7d --format tsv > /tmp/codex.tsv

# Drop headers, merge, sort chronologically. updated_at (column 3) is normalized
# ISO-8601 UTC on both platforms, so a plain string sort is a time sort.
tail -n +2 /tmp/claude.tsv > /tmp/merged-sessions.tsv
tail -n +2 /tmp/codex.tsv >> /tmp/merged-sessions.tsv
sort -t $'\t' -k3,3 /tmp/merged-sessions.tsv | column -t -s $'\t'
```

When iterating rows, never name a loop variable `path`: in zsh, `read ... path` assigns the tied `$path` array and clobbers `$PATH`, breaking every later command lookup in the shell. Use `transcript` (or similar) instead:

```bash
while IFS=$'\t' read -r score runtime updated source cwd title transcript; do
  printf '%s\t%s\t%s\t%s\n' "$updated" "$runtime" "$cwd" "$transcript"
done < /tmp/merged-sessions.tsv | sort -t $'\t' -k1,1
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
