import unittest
from unittest import mock

import flask

from wrapweb import api
from wrapweb import testing


class ApiTest(testing.TestBase):

    BLUEPRINT = api.BP

    def test_query_byname(self):
        self.database.insert('foo', '1.2.3', 3, '', b'')
        self.database.insert('foobar', '1.2.3', 3, '', b'')
        self.database.insert('bar', '1.2.3', 3, '', b'')
        rv = self.client.get('/v1/query/byname/foo')
        self.assertOk(rv)
        self.assertCountEqual(rv.get_json()['projects'],
                              ['foo', 'foobar'])

    def test_projects(self):
        self.database.insert('foo', '1.2.3', 3, '', b'')
        self.database.insert('foobar', '1.2.3', 3, '', b'')
        self.database.insert('bar', '1.2.3', 3, '', b'')
        rv = self.client.get('/v1/projects')
        self.assertOk(rv)
        self.assertCountEqual(rv.get_json()['projects'],
                              ['foo', 'foobar', 'bar'])

    def test_project(self):
        self.database.insert('foo', '1.2.3', 1, '', b'')
        self.database.insert('foo', '1.2.3', 3, '', b'')
        self.database.insert('foo', '1.2.4', 3, '', b'')
        rv = self.client.get('/v1/projects/foo')
        self.assertOk(rv)
        self.assertCountEqual(rv.get_json()['versions'], [
            dict(branch='1.2.3', revision=1),
            dict(branch='1.2.3', revision=3),
            dict(branch='1.2.4', revision=3),
        ])

    def test_get_wrap(self):
        self.database.insert('foo', '1.2.3', 1, 'some text', b'')
        rv = self.client.get('/v1/projects/foo/1.2.3/1/get_wrap')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_data(as_text=True),
                         'some text')

    def test_get_wrap(self):
        self.database.insert('foo', '1.2.3', 1, '', b'some data')
        rv = self.client.get('/v1/projects/foo/1.2.3/1/get_zip')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, b'some data')


if __name__ == '__main__':
    unittest.main()
