import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_tool(name):
    path = ROOT / "host-tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"mission006_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Mission006Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_tool = load_tool("server_minimal_config")
        cls.manifest = json.loads(
            (ROOT / "devices/xiaomi-sea/reconstruction/manifest.json").read_text(encoding="utf-8")
        )
        cls.plan = json.loads(
            (ROOT / "devices/xiaomi-sea/server-minimal/manifests/build-plan.json").read_text(encoding="utf-8")
        )
        cls.graph = json.loads(
            (ROOT / "devices/xiaomi-sea/server-minimal/manifests/dependency-graph.json").read_text(encoding="utf-8")
        )

    def test_derivation_changes_only_explicit_modem_options(self):
        symbols = sorted(self.config_tool.CRITICAL_SYMBOLS)
        base_lines = [f"{symbol}=y" for symbol in symbols]
        base_lines.extend(
            [
                "CONFIG_MTK_CCCI_DEVICES=y",
                "CONFIG_MTK_ECCCI_DRIVER=y",
                "CONFIG_MTK_ECCCI_C2K=y",
                "CONFIG_MTK_MD1_SUPPORT=11",
            ]
        )
        base = "\n".join(base_lines) + "\n"
        fragment = (ROOT / "devices/xiaomi-sea/server-minimal/config/topazio_sea_server_defconfig").read_text(
            encoding="utf-8"
        )
        derived = self.config_tool.derive(base, fragment)
        self.assertEqual(self.config_tool.validate_critical(derived), [])
        changes = self.config_tool.diff_config(base, derived)
        self.assertEqual(
            [(item["symbol"], item["new"]) for item in changes],
            [
                ("CONFIG_MTK_CCCI_DEVICES", "n"),
                ("CONFIG_MTK_ECCCI_C2K", "n"),
                ("CONFIG_MTK_ECCCI_DRIVER", "n"),
                ("CONFIG_MTK_MD1_SUPPORT", "0"),
            ],
        )

    def test_profile_and_graph_preserve_critical_capabilities(self):
        minimal = self.manifest["profiles"]["SERVER_MINIMAL"]
        self.assertEqual(self.manifest["profiles"]["VENDOR_REFERENCE"]["status"], "BLOCKED")
        self.assertEqual(minimal["status"], "SOURCE_ONLY")
        self.assertEqual(minimal["outputs"]["kernel"], "BLOCKED")
        self.assertEqual(minimal["outputs"]["dtb"], "BLOCKED")
        self.assertEqual(self.plan["status"], "SOURCE_ONLY")
        node_ids = {node["id"] for node in self.graph["nodes"]}
        for required in {
            "cpu-memory-interrupts",
            "ufs-storage",
            "usb",
            "wifi-networking",
            "battery-charging",
            "thermal-watchdog",
            "display-touch-input",
            "console-filesystem",
        }:
            self.assertIn(required, node_ids)

    def test_focaltech_patch_disables_only_auto_upgrade(self):
        patch = (
            ROOT / "devices/xiaomi-sea/server-minimal/patches/0001-focaltech-no-auto-upgrade.patch"
        ).read_text(encoding="utf-8")
        self.assertIn("FTS_AUTO_UPGRADE_EN                     0", patch)
        self.assertIn("+#if FTS_AUTO_UPGRADE_EN", patch)
        self.assertNotIn("CONFIG_TOUCHSCREEN_FTS is not set", patch)
        self.assertNotIn("fw_sample.i\n+", patch)

    def test_no_physical_write_or_boot_image_policy(self):
        self.assertFalse(self.plan["build_policy"]["write_device"])
        self.assertFalse(self.plan["build_policy"]["create_boot_image"])
        self.assertEqual(self.plan["outputs"]["boot_image"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
