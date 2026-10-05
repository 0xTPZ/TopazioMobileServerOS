import gzip
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


ROOT = Path(__file__).resolve().parents[1]


def load_core():
    package_path = ROOT / "host-tools"
    if str(package_path) not in sys.path:
        sys.path.insert(0, str(package_path))
    from firmware_forensics import core

    return core


def synthetic_fdt(properties):
    strings = bytearray()
    offsets = {}
    for name, _value in properties:
        if name not in offsets:
            offsets[name] = len(strings)
            strings.extend(name.encode() + b"\x00")
    structure = bytearray(struct.pack(">I", 1) + b"\x00\x00\x00\x00")
    for name, value in properties:
        structure.extend(struct.pack(">III", 3, len(value), offsets[name]))
        structure.extend(value)
        structure.extend(b"\x00" * ((-len(value)) % 4))
    structure.extend(struct.pack(">I", 2))
    structure.extend(struct.pack(">I", 9))
    structure_offset = 56
    strings_offset = structure_offset + len(structure)
    total_size = strings_offset + len(strings)
    header = struct.pack(
        ">10I",
        0xD00DFEED,
        total_size,
        structure_offset,
        strings_offset,
        40,
        17,
        16,
        0,
        len(strings),
        len(structure),
    )
    return header + b"\x00" * 16 + bytes(structure) + bytes(strings)


class Mission011Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = load_core()

    def test_fdt_scanner_rejects_magic_only_and_accepts_complete_tree(self):
        tree = synthetic_fdt([("compatible", b"mediatek,mt6781\x00")])
        data = b"prefix\xd0\x0d\xfe\xednot-a-tree" + tree + b"suffix"
        result = self.core.scan_fdt_candidates(data, "synthetic")
        self.assertEqual(result["candidate_count"], 2)
        self.assertEqual(result["valid_count"], 1)
        valid = [item for item in result["candidates"] if item["valid"]][0]
        self.assertEqual(valid["compatible"], ["mediatek,mt6781"])

    def test_dt_matcher_is_explicitly_not_stock_confirmation(self):
        dtbo = {
            "required_base_symbols": [{"symbol": "pio"}, {"symbol": "i2c0"}],
        }
        candidate = {
            "name": "public-mt6781",
            "sha256": "candidate",
            "compatible": ["mediatek,mt6781"],
            "symbols": ["pio", "i2c0"],
        }
        result = self.core.match_dt_base(dtbo, [candidate])
        self.assertEqual(result["candidates"][0]["status"], "CANDIDATE_ONLY")
        self.assertFalse(result["stock_confirmation"])

    def test_kernel_analysis_reports_gki_evidence_and_ikconfig(self):
        config = b"CONFIG_MODULES=y\nCONFIG_MODVERSIONS=y\nCONFIG_GKI_HACKS_TO_FIX=y\n"
        payload = b"\x00" * 0x38 + b"ARMd" + b"Linux version 6.6.58-android15-8 (kleaf@build-host) clang version 18.0.0\x00"
        payload += b"IKCFG_ST" + gzip.compress(config) + b"IKCFG_ED"
        result = self.core.analyze_kernel(gzip.compress(payload))
        self.assertEqual(result["analysis_status"], "DECOMPRESSED")
        self.assertEqual(result["embedded_ikconfig"]["status"], "CONFIRMED")
        self.assertEqual(result["gki_evidence"]["status"], "GKI_LIKELY")
        self.assertEqual(result["embedded_ikconfig"]["selected_options"]["CONFIG_MODULES"], "y")

    def test_dtbo_analysis_and_symbol_inventory_are_traceable(self):
        report = json.loads(
            (ROOT / "devices/xiaomi-sea/reconstruction/stock-required-base-symbols.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(report["status"], "REQUIRED_SYMBOLS_EXTRACTED")
        self.assertEqual(len(report["symbols"]), 60)
        self.assertFalse(report["stock_base_dtb_confirmed"])

    def test_module_metadata_inventory_does_not_inspect_binaries(self):
        with tempfile.TemporaryDirectory() as temp:
            modules = Path(temp) / "lib" / "modules"
            modules.mkdir(parents=True)
            (modules / "modules.load").write_text("wifi.ko\n", encoding="utf-8")
            (modules / "modules.dep").write_text("wifi.ko:\n", encoding="utf-8")
            (modules / "wifi.ko").write_bytes(b"not inspected")
            result = self.core.analyze_module_metadata(modules)
            self.assertEqual(result["status"], "FOUND")
            self.assertEqual(result["metadata_file_count"], 2)
            self.assertFalse(result["module_binaries_inspected"])

    def test_dual_kernel_tracks_and_readonly_plan_are_recorded(self):
        report = json.loads(
            (ROOT / "devices/xiaomi-sea/firmware-forensics/mission-011.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(report["dual_kernel_tracks"]["legacy"]["kernel_version"], "4.19.191")
        self.assertEqual(report["dual_kernel_tracks"]["current_stock"]["kernel_version"], "6.6.58-android15-8")
        self.assertEqual(report["read_only_inventory_plan"]["execution_status"], "NOT_EXECUTED")
        self.assertFalse(report["decision"]["phone_writes_performed"])

    def test_command_safety_classification(self):
        from device_command_safety import classify_command

        self.assertEqual(classify_command("adb shell cat /proc/meminfo"), "READ_ONLY_SAFE")
        self.assertEqual(classify_command("fastboot getvar all"), "UNKNOWN")
        self.assertEqual(classify_command("adb reboot bootloader"), "STATE_CHANGING")
        self.assertEqual(classify_command("fastboot flash boot boot.img"), "WRITE")
        self.assertEqual(classify_command("adb shell dd if=x of=y"), "WRITE")


if __name__ == "__main__":
    unittest.main()
