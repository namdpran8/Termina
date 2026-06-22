import os
import json
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

from config import load_config, get_api_key, set_api_key, set_default_model, get_default_model

# Mock config file path for testing
MOCK_CONFIG_DIR = Path("/tmp/mock_termina")
MOCK_CONFIG_FILE = MOCK_CONFIG_DIR / "config.json"

@pytest.fixture
def mock_config_path(monkeypatch):
    """Fixture to mock the CONFIG_FILE and CONFIG_DIR paths in config.py"""
    monkeypatch.setattr("config.CONFIG_DIR", MOCK_CONFIG_DIR)
    monkeypatch.setattr("config.CONFIG_FILE", MOCK_CONFIG_FILE)

def test_load_config_creates_default(mock_config_path, tmp_path):
    """Test that load_config creates a default config if one doesn't exist."""
    # Use a real temp file so we can verify it gets created
    temp_config_dir = tmp_path / ".termina"
    temp_config_file = temp_config_dir / "config.json"
    
    with patch("config.CONFIG_DIR", temp_config_dir), patch("config.CONFIG_FILE", temp_config_file):
        config = load_config()
        assert temp_config_file.exists()
        assert config["default_provider"] == "nvidia"
        assert "api_keys" in config

def test_get_api_key_from_env(monkeypatch):
    """Test that get_api_key prioritizes environment variables."""
    monkeypatch.setenv("NVIDIA_API_KEY", "env_nvidia_key")
    key = get_api_key("nvidia")
    assert key == "env_nvidia_key"

@patch("config.load_config")
def test_get_api_key_from_config(mock_load_config, monkeypatch):
    """Test that get_api_key falls back to config file if env var is missing."""
    # Ensure no env var
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    mock_load_config.return_value = {"api_keys": {"openai": "config_openai_key"}}
    key = get_api_key("openai")
    assert key == "config_openai_key"

@patch("config.save_config")
@patch("config.load_config")
def test_set_api_key(mock_load_config, mock_save_config):
    """Test that set_api_key updates the config file."""
    mock_load_config.return_value = {"api_keys": {}}
    set_api_key("gemini", "new_gemini_key")
    
    mock_save_config.assert_called_once()
    saved_dict = mock_save_config.call_args[0][0]
    assert saved_dict["api_keys"]["gemini"] == "new_gemini_key"

@patch("config.save_config")
@patch("config.load_config")
def test_set_default_model(mock_load_config, mock_save_config):
    """Test that set_default_model updates the config file."""
    mock_load_config.return_value = {"default_provider": "old", "default_model": "old_model"}
    set_default_model("anthropic", "claude-3-5-sonnet")
    
    mock_save_config.assert_called_once()
    saved_dict = mock_save_config.call_args[0][0]
    assert saved_dict["default_provider"] == "anthropic"
    assert saved_dict["default_model"] == "claude-3-5-sonnet"
