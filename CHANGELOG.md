# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Console and markdown log output for server-side tool invocations (`web_search_20260209`, `web_fetch_20260209`). Query/URL is now visible in the terminal during `pause_turn` continuations.

### Removed
- Dead code branches for `web_search` / `fetch_url` in custom tool console block (these tool names were never reachable through that path).

## [0.1.0] - 2026-02-26

Initial public release.

### Features
- Self-prompting autonomy loop with sustained context across turns
- Custom tools: `read_file`, `write_file`, `list_files`, `run_command`, `write_notes`
- Server-side tools: `web_search_20260209`, `web_fetch_20260209`
- Markdown log file written in real time (`logs/autonomy_YYYY-MM-DD_HHMMSS.md`)
- `system_prompt.txt` override for customizing the agent's persona
- `INITIAL_TASK` env var for task-directed runs
- Docker-first design with example `docker-compose.yml`
- Token usage summary at end of each run
- Model self-termination via `DONE` keyword
