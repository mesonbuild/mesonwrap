import unittest

from mesonwrap import ini


class TestIni(ini.IniFile):

    field1 = ini.IniField('section1')
    field2 = ini.IniField('section2', '_field2_')
    field3 = ini.IniField('section2')


class WrapFileTest(unittest.TestCase):

    def test_init(self):
        f = TestIni(field1='value1', field2='value2', field3='value3')

        self.assertEqual(f.field1, 'value1')
        self.assertTrue(f.has_field1)
        self.assertEqual(f._cfg.get('section1', 'field1'), 'value1')

        self.assertEqual(f.field2, 'value2')
        self.assertTrue(f.has_field2)
        self.assertEqual(f._cfg.get('section2', '_field2_'), 'value2')

        self.assertEqual(f.field3, 'value3')
        self.assertTrue(f.has_field3)
        self.assertEqual(f._cfg.get('section2', 'field3'), 'value3')

    def test_attr(self):
        f = TestIni()
        for attr in ('field1', 'field2', 'field3'):
            setattr(f, attr, 'test-value')
            self.assertEqual(getattr(f, attr), 'test-value')
            self.assertTrue(getattr(f, 'has_' + attr))
            self.assertTrue(f.has(attr))

    def test_section_not_found(self):
        f = TestIni()
        self.assertFalse(f.has_field1)
        self.assertFalse(f.has('field1'))
        with self.assertRaises(ValueError):
            _ = f.field1

    def test_option_not_found(self):
        f = TestIni(field2='hello')  # create section2
        self.assertFalse(f.has_field3)
        self.assertFalse(f.has('field3'))
        with self.assertRaises(ValueError):
            _ = f.field3

    def test_write(self):
        f = TestIni()
        f.field1 = '/hello/world'
        s = f.write_string()
        self.assertIn('field1 = /hello/world', s)
        self.assertIn('[section1]', s)


class WrapFileTest(unittest.TestCase):

    def test_attr(self):
        w = ini.WrapFile()
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
        w = ini.WrapFile()
        w.directory = '/hello/world'
        s = w.write_string()
        self.assertIn('/hello/world', s)
        self.assertIn('[wrap-file]', s)


if __name__ == '__main__':
    unittest.main()
