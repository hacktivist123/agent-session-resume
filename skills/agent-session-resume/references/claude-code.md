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

Common useful formats include JSONL transcripts, Markdown exports, text exports, and metadata files. If a session name is provided, search contents and metadata before sorting by time:

```bash
rg -i "<session name>" .claude ~/.claude 2>/dev/null
```

If no title is provided, sort candidate files by modified time and inspect the most recent relevant transcript first.

## Reading

For JSONL transcripts, read entries in order. Capture user messages, assistant responses, tool calls, tool results, system reminders, compaction summaries, and any error output that explains the stopping point.

Do not stop at the first TODO list. Continue through the end of the transcript so later changes, corrections, or completed tasks are not missed.

## Resume Notes

- Prefer `.claude/` inside the current project over global Claude history.
- If both a transcript and `.meta.json` exist, use metadata for title and timing, but use the transcript for task state.
- Claude Code sessions often include plans and tool output; classify task status from what actually happened, not from the plan text alone.
