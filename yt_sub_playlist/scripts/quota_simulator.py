# quota_simulator.py

import json
import sys
import os
from pathlib import Path

# Add parent directory to path to enable relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.quota_costs import get_quota_cost


def load_api_call_log() -> dict:
    """
    Load API call counts from the generated log file.
    
    Returns:
        Dictionary of API call counts, or fallback hardcoded values if log missing.
    """
    log_path = Path("yt_sub_playlist/data/api_call_log.json")
    
    try:
        if log_path.exists():
            with open(log_path, 'r') as f:
                api_calls = json.load(f)
            print(f"📄 Loaded API call counts from {log_path}")
            return api_calls
        else:
            print(f"⚠️ API call log not found at {log_path}")
            print("   Run the main application first to generate real usage data")
            print("   Using fallback simulated values...")
    except Exception as e:
        print(f"⚠️ Failed to load API call log: {e}")
        print("   Using fallback simulated values...")
    
    # Fallback hardcoded values
    return {
        "channels.list": 182,
        "playlistItems.insert": 156,
        "playlistItems.list": 180,
        "playlists.list": 1,
        "subscriptions.list": 4,
        "videos.list": 180,
        "search.list": 0,  # deprecated in your code, but useful for comparison
    }

DAILY_QUOTA_LIMIT = 10_000


def calculate_quota_usage(api_calls):
    usage = {}
    total = 0
    for method, count in api_calls.items():
        unit_cost = get_quota_cost(method)
        cost = unit_cost * count
        usage[method] = cost
        total += cost
    return usage, total


def suggest_reductions(usage):
    suggestions = []
    
    insert_cost = get_quota_cost("playlistItems.insert")
    if usage.get("playlistItems.insert", 0) > 5000:
        suggestions.append(
            f"🔻 Reduce `playlistItems.insert` calls ({insert_cost} units each) by:\n"
            "   – Filtering out already-added videos\n"
            "   – Consolidating inserts per session"
        )
    if usage.get("channels.list", 0) > 500:
        suggestions.append(
            "🔻 Cache `channels.list` results if you don't need fresh data per run"
        )
    if usage.get("videos.list", 0) > 500:
        suggestions.append("🔻 Limit `videos.list` to only new/unprocessed video IDs")
    return suggestions


def main():
    api_calls = load_api_call_log()
    usage, total = calculate_quota_usage(api_calls)
    print(f"\n📊 Quota Usage Analysis:")
    for method, cost in usage.items():
        count = api_calls.get(method, 0)
        unit_cost = get_quota_cost(method)
        print(f"  {method:<25}: {count:>3} calls × {unit_cost:>2} units = {cost:>4} units")

    print(f"\n🔢 Total Estimated Usage: {total} / {DAILY_QUOTA_LIMIT} units")

    if total >= DAILY_QUOTA_LIMIT:
        print("\n❗ You're exceeding your quota!")
    elif total >= 0.8 * DAILY_QUOTA_LIMIT:
        print("\n⚠️ Close to quota limit. Consider optimizing:")

    for suggestion in suggest_reductions(usage):
        print(suggestion)


if __name__ == "__main__":
    main()
