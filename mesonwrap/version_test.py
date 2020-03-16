import unittest

from mesonwrap import version


class VersionTest(unittest.TestCase):

    def test_semantic(self):
        versions = [
            ('1.2.3', 8),
            ('1.2.11', 1),
            ('1.2.11', 2),
            ('11.2.3', 9),
            ('11.2.3', 11),
        ]
        sorted_versions = sorted(versions,
                                 key=version.version_key)
        self.assertEqual(versions, sorted_versions)

    def test_non_semantic(self):
        versions = [
            ('1.2', 1),
            ('1.3', 5),
            ('1.7', 2),
        ]
        sorted_versions = sorted(versions,
                                 key=version.version_key)
        self.assertEqual(versions, sorted_versions)

    def test_non_semantic_single_number(self):
        versions = [
            ('12345', 1),
            ('212345', 1),
        ]
        sorted_versions = sorted(versions,
                                 key=version.version_key)
        self.assertEqual(versions, sorted_versions)

    def test_non_semantic_version_letters(self):
        versions = [
            ('2b', 1),
            ('17a', 1),
        ]
        sorted_versions = sorted(versions,
                                 key=version.version_key)
        self.assertEqual(versions, sorted_versions)


if __name__ == '__main__':
    unittest.main()
