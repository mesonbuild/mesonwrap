import unittest

from mesonwrap import upstream


class UpstreamWrapTest(unittest.TestCase):

    def test_init(self):
        w = upstream.UpstreamWrap(source_url='hello',
                                  source_hash='world')
        self.assertEqual(w.source_url, 'hello')
        self.assertEqual(w.source_hash, 'world')

    def test_attr(self):
        w = upstream.UpstreamWrap()
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

    def test_section_not_found(self):
        w = upstream.UpstreamWrap()
        self.assertFalse(w.has_directory)
        with self.assertRaises(ValueError):
            self.assertIsNone(w.directory)

    def test_option_not_found(self):
        w = upstream.UpstreamWrap()
        w.source_filename = 'hello'
        self.assertFalse(w.has_directory)
        with self.assertRaises(ValueError):
            _ = w.directory

    def test_write(self):
        w = upstream.UpstreamWrap()
        w.directory = '/hello/world'
        s = w.write_string()
        self.assertIn('/hello/world', s)


if __name__ == '__main__':
    unittest.main()
