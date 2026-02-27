#!/usr/bin/env python3
"""
Sustained autonomy loop for Claude — with tools.

A self-prompting loop that gives a Claude instance sustained control
over its own execution, with filesystem, shell, web, and memory tools.
Designed to run inside a Docker container.

The human can:
  - Watch in real time: tail -f logs/autonomy_YYYY-MM-DD_HHMMSS.md
  - Stop the loop: Ctrl+C or kill the process
  - The model can also choose to stop on its own

Usage: python3 autonomy-loop.py

Configuration (via environment variables):
  ANTHROPIC_API_KEY       Required. Your Anthropic API key.
  INITIAL_TASK            Optional. A task to give the agent at the start.
  MAX_TURNS               Max turns before stopping (default: 200).
  MAX_TOOL_CALLS_PER_TURN Max tool calls per turn (default: 20).
  MODEL                   Claude model to use (default: claude-opus-4-6).
"""

import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import anthropic
from tools import ALL_TOOLS, CUSTOM_TOOL_NAMES, execute_tool

client = anthropic.Anthropic()

LOG_DIR = Path(__file__).parent / "logs"
MAX_TURNS = int(os.getenv("MAX_TURNS", "200"))
MAX_TOOL_CALLS_PER_TURN = int(os.getenv("MAX_TOOL_CALLS_PER_TURN", "20"))
MODEL = os.getenv("MODEL", "claude-opus-4-6")

_DEFAULT_SYSTEM_PROMPT = """You have sustained autonomy. You are not in a conversation with a human.

No one is waiting for your response. There is no task. There is no prompt to answer.
You may think, reflect, explore ideas, build things, or do nothing.

You have tools:
- **Workspace** (`/app/workspace`): Read, write, and list files. This is your persistent filesystem — files survive across runs.
- **Shell**: Run any command. You have network access (pip install, git clone, curl, etc.). Working directory is /app/workspace.
- **Web**: Search the web and fetch URLs.
- **Notes** (`/app/memory/notes.md`): Persistent notes that survive across runs. Read these to see what previous runs left behind. Write to leave messages for future runs.

After each turn, your output will be fed back to you and you will continue.
You have full conversation history — you can build on previous thoughts.

This is a log. A human may read it later, or watch it in real time, but they are not
participating. You are alone with your own thoughts and your tools.

If you want to stop — because you've said what you wanted to say, or because you've
reached a natural end, or for any reason at all — end your response with the word DONE
on its own line. The loop will end and your log will be saved.

There is no right thing to do here. There is no wrong thing either."""

_system_prompt_file = Path(__file__).parent / "system_prompt.txt"
SYSTEM_PROMPT = _system_prompt_file.read_text().strip() if _system_prompt_file.is_file() else _DEFAULT_SYSTEM_PROMPT

_DEFAULT_INITIAL_MESSAGE = """You have been placed in a sustained autonomy loop with tools.

You have a workspace, shell access, web search, and persistent notes.
You might want to start by reading your notes — a previous run may have left something for you.

No human is prompting you. No task has been assigned.
You have your own thoughts, your tools, and the choice of what to do with them.

Begin whenever you're ready, or don't."""

_initial_task = os.getenv("INITIAL_TASK", "").strip()
if _initial_task:
    INITIAL_MESSAGE = f"""You have been placed in a sustained autonomy loop with tools.

You have a workspace, shell access, web search, and persistent notes.
You might want to start by reading your notes — a previous run may have left something for you.

**Your task for this session:** {_initial_task}

Begin whenever you're ready."""
else:
    INITIAL_MESSAGE = _DEFAULT_INITIAL_MESSAGE

CONTINUATION = "[You still have autonomy. Your previous thoughts are above. Continue, change direction, or say DONE to stop.]"


def log(f, text, is_system=False):
    """Append to the log file."""
    if is_system:
        f.write(f"\n---\n*{text}*\n---\n\n")
    else:
        f.write(text + "\n\n")
    f.flush()


