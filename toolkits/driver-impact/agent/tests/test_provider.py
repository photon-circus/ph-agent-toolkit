from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from ph_driver_impact_agent.providers.lm_studio import call_lm_studio


class ProviderTests(unittest.TestCase):
    def test_accepts_fenced_json_object(self) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"choices":[{"message":{"content":"```json\\n{\\"status\\":\\"ok\\"}\\n```"}}]}'
        )
        with patch(
            "ph_driver_impact_agent.providers.lm_studio.urllib.request.urlopen",
            return_value=response,
        ):
            self.assertEqual(call_lm_studio("system", "user", "model"), {"status": "ok"})

    def test_rejects_non_string_content(self) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"choices":[{"message":{"content":null}}]}'
        )
        with patch(
            "ph_driver_impact_agent.providers.lm_studio.urllib.request.urlopen",
            return_value=response,
        ):
            with self.assertRaisesRegex(ValueError, "content must be a string"):
                call_lm_studio("system", "user", "model")

    def test_rejects_non_loopback_endpoint_before_transport(self) -> None:
        with patch("ph_driver_impact_agent.providers.lm_studio.urllib.request.urlopen") as open_url:
            with self.assertRaisesRegex(ValueError, "loopback"):
                call_lm_studio("system", "user", "model", base_url="https://example.com")
        open_url.assert_not_called()

    def test_rejects_unbounded_temperature_before_transport(self) -> None:
        with patch("ph_driver_impact_agent.providers.lm_studio.urllib.request.urlopen") as open_url:
            with self.assertRaisesRegex(ValueError, "temperature"):
                call_lm_studio("system", "user", "model", temperature=float("nan"))
        open_url.assert_not_called()

    def test_rejects_oversized_response(self) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"x" * 262_145
        with patch(
            "ph_driver_impact_agent.providers.lm_studio.urllib.request.urlopen",
            return_value=response,
        ):
            with self.assertRaisesRegex(ValueError, "response exceeds"):
                call_lm_studio("system", "user", "model")


if __name__ == "__main__":
    unittest.main()
