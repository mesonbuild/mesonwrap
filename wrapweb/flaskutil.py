from typing import Any, Callable, Union

import flask
from flask import blueprints

AppOrBlueprint = Union[flask.Flask, blueprints.Blueprint]
Initializer = Callable[[], Any]


class _AppcontextVariable:
    """Wrapper for flask.g cached variables pattern."""

    def __init__(self, app: AppOrBlueprint, name: str, init: Initializer):
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
        """Registers closer.

        Calls closer(value) on context destruction if the value was created.
        """
        def actual_closer(exception):
            del exception  # unused
            value = self._value
            if value is not None:
                closer(value)

        def register_closer(setup: blueprints.BlueprintSetupState):
            setup.app.teardown_appcontext(actual_closer)
        if hasattr(self._app, 'record'):
            self._app.record(register_closer)
        elif hasattr(self._app, 'teardown_appcontext'):
            self._app.teardown_appcontext(actual_closer)
        else:
            raise AttributeError(
                'teardown is not supported by', type(self._app))


def appcontext_var(
    app: AppOrBlueprint, /
) -> Callable[[Initializer], _AppcontextVariable]:
    """Wraps appcontext variable initializer.

    Example:
    @flaskutil.appcontext_var(app)
    def mydb():
        return MyDB()

    @mydb.teardown
    def closedb(db):
        db.close()
    """
    def decorator(initializer: Initializer) -> _AppcontextVariable:
        return _AppcontextVariable(app, initializer.__name__, initializer)
    return decorator
