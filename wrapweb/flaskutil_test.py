import unittest
from unittest import mock

import flask

from wrapweb import flaskutil

TEST_APP = flask.Flask(__name__)


def creator_proxy():
    pass


@flaskutil.appcontext_var(TEST_APP)
def appvar():
    return creator_proxy()


@appvar.teardown
def appvar_close(obj):
    obj.close()


TEST_BP = flask.Blueprint('test_bp', __name__)


@flaskutil.appcontext_var(TEST_BP)
def bpvar():
    return creator_proxy()


@bpvar.teardown
def bpvar_close(obj):
    obj.close()


TEST_APP.register_blueprint(TEST_BP)


class TestAppcontextVar(unittest.TestCase):

    @mock.patch(__name__ + '.creator_proxy')
    def test_call_app(self, proxy):
        with TEST_APP.app_context():
            appvar()
            proxy.assert_called_once_with()
        proxy.return_value.close.assert_called_once_with()

    @mock.patch(__name__ + '.creator_proxy')
    def test_no_teardown_on_error(self, proxy):
        proxy.side_effect = ValueError()
        with TEST_APP.app_context():
            with self.assertRaises(ValueError):
                appvar()
            proxy.assert_called_once_with()
        proxy.return_value.close.assert_not_called()

    @mock.patch(__name__ + '.creator_proxy')
    def test_call_bp(self, proxy):
        with TEST_APP.app_context():
            bpvar()
            proxy.assert_called_once_with()
        proxy.return_value.close.assert_called_once_with()

    @mock.patch(__name__ + '.creator_proxy')
    def test_no_teardown_on_error_bp(self, proxy):
        proxy.side_effect = ValueError()
        with TEST_APP.app_context():
            with self.assertRaises(ValueError):
                bpvar()
            proxy.assert_called_once_with()
        proxy.return_value.close.assert_not_called()


if __name__ == '__main__':
    unittest.main()
