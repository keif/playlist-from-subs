"""
Configuration Manager for Dashboard

Handles configuration persistence using a hybrid approach:
- Secrets (API keys) in .env file (gitignored)
- User preferences in config.json (can be committed)
- Merges both sources for complete configuration
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default configuration file location
CONFIG_FILE = Path(__file__).parent.parent.parent / "config.json"


class ConfigManager:
    """
    Manages configuration persistence and retrieval.

    Separates secrets (in .env) from user preferences (in config.json).
    Provides validation and default values.
    """

    # Default user preferences
    DEFAULT_CONFIG = {
        "playlist_name": "Auto Playlist from Subscriptions",
        "playlist_visibility": "unlisted",
        "min_duration_seconds": 60,
        "lookback_hours": 24,
        "max_videos": 50,
        "skip_live_content": True,
        "channel_whitelist": None,  # Legacy - kept for backward compatibility
        "channel_filter_mode": "none",
        "channel_allowlist": None,
        "channel_blocklist": None
    }

    # Validation ranges
    VALIDATION_RULES = {
        "min_duration_seconds": {"min": 0, "max": 86400, "type": int},
        "lookback_hours": {"min": 1, "max": 168, "type": int},
        "max_videos": {"min": 1, "max": 200, "type": int},
        "playlist_visibility": {"options": ["private", "unlisted", "public"]},
        "skip_live_content": {"type": bool},
        "channel_filter_mode": {"options": ["none", "allowlist", "blocklist"]}
    }

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_file: Path to config.json file (uses default if None)
        """
        self.config_file = config_file or CONFIG_FILE
        self._ensure_config_file_exists()

    def _ensure_config_file_exists(self) -> None:
        """Create config file with defaults if it doesn't exist."""
        if not self.config_file.exists():
            logger.info(f"Creating default config file at {self.config_file}")
            self.save_config(self.DEFAULT_CONFIG)

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from config.json.

        Returns:
            Configuration dictionary with user preferences
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Merge with defaults for any missing keys
            merged_config = self.DEFAULT_CONFIG.copy()
            merged_config.update(config)

            logger.debug(f"Loaded config from {self.config_file}")
            return merged_config

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            logger.warning("Using default configuration")
            return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to config.json.

        Args:
            config: Configuration dictionary to save

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Validate before saving
            validation_result = self.validate_config(config)
            if not validation_result["valid"]:
                logger.error(f"Config validation failed: {validation_result['errors']}")
                return False

            # Create backup of existing config
            if self.config_file.exists():
                backup_path = self.config_file.with_suffix('.json.bak')
                with open(self.config_file, 'r') as f:
                    backup_data = f.read()
                with open(backup_path, 'w') as f:
                    f.write(backup_data)

            # Save new config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"Config saved to {self.config_file}")
            return True

        except Exception as e:
            logger.exception(f"Error saving config: {e}")
            return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration values.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Dict with 'valid' boolean and list of 'errors'
        """
        errors = []

        for key, rules in self.VALIDATION_RULES.items():
            if key not in config:
                continue

            value = config[key]

            # Type validation
            if "type" in rules:
                if not isinstance(value, rules["type"]):
                    errors.append(f"{key} must be {rules['type'].__name__}, got {type(value).__name__}")
                    continue

            # Range validation for integers
            if "min" in rules and "max" in rules:
                if not isinstance(value, int):
                    errors.append(f"{key} must be an integer")
                elif value < rules["min"] or value > rules["max"]:
                    errors.append(f"{key} must be between {rules['min']} and {rules['max']}")

            # Options validation
            if "options" in rules:
                if value not in rules["options"]:
                    errors.append(f"{key} must be one of: {', '.join(rules['options'])}")

        # Validate channel_whitelist format (legacy)
        if "channel_whitelist" in config:
            whitelist = config["channel_whitelist"]
            if whitelist is not None:
                if not isinstance(whitelist, list):
                    errors.append("channel_whitelist must be a list or null")
                else:
                    if not all(isinstance(ch, str) for ch in whitelist):
                        errors.append("channel_whitelist must contain only strings")

        # Validate channel_allowlist format
        if "channel_allowlist" in config:
            allowlist = config["channel_allowlist"]
            if allowlist is not None:
                if not isinstance(allowlist, list):
                    errors.append("channel_allowlist must be a list or null")
                else:
                    if not all(isinstance(ch, str) for ch in allowlist):
                        errors.append("channel_allowlist must contain only strings")

        # Validate channel_blocklist format
        if "channel_blocklist" in config:
            blocklist = config["channel_blocklist"]
            if blocklist is not None:
                if not isinstance(blocklist, list):
                    errors.append("channel_blocklist must be a list or null")
                else:
                    if not all(isinstance(ch, str) for ch in blocklist):
                        errors.append("channel_blocklist must contain only strings")

        # Validate channel filter mode consistency
        mode = config.get("channel_filter_mode", "none")
        allowlist = config.get("channel_allowlist")
        blocklist = config.get("channel_blocklist")

        if allowlist and blocklist:
            # Check for conflicts
            allowlist_set = set(allowlist) if allowlist else set()
            blocklist_set = set(blocklist) if blocklist else set()
            conflicts = allowlist_set & blocklist_set
            if conflicts:
                errors.append(f"Channels cannot be in both allowlist and blocklist")

        if mode == "allowlist" and blocklist:
            errors.append("Cannot use blocklist when filter mode is 'allowlist'")

        if mode == "blocklist" and allowlist:
            errors.append("Cannot use allowlist when filter mode is 'blocklist'")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def get_defaults(self) -> Dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            Dictionary of default configuration values
        """
        return self.DEFAULT_CONFIG.copy()

    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults.

        Returns:
            True if reset successful, False otherwise
        """
        return self.save_config(self.DEFAULT_CONFIG)

    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update specific configuration values.

        Args:
            updates: Dictionary of values to update

        Returns:
            Dict with 'success' boolean and updated 'config' or 'errors'
        """
        try:
            # Load current config
            current_config = self.load_config()

            # Apply updates
            updated_config = current_config.copy()
            updated_config.update(updates)

            # Validate
            validation = self.validate_config(updated_config)
            if not validation["valid"]:
                return {
                    "success": False,
                    "errors": validation["errors"]
                }

            # Save
            if self.save_config(updated_config):
                return {
                    "success": True,
                    "config": updated_config
                }
            else:
                return {
                    "success": False,
                    "errors": ["Failed to save configuration"]
                }

        except Exception as e:
            logger.exception("Error updating config")
            return {
                "success": False,
                "errors": [str(e)]
            }

    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration.

        Returns:
            Dictionary with config summary information
        """
        config = self.load_config()

        # Build channel filter summary
        filter_mode = config.get("channel_filter_mode", "none")
        channel_filter_summary = {
            "mode": filter_mode
        }

        if filter_mode == "allowlist":
            allowlist = config.get("channel_allowlist", [])
            channel_filter_summary["allowlist"] = {
                "enabled": True,
                "count": len(allowlist) if allowlist else 0,
                "channels": allowlist
            }
        elif filter_mode == "blocklist":
            blocklist = config.get("channel_blocklist", [])
            channel_filter_summary["blocklist"] = {
                "enabled": True,
                "count": len(blocklist) if blocklist else 0,
                "channels": blocklist
            }
        elif config.get("channel_whitelist"):
            # Legacy whitelist
            channel_filter_summary["legacy_whitelist"] = {
                "enabled": True,
                "count": len(config["channel_whitelist"]),
                "channels": config["channel_whitelist"]
            }

        return {
            "playlist": {
                "name": config["playlist_name"],
                "visibility": config["playlist_visibility"]
            },
            "filters": {
                "min_duration_seconds": config["min_duration_seconds"],
                "lookback_hours": config["lookback_hours"],
                "max_videos": config["max_videos"],
                "skip_live_content": config["skip_live_content"]
            },
            "channel_filter": channel_filter_summary
        }
