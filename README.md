# agent-session-resume

`agent-session-resume` is a reusable skill for continuing work from a prior AI coding-agent session without losing context, duplicating completed work, or overwriting unrelated changes.

It is designed for handoffs between tools such as Claude Code, Codex, Antigravity, and OpenCode.

## What It Does

The skill gives an agent a disciplined resume workflow:

- locate the most relevant prior transcript, export, artifact, or session summary
- read the full available context before taking action
- reconstruct the original goal, completed work, decisions, and stopping point
- extract explicit and implicit tasks
- classify each task as `DONE`, `PARTIALLY DONE`, or `NOT DONE`
- continue from the first unfinished step without repeating completed work

## Repository Layout

```text
skills/
  agent-session-resume/
    SKILL.md
    agents/
      openai.yaml
    references/
      antigravity.md
      claude-code.md
      codex.md
      opencode.md
```

## Install

Copy `skills/agent-session-resume` into the skill directory used by your agent runtime.

For agents that do not support skill folders directly, use `SKILL.md` as the main instruction document and load the relevant platform file from `references/`.

## Usage

Example prompt:

```text
Use agent-session-resume to continue the previous session. The prior transcript is in .claude/.
Read the full transcript first, summarize the goal and task status, then resume from the last unfinished step.
```

## License

MIT
