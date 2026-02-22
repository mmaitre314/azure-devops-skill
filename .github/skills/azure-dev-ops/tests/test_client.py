"""Tests for ado/client.py — URL building, org handling, output, retry, timeout."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from ado import client


class TestSetOrg(unittest.TestCase):
    """set_org / _org helpers."""

    def setUp(self):
        # Reset global between tests
        client._org_url = None

    def test_plain_name(self):
        client.set_org("myorg")
        self.assertEqual(client._org(), "https://dev.azure.com/myorg")

    def test_full_url(self):
        client.set_org("https://dev.azure.com/contoso")
        self.assertEqual(client._org(), "https://dev.azure.com/contoso")

    def test_trailing_slash_stripped(self):
        client.set_org("https://dev.azure.com/contoso/")
        self.assertEqual(client._org(), "https://dev.azure.com/contoso")

    def test_org_not_set_raises(self):
        with self.assertRaises(RuntimeError):
            client._org()


class TestBuildUrl(unittest.TestCase):
    """_build_url constructs correct URLs."""

    def setUp(self):
        client.set_org("myorg")

    def test_simple_path(self):
        url = client._build_url("_apis/projects")
        self.assertEqual(url, "https://dev.azure.com/myorg/_apis/projects")

    def test_with_project(self):
        url = client._build_url("_apis/git/repositories", project="MyProject")
        self.assertEqual(url, "https://dev.azure.com/myorg/MyProject/_apis/git/repositories")

    def test_project_with_spaces_encoded(self):
        url = client._build_url("_apis/git/repositories", project="My Project")
        self.assertIn("My%20Project", url)

    def test_search_area(self):
        url = client._build_url("_apis/search/codesearchresults", area="almsearch.dev.azure.com")
        self.assertEqual(url, "https://almsearch.dev.azure.com/myorg/_apis/search/codesearchresults")

    def test_vssps_area(self):
        url = client._build_url("_apis/identities", area="vssps.dev.azure.com")
        self.assertIn("vssps.dev.azure.com", url)


class TestTimeoutForArea(unittest.TestCase):
    """_timeout_for_area returns appropriate timeout values."""

    def test_default_area(self):
        self.assertEqual(client._timeout_for_area("dev.azure.com"), client._DEFAULT_TIMEOUT)

    def test_search_area(self):
        self.assertEqual(client._timeout_for_area("almsearch.dev.azure.com"), client._SEARCH_TIMEOUT)

    def test_non_search_area(self):
        self.assertEqual(client._timeout_for_area("vsrm.dev.azure.com"), client._DEFAULT_TIMEOUT)


class TestOutput(unittest.TestCase):
    """output() and output_text() write to stdout or file."""

    def setUp(self):
        client.set_output_file(None)

    def test_output_json_to_stdout(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            client.output({"key": "value"})
            out = mock_out.getvalue()
        parsed = json.loads(out.strip())
        self.assertEqual(parsed, {"key": "value"})

    def test_output_json_to_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "out.json")
            client.set_output_file(path)
            client.output({"a": 1})
            client.set_output_file(None)

            with open(path) as f:
                data = json.load(f)
            self.assertEqual(data, {"a": 1})

    def test_output_text_to_stdout(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            client.output_text("hello world")
            self.assertIn("hello world", mock_out.getvalue())

    def test_output_text_to_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "out.txt")
            client.set_output_file(path)
            client.output_text("hello")
            client.set_output_file(None)

            with open(path) as f:
                self.assertEqual(f.read(), "hello")

    def test_output_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "sub", "dir", "out.json")
            client.set_output_file(path)
            client.output([1, 2, 3])
            client.set_output_file(None)
            self.assertTrue(os.path.exists(path))


class TestRequestWithRetry(unittest.TestCase):
    """_request_with_retry retries on transient errors."""

    @patch("ado.client.time.sleep")
    @patch("ado.client.requests.get")
    def test_success_on_first_try(self, mock_get, mock_sleep):
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp

        result = client._request_with_retry("GET", "http://example.com", headers={})
        self.assertEqual(result, resp)
        mock_sleep.assert_not_called()

    @patch("ado.client.time.sleep")
    @patch("ado.client.requests.get")
    def test_retry_on_429(self, mock_get, mock_sleep):
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.raise_for_status = MagicMock()

        resp_ok = MagicMock()
        resp_ok.status_code = 200
        resp_ok.raise_for_status = MagicMock()

        mock_get.side_effect = [resp_429, resp_ok]
        result = client._request_with_retry("GET", "http://example.com", headers={})
        self.assertEqual(result, resp_ok)
        self.assertEqual(mock_get.call_count, 2)

    @patch("ado.client.time.sleep")
    @patch("ado.client.requests.get")
    def test_retry_on_503(self, mock_get, mock_sleep):
        resp_503 = MagicMock()
        resp_503.status_code = 503

        resp_ok = MagicMock()
        resp_ok.status_code = 200
        resp_ok.raise_for_status = MagicMock()

        mock_get.side_effect = [resp_503, resp_ok]
        result = client._request_with_retry("GET", "http://example.com", headers={})
        self.assertEqual(result, resp_ok)

    @patch("ado.client.time.sleep")
    @patch("ado.client.requests.get")
    def test_retry_on_timeout(self, mock_get, mock_sleep):
        import requests as req
        resp_ok = MagicMock()
        resp_ok.status_code = 200
        resp_ok.raise_for_status = MagicMock()

        mock_get.side_effect = [req.exceptions.Timeout("timed out"), resp_ok]
        result = client._request_with_retry("GET", "http://example.com", headers={})
        self.assertEqual(result, resp_ok)

    @patch("ado.client.time.sleep")
    @patch("ado.client.requests.post")
    def test_post_method(self, mock_post, mock_sleep):
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp

        result = client._request_with_retry(
            "POST", "http://example.com",
            headers={}, json_body={"q": "test"},
        )
        self.assertEqual(result, resp)
        mock_post.assert_called_once()


class TestGetAll(unittest.TestCase):
    """get_all paginates using continuationToken."""

    @patch("ado.client._headers", return_value={"Authorization": "Bearer fake"})
    @patch("ado.client._request_with_retry")
    def test_single_page(self, mock_req, mock_headers):
        client.set_org("myorg")

        resp = MagicMock()
        resp.headers = {"Content-Type": "application/json"}
        resp.json.return_value = {"value": [{"id": 1}, {"id": 2}]}
        mock_req.return_value = resp

        items = client.get_all("_apis/projects")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], 1)

    @patch("ado.client._headers", return_value={"Authorization": "Bearer fake"})
    @patch("ado.client._request_with_retry")
    def test_two_pages(self, mock_req, mock_headers):
        client.set_org("myorg")

        resp1 = MagicMock()
        resp1.headers = {"Content-Type": "application/json"}
        resp1.json.return_value = {"value": [{"id": 1}], "continuationToken": "abc"}

        resp2 = MagicMock()
        resp2.headers = {"Content-Type": "application/json"}
        resp2.json.return_value = {"value": [{"id": 2}]}

        mock_req.side_effect = [resp1, resp2]
        items = client.get_all("_apis/projects")
        self.assertEqual(len(items), 2)
        self.assertEqual(mock_req.call_count, 2)


if __name__ == "__main__":
    unittest.main()
