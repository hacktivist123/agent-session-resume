# OpenCode Adapter

Use this adapter when resuming work from OpenCode or an OpenCode session export, share link, summary, or configured agent workflow.

## Discovery

Prefer official session exports, share links, SDK access, or CLI-supported session commands over scraping internal storage.

Inspect the workspace for OpenCode configuration and project-local agents:

```bash
find . -maxdepth 4 -type f \( -name 'opencode.json' -o -path '*/.opencode/*' \) 2>/dev/null
```

Use configuration files as routing context, not as session evidence. They can explain which agents, models, or project rules shaped the prior work, but they do not prove what was done.

If the `opencode` CLI is installed, inspect its help for session-related commands before using them:

```bash
opencode --help
opencode session --help
```

Prefer documented session commands when they are available. Common next checks are:

```bash
opencode session list --help
opencode session export --help
opencode session show --help
```

If a command exists, use it to list sessions first, then fetch or export only the likely session. Prefer filters such as title, session ID, timestamp, cwd, or project path over dumping every session.

If an OpenCode server or SDK context is available, prefer session API access to retrieve session, message, and summary data.

When no CLI/API path is available, search only likely export and handoff files before considering broad workspace scans:

```bash
find . -maxdepth 5 -type f \( \
  -iname '*opencode*' -o \
  -iname '*session*' -o \
  -iname '*handoff*' -o \
  -iname '*transcript*' -o \
  -iname '*summary*' \
\) 2>/dev/null
```

## Reading

Read the full session export or fetched session messages when available. If only a generated title or summary is available, treat it as incomplete and verify against files, tests, and git state.

OpenCode supports session titles, summaries, multiple sessions, and configured agents. Use these as navigation aids, not as replacements for reading the actual session record.

When multiple sessions could match, rank them by:

1. Explicit path, share link, or session ID supplied by the user.
2. Exact cwd, project path, or repository match.
3. Session title or summary match.
4. Files, package names, branch names, or agents mentioned in the current workspace.
5. Recency, used only as a tie-breaker.

If only a summary is available, state that task status is summary-derived until confirmed against repository files, tests, and git state.

## Resume Notes

- Inspect `opencode.json` and `.opencode/agents/` to understand any project-specific agent behavior that shaped the prior session.
- If a shared session link is provided, fetch or open it using the environment's allowed tools and summarize only enough to resume.
- Do not assume a stable private storage path. Prefer documented CLI, SDK, or export paths.

References:

- OpenCode overview and session sharing: https://dev.opencode.ai/
- OpenCode agents, session titles, summaries, and agent config: https://open-code.ai/en/docs/agents
- OpenCode SDK session types and client access: https://opencode.ai/docs/sdk/
