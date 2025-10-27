"""
Configuration schema and validation.

This module defines the configuration contract for the application,
including default values, validation rules, and type definitions.
"""

from datetime import datetime
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
        "max_duration_seconds": None,  # None = unlimited
        "lookback_hours": 24,
        "date_filter_mode": "lookback",  # "lookback", "days", "date_range"
        "date_filter_days": None,        # Override lookback_hours with "last N days"
        "date_filter_start": None,       # YYYY-MM-DD
        "date_filter_end": None,         # YYYY-MM-DD
        "max_videos": 50,
        "skip_live_content": True,
        "channel_filter_mode": "none",
        "channel_allowlist": None,
        "channel_blocklist": None,
        "keyword_filter_mode": "none",   # "none", "include", "exclude", "both"
        "keyword_include": None,         # List of keywords to include
        "keyword_exclude": None,         # List of keywords to exclude
        "keyword_match_type": "any",     # "any" or "all"
        "keyword_case_sensitive": False,
        "keyword_search_description": False,  # Search in description too
    }
    
    # Required configuration keys
    OPTIONAL_KEYS = {
        "playlist_id",
        "playlist_name",
        "playlist_visibility",
        "min_duration_seconds",
        "max_duration_seconds",
        "lookback_hours",
        "date_filter_mode",
        "date_filter_days",
        "date_filter_start",
        "date_filter_end",
        "channel_whitelist",  # Legacy - kept for backward compatibility
        "channel_filter_mode",
        "channel_allowlist",
        "channel_blocklist",
        "keyword_filter_mode",
        "keyword_include",
        "keyword_exclude",
        "keyword_match_type",
        "keyword_case_sensitive",
        "keyword_search_description",
        "max_videos",
        "skip_live_content",
    }
    
    # Valid values for specific configuration keys
    VALID_VALUES = {
        "playlist_visibility": {"private", "unlisted", "public"},
        "channel_filter_mode": {"none", "allowlist", "blocklist"},
        "date_filter_mode": {"lookback", "days", "date_range"},
        "keyword_filter_mode": {"none", "include", "exclude", "both"},
        "keyword_match_type": {"any", "all"},
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
        cls._validate_date_filter_mode(validated_config.get("date_filter_mode"))
        cls._validate_date_filters(validated_config)
        cls._validate_keyword_filter_mode(validated_config.get("keyword_filter_mode"))
        cls._validate_keyword_match_type(validated_config.get("keyword_match_type"))
        cls._validate_keyword_filters(validated_config)

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
            "max_duration_seconds": (1, 86400),  # 1 second to 24 hours (None allowed)
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

        # Validate duration range logic
        min_duration = config.get("min_duration_seconds")
        max_duration = config.get("max_duration_seconds")
        if min_duration is not None and max_duration is not None:
            if max_duration < min_duration:
                raise ValueError(
                    f"max_duration_seconds ({max_duration}) cannot be less than "
                    f"min_duration_seconds ({min_duration})"
                )

    @classmethod
    def _validate_date_filter_mode(cls, mode: str) -> None:
        """Validate date filter mode setting."""
        valid_values = cls.VALID_VALUES["date_filter_mode"]
        if mode not in valid_values:
            raise ValueError(
                f"Invalid date_filter_mode: {mode}. "
                f"Must be one of: {', '.join(valid_values)}"
            )

    @classmethod
    def _validate_date_filters(cls, config: Dict[str, Any]) -> None:
        """Validate date filter configuration fields."""
        mode = config.get("date_filter_mode", "lookback")

        # Validate date_filter_days (if set)
        days = config.get("date_filter_days")
        if days is not None:
            if not isinstance(days, int) or days < 1 or days > 365:
                raise ValueError(
                    f"Invalid date_filter_days: {days}. "
                    f"Must be an integer between 1 and 365"
                )

        # Validate date_filter_start and date_filter_end (if set)
        start_date_str = config.get("date_filter_start")
        end_date_str = config.get("date_filter_end")

        if start_date_str is not None:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid date_filter_start: {start_date_str}. "
                    f"Must be in YYYY-MM-DD format"
                )

        if end_date_str is not None:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid date_filter_end: {end_date_str}. "
                    f"Must be in YYYY-MM-DD format"
                )

        # Validate date range logic (start <= end)
        if start_date_str is not None and end_date_str is not None:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            if end_date < start_date:
                raise ValueError(
                    f"date_filter_end ({end_date_str}) cannot be before "
                    f"date_filter_start ({start_date_str})"
                )

        # Validate mode-specific requirements
        if mode == "days" and days is None:
            raise ValueError(
                "date_filter_days is required when date_filter_mode is 'days'"
            )

        if mode == "date_range":
            if start_date_str is None or end_date_str is None:
                raise ValueError(
                    "Both date_filter_start and date_filter_end are required "
                    "when date_filter_mode is 'date_range'"
                )

    @classmethod
    def _validate_keyword_filter_mode(cls, mode: str) -> None:
        """Validate keyword filter mode setting."""
        valid_values = cls.VALID_VALUES["keyword_filter_mode"]
        if mode not in valid_values:
            raise ValueError(
                f"Invalid keyword_filter_mode: {mode}. "
                f"Must be one of: {', '.join(valid_values)}"
            )

    @classmethod
    def _validate_keyword_match_type(cls, match_type: str) -> None:
        """Validate keyword match type setting."""
        valid_values = cls.VALID_VALUES["keyword_match_type"]
        if match_type not in valid_values:
            raise ValueError(
                f"Invalid keyword_match_type: {match_type}. "
                f"Must be one of: {', '.join(valid_values)}"
            )

    @classmethod
    def _validate_keyword_filters(cls, config: Dict[str, Any]) -> None:
        """Validate keyword filter configuration fields."""
        mode = config.get("keyword_filter_mode", "none")
        include_list = config.get("keyword_include")
        exclude_list = config.get("keyword_exclude")

        # Validate list types
        if include_list is not None:
            if not isinstance(include_list, list):
                raise ValueError("keyword_include must be a list of strings")
            # Check all items are strings
            if not all(isinstance(k, str) for k in include_list):
                raise ValueError("keyword_include must contain only strings")

        if exclude_list is not None:
            if not isinstance(exclude_list, list):
                raise ValueError("keyword_exclude must be a list of strings")
            # Check all items are strings
            if not all(isinstance(k, str) for k in exclude_list):
                raise ValueError("keyword_exclude must contain only strings")

        # Validate boolean fields
        case_sensitive = config.get("keyword_case_sensitive", False)
        search_description = config.get("keyword_search_description", False)

        if not isinstance(case_sensitive, bool):
            raise ValueError("keyword_case_sensitive must be a boolean")

        if not isinstance(search_description, bool):
            raise ValueError("keyword_search_description must be a boolean")

        # Validate mode-specific requirements
        if mode == "include" and (not include_list or len(include_list) == 0):
            raise ValueError(
                "keyword_include list is required and must not be empty "
                "when keyword_filter_mode is 'include'"
            )

        if mode == "exclude" and (not exclude_list or len(exclude_list) == 0):
            raise ValueError(
                "keyword_exclude list is required and must not be empty "
                "when keyword_filter_mode is 'exclude'"
            )

        if mode == "both":
            if not include_list or len(include_list) == 0:
                raise ValueError(
                    "keyword_include list is required and must not be empty "
                    "when keyword_filter_mode is 'both'"
                )
            if not exclude_list or len(exclude_list) == 0:
                raise ValueError(
                    "keyword_exclude list is required and must not be empty "
                    "when keyword_filter_mode is 'both'"
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
        ]

        # Duration summary
        min_dur = config.get('min_duration_seconds', 60)
        max_dur = config.get('max_duration_seconds')
        if max_dur:
            summary_lines.append(f"  Duration Range: {min_dur}s - {max_dur}s")
        else:
            summary_lines.append(f"  Min Duration: {min_dur}s")

        # Date filtering summary
        date_mode = config.get('date_filter_mode', 'lookback')
        if date_mode == 'lookback':
            summary_lines.append(f"  Lookback: {config.get('lookback_hours', 24)} hours")
        elif date_mode == 'days':
            days = config.get('date_filter_days', 7)
            summary_lines.append(f"  Date Filter: Last {days} days")
        elif date_mode == 'date_range':
            start = config.get('date_filter_start', 'N/A')
            end = config.get('date_filter_end', 'N/A')
            summary_lines.append(f"  Date Filter: {start} to {end}")

        summary_lines.extend([
            f"  Max Videos: {config.get('max_videos', 50)}",
            f"  Skip Live: {config.get('skip_live_content', True)}",
        ])

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

        # Keyword filtering summary
        keyword_mode = config.get('keyword_filter_mode', 'none')
        if keyword_mode != 'none':
            include_list = config.get('keyword_include', [])
            exclude_list = config.get('keyword_exclude', [])
            match_type = config.get('keyword_match_type', 'any')

            if keyword_mode == 'include':
                summary_lines.append(f"  Keyword Filter: Include ({len(include_list)} keywords, {match_type})")
            elif keyword_mode == 'exclude':
                summary_lines.append(f"  Keyword Filter: Exclude ({len(exclude_list)} keywords)")
            elif keyword_mode == 'both':
                summary_lines.append(f"  Keyword Filter: Include ({len(include_list)}) + Exclude ({len(exclude_list)})")

        return "\n".join(summary_lines)