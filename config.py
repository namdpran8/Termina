import os
import json
from pathlib import Path

# The path where our configuration will be stored
CONFIG_DIR = Path.home() / ".termina"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "default_provider": "nvidia",
    "default_model": "meta/llama-3.1-70b-instruct",
    "api_keys": {
        "nvidia": "",
        "openai": "",
        "anthropic": "",
        "gemini": ""
    },
    # New local providers block
    "local_providers": {
        "ollama": {
            "api_base": "http://localhost:11434",
            "enabled": False
        },
        "lmstudio": {
            "api_base": "http://localhost:1234/v1",
            "enabled": False
        },
        "custom": {
            "api_base": "",
            "enabled": False
        }
    }
}

# Model presets for quick reference — shown by `termina config list-models`
MODEL_PRESETS = {
    "nvidia": [
        ("meta/llama-3.1-70b-instruct",      "Default — fast general use (free tier)"),
        ("nvidia/nemotron-3-nano-9b",          "Nemotron Nano — fastest, lowest cost"),
        ("nvidia/nemotron-3-super-120b-a12b",  "Nemotron Super — best tool-calling, agents"),
        ("nvidia/nemotron-ultra-253b-v1",      "Nemotron Ultra — max reasoning"),
    ],
    "openai": [
        ("gpt-4o",       "Best balance of speed and quality"),
        ("gpt-4o-mini",  "Fast and cheap for simple tasks"),
    ],
    "anthropic": [
        ("claude-sonnet-4-6",  "Fast, capable everyday model"),
        ("claude-opus-4-6",    "Most capable, slower"),
    ],
    "gemini": [
        ("gemini-2.0-flash",   "Fast and capable"),
        ("gemini-2.5-pro",     "Best reasoning"),
    ],
    "ollama": [
        ("llama3.2:8b",        "Good tool-calling support"),
        ("qwen2.5-coder:14b",  "Best for coding tasks"),
        ("mistral:7b",         "Fast and lightweight"),
        ("deepseek-coder-v2",  "Strong code generation"),
    ],
    "lmstudio": [
        ("(use whatever model is loaded in LM Studio)", ""),
    ],
}

def load_config() -> dict:
    """
    Loads the configuration from the local config file.
    If it doesn't exist, it creates it with the default configuration.
    """
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all default keys exist
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG

def save_config(config: dict) -> None:
    """
    Saves the provided configuration dictionary to the local config file.
    Creates the directory if it doesn't exist.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_api_key(provider: str) -> str:
    """
    Retrieves the API key for the specified provider.
    First checks environment variables, then falls back to the local config file.
    """
    # Define standard environment variable names for common providers
    env_vars = {
        "nvidia": "NVIDIA_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY"
    }
    
    env_var_name = env_vars.get(provider.lower())
    
    # Check Environment Variable first
    if env_var_name and env_var_name in os.environ:
        return os.environ[env_var_name]
    
    # Fallback to config file
    config = load_config()
    return config.get("api_keys", {}).get(provider.lower(), "")

def set_api_key(provider: str, key: str) -> None:
    """
    Saves a new API key for the specified provider to the local config file.
    """
    config = load_config()
    if "api_keys" not in config:
        config["api_keys"] = {}
    config["api_keys"][provider.lower()] = key
    save_config(config)

def set_default_model(provider: str, model_name: str) -> None:
    """
    Sets the default provider and model in the local config file.
    """
    config = load_config()
    config["default_provider"] = provider
    config["default_model"] = model_name
    save_config(config)

def get_default_model() -> tuple[str, str]:
    """
    Returns the default provider and model.
    """
    config = load_config()
    return config.get("default_provider", "nvidia"), config.get("default_model", "meta/llama-3.1-70b-instruct")

def set_local_provider(provider: str, api_base: str = None) -> None:
    """Enable a local provider, optionally overriding its default api_base."""
    config = load_config()
    if "local_providers" not in config:
        config["local_providers"] = DEFAULT_CONFIG["local_providers"].copy()
    
    defaults = {
        "ollama":   "http://localhost:11434",
        "lmstudio": "http://localhost:1234/v1",
        "custom":   ""
    }
    
    config["local_providers"][provider] = {
        "api_base": api_base or defaults.get(provider, ""),
        "enabled": True
    }
    save_config(config)

def get_local_provider_base(provider: str) -> str:
    """Return the api_base for a local provider."""
    config = load_config()
    return (
        config.get("local_providers", {})
              .get(provider, {})
              .get("api_base", "")
    )
