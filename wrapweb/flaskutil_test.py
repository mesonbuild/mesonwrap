import unittest
from unittest import mock

import flask

from wrapweb import flaskutil

TEST_APP = flask.Flask(__name__)


def creator_proxy():
    pass


@flaskutil.appcontext_var(TEST_APP)
def foobar():
    return creator_proxy()


@foobar.teardown
def close(obj):
    obj.close()


class TestAppcontextVar(unittest.TestCase):

    @mock.patch(__name__ + '.creator_proxy')
    def test_call(self, proxy):
        with TEST_APP.app_context():
            foobar()
            proxy.assert_called_once_with()
        proxy.return_value.close.assert_called_once_with()

    @mock.patch(__name__ + '.creator_proxy')
    def test_no_teardown_on_error(self, proxy):
        proxy.side_effect = ValueError()
        with TEST_APP.app_context():
            with self.assertRaises(ValueError):
                foobar()
            proxy.assert_called_once_with()
        proxy.return_value.close.assert_not_called()


if __name__ == '__main__':
    unittest.main()
