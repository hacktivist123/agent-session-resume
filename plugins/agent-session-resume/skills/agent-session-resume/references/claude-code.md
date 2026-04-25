# Claude Code Adapter

Use this adapter when the prior session came from Claude Code or when the user points to a `.claude/` directory.

## Discovery

Start in the current workspace:

```bash
find .claude -type f 2>/dev/null
```

If no workspace-local transcript exists and the user did not provide a path, check known user-level Claude Code history locations only if they are accessible:

```bash
find ~/.claude -type f 2>/dev/null
```

Claude Code stores full transcripts and prompt history in different places:

- `~/.claude/projects/<project>/<session>.jsonl`: full conversation transcript with messages, tool calls, and tool results.
- `~/.claude/history.jsonl`: prompt history used for up-arrow recall, containing prompts with timestamps and project paths.

Use `history.jsonl` as a locator and context supplement, not as a transcript replacement. It can reveal the project path, the user's exact prompts, and nearby session intent even when the matching transcript is hard to identify. When a relevant history entry is used, include the project path or prompt-history clue in the context summary.

Common useful formats include JSONL transcripts, Markdown exports, text exports, and metadata files. If a session name is provided, search contents and metadata before sorting by time:

```bash
rg -i "<session name>" .claude ~/.claude ~/.claude/history.jsonl 2>/dev/null
```

To filter prompt history by the current workspace path:

```bash
rg -F "$(pwd)" ~/.claude/history.jsonl 2>/dev/null
```

If no title is provided, sort candidate files by modified time and inspect the most recent relevant transcript first.

## Reading

For JSONL transcripts, read entries in order. Capture user messages, assistant responses, tool calls, tool results, system reminders, compaction summaries, and any error output that explains the stopping point.

Do not stop at the first TODO list. Continue through the end of the transcript so later changes, corrections, or completed tasks are not missed.

When using `history.jsonl`, read it near the relevant timestamp or project path to recover user intent, but classify task status from the full transcript and current workspace whenever possible.

## Resume Notes

- Prefer `.claude/` inside the current project over global Claude history.
- If both a transcript and `.meta.json` exist, use metadata for title and timing, but use the transcript for task state.
- Use `~/.claude/history.jsonl` to find prompts, project paths, and likely sessions; do not treat it as evidence that implementation or verification happened.
- Claude Code sessions often include plans and tool output; classify task status from what actually happened, not from the plan text alone.

Reference: Claude Code documents `history.jsonl` as prompt history and `projects/<project>/<session>.jsonl` as full transcripts: https://code.claude.com/docs/en/claude-directory
