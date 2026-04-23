"""
Mini-Ultra Configuration Loader
Loads config from JSON file and environment variables.
"""
import json
import os
from pathlib import Path
from typing import Any, Optional
from utils.logger import log_info, log_error, log_warning
from utils.error_handlers import ConfigError


DEFAULT_CONFIG = {
    "agent_name": "Mini-Ultra",
    "version": "1.0.0",
    "llm": {
        "provider": "ollama",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llama3.2:latest",
        "openai_api_key": "",
        "openai_model": "gpt-4.1-mini",
        "openai_base_url": "https://api.openai.com/v1",
        "temperature": 0.7,
        "max_tokens": 2000,
        "timeout": 30
    },
    "features": {
        "voice_enabled": False,
        "vision_enabled": False,
        "memory_enabled": True,
        "tools_enabled": True
    },
    "server": {
        "api_host": "0.0.0.0",
        "api_port": 5000,
        "web_host": "0.0.0.0",
        "web_port": 8080
    },
    "memory": {
        "max_items": 1000,
        "persist_path": "data/memory.json"
    },
    "logging": {
        "level": "INFO",
        "file": "logs/mini_ultra.log"
    },
    "debug": False
}


class Config:
    """Configuration container with dot-notation access."""

    def __init__(self, data: dict):
        self._data = data

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value using dot notation (e.g., 'llm.provider')."""
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any):
        """Set config value using dot notation."""
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value

    @property
    def raw(self) -> dict:
        return self._data

    def __repr__(self):
        return f"Config({json.dumps(self._data, indent=2)})"


def load_config(config_path: str = "mini_ultra_config.json") -> Config:
    """Load configuration from file, with env var overrides."""
    config_data = DEFAULT_CONFIG.copy()

    # Load from file
    path = Path(config_path)
    if path.exists():
        try:
            with open(path, "r") as f:
                file_config = json.load(f)
            config_data = _deep_merge(config_data, file_config)
            log_info("config", f"Loaded config from {config_path}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {config_path}: {e}")
        except Exception as e:
            log_warning("config", f"Could not load {config_path}: {e}, using defaults")
    else:
        log_warning("config", f"Config file {config_path} not found, using defaults")

    # Environment variable overrides
    env_overrides = {
        "OPENAI_API_KEY": "llm.openai_api_key",
        "OPENAI_BASE_URL": "llm.openai_base_url",
        "OLLAMA_BASE_URL": "llm.ollama_base_url",
        "OLLAMA_MODEL": "llm.ollama_model",
        "API_HOST": "server.api_host",
        "API_PORT": "server.api_port",
        "WEB_HOST": "server.web_host",
        "WEB_PORT": "server.web_port",
        "LOG_LEVEL": "logging.level",
        "DEBUG": "debug",
    }

    config = Config(config_data)
    for env_key, config_key in env_overrides.items():
        env_val = os.environ.get(env_key)
        if env_val is not None:
            # Type coercion
            if env_val.lower() in ("true", "false"):
                env_val = env_val.lower() == "true"
            elif env_val.isdigit():
                env_val = int(env_val)
            config.set(config_key, env_val)
            log_info("config", f"Override from env: {env_key} -> {config_key}")

    # Auto-detect provider from available keys
    if config.get("llm.openai_api_key") and not config.get("llm.provider"):
        config.set("llm.provider", "openai")

    return config


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts, override takes priority."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
