"""
Regression tests for issue #25: --dry-run must not create a playlist.

Prior behaviour: PlaylistManager.get_or_create_playlist called the underlying
YouTubeClient unconditionally, and YouTubeClient.get_or_create_playlist
inserted a new playlist whenever it was passed a None playlist_id. Running
`--dry-run` with PLAYLIST_ID unset therefore mutated the user's YouTube
account before the dry-run branch of the sync ever ran.

These tests pin the fixed behaviour:

- dry-run + no playlist_id → no API insert, sentinel returned, warning logged
- dry-run + explicit playlist_id → read-only verification still happens
- non-dry-run + no playlist_id → insert path still runs (unchanged)
"""
import unittest
from unittest.mock import MagicMock, patch

from yt_sub_playlist.core.playlist_manager import PlaylistManager


class DryRunPlaylistTests(unittest.TestCase):
    def _make_manager(self):
        manager = PlaylistManager.__new__(PlaylistManager)
        manager.client = MagicMock()
        manager.cache = MagicMock()
        manager.filter = MagicMock()
        manager.data_dir = "yt_sub_playlist/data"
        manager.config = {}
        return manager

    def test_dry_run_without_playlist_id_never_calls_client(self):
        manager = self._make_manager()

        result = manager.get_or_create_playlist(
            playlist_id=None,
            playlist_name="my playlist",
            privacy_status="unlisted",
            dry_run=True,
        )

        manager.client.get_or_create_playlist.assert_not_called()
        self.assertEqual(result, PlaylistManager.DRY_RUN_PLAYLIST_ID)

    def test_dry_run_with_playlist_id_still_verifies_existence(self):
        manager = self._make_manager()
        manager.client.get_or_create_playlist.return_value = "PLxxx"

        result = manager.get_or_create_playlist(
            playlist_id="PLxxx",
            playlist_name="my playlist",
            privacy_status="unlisted",
            dry_run=True,
        )

        manager.client.get_or_create_playlist.assert_called_once_with(
            playlist_id="PLxxx",
            playlist_name="my playlist",
            privacy_status="unlisted",
        )
        self.assertEqual(result, "PLxxx")

    def test_non_dry_run_without_playlist_id_still_creates(self):
        manager = self._make_manager()
        manager.client.get_or_create_playlist.return_value = "PLnew"

        result = manager.get_or_create_playlist(
            playlist_id=None,
            playlist_name=None,
            privacy_status="unlisted",
            dry_run=False,
        )

        manager.client.get_or_create_playlist.assert_called_once()
        _, kwargs = manager.client.get_or_create_playlist.call_args
        self.assertIsNone(kwargs["playlist_id"])
        self.assertEqual(kwargs["playlist_name"], "Auto Playlist from Subscriptions")
        self.assertEqual(result, "PLnew")

    def test_dry_run_sentinel_is_reserved(self):
        # If anyone ever changes the sentinel to a plausible-looking real ID,
        # tests that check "is this a real id" would silently miss the sentinel.
        self.assertTrue(PlaylistManager.DRY_RUN_PLAYLIST_ID.startswith("("))
        self.assertIn("dry-run", PlaylistManager.DRY_RUN_PLAYLIST_ID)


if __name__ == "__main__":
    unittest.main()
