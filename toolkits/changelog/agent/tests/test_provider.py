from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from ph_changelog_agent.providers.lm_studio import call_lm_studio


class LmStudioProviderTests(unittest.TestCase):
    def test_rejects_non_string_message_content_as_controlled_error(self) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = (
            b'{"choices":[{"message":{"content":null}}]}'
        )
        with patch(
            "ph_changelog_agent.providers.lm_studio.urllib.request.urlopen",
            return_value=response,
        ):
            with self.assertRaisesRegex(ValueError, "content must be a string"):
                call_lm_studio("system", "user", model="test")


if __name__ == "__main__":
    unittest.main()
