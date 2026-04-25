# agent-session-resume

`agent-session-resume` is a reusable skill for continuing work from a prior AI coding-agent session without losing context, duplicating completed work, or overwriting unrelated changes.

It is designed for handoffs between tools such as Claude Code, Codex, Antigravity, and OpenCode.

Instead of asking the next agent to guess what happened, the skill makes it produce a handoff checkpoint first: the prior goal, what is already done, what is still open, and the next action to take before editing.

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
.claude-plugin/
  marketplace.json
plugins/
  agent-session-resume/
    .claude-plugin/
      plugin.json
    skills/
      agent-session-resume/
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

This repo is distributed primarily as a skill. The canonical installable package is:

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

Recommended standalone install:

```text
Install the skill from https://github.com/hacktivist123/agent-session-resume.
Use the skill folder at skills/agent-session-resume and install it into ~/.claude/skills/agent-session-resume.
Use the standalone skill install, not the marketplace plugin wrapper.
```

Claude Code standalone skills live on disk under `~/.claude/skills`. Its repo-based marketplace install flow is for plugins, so use the optional plugin wrapper below if you prefer that install path.

Manual install:

```bash
tmp_dir="$(mktemp -d)"
git clone --depth 1 https://github.com/hacktivist123/agent-session-resume "$tmp_dir/agent-session-resume"
mkdir -p "$HOME/.claude/skills"
cp -R "$tmp_dir/agent-session-resume/skills/agent-session-resume" "$HOME/.claude/skills/"
```

Restart Claude Code after installing.

Optional marketplace plugin install:

```text
/plugin marketplace add hacktivist123/agent-session-resume
/plugin install agent-session-resume@hacktivist123
/reload-plugins
```

CLI equivalent:

```bash
claude plugin marketplace add hacktivist123/agent-session-resume
claude plugin install agent-session-resume@hacktivist123
```

The standalone skill stays canonical and gives you `/agent-session-resume`. The plugin wraps the same skill for Claude Code marketplace installs, so it is namespaced as `/agent-session-resume:agent-session-resume`.

### Other Agents

For agents that do not support skill folders directly, load `skills/agent-session-resume/SKILL.md` as the main instruction document and use the relevant platform file from `skills/agent-session-resume/references/`.

## Usage

Example prompt:

```text
Use agent-session-resume to continue the previous session. The prior transcript is in .claude/.
Read the full transcript first, summarize the goal and task status, then resume from the last unfinished step.
```

Expected first response shape:

```text
Brief context summary
Task status breakdown
Clear next action
```

After that checkpoint, the agent should continue from the first unfinished step without redoing completed work.

## Claude Code Notes

Standalone install gives the shorter skill command:

```text
/agent-session-resume
```

Marketplace plugin install gives the namespaced command:

```text
/agent-session-resume:agent-session-resume
```

If the plugin command does not appear after installation, run `/reload-plugins` and check the marketplace/plugin manifests with:

```bash
claude plugin validate .
claude plugin validate plugins/agent-session-resume
```

## Checks

Run the package and fixture validators:

```bash
python3 scripts/sync-claude-plugin.py
python3 scripts/validate-skill-package.py
python3 scripts/validate-fixtures.py
python3 scripts/validate-trigger-matrix.py
claude plugin validate .
claude plugin validate plugins/agent-session-resume
```

The standalone skill under `skills/agent-session-resume` is the source of truth. `scripts/sync-claude-plugin.py` refreshes the optional Claude plugin copy before validation. The fixtures in `tests/fixtures/` cover Claude Code, Codex, Antigravity, and OpenCode handoff shapes. Each scenario pairs sample session material with the expected context summary, task status breakdown, and next action. `tests/trigger-matrix.json` tracks prompt coverage for manual or automated trigger testing.

## License

MIT
