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

This repo is distributed as a skill. The installable package is:

```text
skills/agent-session-resume
```

### Codex

Ask Codex to install it:

```text
Install the skill from hacktivist123/agent-session-resume at skills/agent-session-resume
```

Manual install:

```bash
tmp_dir="$(mktemp -d)"
git clone --depth 1 https://github.com/hacktivist123/agent-session-resume "$tmp_dir/agent-session-resume"
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R "$tmp_dir/agent-session-resume/skills/agent-session-resume" "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex after installing.

### Claude Code

Manual install:

```bash
tmp_dir="$(mktemp -d)"
git clone --depth 1 https://github.com/hacktivist123/agent-session-resume "$tmp_dir/agent-session-resume"
mkdir -p "$HOME/.claude/skills"
cp -R "$tmp_dir/agent-session-resume/skills/agent-session-resume" "$HOME/.claude/skills/"
```

Restart Claude Code after installing.

### Other Agents

For agents that do not support skill folders directly, load `skills/agent-session-resume/SKILL.md` as the main instruction document and use the relevant platform file from `skills/agent-session-resume/references/`.

## Usage

Example prompt:

```text
Use agent-session-resume to continue the previous session. The prior transcript is in .claude/.
Read the full transcript first, summarize the goal and task status, then resume from the last unfinished step.
```

## Checks

Run the package and fixture validators:

```bash
python3 scripts/validate-skill-package.py
python3 scripts/validate-fixtures.py
```

The fixtures in `tests/fixtures/` cover Claude Code, Codex, Antigravity, and OpenCode handoff shapes. Each scenario pairs sample session material with the expected context summary, task status breakdown, and next action.

## License

MIT
