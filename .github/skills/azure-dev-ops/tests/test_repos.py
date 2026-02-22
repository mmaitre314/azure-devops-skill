"""Tests for ado/repos.py — PR changes normalization, summary, download."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from ado import repos


class TestGetPullRequestChanges(unittest.TestCase):
    """get_pull_request_changes unwraps changeEntries."""

    @patch("ado.repos.get_pull_request_iterations")
    @patch("ado.repos.client.get")
    def test_unwraps_change_entries(self, mock_get, mock_iters):
        mock_iters.return_value = [{"id": 1}]
        mock_get.return_value = {
            "changeEntries": [
                {"changeType": "add", "item": {"path": "/src/A.cs"}},
                {"changeType": "edit", "item": {"path": "/src/B.cs"}},
            ]
        }
        result = repos.get_pull_request_changes("proj", "repo", 123)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["changeType"], "add")

    @patch("ado.repos.get_pull_request_iterations")
    @patch("ado.repos.client.get")
    def test_falls_back_to_value_key(self, mock_get, mock_iters):
        mock_iters.return_value = [{"id": 1}]
        mock_get.return_value = {"value": [{"changeType": "delete"}]}
        result = repos.get_pull_request_changes("proj", "repo", 1)
        self.assertEqual(len(result), 1)

    @patch("ado.repos.get_pull_request_iterations")
    @patch("ado.repos.client.get")
    def test_returns_list_as_is(self, mock_get, mock_iters):
        mock_iters.return_value = [{"id": 1}]
        entries = [{"changeType": "edit", "item": {"path": "/x"}}]
        mock_get.return_value = entries  # already a list
        result = repos.get_pull_request_changes("proj", "repo", 1)
        self.assertEqual(result, entries)

    @patch("ado.repos.get_pull_request_iterations")
    @patch("ado.repos.client.get")
    def test_uses_explicit_iteration(self, mock_get, mock_iters):
        mock_get.return_value = {"changeEntries": []}
        result = repos.get_pull_request_changes("proj", "repo", 1, iteration_id=3)
        # Should NOT call get_pull_request_iterations when iteration_id is given
        mock_iters.assert_not_called()
        self.assertIn("/iterations/3/changes", mock_get.call_args[0][0])

    @patch("ado.repos.get_pull_request_iterations")
    @patch("ado.repos.client.get")
    def test_uses_last_iteration(self, mock_get, mock_iters):
        mock_iters.return_value = [{"id": 1}, {"id": 2}, {"id": 5}]
        mock_get.return_value = {"changeEntries": []}
        repos.get_pull_request_changes("proj", "repo", 1)
        self.assertIn("/iterations/5/changes", mock_get.call_args[0][0])

    @patch("ado.repos.get_pull_request_iterations")
    @patch("ado.repos.client.get")
    def test_empty_iterations_uses_1(self, mock_get, mock_iters):
        mock_iters.return_value = []
        mock_get.return_value = {"changeEntries": []}
        repos.get_pull_request_changes("proj", "repo", 1)
        self.assertIn("/iterations/1/changes", mock_get.call_args[0][0])


class TestPrSummary(unittest.TestCase):
    """pr_summary combines metadata, files, and threads."""

    def _mock_pr(self):
        return {
            "title": "Test PR",
            "description": "A test PR",
            "status": "active",
            "createdBy": {"displayName": "Alice"},
            "sourceRefName": "refs/heads/feature",
            "targetRefName": "refs/heads/main",
            "lastMergeSourceCommit": {"commitId": "aaa111"},
            "lastMergeTargetCommit": {"commitId": "bbb222"},
            "workItemRefs": [],
        }

    @patch("ado.repos.list_pr_threads")
    @patch("ado.repos.get_pull_request_changes")
    @patch("ado.repos.get_pull_request")
    def test_classifies_files(self, mock_pr, mock_changes, mock_threads):
        mock_pr.return_value = self._mock_pr()
        mock_changes.return_value = [
            {"changeType": "add", "item": {"path": "/src/New.cs"}},
            {"changeType": "edit", "item": {"path": "/src/Existing.cs"}},
            {"changeType": "delete", "item": {"path": "/src/Old.cs"}},
            {"changeType": "edit", "item": {"path": "/src/Another.cs"}},
        ]
        mock_threads.return_value = []

        result = repos.pr_summary("proj", "repo", 1)
        self.assertEqual(result["files"]["added"], ["/src/New.cs"])
        self.assertEqual(result["files"]["edited"], ["/src/Existing.cs", "/src/Another.cs"])
        self.assertEqual(result["files"]["deleted"], ["/src/Old.cs"])

    @patch("ado.repos.list_pr_threads")
    @patch("ado.repos.get_pull_request_changes")
    @patch("ado.repos.get_pull_request")
    def test_filters_text_threads(self, mock_pr, mock_changes, mock_threads):
        mock_pr.return_value = self._mock_pr()
        mock_changes.return_value = []
        mock_threads.return_value = [
            # Human text thread
            {
                "status": "active",
                "threadContext": {"filePath": "/src/A.cs"},
                "comments": [
                    {"commentType": "text", "author": {"displayName": "Bob"}, "content": "Needs fix"},
                ],
            },
            # System thread (no text comments) — should be excluded
            {
                "status": "unknown",
                "comments": [
                    {"commentType": "system", "content": "auto-merged"},
                ],
            },
        ]

        result = repos.pr_summary("proj", "repo", 1)
        self.assertEqual(len(result["reviewComments"]), 1)
        self.assertEqual(result["reviewComments"][0]["author"], "Bob")
        self.assertEqual(result["reviewComments"][0]["filePath"], "/src/A.cs")

    @patch("ado.repos.list_pr_threads")
    @patch("ado.repos.get_pull_request_changes")
    @patch("ado.repos.get_pull_request")
    def test_metadata_fields(self, mock_pr, mock_changes, mock_threads):
        mock_pr.return_value = self._mock_pr()
        mock_changes.return_value = []
        mock_threads.return_value = []

        result = repos.pr_summary("proj", "repo", 1)
        self.assertEqual(result["title"], "Test PR")
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["sourceCommit"], "aaa111")
        self.assertEqual(result["targetCommit"], "bbb222")
        self.assertEqual(result["createdBy"], "Alice")


class TestPrDownload(unittest.TestCase):
    """pr_download calls bulk_download_files correctly."""

    @patch("ado.repos.bulk_download_files")
    @patch("ado.repos.get_pull_request_changes")
    @patch("ado.repos.get_pull_request")
    def test_downloads_correct_sides(self, mock_pr, mock_changes, mock_bulk):
        mock_pr.return_value = {
            "lastMergeSourceCommit": {"commitId": "src123"},
            "lastMergeTargetCommit": {"commitId": "tgt456"},
        }
        mock_changes.return_value = [
            {"changeType": "add", "item": {"path": "/src/New.cs"}},
            {"changeType": "edit", "item": {"path": "/src/Changed.cs"}},
            {"changeType": "delete", "item": {"path": "/src/Gone.cs"}},
        ]
        mock_bulk.return_value = []

        with tempfile.TemporaryDirectory() as td:
            result = repos.pr_download("proj", "repo", 1, td)

        # Target (before) should download edited + deleted
        target_call = mock_bulk.call_args_list[0]
        target_paths = target_call[0][2]  # 3rd positional arg = paths
        self.assertIn("/src/Changed.cs", target_paths)
        self.assertIn("/src/Gone.cs", target_paths)
        self.assertNotIn("/src/New.cs", target_paths)

        # Source (after) should download edited + added
        source_call = mock_bulk.call_args_list[1]
        source_paths = source_call[0][2]
        self.assertIn("/src/Changed.cs", source_paths)
        self.assertIn("/src/New.cs", source_paths)
        self.assertNotIn("/src/Gone.cs", source_paths)

    @patch("ado.repos.get_pull_request")
    def test_raises_if_no_merge_commits(self, mock_pr):
        mock_pr.return_value = {
            "lastMergeSourceCommit": None,
            "lastMergeTargetCommit": None,
        }
        with self.assertRaises(ValueError):
            repos.pr_download("proj", "repo", 1, "/tmp/out")


class TestBulkDownloadFiles(unittest.TestCase):
    """bulk_download_files writes files to disk."""

    @patch("ado.repos.time.sleep")
    @patch("ado.repos.get_file_content")
    def test_downloads_to_correct_paths(self, mock_content, mock_sleep):
        mock_content.return_value = "file content"
        with tempfile.TemporaryDirectory() as td:
            results = repos.bulk_download_files(
                "proj", "repo",
                ["/src/A.cs", "/src/sub/B.cs"],
                td,
                commit="abc123",
            )
            self.assertEqual(len(results), 2)
            self.assertTrue(all(r["status"] == "ok" for r in results))
            self.assertTrue(os.path.exists(os.path.join(td, "src", "A.cs")))
            self.assertTrue(os.path.exists(os.path.join(td, "src", "sub", "B.cs")))

    @patch("ado.repos.time.sleep")
    @patch("ado.repos.get_file_content")
    def test_retries_on_failure(self, mock_content, mock_sleep):
        mock_content.side_effect = [Exception("network error"), "content"]
        with tempfile.TemporaryDirectory() as td:
            results = repos.bulk_download_files(
                "proj", "repo", ["/x.cs"], td, retries=1,
            )
            self.assertEqual(results[0]["status"], "ok")
            self.assertEqual(mock_content.call_count, 2)

    @patch("ado.repos.time.sleep")
    @patch("ado.repos.get_file_content")
    def test_failure_after_exhausted_retries(self, mock_content, mock_sleep):
        mock_content.side_effect = Exception("permanent error")
        with tempfile.TemporaryDirectory() as td:
            results = repos.bulk_download_files(
                "proj", "repo", ["/fail.cs"], td, retries=1,
            )
            self.assertEqual(results[0]["status"], "failed")
            self.assertIn("permanent error", results[0]["error"])


class TestListBranches(unittest.TestCase):
    """list_branches unwraps value key."""

    @patch("ado.repos.client.get")
    def test_unwraps_value(self, mock_get):
        mock_get.return_value = {"value": [{"name": "refs/heads/main"}]}
        result = repos.list_branches("proj", "repo")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "refs/heads/main")

    @patch("ado.repos.client.get")
    def test_returns_list_as_is(self, mock_get):
        mock_get.return_value = [{"name": "refs/heads/main"}]
        result = repos.list_branches("proj", "repo")
        self.assertEqual(len(result), 1)


class TestGetPullRequest(unittest.TestCase):
    """get_pull_request optionally fetches work items."""

    @patch("ado.repos.client.get")
    def test_without_work_items(self, mock_get):
        mock_get.return_value = {"pullRequestId": 1, "title": "PR"}
        result = repos.get_pull_request("proj", "repo", 1)
        self.assertEqual(result["pullRequestId"], 1)
        self.assertNotIn("workItemRefs", result)
        mock_get.assert_called_once()

    @patch("ado.repos.client.get")
    def test_with_work_items(self, mock_get):
        mock_get.side_effect = [
            {"pullRequestId": 1, "title": "PR"},
            {"value": [{"id": 42}]},
        ]
        result = repos.get_pull_request("proj", "repo", 1, include_work_items=True)
        self.assertEqual(result["workItemRefs"], [{"id": 42}])
        self.assertEqual(mock_get.call_count, 2)


class TestGetFileContent(unittest.TestCase):
    """get_file_content passes correct version descriptor params."""

    @patch("ado.repos.client.get_text")
    def test_by_branch(self, mock_text):
        mock_text.return_value = "contents"
        repos.get_file_content("proj", "repo", "/src/A.cs", branch="refs/heads/main")
        params = mock_text.call_args[1]["params"]
        self.assertEqual(params["versionDescriptor.version"], "main")
        self.assertEqual(params["versionDescriptor.versionType"], "branch")

    @patch("ado.repos.client.get_text")
    def test_by_commit(self, mock_text):
        mock_text.return_value = "contents"
        repos.get_file_content("proj", "repo", "/src/A.cs", commit="abc123")
        params = mock_text.call_args[1]["params"]
        self.assertEqual(params["versionDescriptor.version"], "abc123")
        self.assertEqual(params["versionDescriptor.versionType"], "commit")

    @patch("ado.repos.client.get_text")
    def test_no_version(self, mock_text):
        mock_text.return_value = "contents"
        repos.get_file_content("proj", "repo", "/src/A.cs")
        params = mock_text.call_args[1]["params"]
        self.assertNotIn("versionDescriptor.version", params)


if __name__ == "__main__":
    unittest.main()
