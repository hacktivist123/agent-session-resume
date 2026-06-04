# agent-session-resume

`agent-session-resume` is a reusable skill for continuing work from a prior AI coding-agent session without losing context, duplicating completed work, or overwriting unrelated changes.

It is designed for handoffs between tools such as Claude Code, Codex, Cursor, Antigravity, and OpenCode.

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
      cursor.md
      opencode.md
```

## Install

The quickest way to install is the [`skills`](https://github.com/vercel-labs/skills) CLI (`npx skills`). It reads the canonical `skills/agent-session-resume` folder from this repo and installs it for whichever agent you target — no manual cloning or copying.

Install (interactive — choose which agents to install into):

```bash
npx skills add hacktivist123/agent-session-resume
```

Install for specific agents without prompts:

```bash
npx skills add hacktivist123/agent-session-resume -a claude-code -a codex -a cursor -a opencode -y
```

Install globally (user-level instead of the current project) with `-g`:

```bash
npx skills add hacktivist123/agent-session-resume -g
```

Update to the latest version:

```bash
npx skills update agent-session-resume
```

`npx skills update` with no name updates every installed skill. List or remove the skill with `npx skills list` and `npx skills remove agent-session-resume`.

After installing or updating, restart the agent (or start a new session) so it loads the current instructions.

### Claude Code plugin (alternative)

If you prefer a Claude Code plugin with a namespaced command instead of the `npx skills` flow, add the marketplace and install the plugin:

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

This gives the namespaced command `/agent-session-resume:agent-session-resume`. The marketplace id is `hacktivist123` (defined in `.claude-plugin/marketplace.json`), so the install reference is `agent-session-resume@hacktivist123`. Restart Claude Code or run `/reload-plugins` after installing.

### Other Agents

`npx skills` supports 70+ agents; pass `-a <agent>` to target one (for example `-a github-copilot`, `-a windsurf`, or `-a cline`). For an agent the CLI does not cover, load `skills/agent-session-resume/SKILL.md` as the main instruction document and use the relevant platform file from `skills/agent-session-resume/references/`.

## Usage

Short prompts should be enough; the skill carries the platform-specific discovery rules.

For more examples, see the [cookbook](docs/Cookbook.md).

For benchmark areas, fixture expectations, and issue/PR evaluation fields, see [Benchmarking](docs/Benchmarking.md).

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
Loaded skill: path=<loaded SKILL.md path or unknown>; source/version=<marker or unknown>
Task status breakdown
User deferrals
Clear next action
```

After that checkpoint, the agent should continue from the first unfinished step without redoing completed work.

## Skill Source And Deferrals

Resume reports should identify the loaded skill path and source/version marker when available, and should say `unknown` when the runtime does not expose them. Useful markers include the Claude plugin manifest version, marketplace package version, git commit, tag, package source, or a checksum of the loaded `SKILL.md`.

When comparing Codex and Claude Code behavior, compare the known install paths before concluding that the same skill version ran:

```text
${CODEX_HOME:-$HOME/.codex}/skills/agent-session-resume/SKILL.md
$HOME/.claude/skills/agent-session-resume/SKILL.md
```

Explicit user deferrals such as "skip", "park", "leave out", or "not now" should be preserved in resume context. A vague prompt such as "Proceed" should not unpark that scope without confirmation.

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

The standalone skill under `skills/agent-session-resume` is the source of truth. The optional Claude plugin wrapper uses the repo root as its source, so it shares that canonical skill folder instead of maintaining a second copy. The fixtures in `tests/fixtures/` cover Claude Code, Codex, Cursor, Antigravity, and OpenCode handoff shapes. Each scenario pairs sample session material with the expected context summary, task status breakdown, and next action. `tests/trigger-matrix.json` tracks prompt coverage for manual or automated trigger testing.

Use [docs/Benchmarking.md](docs/Benchmarking.md) when proposing improvements so PRs explain what behavior changed, how it was measured, and what a good result looks like.

## License

MIT
