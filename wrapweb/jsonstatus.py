from typing import Union

import flask


def init_app(app: Union[flask.Blueprint, flask.Flask]) -> None:
    app.register_error_handler(WrapWebError, handle_wrap_web_error)


class WrapWebError(Exception):

    def __init__(self, code: int, message: str):
        super().__init__()
        assert isinstance(code, int)
        assert isinstance(message, str)
        self.status_code = code
        self.message = message

    def to_dict(self):
        return dict(output='notok', error=self.message)


def handle_wrap_web_error(err: WrapWebError):
    jsonout = flask.jsonify(err.to_dict())
    jsonout.status_code = err.status_code
    return jsonout


def ok(**kwargs):
    jsonout = flask.jsonify(dict(output='ok', **kwargs))
    jsonout.status_code = 200
    return jsonout


def error(code, message):
    jsonout = flask.jsonify(dict(output='notok', error=message))
    jsonout.status_code = code
    return jsonout
