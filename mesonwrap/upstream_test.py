import unittest

from mesonwrap import upstream


class WrapFileTest(unittest.TestCase):

    def test_attr(self):
        w = upstream.WrapFile()
        for attr in ('directory',
                     'lead_directory_missing',
                     'source_url',
                     'source_filename',
                     'source_hash',
                     'patch_url',
                     'patch_filename',
                     'patch_hash'):
            setattr(w, attr, 'test-value')
            self.assertEqual(getattr(w, attr), 'test-value')
            self.assertTrue(getattr(w, 'has_' + attr))
            self.assertTrue(w.has(attr))

    def test_write(self):
        w = upstream.WrapFile()
        w.directory = '/hello/world'
        s = w.write_string()
        self.assertIn('/hello/world', s)
        self.assertIn('[wrap-file]', s)


if __name__ == '__main__':
    unittest.main()