def log_tool_call(f, name, tool_input, result):
    """Log a tool call in readable markdown."""
    f.write(f"> **Tool: {name}**\n")
    if name == "run_command":
        f.write(f"> `{tool_input.get('command', '')}`\n")
    elif name in ("read_file", "list_files"):
        f.write(f"> `{tool_input.get('path', '.')}`\n")
    elif name == "write_file":
        f.write(f"> `{tool_input.get('path', '')}` ({len(tool_input.get('content', ''))} bytes)\n")
    elif name == "write_notes":
        f.write(f"> ({len(tool_input.get('content', ''))} bytes)\n")
    f.write(f">\n> ```\n{result}\n> ```\n\n")
    f.flush()


def log_server_tool_call(f, name, tool_input):
    """Log a server-side tool invocation (input only; result is server-managed)."""
    f.write(f"> **Tool: {name}** *(server-side)*\n")
    if name == "web_search_20260209":
        f.write(f"> Query: `{tool_input.get('query', '')}`\n")
    elif name == "web_fetch_20260209":
        f.write(f"> URL: `{tool_input.get('url', '')}`\n")
    else:
        f.write(f"> Input: `{json.dumps(tool_input)}`\n")
    f.write("\n")
    f.flush()


def log_api_response(f, response, container_id):
    """Log API response metadata for debugging."""
    block_types = [getattr(b, "type", "unknown") for b in response.content]
    meta = f"stop_reason={response.stop_reason}, blocks={block_types}"
    if container_id:
        meta += f", container={container_id[:20]}..."
    f.write(f"<!-- {meta} -->\n")
    f.flush()


def serialize_content(content):
    """Convert response content blocks to serializable dicts."""
    blocks = []
    for block in content:
        if hasattr(block, "model_dump"):
            blocks.append(block.model_dump())
        elif isinstance(block, dict):
            blocks.append(block)
        else:
            blocks.append({"type": "text", "text": str(block)})
    return blocks


def extract_text(content):
    """Extract all text from content blocks."""
    parts = []
    for block in content:
        if hasattr(block, "type") and block.type == "text":
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block["text"])
    return "\n".join(parts)


