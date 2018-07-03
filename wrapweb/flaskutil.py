import flask
import typing

from wrapweb.app import APP


class LocalVariable:
    """Wrapper for flask.g cached variables pattern."""

    def __init__(self, name: str, init: typing.Callable[[], typing.Any]):
        self._name = name
        self._init = init

    @property
    def _value(self):
        return getattr(flask.g, self._name, None)

    @_value.setter
    def _value(self, value):
        setattr(flask.g, self._name, value)

    def __call__(self):
        """Initializes value if necessary and returns it."""
        value = self._value
        if value is None:
            value = self._init()
            self._value = value
        return value

    def teardown(self, closer):
        """Calls closer(value) on context destruction if value was created."""
        def actual_closer(exception):
            value = self._value
            if value is not None:
                closer(value)
        APP.teardown_appcontext(actual_closer)


def local(initializer):
    """Wraps local variable initializer with LocalVariable.

    Example:
    @flaskutil.local
    def mydb():
        return MyDB()

    @mydb.teardown
    def closedb(db):
        db.close()
    """
    return LocalVariable(initializer.__name__, initializer)
