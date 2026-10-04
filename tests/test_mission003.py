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
        cls.dts = load_tool("dts_graph")
        cls.toolchain = load_tool("toolchain_provenance")
        cls.sea_artifacts = load_tool("validate_sea_artifacts")

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

    def test_recovery_check_can_distinguish_not_ready_from_blocked(self):
        check = load_tool("recovery_check")
        evidence = {name: True for name in check.CHECKS}
        evidence["backup_verified"] = False
        ready_for_evaluation = dict(self.manifest)
        ready_for_evaluation["support_state"] = "SUPPORTED"
        ready_for_evaluation["installable"] = True
        result = check.evaluate(ready_for_evaluation, evidence)
        self.assertEqual(result["decision"], "NOT_READY")

    def test_artifact_hashing_is_explicit_and_local(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(b"test artifact")
            digest = self.pipeline.sha256(path)
            self.assertEqual(len(digest), 64)

    def test_mission004_provenance_is_pinned_without_binaries_in_repo(self):
        record = self.toolchain.load(ROOT / "devices/xiaomi-sea/provenance.json")
        self.assertEqual(self.toolchain.validate(record), [])
        self.assertEqual(record["policy"]["proprietary_blobs_in_repository"], False)
        clang = next(item for item in record["sources"] if item["name"] == "Android Clang prebuilt")
        self.assertEqual(len(clang["sha256"]["clang"]), 64)
        self.assertEqual(len(clang["sha256"]["ld.lld"]), 64)

    def test_mission004_dts_graph_fails_closed_on_missing_include(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = root / "sea.dts"
            entry.write_text('#include "present.dtsi"\n#include <sea/cust.dtsi>\n', encoding="utf-8")
            (root / "present.dtsi").write_text("/ { compatible = \"xiaomi,sea\"; };\n", encoding="utf-8")
            graph = self.dts.build_graph(entry, [root])
            self.assertEqual(graph["status"], "BLOCKED")
            self.assertEqual(graph["missing"][0]["include"], "sea/cust.dtsi")

    def test_mission004_manifest_keeps_recovery_blocked(self):
        self.assertEqual(self.manifest["recovery"]["status"], "BLOCKED")
        self.assertEqual(self.manifest["reconstruction"]["dtb"], "BLOCKED")
        self.assertFalse(self.manifest["reconstruction"]["cust_dtsi"]["imported"])

    def test_mission004_static_artifact_validation_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dtbo = root / "candidate.dtbo"
            dtbo.write_bytes(b"\xd0\x0d\xfe\xed" + b"candidate")
            self.assertEqual(self.sea_artifacts.validate(dtbo, "dtbo"), [])
            self.assertTrue(self.sea_artifacts.validate(root / "boot.img", "dtbo"))
            bad = root / "bad.dtbo"
            bad.write_bytes(b"not-fdt")
            self.assertTrue(self.sea_artifacts.validate(bad, "dtbo"))


if __name__ == "__main__":
    unittest.main()
