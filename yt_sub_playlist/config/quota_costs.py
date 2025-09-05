"""
YouTube API quota cost management.

Provides functions to load and retrieve quota costs for YouTube Data API v3 methods.
"""

import json
import logging
import os
from typing import Dict, Optional

# Global cache for quota costs
_QUOTA_COSTS: Optional[Dict[str, int]] = None

logger = logging.getLogger(__name__)


def load_quota_costs() -> Dict[str, int]:
    """
    Load quota costs from the JSON configuration file.
    
    Returns:
        Dict mapping API method names to their quota costs.
        
    Raises:
        FileNotFoundError: If the quota costs file doesn't exist.
        json.JSONDecodeError: If the JSON file is malformed.
    """
    global _QUOTA_COSTS
    
    if _QUOTA_COSTS is not None:
        return _QUOTA_COSTS
    
    # Get the directory containing this module
    config_dir = os.path.dirname(__file__)
    quota_file = os.path.join(config_dir, 'youtube_quota_costs.json')
    
    try:
        with open(quota_file, 'r') as f:
            _QUOTA_COSTS = json.load(f)
        
        logger.debug(f"Loaded {len(_QUOTA_COSTS)} quota cost entries from {quota_file}")
        return _QUOTA_COSTS
        
    except FileNotFoundError:
        logger.error(f"Quota costs file not found: {quota_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in quota costs file: {e}")
        raise


def get_quota_cost(api_call: str) -> int:
    """
    Get the quota cost for a specific YouTube API method.
    
    Args:
        api_call: The API method name (e.g., "videos.list", "playlistItems.insert")
        
    Returns:
        The quota cost for the API call, or 1 if unknown.
    """
    try:
        quota_costs = load_quota_costs()
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning(f"Could not load quota costs, using default cost of 1 for '{api_call}'")
        return 1
    
    if api_call in quota_costs:
        return quota_costs[api_call]
    else:
        logger.warning(f"Unknown API method '{api_call}', using default quota cost of 1")
        return 1


def get_all_quota_costs() -> Dict[str, int]:
    """
    Get all available quota costs.
    
    Returns:
        Dict mapping API method names to their quota costs.
    """
    try:
        return load_quota_costs()
    except (FileNotFoundError, json.JSONDecodeError):
        logger.warning("Could not load quota costs, returning empty dict")
        return {}


def reload_quota_costs() -> None:
    """Force reload of quota costs from disk."""
    global _QUOTA_COSTS
    _QUOTA_COSTS = None
    load_quota_costs()