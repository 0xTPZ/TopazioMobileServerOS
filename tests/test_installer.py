import unittest

from installer.topazio_installer import DeviceObservation, build_plan


SEA = {"model": "Redmi Note 12S", "support_state": "RESEARCH"}


class InstallerPolicyTests(unittest.TestCase):
    def test_no_device_is_safe(self):
        plan = build_plan(DeviceObservation(), {"xiaomi-sea": SEA})
        self.assertEqual(plan.decision, "NO_DEVICE")

    def test_research_device_is_not_installable(self):
        observation = DeviceObservation(transport="usb", vendor="xiaomi", model="Redmi Note 12S", codename="sea")
        plan = build_plan(observation, {"xiaomi-sea": SEA})
        self.assertEqual(plan.decision, "UNSUPPORTED")

    def test_mismatched_model_aborts(self):
        observation = DeviceObservation(transport="usb", vendor="xiaomi", model="Other", codename="sea")
        plan = build_plan(observation, {"xiaomi-sea": SEA})
        self.assertEqual(plan.decision, "UNSUPPORTED")

    def test_non_read_only_observation_aborts_even_if_registry_is_ready(self):
        registry = {"vendor-code": {"model": "Model", "support_state": "SUPPORTED"}}
        observation = DeviceObservation(
            transport="usb", vendor="vendor", model="Model", codename="code",
            recovery_ready="CONFIRMED", bootloader_state="AUTHORIZED", read_only=False,
        )
        plan = build_plan(observation, registry)
        self.assertEqual(plan.decision, "ABORTED")


if __name__ == "__main__":
    unittest.main()
