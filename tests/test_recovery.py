import unittest

from recovery.readiness import evaluate


class RecoveryTests(unittest.TestCase):
    def test_missing_prerequisites_block(self):
        result = evaluate(
            identity_confirmed=True,
            exact_dsp=False,
            backup_verified=False,
            recovery_procedure_verified=False,
            artifacts_hashed=True,
            permitted_partitions_enumerated=False,
        )
        self.assertEqual(result.decision, "BLOCKED")
        self.assertIn("exact-dsp", result.missing)

    def test_all_prerequisites_can_be_ready_without_writing(self):
        result = evaluate(
            identity_confirmed=True,
            exact_dsp=True,
            backup_verified=True,
            recovery_procedure_verified=True,
            artifacts_hashed=True,
            permitted_partitions_enumerated=True,
        )
        self.assertEqual(result.decision, "READY")


if __name__ == "__main__":
    unittest.main()
