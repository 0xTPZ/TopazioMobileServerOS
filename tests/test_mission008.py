import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_tool(name):
    path = ROOT / "host-tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"mission008_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Mission008Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analysis = json.loads(
            (ROOT / "devices/xiaomi-sea/reconstruction/dt-analysis.json").read_text(
                encoding="utf-8"
            )
        )
        cls.sea_graph = json.loads(
            (ROOT / "devices/xiaomi-sea/reconstruction/official-sea-dts-graph.json").read_text(
                encoding="utf-8"
            )
        )
        cls.k_graph = json.loads(
            (ROOT / "devices/xiaomi-sea/reconstruction/official-k6781-dts-graph.json").read_text(
                encoding="utf-8"
            )
        )
        cls.base_graph = json.loads(
            (ROOT / "devices/xiaomi-sea/reconstruction/official-mt6781-base-dts-graph.json").read_text(
                encoding="utf-8"
            )
        )
        cls.baseline = json.loads(
            (ROOT / "devices/xiaomi-sea/server-minimal/kernel-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        cls.gate = json.loads(
            (ROOT / "devices/xiaomi-sea/server-minimal/build-gate.json").read_text(
                encoding="utf-8"
            )
        )
        cls.baseline_tool = load_tool("verify_kernel_baseline")

    def test_graphs_fail_closed_and_have_provenance_contract(self):
        self.assertEqual(self.sea_graph["status"], "BLOCKED")
        self.assertEqual(self.k_graph["status"], "BLOCKED")
        self.assertEqual(self.base_graph["status"], "COMPLETE")
        self.assertEqual(self.base_graph["missing"], [])
        self.assertEqual(self.sea_graph["missing"][0]["include"], "sea/cust.dtsi")
        self.assertEqual(
            self.k_graph["missing"][0]["include"], "k6781v1_64_k419/cust.dtsi"
        )
        for graph in (self.sea_graph, self.k_graph, self.base_graph):
            for node in graph["nodes"]:
                for field in (
                    "path",
                    "source",
                    "sha256",
                    "provenance",
                    "confidence",
                    "required",
                    "available",
                ):
                    self.assertIn(field, node)
            self.assertEqual(graph["provenance"]["source_id"], "xiaomi-kernel-sea-t-oss")

    def test_roles_and_cust_confidence_are_explicit(self):
        self.assertTrue(
            any("/plugin/" in item for item in self.analysis["source_roles"]["sea_dts"]["evidence"])
        )
        self.assertEqual(
            self.analysis["cust_dtsi_audit"]["sea/cust.dtsi"]["confidence"],
            "STRONG_CANDIDATE",
        )
        self.assertFalse(
            self.analysis["cust_dtsi_audit"]["sea/cust.dtsi"]["imported_into_topazio"]
        )
        self.assertEqual(
            self.analysis["cust_dtsi_audit"]["k6781v1_64_k419/cust.dtsi"][
                "public_versions_located"
            ],
            0,
        )

    def test_overlay_provenance_and_offline_apply(self):
        candidate = self.analysis["dtbo_candidate"]
        self.assertEqual(candidate["sha256"], "34febe33284575825169a1b46f6f438491bd5f7ffd7931ed44dc746f0f1b01ab")
        self.assertEqual(candidate["structure"]["fragment_count"], 65)
        self.assertEqual(candidate["structure"]["fixup_symbol_count"], 51)
        self.assertFalse(candidate["installable"])
        apply = self.analysis["offline_apply"]
        self.assertEqual(apply["merged"]["tool"], "fdtoverlay")
        self.assertEqual(apply["merged"]["exit_code"], 0)
        self.assertEqual(apply["merged"]["structural_recompile_exit_code"], 0)
        self.assertNotIn(
            "auto2712p1v1-ivi-boot.dtb",
            self.analysis["base_candidates"]["most_defensible_public_candidate"]["name"],
        )

    def test_required_symbols_and_critical_safety_gates(self):
        symbols = self.analysis["required_base_symbols"]
        self.assertIn("i2c5", symbols)
        self.assertIn("reserved_memory", symbols)
        self.assertIn("dsi0", symbols)
        self.assertEqual(len(symbols), 51)
        self.assertEqual(self.analysis["critical_coverage"]["ram"]["safety"], "DANGEROUS_AMBIGUITY")
        self.assertEqual(self.analysis["critical_coverage"]["ufs"]["safety"], "DANGEROUS_AMBIGUITY")
        self.assertEqual(self.analysis["highest_achieved_level"], "DT_STRUCTURALLY_VALID")
        self.assertFalse(self.analysis["level_policy"]["dt_sea_candidate"])
        self.assertFalse(self.analysis["level_policy"]["dt_working"])

    def test_kernel_baseline_is_verified_and_detects_regression(self):
        self.assertEqual(
            self.baseline_tool.validate_baseline(
                self.baseline, self.gate, ROOT, require_files=False
            ),
            [],
        )
        changed = copy.deepcopy(self.gate)
        changed["source"]["commit"] = "regression"
        self.assertTrue(
            self.baseline_tool.validate_baseline(
                self.baseline, changed, ROOT, require_files=False
            )
        )

    def test_recovery_and_phone_write_remain_blocked(self):
        decision = self.analysis["decision"]
        self.assertEqual(decision["recovery_readiness"], "BLOCKED")
        self.assertFalse(decision["ready_for_phone_write"])
        self.assertFalse(decision["phone_writes_performed"])
        self.assertFalse(decision["mission_009_started"])


if __name__ == "__main__":
    unittest.main()
