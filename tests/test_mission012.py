import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host-tools"))

from device_command_safety import classify_command  # noqa: E402
from device_inventory.report import build_observation  # noqa: E402
from device_inventory.sanitize import sanitize_text  # noqa: E402
from device_inventory.transport import CommandResult, collect_transport_commands  # noqa: E402


def result(command_id, command, stdout="", stderr="", exit_code=0, executable=True):
    return CommandResult(
        command_id=command_id,
        transport="adb" if command.startswith("adb ") else "fastboot",
        command=command,
        safety_class="READ_ONLY_SAFE",
        executable_present=executable,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        sanitized_stdout=sanitize_text(stdout),
        sanitized_stderr=sanitize_text(stderr),
        result_hash="hash",
        timestamp="2026-10-05T00:00:00+00:00",
    )


class Mission012Tests(unittest.TestCase):
    def test_allowlist_and_rejections(self):
        self.assertEqual(classify_command("adb devices"), "READ_ONLY_SAFE")
        self.assertEqual(classify_command("fastboot devices"), "READ_ONLY_SAFE")
        self.assertEqual(classify_command("fastboot getvar product"), "READ_ONLY_SAFE")
        self.assertEqual(classify_command("fastboot getvar all"), "UNKNOWN")
        self.assertEqual(classify_command("adb shell dd if=x of=y"), "WRITE")
        self.assertEqual(classify_command("adb reboot bootloader"), "STATE_CHANGING")
        self.assertEqual(classify_command("adb shell su"), "UNKNOWN")

    def test_sanitization_removes_identifiers_and_transport_serial(self):
        raw = "[ro.serialno]: [ABC123]\nIMEI=123456789012345\nAA:BB:CC:DD:EE:FF\nserial123\tdevice\n"
        sanitized = sanitize_text(raw)
        self.assertNotIn("ABC123", sanitized)
        self.assertNotIn("123456789012345", sanitized)
        self.assertNotIn("AA:BB:CC:DD:EE:FF", sanitized)
        self.assertNotIn("serial123", sanitized)
        self.assertIn("<REDACTED_SERIAL>", sanitized)

    def test_dry_run_marks_every_command_safe_without_execution(self):
        results = collect_transport_commands(dry_run=True)
        self.assertGreater(len(results), 0)
        self.assertTrue(all(item.safety_class == "READ_ONLY_SAFE" for item in results))
        self.assertTrue(all(item.exit_code is None for item in results))
        self.assertTrue(all(item.stderr == "DRY_RUN" for item in results))

    def test_sanitized_observation_ota_comparison_and_recovery(self):
        props = "\n".join(
            [
                "[ro.product.manufacturer]: [Xiaomi]",
                "[ro.product.model]: [Redmi Note 12S]",
                "[ro.product.device]: [sea]",
                "[ro.product.name]: [sea_global]",
                "[ro.build.fingerprint]: [Redmi/sea_global/sea:15/AP3A.240905.015.A2/OS2.0.209.0.VHZMIXM:user/release-keys]",
                "[ro.build.id]: [AP3A.240905.015.A2]",
                "[ro.build.version.release]: [15]",
                "[ro.product.cpu.abilist64]: [arm64-v8a]",
                "[ro.boot.slot_suffix]: [_a]",
                "[ro.boot.flash.locked]: [1]",
                "[ro.boot.verifiedbootstate]: [green]",
            ]
        )
        report = build_observation(
            [
                result("adb_devices", "adb devices", "ABC123\tdevice\n"),
                result("adb_getprop", "adb shell getprop", props + "\n"),
                result("adb_uname", "adb shell uname -a", "Linux localhost 6.6.58-android15-8 #1 SMP aarch64\n"),
                result("adb_meminfo", "adb shell cat /proc/meminfo", "MemTotal:       8192000 kB\n"),
                result("adb_modules", "adb shell cat /proc/modules", "cfg80211 123 0 - Live 0\n"),
            ]
        )
        self.assertEqual(report["transport"]["adb"]["value"], "PRESENT_AUTHORIZED")
        self.assertEqual(report["identity"]["codename_assessment"]["value"], "sea")
        self.assertEqual(report["software"]["ota_comparison"]["value"], "EXACT_MATCH")
        self.assertEqual(report["kernel"]["unit_matches_stock_kernel"]["value"], "YES")
        self.assertEqual(report["ram"]["unit_ram_total_bytes"]["value"], 8192000 * 1024)
        self.assertEqual(report["recovery_readiness"], "NOT_READY")
        self.assertFalse(report["phone_writes_performed"])
        self.assertFalse(report["phone_state_changed"])
        self.assertNotIn("ABC123", str(report))

    def test_empty_observation_is_transport_blocked_and_schema_complete(self):
        report = build_observation([])
        self.assertEqual(report["next_hardware_gate"], "PHYSICAL_TRANSPORT_BLOCKED")
        self.assertEqual(report["recovery_readiness"], "BLOCKED")
        for section in ("identity", "software", "kernel", "ram", "storage", "ufs", "slot", "partition_names", "boot_state", "avb_state", "dt_metadata", "modules", "thermal", "power", "display", "touch", "transport"):
            self.assertIn(section, report)


if __name__ == "__main__":
    unittest.main()
