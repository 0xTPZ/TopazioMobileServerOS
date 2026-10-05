import gzip
import importlib.util
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_forensics_cli():
    path = ROOT / "host-tools" / "firmware_forensics.py"
    spec = importlib.util.spec_from_file_location("mission009_firmware_forensics", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load firmware forensics CLI")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_core():
    package_path = ROOT / "host-tools"
    import sys

    if str(package_path) not in sys.path:
        sys.path.insert(0, str(package_path))
    from firmware_forensics import core

    return core


def cpio_entry(name, body=b""):
    fields = [
        b"070701",
        f"{0:08x}".encode(),
        f"{0o100644:08x}".encode(),
        f"{0:08x}".encode(),
        f"{0:08x}".encode(),
        f"{1:08x}".encode(),
        f"{0:08x}".encode(),
        f"{len(body):08x}".encode(),
        f"{0:08x}".encode(),
        f"{0:08x}".encode(),
        f"{0:08x}".encode(),
        f"{0:08x}".encode(),
        f"{len(name) + 1:08x}".encode(),
        b"00000000",
    ]
    header = b"".join(fields)
    result = header + name.encode() + b"\x00"
    result += b"\x00" * ((-len(result)) % 4)
    result += body
    result += b"\x00" * ((-len(result)) % 4)
    return result


class Mission009Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(
            (ROOT / "devices/xiaomi-sea/firmware-forensics/mission-009.json").read_text(
                encoding="utf-8"
            )
        )
        cls.device = json.loads(
            (ROOT / "devices/xiaomi-sea/device.json").read_text(encoding="utf-8")
        )
        cls.core = load_core()
        cls.cli = load_forensics_cli()

    def test_report_is_partial_and_fail_closed(self):
        self.assertEqual(self.report["status"], "PARTIAL")
        self.assertFalse(self.report["pass_gate"])
        self.assertFalse(self.report["decision"]["phone_writes_performed"])
        self.assertEqual(self.report["decision"]["recovery_readiness"], "BLOCKED")
        self.assertFalse(self.report["decision"]["dt_sea_candidate"])
        self.assertIsNone(self.report["source_trust"]["official_package_metadata"]["package_sha256"])

    def test_stock_component_identity_and_hash_contract(self):
        component = self.report["source_trust"]["boot_component"]
        self.assertEqual(component["size_bytes"], 67108864)
        self.assertEqual(len(component["sha256"]), 64)
        self.assertTrue(component["mirror_sha256_verified"])
        boot = self.report["boot_image"]
        self.assertEqual(boot["header"]["version"], 3)
        self.assertEqual(boot["kernel"]["linux_version"], "6.6.58-android15-8-g19e0e8cef6b2-4k")
        self.assertEqual(boot["ramdisk"]["bootimage_device"], "sea")

    def test_boot_header_parser_and_extraction(self):
        kernel = gzip.compress(b"Linux version 6.6-test\x00")
        ramdisk = cpio_entry("system/etc/ramdisk/build.prop", b"ro.product.bootimage.device=sea\n")
        ramdisk += cpio_entry("TRAILER!!!")
        page = 4096
        image = bytearray(page)
        image[:8] = b"ANDROID!"
        struct.pack_into("<IIII", image, 8, len(kernel), len(ramdisk), 0x1E00019C, 1580)
        struct.pack_into("<I", image, 40, 3)
        image.extend(kernel)
        image.extend(b"\x00" * ((-len(image)) % page))
        image.extend(ramdisk)
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "boot.img"
            source.write_bytes(image)
            result = self.core.parse_android_boot(source, Path(temp) / "parts")
            self.assertEqual(result["header_version"], 3)
            self.assertEqual(result["kernel_analysis"]["analysis_status"], "DECOMPRESSED")
            self.assertTrue(result["ramdisk_analysis"]["cpio"]["parse_complete"])
            self.assertEqual(Path(result["extracted"]["kernel"]).name, "kernel")

    def test_dtbo_and_avb_parsers(self):
        dtbo = bytearray(struct.pack(">8I", 0xD7B7AB1E, 68, 32, 32, 1, 32, 4096, 0))
        dtbo.extend(struct.pack(">8I", 4, 64, 7, 2, 11, 12, 13, 14))
        dtbo.extend(b"DTBO")
        with tempfile.TemporaryDirectory() as temp:
            dtbo_path = Path(temp) / "dtbo.img"
            dtbo_path.write_bytes(dtbo)
            parsed = self.core.parse_dtbo(dtbo_path)
            self.assertEqual(parsed["entry_count"], 1)
            self.assertEqual(parsed["entries"][0]["id"], 7)

            vbmeta = bytearray(256)
            vbmeta[:4] = b"AVB0"
            values = [1, 0] + [0] * 16
            struct.pack_into(">IIQQIQQQQQQQQQQQII", vbmeta, 4, *values)
            vbmeta_path = Path(temp) / "vbmeta.img"
            vbmeta_path.write_bytes(vbmeta)
            avb = self.core.parse_vbmeta(vbmeta_path)
            self.assertEqual(avb["magic"], "AVB0")
            self.assertEqual(avb["version"]["major"], 1)

    def test_package_inventory_and_device_manifest_link(self):
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp) / "package.zip"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("images/boot.img", b"boot")
                archive.writestr("payload.bin", b"payload")
            inventory = self.core.inventory_package(package)
            self.assertEqual(inventory["type"], "zip")
            self.assertTrue(inventory["known_names"]["boot.img"])
            self.assertTrue(inventory["known_names"]["payload.bin"])
        self.assertEqual(
            self.device["mission_009_stock_forensics"]["report"],
            "firmware-forensics/mission-009.json",
        )

    def test_acquisition_has_no_device_transport(self):
        source = (ROOT / "host-tools/firmware_forensics/acquire.py").read_text(
            encoding="utf-8"
        ).lower()
        self.assertNotIn("subprocess", source)
        self.assertNotIn("adb", source)
        self.assertNotIn("fastboot", source)


if __name__ == "__main__":
    unittest.main()
