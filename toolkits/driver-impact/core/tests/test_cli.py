from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ph_driver_impact.cli import main
from ph_driver_impact.profile import load_profile


class CliTests(unittest.TestCase):
    def test_existing_non_report_inside_repository_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "notes.txt"
            output.write_text("user data", encoding="utf-8")
            with (
                patch("ph_driver_impact.cli.repository_root", return_value=root),
                patch("ph_driver_impact.cli.load_profile", return_value=load_profile()),
            ):
                result = main(["inspect", "--repo", str(root), "--output", str(output)])
            self.assertEqual(result, 2)
            self.assertEqual(output.read_text(encoding="utf-8"), "user data")

    def test_authority_document_output_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "AGENTS.md"
            with (
                patch("ph_driver_impact.cli.repository_root", return_value=root),
                patch("ph_driver_impact.cli.load_profile", return_value=load_profile()),
            ):
                self.assertEqual(main(["inspect", "--repo", str(root), "--output", str(output)]), 2)


if __name__ == "__main__":
    unittest.main()
