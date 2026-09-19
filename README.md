# kiss-sorcar-agent

Autonomous free AI agent running on GitHub Actions, built on
[KISS Sorcar](https://github.com/ksenxx/kiss_ai) (`kiss-agent-framework`).

**Runs at $0.** The model is `glm-4.5-flash` on Z.AI's free tier — its entry in
the framework's bundled `MODEL_INFO.json` carries `input_price_per_1M = 0` and
`output_price_per_1M = 0`, so it is zero-cost both at the provider and inside the
framework's own budget accounting. Verified end-to-end in Actions before this
README was written.

## Why the daemon is not used

The upstream docs suggest the `kiss-web` daemon. That is the wrong entry point for
CI: it is a long-lived local server for the VS Code / web clients. The right one is
the `sorcar` terminal command, which runs a task **without** the daemon, needs a
nonzero `-t`/`-f` argument, and — because stdout is piped — prints exactly the raw
YAML result. It exits `0` on success and `1` otherwise, so CI reads the outcome
directly.

```bash
sorcar -m glm-4.5-flash --work-dir "$GITHUB_WORKSPACE" -t "your task"
```

## Schedule

| Trigger | When |
|---|---|
| `schedule` | `0 7 * * *` (07:00 UTC daily) |
| `workflow_dispatch` | manual, optional custom task |

```bash
gh workflow run "KISS Sorcar Agent" --repo ildus650-pixel/kiss-sorcar-agent \
  -f task="Summarise README.md in three bullet points."
```

## Required secrets

| Secret | Purpose |
|---|---|
| `ZAI_API_KEY` | Z.AI free-tier key (free signup, no card) |
| `TELEGRAM_BOT_TOKEN` | this agent's own bot |
| `TELEGRAM_CHAT_ID` | your chat id for that bot |

## Model choice is constrained by the framework

`sorcar` raises `Cannot calculate budget for unknown model '<name>'` for any model
absent from its catalog, and the token-cost accounting runs on every request — so
an arbitrary free model name will fail the run. `glm-4.5-flash` is in the catalog
**and** free, which is why it is pinned. Other catalogued free-capable options:
`glm-4.5-flash` (chosen), or a paid key for the `glm-4.7`/`glm-4.6` entries.

If you prefer a different free provider, set the matching key (`GEMINI_API_KEY`,
`OPENROUTER_API_KEY`, `MOONSHOT_API_KEY`, `TOGETHER_API_KEY`) and pass a catalogued
model with `-m`; `get_default_model()` otherwise picks the "best" model for
whatever keys exist — which for `OPENROUTER_API_KEY` is the **paid**
`openrouter/anthropic/claude-opus-4.7`, so set `-m` explicitly when using OpenRouter.

## Files

| File | Role |
|---|---|
| `.github/workflows/agent.yml` | install, run, notify, commit |
| `scripts/render_result.py` | turns the raw YAML result into a short message |
| `scripts/notify.py` | chunks and posts to Telegram |

## Notes

- Python 3.13 is required by the package (`requires_python >=3.13`).
- The workflow installs with plain `pip`, not `pipx`: pipx's bin directory is not
  reliably on `PATH` in Actions, and the first attempt died with exit 127. The
  console script is resolved explicitly, with a fallback that calls `main()`
  directly (the module has no `__main__` guard).
- Beware `set -o pipefail` combined with `| head`: the SIGPIPE makes the step fail
  with exit 120 even when the command succeeded.
