#!/bin/bash
set -e

cd "$(dirname "$0")"

mkdir -p workspace memory logs

# Load .env if present, otherwise expect ANTHROPIC_API_KEY in environment
ENV_FLAG=()
if [ -f .env ]; then
  ENV_FLAG=(--env-file .env)
elif [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "Error: No .env file and ANTHROPIC_API_KEY not set."
  echo "Copy .env.example to .env and add your key, or export ANTHROPIC_API_KEY."
  exit 1
else
  ENV_FLAG=(-e ANTHROPIC_API_KEY)
fi

docker build -t autonomy-loop .
docker run -it --rm \
  "${ENV_FLAG[@]}" \
  -v ./workspace:/app/workspace \
  -v ./memory:/app/memory \
  -v ./logs:/app/logs \
  autonomy-loop
