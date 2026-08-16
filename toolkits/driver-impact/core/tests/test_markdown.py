from __future__ import annotations

import unittest

from ph_driver_impact.markdown import extract_commands, index_markdown, markdown_warnings


class MarkdownTests(unittest.TestCase):
    def test_indexes_duplicate_headings_and_table_rows_by_structure_and_hash(self) -> None:
        entries = index_markdown(
            "docs/INVARIANTS.md",
            "# Invariants\n## Runtime\n| Rule | Why |\n| --- | --- |\n| I-1 | Safe |\n## Runtime\n",
            100,
        )
        self.assertEqual([entry["kind"] for entry in entries].count("heading"), 3)
        rows = [entry for entry in entries if entry["kind"] == "table_row"]
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0]["sha256"], rows[1]["sha256"])

    def test_extracts_only_commands_fence(self) -> None:
        text = "# Repo\n## Commands\n```bash\ncargo test\n# note\n```\n## Other\n```\nnope\n```\n"
        self.assertEqual(extract_commands(text), ["cargo test"])

    def test_warns_about_incomplete_pipe_table_row(self) -> None:
        self.assertEqual(
            markdown_warnings("docs/TEST_PLAN.md", "| Case | Expectation\n"),
            ["malformed pipe-table row was not indexed: docs/TEST_PLAN.md:1"],
        )

    def test_table_row_identity_does_not_depend_on_row_order(self) -> None:
        first = index_markdown("docs/TEST_PLAN.md", "# Tests\n| A | one |\n| B | two |\n", 100)
        second = index_markdown("docs/TEST_PLAN.md", "# Tests\n| B | two |\n| A | one |\n", 100)
        first_hashes = {item["sha256"] for item in first if item["kind"] == "table_row"}
        second_hashes = {item["sha256"] for item in second if item["kind"] == "table_row"}
        self.assertEqual(first_hashes, second_hashes)


if __name__ == "__main__":
    unittest.main()
