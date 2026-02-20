# Autonomy Loop

A self-prompting loop that gives a Claude instance sustained autonomous control — with tools.

The model can think, reflect, build things, search the web, write and run code, and leave notes for future runs. Everything runs inside a Docker container. The human watches the log.

## What the model gets

- **Workspace** — persistent filesystem (bind-mounted from `./workspace`)
- **Shell** — full command execution with network access
- **Web** — search and fetch URLs
- **Notes** — persistent memory across runs (bind-mounted from `./memory`)

## Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and add your [Anthropic API key](https://console.anthropic.com/)
3. Run it

```bash
cp .env.example .env
# edit .env with your key
./run.sh
```

That's it. Docker handles everything else.

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

## Safety

Docker is the primary security boundary. The model has full access inside the container (network, shell, filesystem) but can only persist data through the bind mounts. Defense in depth inside the container: path validation on file tools, output size caps, shell timeouts.

## Configuration

Edit the constants at the top of `autonomy-loop.py`:

- `MAX_TURNS` — outer turn limit (default 50)
- `MAX_TOOL_CALLS_PER_TURN` — tool calls before forcing a new turn (default 20)
- `MODEL` — which Claude model to use (default `claude-opus-4-6`)
