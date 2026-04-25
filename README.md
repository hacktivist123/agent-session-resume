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
  plugin.json
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

Recommended plugin install:

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

After CLI install, restart Claude Code or run `/reload-plugins` in Claude Code.

This installs the skill as a Claude Code plugin command:

```text
/agent-session-resume:agent-session-resume
```

The plugin points at the same canonical `skills/agent-session-resume` folder used by the standalone skill package.

Alternative standalone skill install:

```text
Install the standalone Claude Code skill from https://github.com/hacktivist123/agent-session-resume.
Copy the repository folder skills/agent-session-resume into ~/.claude/skills/agent-session-resume.
Do not use the Claude Code plugin marketplace for this standalone flow.
```

Manual standalone install:

```bash
tmp_dir="$(mktemp -d)"
git clone --depth 1 https://github.com/hacktivist123/agent-session-resume "$tmp_dir/agent-session-resume"
mkdir -p "$HOME/.claude/skills"
cp -R "$tmp_dir/agent-session-resume/skills/agent-session-resume" "$HOME/.claude/skills/"
```

Restart Claude Code after installing.

Use the standalone install if you prefer the shorter `/agent-session-resume` command or do not want to use Claude Code plugins.

Choose one Claude Code install path. Installing both the plugin and standalone skill can show duplicate short command suggestions; the namespaced plugin command avoids ambiguity.

### Other Agents

For agents that do not support skill folders directly, load `skills/agent-session-resume/SKILL.md` as the main instruction document and use the relevant platform file from `skills/agent-session-resume/references/`.

## Usage

Short prompts should be enough; the skill carries the platform-specific discovery rules.

For more examples, see the [cookbook](docs/Cookbook.md).

Continue the most recent Codex session for the current repository:

```text
/agent-session-resume:agent-session-resume

Continue the most recent Codex session for this repository.
```

Continue from a specific handoff file:

```text
/agent-session-resume:agent-session-resume

Continue from ./handoff.md.
```

Expected first response shape:

```text
Brief context summary
Task status breakdown
Clear next action
```

After that checkpoint, the agent should continue from the first unfinished step without redoing completed work.

## Claude Code Notes

Recommended plugin install gives the namespaced command:

```text
/agent-session-resume:agent-session-resume
```

Alternative standalone install gives the shorter skill command:

```text
/agent-session-resume
```

If the plugin command does not appear after installation, run `/reload-plugins` and check the marketplace/plugin manifests with:

```bash
claude plugin validate .
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json
```

## Checks

Run the package and fixture validators:

```bash
python3 scripts/validate-skill-package.py
python3 scripts/validate-fixtures.py
python3 scripts/validate-trigger-matrix.py
claude plugin validate .
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json
```

The standalone skill under `skills/agent-session-resume` is the source of truth. The optional Claude plugin wrapper uses the repo root as its source, so it shares that canonical skill folder instead of maintaining a second copy. The fixtures in `tests/fixtures/` cover Claude Code, Codex, Antigravity, and OpenCode handoff shapes. Each scenario pairs sample session material with the expected context summary, task status breakdown, and next action. `tests/trigger-matrix.json` tracks prompt coverage for manual or automated trigger testing.

## License

MIT
