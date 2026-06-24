# Configuration (BYOK)

Before using Termina, you need to set up your API key for the provider you want to use. Keys are securely stored in `~/.termina/config.json`.

Termina defaults to using Nvidia's free hosted models (`meta/llama-3.1-70b-instruct`).

## Setting API Keys

To set your API keys for various providers, use the `termina config set-key` command:

```bash
# Nvidia (default)
termina config set-key nvidia YOUR_NVIDIA_API_KEY

# OpenAI
termina config set-key openai YOUR_OPENAI_API_KEY

# Anthropic
termina config set-key anthropic YOUR_ANTHROPIC_API_KEY

# Gemini
termina config set-key gemini YOUR_GEMINI_API_KEY
```

## Changing the Default Model and Provider

You can change the default model and provider at any time:

```bash
# Example: Switch to OpenAI's GPT-4o
termina config set-model openai gpt-4o

# Example: Switch to a local Ollama model
termina config set-model ollama llama3.2:8b
```

To see all available presets (including Nvidia Nemotron models), run:
```bash
termina config list-models
```

## Local Providers

If you use **Ollama** or **LM Studio**, Termina will auto-detect them on startup. To switch to a local model, simply run:
```bash
termina config set-model <provider> <model>
```

Examples:
```bash
termina config set-model ollama llama3:8b
termina config set-model lmstudio phi-3-mini
```

## Configuration File Location

Your configuration is stored in:
- `~/.termina/config.json` (Linux/macOS)
- `%USERPROFILE%\.termina\config.json` (Windows)

You can also edit this file directly if needed, but using the `termina config` commands is recommended.

## Viewing Current Configuration

To see your current configuration:
```bash
termina config show
```

## Resetting Configuration

To reset your configuration to defaults:
```bash
termina config reset
```