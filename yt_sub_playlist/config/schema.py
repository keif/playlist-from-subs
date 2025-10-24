"""
Configuration schema and validation.

This module defines the configuration contract for the application,
including default values, validation rules, and type definitions.
"""

from typing import Any, Dict, Optional, Set


class ConfigSchema:
    """
    Configuration schema definition and validation.
    
    Defines the expected configuration structure, default values,
    and validation rules for the application.
    """
    
    # Default configuration values
    DEFAULTS = {
        "playlist_name": "Auto Playlist from Subscriptions",
        "playlist_visibility": "unlisted",
        "min_duration_seconds": 60,
        "lookback_hours": 24,
        "max_videos": 50,
        "skip_live_content": True,
        "channel_filter_mode": "none",
        "channel_allowlist": None,
        "channel_blocklist": None,
    }
    
    # Required configuration keys
    OPTIONAL_KEYS = {
        "playlist_id",
        "playlist_name",
        "playlist_visibility",
        "min_duration_seconds",
        "lookback_hours",
        "channel_whitelist",  # Legacy - kept for backward compatibility
        "channel_filter_mode",
        "channel_allowlist",
        "channel_blocklist",
        "max_videos",
        "skip_live_content",
    }
    
    # Valid values for specific configuration keys
    VALID_VALUES = {
        "playlist_visibility": {"private", "unlisted", "public"},
        "channel_filter_mode": {"none", "allowlist", "blocklist"},
    }
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize configuration dictionary.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Validated and normalized configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Apply defaults for missing values
        validated_config = cls.DEFAULTS.copy()
        validated_config.update(config)

        # Migrate legacy whitelist to allowlist if needed
        validated_config = cls._migrate_legacy_whitelist(validated_config)

        # Validate specific fields
        cls._validate_playlist_visibility(validated_config.get("playlist_visibility"))
        cls._validate_channel_filter_mode(validated_config.get("channel_filter_mode"))
        cls._validate_channel_lists(validated_config)
        cls._validate_numeric_fields(validated_config)

        return validated_config
    
    @classmethod
    def _migrate_legacy_whitelist(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate legacy channel_whitelist to new allowlist/blocklist system.

        If channel_whitelist exists and new fields are not set, migrate to allowlist mode.
        """
        # If new system is already configured, skip migration
        if config.get("channel_filter_mode") != "none" or config.get("channel_allowlist") or config.get("channel_blocklist"):
            return config

        # Check for legacy whitelist
        legacy_whitelist = config.get("channel_whitelist")
        if legacy_whitelist:
            # Migrate to allowlist mode
            config["channel_filter_mode"] = "allowlist"
            config["channel_allowlist"] = list(legacy_whitelist) if isinstance(legacy_whitelist, set) else legacy_whitelist
            # Keep legacy field for backward compatibility

        return config

    @classmethod
    def _validate_playlist_visibility(cls, visibility: str) -> None:
        """Validate playlist visibility setting."""
        valid_values = cls.VALID_VALUES["playlist_visibility"]
        if visibility not in valid_values:
            raise ValueError(
                f"Invalid playlist_visibility: {visibility}. "
                f"Must be one of: {', '.join(valid_values)}"
            )

    @classmethod
    def _validate_channel_filter_mode(cls, mode: str) -> None:
        """Validate channel filter mode setting."""
        valid_values = cls.VALID_VALUES["channel_filter_mode"]
        if mode not in valid_values:
            raise ValueError(
                f"Invalid channel_filter_mode: {mode}. "
                f"Must be one of: {', '.join(valid_values)}"
            )

    @classmethod
    def _validate_channel_lists(cls, config: Dict[str, Any]) -> None:
        """Validate channel allowlist and blocklist."""
        mode = config.get("channel_filter_mode", "none")
        allowlist = config.get("channel_allowlist")
        blocklist = config.get("channel_blocklist")

        # Validate list types
        if allowlist is not None and not isinstance(allowlist, (list, set)):
            raise ValueError("channel_allowlist must be a list or set of channel IDs")

        if blocklist is not None and not isinstance(blocklist, (list, set)):
            raise ValueError("channel_blocklist must be a list or set of channel IDs")

        # Check for conflicting configuration
        if allowlist and blocklist:
            # Find channels in both lists
            allowlist_set = set(allowlist) if allowlist else set()
            blocklist_set = set(blocklist) if blocklist else set()
            conflicts = allowlist_set & blocklist_set

            if conflicts:
                raise ValueError(
                    f"Channels cannot be in both allowlist and blocklist: {conflicts}"
                )

        # Warn if lists are set but mode doesn't match
        if mode == "allowlist" and blocklist:
            raise ValueError("Cannot use blocklist when filter mode is 'allowlist'")

        if mode == "blocklist" and allowlist:
            raise ValueError("Cannot use allowlist when filter mode is 'blocklist'")
    
    @classmethod
    def _validate_numeric_fields(cls, config: Dict[str, Any]) -> None:
        """Validate numeric configuration fields."""
        numeric_fields = {
            "min_duration_seconds": (0, 86400),  # 0 seconds to 24 hours
            "lookback_hours": (1, 168),          # 1 hour to 7 days
            "max_videos": (1, 200),              # 1 to 200 videos
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            value = config.get(field)
            if value is not None:
                if not isinstance(value, int) or value < min_val or value > max_val:
                    raise ValueError(
                        f"Invalid {field}: {value}. "
                        f"Must be an integer between {min_val} and {max_val}"
                    )
    
    @classmethod
    def get_config_summary(cls, config: Dict[str, Any]) -> str:
        """
        Generate a human-readable configuration summary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Formatted configuration summary string
        """
        summary_lines = [
            "Configuration Summary:",
            f"  Playlist: {config.get('playlist_name', 'Auto Playlist from Subscriptions')}",
            f"  Visibility: {config.get('playlist_visibility', 'unlisted')}",
            f"  Min Duration: {config.get('min_duration_seconds', 60)}s",
            f"  Lookback: {config.get('lookback_hours', 24)} hours",
            f"  Max Videos: {config.get('max_videos', 50)}",
            f"  Skip Live: {config.get('skip_live_content', True)}",
        ]

        # Channel filtering summary
        filter_mode = config.get('channel_filter_mode', 'none')
        if filter_mode == 'allowlist':
            allowlist = config.get('channel_allowlist', [])
            count = len(allowlist) if allowlist else 0
            summary_lines.append(f"  Channel Filter: Allowlist ({count} channels)")
        elif filter_mode == 'blocklist':
            blocklist = config.get('channel_blocklist', [])
            count = len(blocklist) if blocklist else 0
            summary_lines.append(f"  Channel Filter: Blocklist ({count} channels)")
        elif config.get('channel_whitelist'):
            # Legacy whitelist
            whitelist_count = len(config['channel_whitelist'])
            summary_lines.append(f"  Channel Filter: Legacy Whitelist ({whitelist_count} channels)")
        else:
            summary_lines.append(f"  Channel Filter: None (all channels)")

        return "\n".join(summary_lines)