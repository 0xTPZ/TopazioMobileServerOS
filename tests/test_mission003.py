import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from recovery.readiness import evaluate_manifest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host-tools"))


def load_tool(name):
    path = ROOT / "host-tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"mission003_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Mission003Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "devices/xiaomi-sea/device.json").read_text(encoding="utf-8"))
        cls.probe = load_tool("host_probe")
        cls.pipeline = load_tool("device_artifact_pipeline")

    def test_manifest_is_research_only(self):
        self.assertEqual(self.manifest["support_state"], "RESEARCH")
        self.assertFalse(self.manifest["installable"])
        self.assertEqual(self.manifest["kernel_source"]["branch"], "sea-t-oss")
        self.assertEqual(len(self.manifest["kernel_source"]["commit"]), 40)

    def test_host_probe_blocks_empty_transport(self):
        result = self.probe.evaluate({}, self.manifest)
        self.assertEqual(result["decision"], "BLOCKED_NO_READ_ONLY_TRANSPORT")
        self.assertFalse(result["installation_enabled"])

    def test_host_probe_aborts_mismatched_identity(self):
        result = self.probe.evaluate({"vendor": "xiaomi", "model": "Other", "codename": "sea"}, self.manifest)
        self.assertEqual(result["decision"], "ABORTED_IDENTITY_MISMATCH")

    def test_artifact_pipeline_blocks_missing_inputs_and_research_dsp(self):
        result = self.pipeline.plan(self.manifest, {"kernel": None, "dtb": None, "boot_image": None})
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("DSP_not_installable", result["missing"])

    def test_recovery_manifest_is_blocked_without_evidence(self):
        result = evaluate_manifest(self.manifest)
        self.assertEqual(result.decision, "BLOCKED")
        self.assertIn("dsp-installable", result.missing)

    def test_artifact_hashing_is_explicit_and_local(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(b"test artifact")
            digest = self.pipeline.sha256(path)
            self.assertEqual(len(digest), 64)


if __name__ == "__main__":
    unittest.main()
