import unittest

from mesonwrap import upstream


class UpstreamWrapTest(unittest.TestCase):

    def test_attr(self):
        w = upstream.UpstreamWrap()
        for attr in ('directory',
                     'source_url',
                     'source_filename',
                     'source_hash',
                     'patch_url',
                     'patch_filename',
                     'patch_hash'):
            setattr(w, attr, 'test-value')
            self.assertEqual(getattr(w, attr), 'test-value')

    def test_write(self):
        w = upstream.UpstreamWrap()
        w.directory = '/hello/world'
        s = w.write_string()
        self.assertIn('/hello/world', s)


if __name__ == '__main__':
    unittest.main()
