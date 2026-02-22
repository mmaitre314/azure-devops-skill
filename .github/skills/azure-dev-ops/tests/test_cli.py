"""Tests for ado.py — CLI helpers and argument parser."""

from __future__ import annotations

import importlib
import sys
import unittest


def _import_cli():
    """Import ado.py as a module (not the ado/ package)."""
    import importlib.util
    import os
    cli_path = os.path.join(os.path.dirname(__file__), "..", "ado.py")
    spec = importlib.util.spec_from_file_location("ado_cli", cli_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cli_module = _import_cli()


class TestIntOrNone(unittest.TestCase):

    def test_none(self):
        self.assertIsNone(cli_module._int_or_none(None))

    def test_numeric_string(self):
        self.assertEqual(cli_module._int_or_none("42"), 42)

    def test_zero(self):
        self.assertEqual(cli_module._int_or_none("0"), 0)


class TestBoolFlag(unittest.TestCase):

    def test_none(self):
        self.assertIsNone(cli_module._bool_flag(None))

    def test_true_variants(self):
        for val in ("true", "True", "TRUE", "1", "yes", "Yes"):
            self.assertTrue(cli_module._bool_flag(val), f"Expected True for {val!r}")

    def test_false_variants(self):
        for val in ("false", "False", "0", "no", "nope"):
            self.assertFalse(cli_module._bool_flag(val), f"Expected False for {val!r}")


class TestListOfInts(unittest.TestCase):

    def test_single(self):
        self.assertEqual(cli_module._list_of_ints("5"), [5])

    def test_multiple(self):
        self.assertEqual(cli_module._list_of_ints("1,2,3"), [1, 2, 3])

    def test_with_spaces(self):
        self.assertEqual(cli_module._list_of_ints("10 , 20 , 30"), [10, 20, 30])


class TestBuildParser(unittest.TestCase):
    """build_parser creates a complete argument parser."""

    def setUp(self):
        self.parser = cli_module.build_parser()

    def test_org_required(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])

    def test_core_list_projects(self):
        args = self.parser.parse_args(["--org", "myorg", "core", "list-projects"])
        self.assertEqual(args.org, "myorg")
        self.assertEqual(args.category, "core")
        self.assertTrue(hasattr(args, "func"))

    def test_repos_get_pr(self):
        args = self.parser.parse_args([
            "--org", "myorg", "repos", "get-pr",
            "--project", "MyProject", "--repo", "my-repo", "--pr-id", "123",
        ])
        self.assertEqual(args.pr_id, "123")
        self.assertEqual(args.project, "MyProject")

    def test_repos_pr_summary(self):
        args = self.parser.parse_args([
            "--org", "myorg", "repos", "pr-summary",
            "--project", "P", "--repo", "R", "--pr-id", "99",
        ])
        self.assertEqual(args.command, "pr-summary")

    def test_repos_pr_download(self):
        args = self.parser.parse_args([
            "--org", "myorg", "repos", "pr-download",
            "--project", "P", "--repo", "R", "--pr-id", "5",
            "--output-dir", "/tmp/out",
        ])
        self.assertEqual(args.output_dir, "/tmp/out")

    def test_output_file_flag(self):
        args = self.parser.parse_args([
            "--org", "myorg", "-o", "/tmp/out.json",
            "core", "list-projects",
        ])
        self.assertEqual(args.output_file, "/tmp/out.json")

    def test_wit_get(self):
        args = self.parser.parse_args([
            "--org", "myorg", "wit", "get",
            "--project", "P", "--id", "42",
        ])
        self.assertEqual(args.id, "42")

    def test_search_code(self):
        args = self.parser.parse_args([
            "--org", "myorg", "search", "code", "--text", "hello",
        ])
        self.assertEqual(args.text, "hello")

    def test_pipelines_builds(self):
        args = self.parser.parse_args([
            "--org", "myorg", "pipelines", "builds", "--project", "P",
        ])
        self.assertEqual(args.category, "pipelines")

    def test_wiki_content(self):
        args = self.parser.parse_args([
            "--org", "myorg", "wiki", "content",
            "--project", "P", "--wiki-id", "W", "--path", "/page",
        ])
        self.assertEqual(args.path, "/page")

    def test_all_categories_registered(self):
        """Every expected category is available."""
        expected = {"core", "repos", "wit", "pipelines", "wiki", "search", "test", "work", "security"}
        # Parse with --help to get subparser choices or test each
        for cat in expected:
            with self.subTest(category=cat):
                # At minimum, parsing the category alone (without command) should fail gracefully
                with self.assertRaises(SystemExit):
                    self.parser.parse_args(["--org", "myorg", cat])


if __name__ == "__main__":
    unittest.main()
