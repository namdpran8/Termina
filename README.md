# Termina - AI Coding Assistant

Termina is a powerful, globally installable terminal-based AI coding assistant designed as an open-source alternative to Claude Code. It allows you to Bring Your Own Key (BYOK) and interact with multiple AI providers (Nvidia, OpenAI, Anthropic, Gemini) directly from your command line.

It can explore your local file system, safely read/edit files, and execute shell commands to help you code efficiently.

## Features
- **Project Awareness:** Automatically detects your project type, file counts, and reads your `README.md` on startup.
- **Strict Permissions:** Prompts `[y/N]` before writing files or executing shell commands.
- **Surgical Editing:** Edits specific blocks of text instead of overwriting entire files, complete with a visual unified diff.
- **Streaming Responses:** Beautiful, snappy streaming outputs in the terminal using `rich`.
- **Slash Commands:** Integrated `/help`, `/clear`, `/cost`, `/tree`, and `/undo` commands.
- **Cost Tracking:** Tracks tokens and calculates estimated usage cost in real-time.
- **Local Undo Memory:** Instantly revert accidental file modifications using `/undo`.
- **Git Aware:** The agent can view `git status`, diffs, and generate commits for you.

## Prerequisites
- Python 3.10+

## Installation

Termina can be installed globally on your system, allowing you to invoke it from anywhere using the `termina` command.

1. Clone or download this repository.
2. Navigate to the project directory and install it globally using `pip`:
   ```bash
   pip install -e .
   ```

## Configuration (BYOK)

Before using Termina, you need to set up your API key for the provider you want to use. Keys are securely stored in `~/.termina/config.json`.

Termina defaults to using Nvidia's free hosted models (`meta/llama-3.1-70b-instruct`).

To set your Nvidia API key:
```bash
termina config set-key nvidia YOUR_NVIDIA_API_KEY
```

You can also set keys for other providers:
```bash
termina config set-key openai YOUR_OPENAI_API_KEY
termina config set-key anthropic YOUR_ANTHROPIC_API_KEY
termina config set-key gemini YOUR_GEMINI_API_KEY
```

To change the default model and provider:
```bash
termina config set-model openai gpt-4o
```

## Usage

Start the interactive chat session from **any folder** on your computer:
```bash
termina
```
*(You can also use `termina chat`)*

Once inside the chat, you can ask Termina to:
- "List the files in the current directory."
- "Read `agent.py` and explain what it does."
- "Write a python script that calculates the Fibonacci sequence to a file named `fib.py`."
- "Run `python fib.py` and tell me the output."
- "Review my git changes and commit them."

Type `/help` to see local interactive commands.
Type `exit` or `quit` to leave the chat.

## Architecture

- **`cli.py`**: The entry point using `Typer` for handling commands.
- **`config.py`**: Manages user configuration and API keys locally.
- **`agent.py`**: The core loop using `litellm` to communicate with the LLM and stream responses.
- **`startup.py`**: Builds project context when launching the CLI.
- **`permissions.py`**: Hooks into tools to ensure user safety.
- **`change_tracker.py`**: Memory log for file modifications and the `/undo` system.
- **`tools/`**: Contains the tools the AI can use (`filesystem.py`, `terminal.py`, `search.py`, `git.py`).
- **`setup.py`**: Registers the global `termina` CLI executable.
