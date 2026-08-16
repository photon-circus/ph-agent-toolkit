from __future__ import annotations

import copy
import unittest

from ph_driver_impact.inspect import _matches
from ph_driver_impact.profile import load_profile, validate_profile


class ProfileTests(unittest.TestCase):
    def test_built_in_profile_is_closed_and_loadable(self) -> None:
        profile = load_profile("photon-circus-driver-v1")
        self.assertEqual(profile.name, "photon-circus-driver-v1")
        self.assertGreater(len(profile.rules), 5)

    def test_unknown_top_level_field_is_rejected(self) -> None:
        profile = load_profile()
        raw = {
            "schema_version": 1,
            "name": profile.name,
            "documents": [copy.deepcopy(item) for item in profile.documents],
            "ignored": list(profile.ignored),
            "rules": [copy.deepcopy(item) for item in profile.rules],
            "limits": dict(profile.limits),
            "typo": True,
        }
        with self.assertRaisesRegex(ValueError, "unexpected field"):
            validate_profile(raw)

    def test_every_built_in_rule_matches_a_representative_path(self) -> None:
        samples = {
            "workspace.manifest": "Cargo.toml",
            "driver.public_api": "crates/device/src/lib.rs",
            "driver.codec": "crates/device/src/register.rs",
            "driver.transport": "crates/device/src/driver.rs",
            "driver.errors": "crates/device/src/error.rs",
            "driver.behavioral_model": "crates/device/src/model.rs",
            "driver.tests": "crates/device/tests/traffic.rs",
            "driver.hil": "hil/plan.toml",
            "driver.evidence": "hardware-evidence/run.json",
            "driver.vendor_sources": "docs/vendor/device.pdf",
            "repository.automation": ".github/workflows/ci.yml",
            "repository.metadata": ".gitattributes",
            "repository.contract_docs": "docs/INVARIANTS.md",
            "repository.public_docs": "README.md",
            "repository.distribution": "PACK_MANIFEST.md",
            "driver.rust_other": "crates/device/src/feature.rs",
        }
        profile = load_profile()
        self.assertEqual({rule["id"] for rule in profile.rules}, set(samples))
        for rule in profile.rules:
            self.assertTrue(_matches(samples[rule["id"]], rule["globs"]), rule["id"])


if __name__ == "__main__":
    unittest.main()
