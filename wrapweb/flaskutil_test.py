import unittest
from unittest import mock

from wrapweb.app import APP
from wrapweb import flaskutil


def creator_proxy():
    pass


@flaskutil.local
def foobar():
    return creator_proxy()


@foobar.teardown
def close(obj):
    obj.close()


class TestLocalVariable(unittest.TestCase):

    @mock.patch(__name__ + '.creator_proxy')
    def test_local(self, proxy):
        with APP.app_context():
            foobar()
            proxy.assert_called_once_with()
        proxy.return_value.close.assert_called_once_with()

    @mock.patch(__name__ + '.creator_proxy')
    def test_no_teardown(self, proxy):
        proxy.side_effect = ValueError()
        with APP.app_context():
            pass
        proxy.assert_not_called()
        proxy.return_value.close.assert_not_called()


if __name__ == '__main__':
    unittest.main()
