from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from support import impact_document

from ph_driver_impact_agent.cli import cmd_run
from ph_driver_impact_agent.stale import StaleImpactError


class CliTests(unittest.TestCase):
    def test_needs_supervisor_exits_three_after_two_snapshot_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            impact_path = Path(directory) / "impact.json"
            output_path = Path(directory) / "output.json"
            impact_path.write_text(json.dumps(impact_document()), encoding="utf-8")
            args = argparse.Namespace(
                impact=str(impact_path),
                profile=None,
                model="coder",
                base_url=None,
                temperature=0.1,
                output=str(output_path),
            )
            escalation = {
                "status": "needs_supervisor",
                "reason": "Need owner decision.",
                "change_refs": ["C-001"],
                "authority_refs": ["A-0001"],
            }
            with (
                patch("ph_driver_impact_agent.cli.verify_current") as verify,
                patch("ph_driver_impact_agent.cli.generate_output", return_value=escalation),
            ):
                self.assertEqual(cmd_run(args), 3)
            self.assertEqual(verify.call_count, 2)
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), escalation)

    def test_stale_after_model_never_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            impact_path = Path(directory) / "impact.json"
            output_path = Path(directory) / "output.json"
            impact_path.write_text(json.dumps(impact_document()), encoding="utf-8")
            args = argparse.Namespace(
                impact=str(impact_path),
                profile=None,
                model="coder",
                base_url=None,
                temperature=0.1,
                output=str(output_path),
            )
            with (
                patch(
                    "ph_driver_impact_agent.cli.verify_current",
                    side_effect=[None, StaleImpactError("stale")],
                ),
                patch("ph_driver_impact_agent.cli.generate_output", return_value={}),
            ):
                with self.assertRaises(StaleImpactError):
                    cmd_run(args)
            self.assertFalse(output_path.exists())


if __name__ == "__main__":
    unittest.main()
