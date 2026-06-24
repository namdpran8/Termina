# Termina Documentation

Termina is a powerful, globally installable terminal-based AI coding assistant designed as an open-source alternative to Claude Code. It allows you to Bring Your Own Key (BYOK) and interact with multiple AI providers (Nvidia, OpenAI, Anthropic, Gemini) as well as local LLMs (Ollama, LM Studio) directly from your command line.

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Features](#features)
- [Architecture](#architecture)
- [Slash Commands](#slash-commands)
- [Skills System](#skills-system)
- [Session Management](#session-management)
- [Project Customization](#project-customization)
- [Local AI Support](#local-ai-support)
- [Cost Tracking](#cost-tracking)
- [Local Undo Memory](#local-undo-memory)
- [Git Awareness](#git-awareness)
- [Strict Permissions](#strict-permissions)
- [Surgical Editing](#surgical-editing)
- [Streaming Responses](#streaming-responses)

## Installation

Termina can be installed globally on your system, allowing you to invoke it from anywhere using the `termina` command.

1. Clone or download this repository.
2. Navigate to the project directory and install it globally using pip:
   ```bash
   pip install -e .
   ```

## Configuration (BYOK)

Before using Termina, you need to set up your API key for the provider you wish to use. Keys are securely stored in `~/.termina/config.json`.

Termina defaults to using Nvidia's free hosted models (`meta/llama-3.1-70b-instruct`).

To set your API keys:
```bash
termina config set-key nvidia YOUR_NVIDIA_API_KEY
termina config set-key openai YOUR_OPENAI_API_KEY
termina config set-key anthropic YOUR_ANTHROPIC_API_KEY
termina config set-key gemini YOUR_GEMINI_API_KEY
```

To change the default model and provider:
```bash
termina config set-model openai gpt-4o
```
*(Tip: Run `termina config list-models` to see all available presets including Nvidia Nemotron models!)*

### Local Providers
If you use Ollama or LM Studio, Termina will auto-detect them on startup. To switch to a local model:
```bash
termina config set-model ollama llama3.2:8b
```

## Usage

Start an interactive chat session from any folder on your computer:
```bash
termina
```

For a one-shot non-interactive command, use the `-p` or `--prompt` flag (you can also pipe stdin into it):
```bash
termina -p "Refactor the authentication logic in auth.py"
```

Once inside the chat, you can ask Termina to:
- "List the files in the current directory."
- "Read `agent.py` and explain what it does."
- "Write a Python script that calculates the Fibonacci sequence to a file named `fib.py`."
- "Run `python fib.py` and tell me the output."
- "Review my git changes and commit them."

## Features

- **Project Awareness**: Automatically detects your project type, file counts, and reads your `README.md` and `TERMINA.md` custom rules on extremely fast cached startup.
- **Strict Permissions**: Prompts `[y/N]` before writing files or executing shell commands.
- **Surgical Editing**: Edits specific blocks of text instead of overwriting entire files, complete with a visual unified diff.
- **Streaming Responses**: Beautiful, snappy streaming outputs in the terminal using `rich`.
- **Extensive Slash Commands**: Control the agent mid-conversation with `/help`, `/clear`, `/cost`, `/tree`, `/undo`, `/plan`, `/compact`, and `/model`.
- **Skills System**: Create, manage, and execute reusable custom agent workflows and instructions (`/skill`).
- **Cost Tracking**: Tracks tokens and calculates estimated usage cost in real-time with per-model pricing logic.
- **Local Undo Memory**: Instantly revert accidental file modifications—even across multiple files in a single transaction—using `/undo`.
- **Git Aware**: The agent can view `git status`, diffs, and generate commits for you.
- **Local AI Support**: Auto-detects local providers running on your machine (e.g., Ollama, LM Studio) and connects seamlessly.

## Architecture

- **`cli.py`**: The entry point using `Typer` for handling commands.
- **`config.py`**: Manages user configuration, local providers, and API keys.
- **`agent.py`**: The core loop using `litellm` to communicate with the LLM, managing state, skills, and tools.
- **`startup.py`**: Builds cached project context when launching the CLI.
- **`skills.py`**: The engine for discovering, parsing, and loading custom Markdown skills.
- **`permissions.py`**: Hooks into tools to ensure user safety before system execution.
- **`cost_tracker.py`**: Tracks token usage and calculates costs.
- **`session.py`**: Manages chat session history and persistence.
- **`change_tracker.py`**: Tracks file changes for the undo functionality.
- **`tools/`**: Contains implementations of various tools the agent can use (file operations, shell commands, git, etc.).

## Slash Commands

Inside a chat session, type `/help` to see all available slash commands. Highlights include:

- `/plan` - Pause immediate execution and ask the agent to formulate an architectural plan.
- `/compact` - Compress the chat history to save tokens while retaining context.
- `/model <provider> <model>` - Switch to a different LLM mid-session without losing history.
- `/undo` - Revert the file changes made in the last turn.
- `/clear` - Clear the current conversation history.
- `/cost` - Show the current session's token usage and estimated cost.
- `/tree` - Display the project directory structure.
- `/skill` - Manage and execute custom skills.

## Project Customization

Run `termina init` in any project to scaffold a `TERMINA.md` file. Add your project's specific coding guidelines, architecture notes, and rules here. Termina will automatically read it every time it boots up in that directory.

## Skills System

Extend Termina's capabilities by writing custom AI skills (standard Markdown files with YAML frontmatter).
- `termina skill new <name>` - Scaffold a new skill file.
- `termina skill list` - View all available global and project-local skills.
- `termina skill install <path_or_url>` - Install external community skills.

## Session Management

Termina automatically saves your chats.
- `termina history` - List all past sessions.
- `termina resume <session_id>` - Resume exactly where you left off.
- `termina sessions --clear` - Wipe all saved session history.

## Local AI Support

If you use Ollama or LM Studio, Termina will auto-detect them on startup. To switch to a local model:
```bash
termina config set-model ollama llama3.2:8b
```
*(Replace `ollama llama3.2:8b` with your local provider and model name)*

## Cost Tracking

Termina tracks token usage and calculates estimated costs in real-time using per-model pricing logic. View your current session's cost with `/cost`.

## Local Undo Memory

Instantly revert accidental file modifications—even across multiple files in a single transaction—using the `/undo` command.

## Git Awareness

The agent can:
- View `git status`
- Show diffs
- Generate commits for you

## Strict Permissions

Termina prompts `[y/N]` before writing files or executing shell commands, ensuring you remain in control.

## Surgical Editing

Instead of overwriting entire files, Termina edits specific blocks of text and shows you a visual unified diff of the changes.

## Streaming Responses

Responses are streamed beautifully in the terminal using the `rich` library for a snappy, responsive experience.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.