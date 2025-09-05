# quota_simulator.py

import sys
import os

# Add parent directory to path to enable relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.quota_costs import get_quota_cost

# Simulate usage — replace these numbers with your actual or expected call counts
api_calls = {
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
    usage, total = calculate_quota_usage(api_calls)
    print(f"\n📊 Simulated Quota Usage:")
    for method, cost in usage.items():
        print(f"  {method:<25}: {cost} units")

    print(f"\n🔢 Total Estimated Usage: {total} / {DAILY_QUOTA_LIMIT} units")

    if total >= DAILY_QUOTA_LIMIT:
        print("\n❗ You're exceeding your quota!")
    elif total >= 0.8 * DAILY_QUOTA_LIMIT:
        print("\n⚠️ Close to quota limit. Consider optimizing:")

    for suggestion in suggest_reductions(usage):
        print(suggestion)


if __name__ == "__main__":
    main()
