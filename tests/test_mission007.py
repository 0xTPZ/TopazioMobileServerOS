import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_gate_tool():
    path = ROOT / "host-tools" / "server_minimal_gate.py"
    spec = importlib.util.spec_from_file_location("mission007_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load gate validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Mission007Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate_tool = load_gate_tool()
        cls.report = json.loads(
            (ROOT / "devices/xiaomi-sea/server-minimal/build-gate.json").read_text(encoding="utf-8")
        )
        cls.fragment = (
            ROOT / "devices/xiaomi-sea/server-minimal/config/topazio_sea_server_defconfig"
        ).read_text(encoding="utf-8")

    def test_gate_report_is_self_consistent(self):
        self.assertEqual(self.gate_tool.validate_gate(self.report), [])

    def test_seven_original_errors_and_bounded_new_debt(self):
        self.assertEqual(len(self.report["reproduction"]["errors"]), 7)
        self.assertEqual(self.report["new_blocker_count"], 1)
        self.assertEqual(self.report["decision"]["sea"], "SEA_CONTINUE")

    def test_charging_and_critical_capabilities_are_preserved(self):
        self.assertEqual(
            self.report["configuration"]["charging_preserved"],
            ["CONFIG_MTK_CHARGER=y", "CONFIG_CHARGER_BQ2589X=y"],
        )
        for capability in ("ufs", "usb", "wifi", "thermal", "display", "touch"):
            self.assertIn(capability, self.report["critical_capability_audit"])

    def test_optional_audio_detectors_are_the_only_new_config_exclusions(self):
        self.assertIn("# CONFIG_SND_SOC_MT6357_ACCDET is not set", self.fragment)
        self.assertIn("# CONFIG_SND_SOC_MT6359_ACCDET is not set", self.fragment)
        self.assertNotIn("CONFIG_MTK_CHARGER is not set", self.fragment)
        self.assertNotIn("CONFIG_CHARGER_BQ2589X is not set", self.fragment)

    def test_dtb_and_recovery_remain_blocked(self):
        self.assertEqual(self.report["artifacts"]["dtb_status"], "BLOCKED")
        self.assertEqual(self.report["decision"]["recovery_readiness"], "BLOCKED")
        self.assertFalse(self.report["decision"]["write_phone_authorized"])


if __name__ == "__main__":
    unittest.main()
