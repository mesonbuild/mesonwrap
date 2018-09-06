import os.path
import unittest

from mesonwrap import tempfile


class ModuleTest(unittest.TestCase):

    def test_names(self):
        for attr in ['mkdtemp', 'TemporaryFile', 'TemporaryDirectory']:
            with self.subTest(attr=attr):
                self.assertTrue(hasattr(tempfile, attr))


class TemporaryDirectoryTest(unittest.TestCase):

    def _test_directory(self, cls):
        with cls() as tmp:
            self.assertTrue(os.path.isdir(tmp))
            with open(os.path.join(tmp, 'test.txt'), 'w') as f:
                f.write('Hello, world!\n')
        self.assertFalse(os.path.exists(tmp))

    def test_TemporaryDirectory(self):
        self._test_directory(tempfile.TemporaryDirectory)

    def test_WindowsTemporaryDirectory(self):
        self._test_directory(tempfile._WindowsTemporaryDirectory)


if __name__ == '__main__':
    unittest.main()
