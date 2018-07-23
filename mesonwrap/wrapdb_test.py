import unittest

from mesonwrap import wrapdb


class WrapDatabaseTest(unittest.TestCase):

    def test_version_key(self):
        versions = [
            ('1.2.3', 8),
            ('1.2.11', 1),
            ('1.2.11', 2),
            ('11.2.3', 9),
            ('11.2.3', 11),
        ]
        sorted_versions = sorted(versions,
                                 key=wrapdb.WrapDatabase._version_key)
        self.assertEqual(versions, sorted_versions)


if __name__ == '__main__':
    unittest.main()
