import flask

from wrapweb.app import APP


class WrapWebError(Exception):

    def __init__(self, code: int, message: str):
        super().__init__()
        assert isinstance(code, int)
        assert isinstance(message, str)
        self.status_code = code
        self.message = message

    def to_dict(self):
        return dict(output='notok', error=self.message)


@APP.errorhandler(WrapWebError)
def handle_wrap_web_error(error: WrapWebError):
    jsonout = flask.jsonify(error.to_dict())
    jsonout.status_code = error.status_code
    return jsonout


def ok(**kwargs):
    jsonout = flask.jsonify(dict(output='ok', **kwargs))
    jsonout.status_code = 200
    return jsonout


def error(code, message):
    jsonout = flask.jsonify(dict(output='notok', error=message))
    jsonout.status_code = code
    return jsonout
