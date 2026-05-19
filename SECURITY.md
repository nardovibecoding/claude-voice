# Security

This is a local voice-control template for Claude Code.

## Do Not Commit

- real Groq API keys
- `.env`
- local audio files
- logs, runtime state, or private machine paths
- private hook bundles or personal Claude settings

Use `.env.example` for public examples.

## Local Settings

The installer can add a `simply-voice` stop-hook entry to
`~/.claude/settings.json`. Remove that hook entry to reverse the integration.

Saving `GROQ_API_KEY` to a shell profile is opt-in.

## Reporting

Open a GitHub issue for template bugs. Do not paste secrets into issues.
