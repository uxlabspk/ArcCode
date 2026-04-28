"""
Settings management for Arc Code CLI - Persistent configuration storage
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class SettingsManager:
    """Manages persistent settings for Arc Code CLI"""

    DEFAULT_SETTINGS = {
        "provider": "llama.cpp",
        "model": "llama.cpp",
        "server_url": "http://localhost:8080",
        "verbose": False,
        "thinking_mode": False,
        "max_context_messages": 20,
        "max_history": 100,
    }

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".arccode"

        self.config_file = self.config_dir / "config.json"
        self.settings = self.DEFAULT_SETTINGS.copy()
        self._load()

    def _load(self):
        """Load settings from config file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                # Merge with defaults (saved settings override defaults)
                self.settings.update(saved_settings)
            except (json.JSONDecodeError, IOError) as e:
                # If file is corrupted, start fresh with defaults
                print(f"Warning: Config file corrupted, using defaults: {e}")
                self.settings = self.DEFAULT_SETTINGS.copy()

    def save(self):
        """Save current settings to config file"""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving settings: {e}")
            return False

    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value

    def update(self, updates: Dict[str, Any]):
        """Update multiple settings at once"""
        self.settings.update(updates)

    def reset(self):
        """Reset all settings to defaults"""
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save()

    def to_dict(self) -> Dict[str, Any]:
        """Return settings as dictionary"""
        return self.settings.copy()

    def __repr__(self):
        return f"SettingsManager({self.config_file})"
