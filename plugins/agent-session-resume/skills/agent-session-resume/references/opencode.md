# OpenCode Adapter

Use this adapter when resuming work from OpenCode or an OpenCode session export, share link, summary, or configured agent workflow.

## Discovery

Prefer official session exports, share links, SDK access, or CLI-supported session commands over scraping internal storage.

Inspect the workspace for OpenCode configuration and project-local agents:

```bash
find . -maxdepth 4 -type f \( -name 'opencode.json' -o -path '*/.opencode/*' \) 2>/dev/null
```

If the `opencode` CLI is installed, inspect its help for session-related commands before using them:

```bash
opencode --help
opencode session --help
```

If an OpenCode server or SDK context is available, prefer session API access to retrieve session, message, and summary data.

## Reading

Read the full session export or fetched session messages when available. If only a generated title or summary is available, treat it as incomplete and verify against files, tests, and git state.

OpenCode supports session titles, summaries, multiple sessions, and configured agents. Use these as navigation aids, not as replacements for reading the actual session record.

## Resume Notes

- Inspect `opencode.json` and `.opencode/agents/` to understand any project-specific agent behavior that shaped the prior session.
- If a shared session link is provided, fetch or open it using the environment's allowed tools and summarize only enough to resume.
- Do not assume a stable private storage path. Prefer documented CLI, SDK, or export paths.

References:

- OpenCode overview and session sharing: https://dev.opencode.ai/
- OpenCode agents, session titles, summaries, and agent config: https://open-code.ai/en/docs/agents
- OpenCode SDK session types and client access: https://opencode.ai/docs/sdk/
