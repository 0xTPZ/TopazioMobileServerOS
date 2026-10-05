import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_core():
    import sys

    package_path = ROOT / "host-tools"
    if str(package_path) not in sys.path:
        sys.path.insert(0, str(package_path))
    from firmware_forensics import core

    return core


def varint(value):
    result = bytearray()
    while value >= 0x80:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value)
    return bytes(result)


def field(number, wire_type, value):
    prefix = varint((number << 3) | wire_type)
    if wire_type == 0:
        return prefix + varint(value)
    if wire_type == 2:
        return prefix + varint(len(value)) + value
    raise AssertionError(wire_type)


def synthetic_payload():
    digest = hashlib.sha256(b"partition").digest()
    extent = field(1, 0, 0) + field(2, 0, 1)
    operation = (
        field(1, 0, 8)
        + field(2, 0, 123)
        + field(3, 0, 456)
        + field(6, 2, extent)
        + field(8, 2, digest)
    )
    partition_info = field(1, 0, 4096) + field(2, 2, digest)
    partition = field(1, 2, b"boot") + field(7, 2, partition_info) + field(8, 2, operation)
    group = field(1, 2, b"main") + field(2, 0, 8192) + field(3, 2, b"system")
    dynamic = field(1, 2, group) + field(2, 0, 1) + field(3, 0, 1) + field(4, 2, b"gz")
    manifest = field(3, 0, 4096) + field(13, 2, partition) + field(15, 2, dynamic)
    return b"CrAU" + struct.pack(">QQI", 2, len(manifest), 0) + manifest


def synthetic_fdt():
    strings = b"compatible\x00model\x00"
    structure = bytearray()
    structure += struct.pack(">I", 1) + b"\x00\x00\x00\x00"
    for name_offset, value in ((0, b"mediatek,sea\x00"), (11, b"Redmi sea\x00")):
        structure += struct.pack(">III", 3, len(value), name_offset)
        structure += value
        structure += b"\x00" * ((-len(value)) % 4)
    structure += struct.pack(">II", 2, 9)
    structure_offset = 56
    strings_offset = structure_offset + len(structure)
    total = strings_offset + len(strings)
    header = struct.pack(
        ">10I", 0xD00DFEED, total, structure_offset, strings_offset, 40, 17, 16, 0, len(strings), len(structure)
    )
    return header + b"\x00" * 16 + bytes(structure) + strings


class Mission010Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = load_core()
        cls.report = json.loads(
            (ROOT / "devices/xiaomi-sea/firmware-forensics/mission-010.json").read_text(
                encoding="utf-8"
            )
        )

    def test_payload_manifest_identity_and_partition_model(self):
        raw_payload = synthetic_payload()
        result = self.core.parse_update_payload(raw_payload, "synthetic-payload.bin")
        self.assertEqual(result["magic"], "CrAU")
        self.assertTrue(result["is_full_payload"])
        self.assertEqual(result["partitions"][0]["name"], "boot")
        self.assertEqual(result["partitions"][0]["operation_types"], ["REPLACE_XZ"])
        self.assertTrue(result["dynamic_partition_metadata"]["snapshot_enabled"])
        self.assertTrue(result["dynamic_partition_metadata"]["vabc_enabled"])
        with tempfile.TemporaryDirectory() as temp:
            payload_path = Path(temp) / "payload.bin"
            payload_path.write_bytes(raw_payload)
            file_result = self.core.parse_update_payload_file(payload_path)
            self.assertEqual(file_result["manifest_sha256"], result["manifest_sha256"])

    def test_fdt_and_vendor_boot_parsers(self):
        with tempfile.TemporaryDirectory() as temp:
            fdt = Path(temp) / "candidate.dtb"
            fdt.write_bytes(synthetic_fdt())
            parsed = self.core.parse_fdt(fdt.read_bytes(), str(fdt))
            names = {item["name"] for item in parsed["properties"]}
            self.assertEqual(parsed["version"], 17)
            self.assertIn("compatible", names)
            self.assertIn("model", names)

            page = 4096
            vendor = bytearray(page * 3)
            vendor[:8] = b"VNDRBOOT"
            struct.pack_into("<7I", vendor, 8, 3, page, 4, 0, 0, 2112, 4)
            struct.pack_into("<Q", vendor, 36, 0x1234)
            vendor[page : page + 4] = b"RAMD"
            vendor[page * 2 : page * 2 + 4] = b"DTB!"
            vendor_path = Path(temp) / "vendor_boot.img"
            vendor_path.write_bytes(vendor)
            vendor_result = self.core.parse_vendor_boot(vendor_path)
            self.assertTrue(vendor_result["vendor_ramdisk"]["bounds_valid"])
            self.assertTrue(vendor_result["dtb"]["bounds_valid"])

    def test_avb_descriptor_parser_consumes_descriptor_sizes(self):
        vbmeta = bytearray(256 + 320 + 72)
        vbmeta[:4] = b"AVB0"
        values = [1, 0, 320, 72, 1, 0, 32, 32, 256, 0, 0, 0, 0, 0, 72, 0, 0, 0]
        struct.pack_into(">IIQQIQQQQQQQQQQQII", vbmeta, 4, *values)
        struct.pack_into(">QQ", vbmeta, 576, 0, 56)
        struct.pack_into(">QQ", vbmeta, 592, 3, 1)
        parsed = self.core.parse_vbmeta_bytes(bytes(vbmeta), "synthetic-vbmeta")
        self.assertTrue(parsed["descriptor_parse_complete"])
        self.assertEqual(parsed["descriptors"][0]["type"], "property")

    def test_semantic_comparison_fails_closed_without_stock(self):
        blocked = self.core.compare_dt_semantics(None, {"properties": []})
        self.assertEqual(blocked["status"], "BLOCKED_NO_STOCK_REFERENCE")
        compared = self.core.compare_dt_semantics(
            {"properties": [{"name": "ufs"}, {"name": "thermal"}]},
            {"properties": [{"name": "ufs"}, {"name": "usb"}]},
        )
        self.assertEqual(compared["status"], "COMPARED_PROPERTY_IDENTITY")

    def test_mission_report_is_partial_and_write_safe(self):
        self.assertEqual(self.report["status"], "PARTIAL")
        self.assertFalse(self.report["pass_gate"])
        self.assertFalse(self.report["decision"]["phone_writes_performed"])
        self.assertEqual(self.report["partition_model"]["ab"], "CONFIRMED")
        self.assertEqual(self.report["partition_model"]["virtual_ab"], "CONFIRMED")
        self.assertEqual(self.report["dtbo"]["status"], "STOCK_CONFIRMED")
        self.assertEqual(self.report["recovery_model"]["readiness"], "NOT_READY")


if __name__ == "__main__":
    unittest.main()
