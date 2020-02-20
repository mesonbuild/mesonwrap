from typing import Any, Callable

import flask


Initializer = Callable[[], Any]


class LocalVariable:
    """Wrapper for flask.g cached variables pattern."""

    def __init__(self, app: flask.Flask, name: str, init: Initializer):
        self._app = app
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
        self._app.teardown_appcontext(actual_closer)


def local(app: flask.Flask) -> Callable[[Initializer], LocalVariable]:
    """Wraps local variable initializer with LocalVariable.

    Example:
    @flaskutil.local(app)
    def mydb():
        return MyDB()

    @mydb.teardown
    def closedb(db):
        db.close()
    """
    def decorator(initializer: Initializer) -> LocalVariable:
        return LocalVariable(app, initializer.__name__, initializer)
    return decorator
