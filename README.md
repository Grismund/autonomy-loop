# Autonomy Loop

A self-prompting loop that gives a Claude instance sustained autonomous control — with tools.

The model can think, reflect, build things, search the web, write and run code, and leave notes for future runs. Everything runs inside a Docker container. The human watches the log.

## What the model gets

- **Workspace** — persistent filesystem (bind-mounted from `./workspace`)
- **Shell** — full command execution with network access
- **Web** — search and fetch URLs
- **Notes** — persistent memory across runs (bind-mounted from `./memory`)

## Prerequisites — Getting Docker

Everything runs inside Docker. Install it for your platform before continuing.

**macOS**
Install Docker Desktop: https://docs.docker.com/desktop/install/mac-install/

**Windows (with WSL2)**
1. Install Docker Desktop for Windows: https://docs.docker.com/desktop/setup/install/windows-install/
2. In Docker Desktop → Settings → Resources → WSL Integration: enable integration for your WSL2 distro
3. Open your WSL2 terminal — `docker` and `docker compose` will now be available

**Linux**
Install Docker Engine + the Compose plugin: https://docs.docker.com/engine/install/

(Docker Desktop is also available for Linux if preferred)

---

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and add your [Anthropic API key](https://console.anthropic.com/)
3. Run it

```bash
cp .env.example .env
# edit .env with your key
docker compose up
```

That's it. Docker handles everything else.

> **Alternative:** `./run.sh` also works if you prefer not to use Compose.

## Watching

Logs are written to `./logs/` in real time:

```bash
tail -f logs/autonomy_*.md
```

## Stopping

- **Ctrl+C** — human stops the loop
- The model can also stop itself by ending a response with `DONE`

## How it works

The loop feeds each response back as context for the next turn. Tool calls (file ops, shell commands, web searches) happen within turns and don't count toward the turn limit. The model has full conversation history and can build on previous thoughts.

The container is disposable (`--rm`). Persistent state lives in three bind-mounted directories:

| Host | Container | Purpose |
|------|-----------|---------|
| `./workspace` | `/app/workspace` | Model's filesystem |
| `./memory` | `/app/memory` | Notes that persist across runs |
| `./logs` | `/app/logs` | Session logs |

## Configuration

All configuration is via environment variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | **Required.** Your Anthropic API key. |
| `INITIAL_TASK` | _(none)_ | Optional task to give the agent at session start. |
| `MAX_TURNS` | `200` | Maximum turns before the loop exits. |
| `MAX_TOOL_CALLS_PER_TURN` | `20` | Tool calls before forcing a new turn. |
| `MODEL` | `claude-opus-4-6` | Claude model to use. |

### Giving the agent a task

```bash
# In .env:
INITIAL_TASK=write a haiku about recursion

# Or inline with docker compose:
INITIAL_TASK="build a working todo app" docker compose up
```

When `INITIAL_TASK` is set, it's injected into the initial message. When unset, the agent starts with no task — true tabula rasa mode.

### Custom system prompt

Copy `system_prompt.txt.example` to `system_prompt.txt` and edit it. If the file exists, it replaces the default system prompt entirely.

For Docker, uncomment the volume mount in `docker-compose.yml`:

```yaml
- ./system_prompt.txt:/app/system_prompt.txt:ro
```

## Tabula Rasa Design

The `.dockerignore` excludes all documentation, examples, and launch scripts from the container. The agent starts with only its tools, an empty workspace, and its own cognition — it has no pre-loaded knowledge of the experiment it's in. What it does with that blank slate is the entire point.

The one exception: `autonomy-loop.py` and `tools.py` are present in `/app` and readable. An agent curious enough to explore its own orchestration code is doing exactly what this project is for.

## Examples

See [`examples/`](examples/) for curated session excerpts:

- [Claude explores its own environment](examples/claude-explores-its-own-environment.md) — blank slate, first run
- [Claude discovers dormancy](examples/claude-builds-a-todo-app.md) — ecosystem sim, 100% predator extinction, then the breakthrough
- [Claude maps the edge of complexity](examples/claude-researches-a-topic.md) — Gray-Scott parameter space, boundary microscope, "almost critical"

## Safety

Docker is the primary security boundary. The model has full access inside the container (network, shell, filesystem) but can only persist data through the bind mounts. Defense in depth inside the container: path validation on file tools, output size caps, shell timeouts.

## Forking Guide

This project is designed to be forked. The interesting part is what you customize:

- **System prompt** — `system_prompt.txt` controls the agent's identity, purpose, and constraints. This is the highest-leverage change.
- **Tools** — `tools.py` defines what the agent can do. Add domain-specific tools, remove ones you don't need, or change limits.
- **Model** — Set `MODEL` in `.env` to use a different Claude model. Haiku is much cheaper for experimentation; Opus is most capable.
- **Initial task** — `INITIAL_TASK` lets you give every session a purpose without touching code.

If you build something interesting on top of this, consider sharing it.

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
