import unittest

from core.status import UNKNOWN, collect_status, render_text


class CoreStatusTests(unittest.TestCase):
    def test_status_has_stable_contract(self):
        status = collect_status(".")
        data = status.to_dict()
        self.assertEqual(data["service"], "topazio-core-prototype")
        self.assertIn("hostname", data)
        self.assertIn("storage", data)

    def test_text_console_is_human_readable(self):
        status = collect_status(".")
        text = render_text(status)
        self.assertIn("TOPAZIO MOBILE SERVER OS", text)

    def test_unknown_is_allowed_for_platform_specific_metrics(self):
        status = collect_status(".")
        self.assertTrue(status.temperature == UNKNOWN or status.temperature.endswith("C"))


if __name__ == "__main__":
    unittest.main()
