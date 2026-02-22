"""Tests for ado/auth.py — token caching logic."""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from ado import auth


class TestLoadCache(unittest.TestCase):
    """_load_cache reads from disk and validates expiry."""

    def test_returns_none_when_no_file(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.object(auth, "_CACHE_FILE", type(auth._CACHE_FILE)(os.path.join(td, "nonexistent.json"))):
                result = auth._load_cache()
                self.assertIsNone(result)

    def test_returns_token_when_valid(self):
        with tempfile.TemporaryDirectory() as td:
            cache_path = os.path.join(td, "token.json")
            token_data = {"token": "abc", "expires_on": time.time() + 3600}
            with open(cache_path, "w") as f:
                json.dump(token_data, f)

            with patch.object(auth, "_CACHE_FILE", type(auth._CACHE_FILE)(cache_path)):
                result = auth._load_cache()
                self.assertIsNotNone(result)
                self.assertEqual(result["token"], "abc")

    def test_returns_none_when_expired(self):
        with tempfile.TemporaryDirectory() as td:
            cache_path = os.path.join(td, "token.json")
            token_data = {"token": "old", "expires_on": time.time() - 100}
            with open(cache_path, "w") as f:
                json.dump(token_data, f)

            with patch.object(auth, "_CACHE_FILE", type(auth._CACHE_FILE)(cache_path)):
                result = auth._load_cache()
                self.assertIsNone(result)

    def test_returns_none_when_near_expiry(self):
        with tempfile.TemporaryDirectory() as td:
            cache_path = os.path.join(td, "token.json")
            # Expires in 2 minutes — within 5-min buffer
            token_data = {"token": "near", "expires_on": time.time() + 120}
            with open(cache_path, "w") as f:
                json.dump(token_data, f)

            with patch.object(auth, "_CACHE_FILE", type(auth._CACHE_FILE)(cache_path)):
                result = auth._load_cache()
                self.assertIsNone(result)


class TestSaveCache(unittest.TestCase):
    """_save_cache writes to disk with 0o600 permissions."""

    def test_creates_file(self):
        with tempfile.TemporaryDirectory() as td:
            cache_dir = os.path.join(td, "subdir")
            cache_path = os.path.join(cache_dir, "token.json")
            with patch.object(auth, "_CACHE_DIR", type(auth._CACHE_DIR)(cache_dir)):
                with patch.object(auth, "_CACHE_FILE", type(auth._CACHE_FILE)(cache_path)):
                    auth._save_cache({"token": "xyz", "expires_on": 12345})
                    self.assertTrue(os.path.exists(cache_path))
                    with open(cache_path) as f:
                        data = json.load(f)
                    self.assertEqual(data["token"], "xyz")


class TestGetToken(unittest.TestCase):
    """get_token resolution order: in-memory → disk → credentials."""

    def setUp(self):
        auth._cached_token = None

    def tearDown(self):
        auth._cached_token = None

    def test_returns_from_memory_cache(self):
        auth._cached_token = {"token": "mem_token", "expires_on": time.time() + 3600}
        result = auth.get_token()
        self.assertEqual(result, "mem_token")

    @patch.object(auth, "_load_cache")
    def test_returns_from_disk_cache(self, mock_load):
        mock_load.return_value = {"token": "disk_token", "expires_on": time.time() + 3600}
        result = auth.get_token()
        self.assertEqual(result, "disk_token")

    @patch.object(auth, "_save_cache")
    @patch.object(auth, "_load_cache", return_value=None)
    def test_falls_through_to_azure_cli(self, mock_load, mock_save):
        mock_access = MagicMock()
        mock_access.token = "cli_token"
        mock_access.expires_on = time.time() + 3600

        mock_cred = MagicMock()
        mock_cred.return_value.get_token.return_value = mock_access

        with patch("ado.auth.AzureCliCredential", mock_cred):
            result = auth.get_token()
            self.assertEqual(result, "cli_token")
            mock_save.assert_called_once()

    @patch.object(auth, "_save_cache")
    @patch.object(auth, "_load_cache", return_value=None)
    def test_raises_when_all_fail(self, mock_load, mock_save):
        with patch("ado.auth.AzureCliCredential", side_effect=Exception("no cli")):
            with patch("ado.auth.DefaultAzureCredential", side_effect=Exception("no default")):
                with self.assertRaises(RuntimeError) as ctx:
                    auth.get_token()
                self.assertIn("Unable to authenticate", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
