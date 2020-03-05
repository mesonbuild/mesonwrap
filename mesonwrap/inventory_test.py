import unittest

from mesonwrap import inventory


class InventoryTest(unittest.TestCase):

    def test_custom(self):
        inv = inventory.Inventory('mesonbuild-test')
        self.assertIn('mesonbuild-test/meson', inv.restricted_projects)
        self.assertEqual('mesonbuild-test/wrapdb', inv.issue_tracker)

    def test_default(self):
        self.assertIn('mesonbuild/meson',
                      inventory.DEFAULT.restricted_projects)
        self.assertEqual('mesonbuild/wrapdb',
                         inventory.DEFAULT.issue_tracker)

    def test_is_wrap_project_name(self):
        projects = ['hello', 'world']
        for project in projects:
            with self.subTest(project=project):
                self.assertTrue(inventory.is_wrap_project_name(project))
        projects = ['meson', 'meson-ci']
        for project in projects:
            with self.subTest(project=project):
                self.assertFalse(inventory.is_wrap_project_name(project))

    def test_is_wrap_full_project_name(self):
        projects = ['mesonbuild/hello', 'mesonbuild/world']
        for project in projects:
            with self.subTest(project=project):
                self.assertTrue(inventory.is_wrap_full_project_name(project))
        projects = ['mesonbuild/meson', 'mesonbuild/meson-ci']
        for project in projects:
            with self.subTest(project=project):
                self.assertFalse(inventory.is_wrap_full_project_name(project))


if __name__ == '__main__':
    unittest.main()
