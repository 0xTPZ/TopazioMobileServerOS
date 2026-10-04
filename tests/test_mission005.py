import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host-tools"))


def load_tool(name):
    path = ROOT / "host-tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"mission005_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Mission005Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = json.loads((ROOT / "devices/xiaomi-sea/sources.json").read_text(encoding="utf-8"))
        cls.reconstruction = json.loads(
            (ROOT / "devices/xiaomi-sea/reconstruction/manifest.json").read_text(encoding="utf-8")
        )
        cls.research_tool = load_tool("research_db")
        cls.reconstruction_tool = load_tool("reconstruction_manifest")

    def test_research_database_is_valid_and_fail_closed(self):
        self.assertEqual(self.research_tool.validate(self.database), [])
        self.assertFalse(self.database["policies"]["community_replaces_official_silently"])
        self.assertFalse(self.database["policies"]["empty_firmware_accepted"])

    def test_cust_convergence_and_firmware_classification_are_explicit(self):
        convergence = self.database["measurements"]["cust_dtsi_independent_convergence"]
        self.assertEqual(convergence, {"sea": 1, "k6781v1_64_k419": 0, "interpretation": convergence["interpretation"]})
        firmware = next(item for item in self.database["components"] if item["id"] == "focaltech-fw-sample")
        self.assertEqual(firmware["classification"], "PROPRIETARY")
        self.assertEqual(firmware["redistributable"], "NOT_ESTABLISHED")

    def test_reconstruction_profiles_and_artifact_states(self):
        self.assertEqual(self.reconstruction_tool.validate(self.reconstruction), [])
        vendor = self.reconstruction["profiles"]["VENDOR_REFERENCE"]
        minimal = self.reconstruction["profiles"]["SERVER_MINIMAL"]
        self.assertEqual(vendor["status"], "BLOCKED")
        self.assertNotEqual(vendor["status"], "WORKING")
        self.assertEqual(vendor["outputs"]["dtbo"], "BUILT_UNTESTED")
        self.assertEqual(minimal["status"], "DESIGN_ONLY")

    def test_patch_order_validator_rejects_gaps(self):
        invalid = copy.deepcopy(self.reconstruction)
        invalid["profiles"]["VENDOR_REFERENCE"]["patches"] = [
            {"order": 1, "id": "first"},
            {"order": 3, "id": "gap"},
        ]
        self.assertTrue(self.reconstruction_tool.validate(invalid))

    def test_all_component_hashes_are_sha256_when_present(self):
        for component in self.database["components"]:
            digest = component.get("hashes", {}).get("sha256")
            if digest is not None:
                self.assertEqual(len(digest), 64)
                self.assertTrue(all(char in "0123456789abcdef" for char in digest))


if __name__ == "__main__":
    unittest.main()
