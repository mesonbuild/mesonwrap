import unittest

import flask

from wrapweb import api
from wrapweb import testing


class ApiTest(testing.TestBase):

    BLUEPRINT = api.BP

    def test_name_query(self):
        self.database.insert('foo', '1.2.3', 3, '', b'')
        self.database.insert('foobar', '1.2.3', 3, '', b'')
        self.database.insert('bar', '1.2.3', 3, '', b'')
        rv = self.client.get('/v1/query/byname/foo')
        self.assertEqual(rv.status_code, 200)
        self.assertCountEqual(rv.get_json()['projects'],
                              ['foo', 'foobar'])


if __name__ == '__main__':
    unittest.main()
