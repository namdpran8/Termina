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
    }
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
