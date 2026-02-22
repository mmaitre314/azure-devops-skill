"""Tests for ado/search.py — request body construction."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from ado import search


class TestSearchCode(unittest.TestCase):

    @patch("ado.search.client.post")
    def test_minimal_body(self, mock_post):
        mock_post.return_value = {"count": 0, "results": []}
        search.search_code("connectionString")
        body = mock_post.call_args[1]["json_body"]
        self.assertEqual(body["searchText"], "connectionString")
        self.assertEqual(body["$top"], 25)
        self.assertEqual(body["$skip"], 0)
        self.assertNotIn("filters", body)

    @patch("ado.search.client.post")
    def test_with_filters(self, mock_post):
        mock_post.return_value = {}
        search.search_code(
            "test", project="P", repository="R", branch="main", path="/src",
        )
        body = mock_post.call_args[1]["json_body"]
        self.assertEqual(body["filters"]["Project"], ["P"])
        self.assertEqual(body["filters"]["Repository"], ["R"])
        self.assertEqual(body["filters"]["Branch"], ["main"])
        self.assertEqual(body["filters"]["Path"], ["/src"])

    @patch("ado.search.client.post")
    def test_uses_almsearch_area(self, mock_post):
        mock_post.return_value = {}
        search.search_code("q")
        self.assertEqual(mock_post.call_args[1]["area"], "almsearch.dev.azure.com")

    @patch("ado.search.client.post")
    def test_custom_top_skip(self, mock_post):
        mock_post.return_value = {}
        search.search_code("q", top=10, skip=5)
        body = mock_post.call_args[1]["json_body"]
        self.assertEqual(body["$top"], 10)
        self.assertEqual(body["$skip"], 5)


class TestSearchWiki(unittest.TestCase):

    @patch("ado.search.client.post")
    def test_minimal(self, mock_post):
        mock_post.return_value = {}
        search.search_wiki("architecture")
        body = mock_post.call_args[1]["json_body"]
        self.assertEqual(body["searchText"], "architecture")

    @patch("ado.search.client.post")
    def test_with_project_filter(self, mock_post):
        mock_post.return_value = {}
        search.search_wiki("arch", project="P")
        body = mock_post.call_args[1]["json_body"]
        self.assertEqual(body["filters"]["Project"], ["P"])


class TestSearchWorkItems(unittest.TestCase):

    @patch("ado.search.client.post")
    def test_all_filters(self, mock_post):
        mock_post.return_value = {}
        search.search_work_items(
            "bug", project="P", work_item_type="Bug",
            state="Active", assigned_to="alice@x.com", area_path="\\Team",
        )
        body = mock_post.call_args[1]["json_body"]
        self.assertEqual(body["filters"]["Work Item Type"], ["Bug"])
        self.assertEqual(body["filters"]["State"], ["Active"])
        self.assertEqual(body["filters"]["Assigned To"], ["alice@x.com"])
        self.assertEqual(body["filters"]["Area Path"], ["\\Team"])


if __name__ == "__main__":
    unittest.main()
