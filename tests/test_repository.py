import unittest

from host_tools_compat import load_verify


class RepositoryTests(unittest.TestCase):
    def test_required_structure(self):
        verify = load_verify()
        self.assertEqual(verify.validate(), [])


if __name__ == "__main__":
    unittest.main()
