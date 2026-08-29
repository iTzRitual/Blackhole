from __future__ import annotations

import unittest

from app.provider import parse_repaired_json


class ProviderParsingTests(unittest.TestCase):
    def test_valid_json_is_not_changed(self) -> None:
        parsed, error, repair = parse_repaired_json('{"ok": true}')
        self.assertEqual(parsed, {"ok": True})
        self.assertIsNone(error)
        self.assertIsNone(repair)

    def test_single_missing_object_delimiter_is_repaired(self) -> None:
        parsed, error, repair = parse_repaired_json('{"queries": {"q": {"assertions": []}}')
        self.assertEqual(parsed, {"queries": {"q": {"assertions": []}}})
        self.assertIsNone(error)
        self.assertEqual(repair, "appended_suffix:}")

    def test_prose_is_not_repaired(self) -> None:
        parsed, error, repair = parse_repaired_json("I cannot answer this.")
        self.assertIsNone(parsed)
        self.assertIsNotNone(error)
        self.assertIsNone(repair)


if __name__ == "__main__":
    unittest.main()
