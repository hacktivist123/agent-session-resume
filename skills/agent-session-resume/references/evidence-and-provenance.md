# Evidence and Provenance

Use this reference for the detailed rules behind the `Loaded skill` line, evidence references, and repeat-resume stability. SKILL.md carries the workflow; this file carries the long tail.

## Provenance Self-Check

Run the bundled checker before writing the resume report:

```bash
python3 skills/agent-session-resume/scripts/skill-provenance.py
```

Run it from the root that contains `skills/agent-session-resume/`. If the script is not at that path (older installs keep it at `scripts/skill-provenance.py` in the repo root), check there before falling back to manual comparison. It compares the repo copy of SKILL.md against the Codex and Claude install paths and prints bytes, lines, and SHA-256 per surface. Pass `--repo-root`, `--codex-home`, `--claude-home`, or `--format json` to adjust.

If the script is unavailable, compare manually:

```bash
wc -c "$HOME/.claude/skills/agent-session-resume/SKILL.md" \
      "${CODEX_HOME:-$HOME/.codex}/skills/agent-session-resume/SKILL.md" 2>/dev/null
shasum -a 256 path/to/loaded/SKILL.md path/to/candidate/SKILL.md 2>/dev/null
```

Report the outcome on the `Loaded skill` line: `matches-repo`, `differs-from-repo` (stale), `missing`, or `unknown`.

## Recording Skill Provenance

- Name the loaded skill file path in the checkpoint when the runtime exposes it, for example a `skills/agent-session-resume/SKILL.md` path. If the runtime does not expose the loaded path, write `unknown`.
- Name a source/version marker when available: plugin manifest version, marketplace package version, git tag or commit, package source, or checksum from the loaded skill file. If none is available, write `unknown`.
- Do not infer the active skill version from an unrelated repository checkout, local clone, docs page, or install command. Label those as candidate sources unless you can prove they are the loaded artifact.
- When comparing Codex and Claude behavior, compare the known install paths and reported source/version markers from each runtime. Common standalone paths are `${CODEX_HOME:-$HOME/.codex}/skills/agent-session-resume/SKILL.md` for Codex and `$HOME/.claude/skills/agent-session-resume/SKILL.md` for Claude Code. Claude Code plugin installs may expose a plugin-managed path or only the plugin manifest/version.
- After updating installed skill files, assume an already-running agent may still be using the previous loaded instructions until the app, CLI, plugin, or session is restarted or reloaded.

## Evidence Rules

- Every task status line must include `evidence:` with at least one concrete source reference.
- `DONE` requires evidence of completion, not just a plan or intention.
- `PARTIALLY DONE` requires evidence that work started plus the missing completion or verification.
- `NOT DONE` requires evidence from an explicit TODO, failing command, missing artifact, or transcript gap.
- If current-repo verification has not happened yet, say so plainly instead of implying the transcript is current.
- The loaded skill path and source/version marker may be `unknown`, but must not be guessed. If only a candidate install path is known, say `unknown` for the loaded path and mention the candidate path separately.
- User deferrals require evidence from the transcript, handoff, or active prompt. Preserve the deferred scope even when the rest of the work is ready to continue. Do not reintroduce deferred scope from a vague go-ahead such as "proceed"; ask for confirmation unless the user clearly names the parked scope or its reopening condition has been met.
- Use compact, stable references so a person or script can trace the claim: `session.jsonl:L4`, `handoff.md:L7-L10`, `src/file.ts:L20-L35`, or `git status --short --branch`.
- Prior resume reports can help route the investigation, but they do not prove task state by themselves. Cite the primary evidence that verifies the claim, or mark the claim unverified when primary evidence is unavailable.

## Static Idempotency Contract

- For static sources, repeated resumes over the same unchanged transcript, artifacts, and workspace should converge on the same task status breakdown and next-action class.
- Exact wording may vary, but evidence references, task classifications, mismatch handling, and whether the next action is blocked or actionable should remain stable.
- Static idempotency does not apply to live or active transcripts, changing repositories, remote GitHub state, running commands, or other sources that may drift between runs.
