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
    }
    
    # Required configuration keys
    OPTIONAL_KEYS = {
        "playlist_id",
        "playlist_name", 
        "playlist_visibility",
        "min_duration_seconds",
        "lookback_hours",
        "channel_whitelist",
        "max_videos",
        "skip_live_content",
    }
    
    # Valid values for specific configuration keys
    VALID_VALUES = {
        "playlist_visibility": {"private", "unlisted", "public"},
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
        
        # Validate specific fields
        cls._validate_playlist_visibility(validated_config.get("playlist_visibility"))
        cls._validate_numeric_fields(validated_config)
        
        return validated_config
    
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
        
        if config.get('channel_whitelist'):
            whitelist_count = len(config['channel_whitelist'])
            summary_lines.append(f"  Channel Whitelist: {whitelist_count} channels")
        
        return "\n".join(summary_lines)