"""
YouTube API quota tracking and estimation utilities.

This module provides tools for monitoring and estimating YouTube Data API v3
quota usage to help optimize API calls and prevent quota exhaustion.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class QuotaTracker:
    """
    Tracks YouTube API quota usage and provides estimation utilities.
    
    Helps monitor API call costs and provides insights for quota optimization.
    The YouTube Data API v3 has a default quota of 10,000 units per day.
    """
    
    # Standard quota costs for different API methods
    QUOTA_COSTS = {
        # Reading operations (1 unit each)
        'channels.list': 1,
        'playlists.list': 1,
        'playlistItems.list': 1,
        'subscriptions.list': 1,
        'videos.list': 1,
        'activities.list': 1,
        
        # Writing operations (higher costs)
        'playlists.insert': 50,
        'playlistItems.insert': 50,
        'playlists.update': 50,
        'playlistItems.update': 50,
        'playlists.delete': 50,
        'playlistItems.delete': 50,
        
        # Expensive operations
        'search.list': 100,  # Very expensive - avoided in our implementation
        'commentThreads.list': 1,
        'comments.list': 1,
    }
    
    def __init__(self):
        """Initialize quota tracker."""
        self.api_calls: List[Dict] = []
        self.daily_quota_limit = 10000
        self.reset()
    
    def reset(self):
        """Reset quota tracking for a new session."""
        self.api_calls.clear()
        logger.debug("Quota tracker reset")
    
    def record_api_call(self, method: str, count: int = 1, items_processed: int = 0):
        """
        Record an API call for quota tracking.
        
        Args:
            method: API method name (e.g., 'videos.list', 'playlistItems.insert')
            count: Number of times this method was called (default: 1)
            items_processed: Number of items processed in the call (for batching info)
        """
        cost_per_call = self.QUOTA_COSTS.get(method, 1)
        total_cost = cost_per_call * count
        
        call_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'method': method,
            'calls': count,
            'cost_per_call': cost_per_call,
            'total_cost': total_cost,
            'items_processed': items_processed
        }
        
        self.api_calls.append(call_record)
        logger.debug(f"Recorded API call: {method} x{count} = {total_cost} quota units")
    
    def get_session_usage(self) -> Dict:
        """
        Get quota usage summary for the current session.
        
        Returns:
            Dictionary with usage statistics
        """
        if not self.api_calls:
            return {
                'total_quota_used': 0,
                'total_calls': 0,
                'methods_used': {},
                'quota_remaining': self.daily_quota_limit,
                'usage_percentage': 0.0
            }
        
        total_quota_used = sum(call['total_cost'] for call in self.api_calls)
        total_calls = sum(call['calls'] for call in self.api_calls)
        
        # Group by method
        methods_used = {}
        for call in self.api_calls:
            method = call['method']
            if method not in methods_used:
                methods_used[method] = {
                    'calls': 0,
                    'total_cost': 0,
                    'items_processed': 0
                }
            methods_used[method]['calls'] += call['calls']
            methods_used[method]['total_cost'] += call['total_cost']
            methods_used[method]['items_processed'] += call['items_processed']
        
        return {
            'total_quota_used': total_quota_used,
            'total_calls': total_calls,
            'methods_used': methods_used,
            'quota_remaining': max(0, self.daily_quota_limit - total_quota_used),
            'usage_percentage': (total_quota_used / self.daily_quota_limit) * 100
        }
    
    def estimate_operation_cost(self, operation: str, item_count: int) -> int:
        """
        Estimate quota cost for a planned operation.
        
        Args:
            operation: Type of operation ('fetch_videos', 'add_to_playlist', etc.)
            item_count: Number of items to process
            
        Returns:
            Estimated quota cost in units
        """
        if operation == 'fetch_videos':
            # videos.list is batched up to 50 items per call
            batch_size = 50
            batches_needed = (item_count + batch_size - 1) // batch_size
            return batches_needed * self.QUOTA_COSTS['videos.list']
        
        elif operation == 'add_to_playlist':
            # Each playlist insertion costs 50 units
            return item_count * self.QUOTA_COSTS['playlistItems.insert']
        
        elif operation == 'fetch_subscriptions':
            # subscriptions.list, typically needs 1-2 calls for most users
            return 2 * self.QUOTA_COSTS['subscriptions.list']
        
        elif operation == 'fetch_playlist_items':
            # playlistItems.list, batched up to 50 items per call
            batch_size = 50
            batches_needed = (item_count + batch_size - 1) // batch_size
            return batches_needed * self.QUOTA_COSTS['playlistItems.list']
        
        else:
            logger.warning(f"Unknown operation for cost estimation: {operation}")
            return item_count  # Conservative estimate
    
    def log_usage_summary(self):
        """Log a detailed usage summary."""
        usage = self.get_session_usage()
        
        logger.info("=== Quota Usage Summary ===")
        logger.info(f"Total quota used: {usage['total_quota_used']} / {self.daily_quota_limit} units")
        logger.info(f"Usage percentage: {usage['usage_percentage']:.1f}%")
        logger.info(f"Quota remaining: {usage['quota_remaining']} units")
        logger.info(f"Total API calls: {usage['total_calls']}")
        
        if usage['methods_used']:
            logger.info("Methods breakdown:")
            for method, stats in usage['methods_used'].items():
                logger.info(f"  {method}: {stats['calls']} calls, {stats['total_cost']} units")
                if stats['items_processed']:
                    efficiency = stats['items_processed'] / stats['calls']
                    logger.info(f"    Efficiency: {efficiency:.1f} items per call")
    
    def is_quota_exceeded(self, threshold_percentage: float = 90.0) -> bool:
        """
        Check if quota usage exceeds a threshold.
        
        Args:
            threshold_percentage: Percentage threshold (default: 90%)
            
        Returns:
            True if quota usage exceeds threshold
        """
        usage = self.get_session_usage()
        return usage['usage_percentage'] >= threshold_percentage
    
    def get_optimization_suggestions(self) -> List[str]:
        """
        Get suggestions for quota optimization based on current usage.
        
        Returns:
            List of optimization suggestions
        """
        usage = self.get_session_usage()
        suggestions = []
        
        methods = usage['methods_used']
        
        # Check for expensive operations
        if 'search.list' in methods:
            suggestions.append(
                "⚠️  Replace search.list calls with uploads playlist lookup (saves ~100 units per call)"
            )
        
        # Check for inefficient batching
        if 'videos.list' in methods:
            video_stats = methods['videos.list']
            if video_stats['items_processed'] > 0:
                efficiency = video_stats['items_processed'] / video_stats['calls']
                if efficiency < 30:  # Less than 30 items per call indicates poor batching
                    suggestions.append(
                        f"💡 Improve videos.list batching efficiency (currently {efficiency:.1f} items per call)"
                    )
        
        # Check for high insertion costs
        if 'playlistItems.insert' in methods:
            insert_cost = methods['playlistItems.insert']['total_cost']
            total_cost = usage['total_quota_used']
            if insert_cost / total_cost > 0.5:  # More than 50% of quota on insertions
                suggestions.append(
                    "💡 Consider pre-filtering duplicates to reduce playlist insertion costs"
                )
        
        # General high usage warning
        if usage['usage_percentage'] > 70:
            suggestions.append(
                "⚠️  High quota usage detected. Consider reducing LOOKBACK_HOURS or using --limit flag"
            )
        
        return suggestions