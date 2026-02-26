# Contributing

Thanks for your interest in autonomy-loop. Contributions are welcome.

## Philosophy

Keep it minimal. The project's value is in its simplicity — a clean loop, a clear architecture, no unnecessary dependencies. Changes that add complexity should have a compelling reason.

## How to contribute

1. **Fork** the repo and create a branch from `master`
2. **Make your changes** — keep commits focused and messages clear
3. **Test** by running a session end-to-end: `docker compose up`
4. **Open a pull request** with a clear description of what you changed and why

## Ideas that fit the project

- New tools for the agent (web, file, shell extensions)
- Better logging or output formatting
- Documentation improvements
- Bug fixes

## Ideas that probably don't fit

- Web dashboards or UIs (use `tail -f` — it's already perfect)
- Authentication layers or multi-user support
- Heavy external dependencies
- Anything that requires always-on infrastructure

## Forking to specialize

If you want to build a domain-specific agent (a coding assistant, a research tool, a creative writing partner), **forking is the right move** rather than opening a PR. The core project is intentionally generic.

See the forking guide in README.md for what to customize.

## Questions

Open an issue. Response time is best-effort.
