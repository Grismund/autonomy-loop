"""Tool definitions and execution for the autonomy loop."""

import json
import os
import subprocess
from pathlib import Path

# Allowed base directories (inside container)
WORKSPACE_DIR = Path("/app/workspace")
MEMORY_DIR = Path("/app/memory")
NOTES_FILE = MEMORY_DIR / "notes.md"

MAX_FILE_READ = 1_000_000  # 1MB
MAX_COMMAND_OUTPUT = 50_000  # 50KB
MAX_COMMAND_TIMEOUT = 120
DEFAULT_COMMAND_TIMEOUT = 30


# --- Custom tool schemas ---

CUSTOM_TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file from the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path within /app/workspace",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the workspace. Creates parent directories as needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path within /app/workspace",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_files",
        "description": "List files and directories in a workspace path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path within /app/workspace. Defaults to root.",
                    "default": ".",
                }
            },
        },
    },
    {
        "name": "run_command",
        "description": "Run a shell command in the workspace directory. Has network access (pip install, git clone, curl, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default 30, max 120)",
                    "default": 30,
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_notes",
        "description": "Read your persistent notes from previous runs. These survive across sessions.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "write_notes",
        "description": "Write to your persistent notes file. This overwrites the entire file — read first if you want to append.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to write to notes",
                }
            },
            "required": ["content"],
        },
    },
]


# --- Server tool schemas (executed by Anthropic, zero client code) ---

SERVER_TOOLS = [
    {
        "type": "web_search_20260209",
        "name": "web_search",
    },
    {
        "type": "web_fetch_20260209",
        "name": "web_fetch",
        "max_uses": 10,
    },
]

ALL_TOOLS = CUSTOM_TOOLS + SERVER_TOOLS
CUSTOM_TOOL_NAMES = {t["name"] for t in CUSTOM_TOOLS}


def _validate_workspace_path(path_str: str) -> Path:
    """Resolve a path and verify it's inside the workspace."""
    resolved = (WORKSPACE_DIR / path_str).resolve()
    if not str(resolved).startswith(str(WORKSPACE_DIR.resolve())):
        raise ValueError(f"Path escapes workspace: {path_str}")
    return resolved


def execute_tool(name: str, tool_input: dict) -> str:
    """Execute a custom tool and return the result as a string."""
    try:
        if name == "read_file":
            path = _validate_workspace_path(tool_input["path"])
            if not path.is_file():
                return f"Error: File not found: {tool_input['path']}"
            content = path.read_text()
            if len(content) > MAX_FILE_READ:
                return content[:MAX_FILE_READ] + f"\n\n[Truncated at {MAX_FILE_READ} bytes]"
            return content

        elif name == "write_file":
            path = _validate_workspace_path(tool_input["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(tool_input["content"])
            return f"Wrote {len(tool_input['content'])} bytes to {tool_input['path']}"

        elif name == "list_files":
            path_str = tool_input.get("path", ".")
            path = _validate_workspace_path(path_str)
            if not path.is_dir():
                return f"Error: Not a directory: {path_str}"
            entries = sorted(path.iterdir())
            lines = []
            for e in entries:
                suffix = "/" if e.is_dir() else ""
                lines.append(f"{e.name}{suffix}")
            return "\n".join(lines) if lines else "(empty directory)"

        elif name == "run_command":
            timeout = min(tool_input.get("timeout", DEFAULT_COMMAND_TIMEOUT), MAX_COMMAND_TIMEOUT)
            try:
                result = subprocess.run(
                    tool_input["command"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(WORKSPACE_DIR),
                )
                output = ""
                if result.stdout:
                    output += result.stdout
                if result.stderr:
                    output += ("\n--- stderr ---\n" if output else "--- stderr ---\n") + result.stderr
                if not output:
                    output = "(no output)"
                if result.returncode != 0:
                    output += f"\n\n[exit code: {result.returncode}]"
                if len(output) > MAX_COMMAND_OUTPUT:
                    output = output[:MAX_COMMAND_OUTPUT] + f"\n\n[Truncated at {MAX_COMMAND_OUTPUT} bytes]"
                return output
            except subprocess.TimeoutExpired:
                return f"Error: Command timed out after {timeout}s"

        elif name == "read_notes":
            if not NOTES_FILE.is_file():
                return "(no notes yet)"
            content = NOTES_FILE.read_text()
            return content if content else "(notes file is empty)"

        elif name == "write_notes":
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            NOTES_FILE.write_text(tool_input["content"])
            return f"Notes saved ({len(tool_input['content'])} bytes)"

        else:
            return f"Error: Unknown tool: {name}"

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error executing {name}: {type(e).__name__}: {e}"
