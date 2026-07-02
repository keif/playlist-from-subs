"""
Regression tests for issue #26: honor YT_SUB_PLAYLIST_DATA_DIR env var.

Prior behavior: PlaylistManager.__init__ hard-coded data_dir to
"yt_sub_playlist/data" as a relative path. When the container entrypoint
cd'd into /data, runtime state files (playlist_cache/, processed_videos.json,
api_call_log.json) ended up buried at /data/yt_sub_playlist/data/ instead
of directly under /data.

Fix: PlaylistManager honors a YT_SUB_PLAYLIST_DATA_DIR env var with
explicit-arg > env var > default precedence. Local dev keeps the historical
default when the env var is unset (backwards compatible).
"""
import os
import unittest
from unittest.mock import patch

from yt_sub_playlist.core.playlist_manager import (
    DEFAULT_DATA_DIR,
    resolve_data_dir,
)


class ResolveDataDirTests(unittest.TestCase):
    def test_explicit_arg_wins_over_env(self):
        with patch.dict(os.environ, {"YT_SUB_PLAYLIST_DATA_DIR": "/from-env"}):
            self.assertEqual(resolve_data_dir("/explicit"), "/explicit")

    def test_env_var_wins_over_default(self):
        with patch.dict(os.environ, {"YT_SUB_PLAYLIST_DATA_DIR": "/data"}):
            self.assertEqual(resolve_data_dir(), "/data")

    def test_default_when_neither_set(self):
        env_without = {k: v for k, v in os.environ.items() if k != "YT_SUB_PLAYLIST_DATA_DIR"}
        with patch.dict(os.environ, env_without, clear=True):
            self.assertEqual(resolve_data_dir(), DEFAULT_DATA_DIR)

    def test_empty_env_var_falls_back_to_default(self):
        # An exported-but-empty env var (`export YT_SUB_PLAYLIST_DATA_DIR=`)
        # should behave the same as unset — accidentally exporting empty
        # values is a common shell mistake and shouldn't crater state
        # into a relative "" path.
        with patch.dict(os.environ, {"YT_SUB_PLAYLIST_DATA_DIR": ""}):
            self.assertEqual(resolve_data_dir(), DEFAULT_DATA_DIR)

    def test_default_matches_historical_relative_path(self):
        # The default is the historical relative path so `python -m
        # yt_sub_playlist` from a fresh repo checkout keeps writing state
        # to yt_sub_playlist/data/ — unchanged behaviour for local dev.
        self.assertEqual(DEFAULT_DATA_DIR, "yt_sub_playlist/data")


if __name__ == "__main__":
    unittest.main()