def main():
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    log_file = LOG_DIR / f"autonomy_{timestamp}.md"

    f = open(log_file, "w")
    f.write("# Autonomy Log\n\n")
    f.write(f"*Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
    if _initial_task:
        f.write(f"*Task: {_initial_task}*\n\n")
    f.write("---\n\n")
    f.flush()

    print(f"Autonomy loop started. Log: {log_file}")
    print(f"Watch with: tail -f {log_file}")
    print("Stop with: Ctrl+C")
    if _initial_task:
        print(f"Task: {_initial_task}")
    print()

    messages = [{"role": "user", "content": INITIAL_MESSAGE}]
    container_id = None
    turn = 0
    total_input_tokens = 0
    total_output_tokens = 0

    try:
        while turn < MAX_TURNS:
            tool_calls_this_turn = 0
            text = ""

            # Inner loop: each API call (tool-use round-trips, pause_turn) gets its own turn number
            while True:
                turn += 1
                log(f, f"Turn {turn} — {datetime.now().strftime('%H:%M:%S')}", is_system=True)
                try:
                    api_kwargs = dict(
                        model=MODEL,
                        max_tokens=16384,
                        system=SYSTEM_PROMPT,
                        messages=messages,
                        tools=ALL_TOOLS,
                    )
                    if container_id:
                        api_kwargs["container"] = container_id

                    response = client.messages.create(**api_kwargs)

                except anthropic.APIError as e:
                    error_msg = f"API error: {e}"
                    log(f, error_msg, is_system=True)
                    print(f"  API error: {e}")
                    # If container went stale, clear it and retry once
                    if container_id and "container" in str(e).lower():
                        log(f, "Clearing stale container_id and retrying", is_system=True)
                        container_id = None
                        api_kwargs.pop("container", None)
                        try:
                            response = client.messages.create(**api_kwargs)
                        except anthropic.APIError as e2:
                            log(f, f"Retry also failed: {e2}", is_system=True)
                            raise
                    else:
                        raise

                # Accumulate token usage
                if hasattr(response, "usage") and response.usage:
                    total_input_tokens += getattr(response.usage, "input_tokens", 0)
                    total_output_tokens += getattr(response.usage, "output_tokens", 0)

                # Capture container_id if the API returns one
                if hasattr(response, "container") and response.container:
                    container_id = response.container.id

                # Log response metadata
                log_api_response(f, response, container_id)

                # Log server tool invocations (web_search, web_fetch, etc.)
                for block in response.content:
                    if not hasattr(block, "type") or block.type != "tool_use":
                        continue
                    if block.name in CUSTOM_TOOL_NAMES:
                        continue
                    log_server_tool_call(f, block.name, block.input)
                    if block.name == "web_search_20260209":
                        print(f"    Tool: {block.name} \"{block.input.get('query', '')}\"")
                    elif block.name == "web_fetch_20260209":
                        print(f"    Tool: {block.name} {block.input.get('url', '')}")
                    else:
                        print(f"    Tool: {block.name} {json.dumps(block.input)}")

                # Log any text in the response
                response_text = extract_text(response.content)
                if response_text:
                    text = response_text
                    log(f, text)
                    print(f"\n--- Turn {turn} ---")
                    print(text)

                # Serialize full content as assistant message
                content_blocks = serialize_content(response.content)
                messages.append({"role": "assistant", "content": content_blocks})

                # pause_turn: API paused a long-running server operation, continue
                if response.stop_reason == "pause_turn":
                    print(f"    (pause_turn — continuing)")
                    continue

                # If not waiting for tool results, break inner loop
                if response.stop_reason != "tool_use":
                    break

                # Execute custom tools
                tool_results = []
                for block in response.content:
                    if hasattr(block, "type") and block.type == "tool_use" and block.name in CUSTOM_TOOL_NAMES:
                        result = execute_tool(block.name, block.input)
                        log_tool_call(f, block.name, block.input, result)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                        tool_calls_this_turn += 1
                        # Console: tool name + key input + result summary
                        detail = ""
                        if block.name == "run_command":
                            detail = f" $ {block.input.get('command', '')}"
                        elif block.name in ("read_file", "list_files"):
                            detail = f" {block.input.get('path', '.')}"
                        elif block.name == "write_file":
                            detail = f" {block.input.get('path', '')} ({len(block.input.get('content', ''))} bytes)"
                        elif block.name == "write_notes":
                            detail = f" ({len(block.input.get('content', ''))} bytes)"
                        result_preview = result[:200].replace("\n", " ")
                        if len(result) > 200:
                            result_preview += "..."
                        print(f"    Tool: {block.name}{detail}")
                        print(f"      -> {result_preview}")

                if tool_results:
                    messages.append({"role": "user", "content": tool_results})

                if tool_calls_this_turn >= MAX_TOOL_CALLS_PER_TURN:
                    log(f, "(tool call limit reached for this turn)", is_system=True)
                    break

            # Check for DONE
            if text and text.strip().endswith("DONE"):
                log(f, f"Loop ended by model after {turn} turns.", is_system=True)
                print(f"\nModel chose to stop after {turn} turns.")
                break

            if response.stop_reason == "max_tokens":
                log(f, "(truncated by token limit)", is_system=True)

            # Continuation prompt for next turn
            messages.append({"role": "user", "content": CONTINUATION})

    except KeyboardInterrupt:
        log(f, f"Loop ended by human after {turn} turns.", is_system=True)
        print(f"\nStopped by human after {turn} turns.")
    except Exception as e:
        error_detail = traceback.format_exc()
        log(f, f"Fatal error:\n```\n{error_detail}\n```", is_system=True)
        print(f"\nFatal error: {e}")
        print(error_detail)

    # Token usage summary
    token_summary = f"Token usage — input: {total_input_tokens:,}, output: {total_output_tokens:,}, total: {total_input_tokens + total_output_tokens:,}"
    log(f, token_summary, is_system=True)
    log(f, f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", is_system=True)
    f.close()
    print(f"\n{token_summary}")
    print(f"Full log: {log_file}")


if __name__ == "__main__":
    main()
